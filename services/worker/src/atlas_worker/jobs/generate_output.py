"""Output generation job — produces structured Markdown documents from vault knowledge.

Pipeline:
  1. Gather relevant vault context via RAGPipeline.gather_context().
  2. Build prompt from OUTPUT_PROMPTS template + context + user instructions.
  3. Generate via InferenceRouter.
  4. Write to vault/outputs/{kind}-{timestamp}.md with full provenance frontmatter.
  5. Return the note path and generation metadata.

Supported output kinds:
  status_report, client_brief, weekly_digest, risk_register,
  followup_email, custom

Invariants:
  - Every output MUST be grounded via RAG — never generate from empty context.
  - Every output note MUST have full provenance (model, sources, timestamp, generation_time_ms).
  - Re-generating creates a NEW file (timestamp in filename), never overwrites.
  - ctx must contain "router" (InferenceRouter) and "rag" (RAGPipeline).

Failure states:
  - Missing router or rag in ctx: raises KeyError immediately.
  - No context passages found: writes note with "Insufficient data in vault." body.
  - Ollama down: propagates httpx.ConnectError to the caller.
  - Unknown output_kind: raises ValueError.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atlas_worker.inference.prompts import OUTPUT_KINDS, OUTPUT_PROMPTS, OUTPUT_SYSTEM_PROMPT
from atlas_worker.inference.router import InferenceRouter
from atlas_worker.search.rag import RAGPipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vault note writing
# ---------------------------------------------------------------------------

_FRONTMATTER_TEMPLATE = """\
---
title: "{title}"
type: output
output_kind: {output_kind}
workspace_id: {workspace_id}
generated_at: "{generated_at}"
model: "{model}"
generation_time_ms: {generation_time_ms}
sources_consulted: {sources_consulted}
notes_referenced:
{notes_list}
custom_instructions: "{custom_instructions_escaped}"
tags:
  - output/{output_kind}
  - status/generated
---

"""


def _build_frontmatter(
    *,
    title: str,
    output_kind: str,
    workspace_id: str,
    generated_at: str,
    model: str,
    generation_time_ms: int,
    note_slugs: list[str],
    custom_instructions: str,
) -> str:
    notes_lines = "\n".join(f"  - {slug}" for slug in note_slugs) if note_slugs else "  []"
    custom_escaped = custom_instructions.replace('"', '\\"').replace("\n", " ")
    return _FRONTMATTER_TEMPLATE.format(
        title=title.replace('"', '\\"'),
        output_kind=output_kind,
        workspace_id=workspace_id,
        generated_at=generated_at,
        model=model,
        generation_time_ms=generation_time_ms,
        sources_consulted=len(note_slugs),
        notes_list=notes_lines,
        custom_instructions_escaped=custom_escaped,
    )


def _output_title(output_kind: str, generated_at: str) -> str:
    """Human-readable title for the output note."""
    kind_label = output_kind.replace("_", " ").title()
    date_part = generated_at[:10]  # YYYY-MM-DD
    return f"{kind_label} — {date_part}"


def write_output_note(
    *,
    vault_root: Path,
    workspace_id: str,
    output_kind: str,
    content: str,
    model: str,
    generation_time_ms: int,
    note_slugs: list[str],
    custom_instructions: str,
    timestamp: str,
) -> Path:
    """Write output note to vault/outputs/{kind}-{timestamp}.md.

    Always creates a new file (timestamp ensures uniqueness).
    Returns the absolute path to the written file.
    """
    outputs_dir = vault_root / workspace_id / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
    filename = f"{output_kind}-{safe_timestamp}.md"
    note_path = outputs_dir / filename

    title = _output_title(output_kind, timestamp)
    frontmatter = _build_frontmatter(
        title=title,
        output_kind=output_kind,
        workspace_id=workspace_id,
        generated_at=timestamp,
        model=model,
        generation_time_ms=generation_time_ms,
        note_slugs=note_slugs,
        custom_instructions=custom_instructions,
    )

    note_path.write_text(frontmatter + content, encoding="utf-8")
    logger.info(
        "generate_output: wrote %s (%d chars, %d sources)",
        note_path,
        len(content),
        len(note_slugs),
    )
    return note_path


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

_CONTEXT_BLOCK_TEMPLATE = "[{i}] [[{slug}]] {title}\n{passage}"

_EMPTY_CONTEXT_BODY = (
    "Insufficient data in vault.\n\n"
    "No relevant passages were found for this topic. "
    "Ingest and compile more sources before generating this output."
)


def _build_context_block(passages: list) -> str:
    """Format RAG passages as a numbered, cited context block."""
    if not passages:
        return ""
    parts = []
    for i, p in enumerate(passages, start=1):
        title = p.note_title or p.note_slug
        parts.append(_CONTEXT_BLOCK_TEMPLATE.format(
            i=i,
            slug=p.note_slug,
            title=title,
            passage=p.passage,
        ))
    return "\n\n".join(parts)


def _build_output_prompt(output_kind: str, context_block: str, params: dict) -> str:
    """Fill the template for the requested output kind."""
    template = OUTPUT_PROMPTS.get(output_kind, OUTPUT_PROMPTS["custom"])
    custom_instructions = params.get("custom_instructions", params.get("custom_prompt", ""))
    return template.format(
        context=context_block,
        custom_instructions=custom_instructions or "",
    )


# ---------------------------------------------------------------------------
# Job entrypoint
# ---------------------------------------------------------------------------


async def generate_output(
    ctx: dict[str, Any],
    workspace_id: str,
    output_kind: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Generate a structured Markdown output document grounded in vault knowledge.

    Args:
        ctx:          arq context. Required keys: "router" (InferenceRouter),
                      "rag" (RAGPipeline), "vault_root" (Path, optional).
        workspace_id: Tenant workspace UUID.
        output_kind:  One of the supported output kinds (see OUTPUT_KINDS).
        params:       Optional keys:
                      - topic:               override search topic (default: output_kind)
                      - custom_instructions: freeform instructions appended to prompt
                      - custom_prompt:       alias for custom_instructions
                      - max_context_tokens:  RAG budget (default 16000)
                      - temperature:         generation temperature (default 0.3)

    Returns:
        dict with "note_path", "output_kind", "sources_consulted",
        "model", "generation_time_ms", "workspace_id".

    Raises:
        ValueError: if output_kind is not recognised and no custom_prompt provided.
        KeyError:   if "router" or "rag" are missing from ctx.
    """
    if output_kind not in OUTPUT_KINDS and "custom_prompt" not in params and "custom_instructions" not in params:
        raise ValueError(
            f"Unknown output_kind '{output_kind}'. Supported: {sorted(OUTPUT_KINDS)}. "
            "For a custom output pass output_kind='custom' with a 'custom_instructions' param."
        )

    router: InferenceRouter = ctx["router"]
    rag: RAGPipeline = ctx["rag"]
    vault_root: Path = ctx.get("vault_root", Path("vault"))

    topic = params.get("topic", output_kind.replace("_", " "))
    max_context_tokens = params.get("max_context_tokens", 16000)
    temperature = params.get("temperature", 0.3)

    logger.info(
        "generate_output: start workspace=%s kind=%s topic=%r",
        workspace_id,
        output_kind,
        topic,
    )

    start = time.monotonic()
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")

    # 1. Gather vault context.
    passages = await rag.gather_context(
        topic=topic,
        workspace_id=workspace_id,
        max_tokens=max_context_tokens,
    )

    note_slugs = [p.note_slug for p in passages]
    context_block = _build_context_block(passages)

    # 2. Build prompt.
    if not passages:
        logger.warning(
            "generate_output: no context passages found for workspace=%s kind=%s — "
            "output will contain placeholder text",
            workspace_id,
            output_kind,
        )
        content = _EMPTY_CONTEXT_BODY
        model_used = "none"
        generation_time_ms = 0
    else:
        prompt = _build_output_prompt(output_kind, context_block, params)

        # 3. Generate via LLM.
        result = await router.generate(
            prompt=prompt,
            system=OUTPUT_SYSTEM_PROMPT,
            temperature=temperature,
            max_tokens=4096,
        )
        content = result.text
        model_used = result.model

    generation_time_ms = int((time.monotonic() - start) * 1000)

    # 4. Write to vault.
    custom_instructions = params.get("custom_instructions", params.get("custom_prompt", ""))
    note_path = write_output_note(
        vault_root=vault_root,
        workspace_id=workspace_id,
        output_kind=output_kind,
        content=content,
        model=model_used,
        generation_time_ms=generation_time_ms,
        note_slugs=note_slugs,
        custom_instructions=str(custom_instructions),
        timestamp=generated_at,
    )

    logger.info(
        "generate_output: complete workspace=%s kind=%s path=%s sources=%d time=%dms",
        workspace_id,
        output_kind,
        note_path,
        len(note_slugs),
        generation_time_ms,
    )

    return {
        "note_path": str(note_path),
        "output_kind": output_kind,
        "sources_consulted": len(note_slugs),
        "model": model_used,
        "generation_time_ms": generation_time_ms,
        "workspace_id": workspace_id,
        "generated_at": generated_at,
    }
