"""Meeting minutes generator — compiler step 3 (LLM, audio sources only).

Inputs:
  - transcript text (timestamped or plain string from Whisper output)
  - known_entities list (participant names already resolved from entity_extraction)
  - InferenceRouter instance

Outputs:
  - MeetingMinutes dataclass with typed decisions and action items

Failure modes:
  - router.generate() raises → propagated to caller
  - Malformed JSON from LLM → logs warning, returns MeetingMinutes with empty lists
  - Empty transcript raises ValueError before any LLM call
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from atlas_worker.inference.models import GenerateResult
from atlas_worker.inference.prompts import MEETING_MINUTES_PROMPT, SYSTEM_PROMPT
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

# Temperature 0.0 for extraction — deterministic parsing.
_MINUTES_TEMPERATURE = 0.0
_MINUTES_MAX_TOKENS = 4096


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """A concrete decision made during a meeting.

    Attributes:
        description: What was decided.
        made_by:     Name of the person or group that made the decision (nullable).
        context:     Brief context from the transcript explaining why.
        timestamp:   Transcript timestamp string (e.g. "00:14:32") if detectable.
    """

    description: str
    made_by: str | None = None
    context: str = ""
    timestamp: str | None = None


@dataclass(frozen=True)
class ActionItem:
    """A task assigned to a specific owner during a meeting.

    Attributes:
        description:  What needs to be done.
        owner:        Responsible person (nullable if not assigned).
        deadline:     ISO 8601 date string or null.
        priority:     "high" | "medium" | "low".
        status:       "open" | "in_progress" | "done" (default "open" for new items).
        source_quote: Exact quote from the transcript as evidence.
    """

    description: str
    owner: str | None = None
    deadline: str | None = None
    priority: str = "medium"
    status: str = "open"
    source_quote: str = ""


@dataclass(frozen=True)
class MeetingMinutes:
    """Structured meeting minutes extracted from a transcript.

    Attributes:
        title:       Short descriptive title inferred from content.
        date:        ISO 8601 date string if detectable, else empty string.
        attendees:   List of participant names found in the transcript.
        agenda_items: Topics discussed.
        decisions:   Concrete decisions made during the meeting.
        action_items: Tasks assigned to owners.
        next_steps:  Agreed next steps paragraph (may be empty).
        model:       LLM model used for extraction.
    """

    title: str
    date: str
    attendees: list[str]
    agenda_items: list[str]
    decisions: list[Decision]
    action_items: list[ActionItem]
    next_steps: str
    model: str


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------


def _parse_decision(raw: dict) -> Decision:
    return Decision(
        description=str(raw.get("description", "")),
        made_by=raw.get("made_by") or None,
        context=str(raw.get("context", "")),
        timestamp=raw.get("timestamp") or None,
    )


def _parse_action_item(raw: dict) -> ActionItem:
    priority = str(raw.get("priority", "medium")).lower()
    if priority not in ("high", "medium", "low"):
        priority = "medium"
    status = str(raw.get("status", "open")).lower()
    if status not in ("open", "in_progress", "done"):
        status = "open"
    return ActionItem(
        description=str(raw.get("description", "")),
        owner=raw.get("owner") or None,
        deadline=raw.get("deadline") or None,
        priority=priority,
        status=status,
        source_quote=str(raw.get("source_quote", "")),
    )


def _parse_minutes_json(raw_json: str, model: str) -> MeetingMinutes:
    """Parse LLM JSON response into MeetingMinutes.

    Graceful degradation: any malformed or missing field logs a warning and
    falls back to an empty value rather than crashing the pipeline.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.warning("meeting_minutes: malformed JSON from LLM — %s", exc)
        return MeetingMinutes(
            title="",
            date="",
            attendees=[],
            agenda_items=[],
            decisions=[],
            action_items=[],
            next_steps="",
            model=model,
        )

    decisions: list[Decision] = []
    for item in data.get("decisions") or []:
        try:
            decisions.append(_parse_decision(item))
        except Exception as exc:
            logger.warning("meeting_minutes: skipping malformed decision — %s", exc)

    action_items: list[ActionItem] = []
    for item in data.get("action_items") or []:
        try:
            action_items.append(_parse_action_item(item))
        except Exception as exc:
            logger.warning("meeting_minutes: skipping malformed action item — %s", exc)

    return MeetingMinutes(
        title=str(data.get("title", "")),
        date=str(data.get("date") or ""),
        attendees=list(data.get("attendees") or []),
        agenda_items=list(data.get("agenda_items") or []),
        decisions=decisions,
        action_items=action_items,
        next_steps=str(data.get("next_steps") or ""),
        model=model,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_meeting_minutes(
    transcript: str,
    known_entities: list[str],
    router: InferenceRouter,
    *,
    model: str | None = None,
) -> MeetingMinutes:
    """Extract structured meeting minutes from a Whisper transcript.

    Args:
        transcript:     Full transcript text (timestamped or plain).
        known_entities: Participant names from a prior entity extraction pass.
        router:         InferenceRouter for LLM generation.
        model:          Optional model override; uses router default if None.

    Returns:
        MeetingMinutes with typed decisions and action items.
        On malformed LLM output, returns an instance with empty collections
        rather than raising.

    Raises:
        ValueError: If transcript is empty or blank.
    """
    if not transcript or not transcript.strip():
        raise ValueError("generate_meeting_minutes: transcript must not be empty")

    entity_str = ", ".join(known_entities) if known_entities else "(none provided)"
    prompt = MEETING_MINUTES_PROMPT.format(
        transcript=transcript,
        known_entities=entity_str,
    )

    result: GenerateResult = await router.generate(
        prompt,
        system=SYSTEM_PROMPT,
        model=model,
        temperature=_MINUTES_TEMPERATURE,
        max_tokens=_MINUTES_MAX_TOKENS,
        format_json=True,
    )

    minutes = _parse_minutes_json(result.text.strip(), model=result.model)

    logger.info(
        "generate_meeting_minutes: model=%s decisions=%d action_items=%d",
        result.model,
        len(minutes.decisions),
        len(minutes.action_items),
    )

    return minutes
