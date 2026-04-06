"""Prompt templates for all LLM-powered compiler steps.

Inputs:
  - String templates with {placeholder} variables
  - Callers format() the template before passing to InferenceRouter.generate()

Outputs:
  - Formatted prompt strings ready for router.generate()

Temperature guidance (applied at call site, not here):
  - Extraction tasks (JSON):     temperature=0.0 (deterministic)
  - Synthesis tasks (summaries): temperature=0.3 (creative but grounded)

All extraction prompts contain "Do NOT invent" to prevent hallucination.
All synthesis prompts instruct the model to cite sources with [source_id].
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompt — applies to all compiler LLM calls
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a precise knowledge compiler assistant.
Your only job is to extract, summarize, or synthesize information that is
explicitly present in the text you are given.

Rules you must never break:
- Do NOT invent facts, names, dates, or claims not present in the source text.
- Do NOT add context, background, or explanations from your training data.
- Always cite the exact source when asked to provide evidence.
- If the text does not contain the requested information, return an empty result.
- When asked for JSON, respond with valid JSON ONLY — no prose, no code fences.
"""

# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

ENTITY_EXTRACTION_PROMPT = """Extract all named entities from the following text.
For each entity provide:
  - name:        the entity's canonical name as it appears in the text
  - kind:        one of: person | company | project | url | email | location | event | unknown
  - aliases:     list of alternative names or spellings found in the text (may be empty)
  - description: one sentence describing the entity based ONLY on the text
  - evidence:    exact quote from the text that supports this entity

Do NOT invent entities not present in the text.
Respond as a JSON array only. Example format:
[
  {{
    "name": "John Smith",
    "kind": "person",
    "aliases": ["J. Smith"],
    "description": "Lead engineer mentioned in the meeting.",
    "evidence": "John Smith reviewed the API design on Tuesday."
  }}
]

Text:
{text}
"""

# ---------------------------------------------------------------------------
# Source summary
# ---------------------------------------------------------------------------

SUMMARY_PROMPT = """Write a concise summary of the following source text.

Requirements:
- 3 to 5 paragraphs, each focusing on a distinct aspect of the content.
- Every claim must be grounded in the source text.
- Where relevant, reference the source using [source:{source_id}].
- Do NOT add background knowledge not present in the text.
- Use plain Markdown formatting (no code blocks, no tables unless the source uses them).

Source ID: {source_id}

Text:
{text}
"""

# ---------------------------------------------------------------------------
# Meeting minutes
# ---------------------------------------------------------------------------

MEETING_MINUTES_PROMPT = """Extract structured meeting minutes from the following transcript.

Return a single JSON object with these fields:
  - title:           short descriptive title for the meeting (infer from content)
  - date:            ISO 8601 date string if detectable, otherwise null
  - attendees:       list of participant names mentioned in the transcript
  - agenda_items:    list of topics discussed (strings)
  - decisions:       list of objects with fields: description, made_by (nullable), context
  - action_items:    list of objects with fields: description, owner (nullable),
                     deadline (nullable ISO date), priority (high|medium|low),
                     status (open), source_quote (exact quote from transcript)
  - next_steps:      short paragraph describing agreed next steps, or empty string

Known participants (use these spellings when they appear): {known_entities}

Do NOT invent decisions or action items not explicitly stated in the transcript.
Do NOT add action items that are merely mentioned, only those explicitly assigned.
Respond with valid JSON only.

Transcript:
{transcript}
"""

# ---------------------------------------------------------------------------
# Reference / bibliography extraction
# ---------------------------------------------------------------------------

REFERENCE_EXTRACTION_PROMPT = """Extract all academic, book, article, and web references
cited or mentioned in the following text.

For each reference provide:
  - title:    full title of the work
  - authors:  list of author names (may be empty)
  - year:     publication year as integer, or null if unknown
  - ref_type: one of: book | article | website | report | paper | other
  - context:  one sentence explaining how this reference is used in the text

Do NOT invent references not explicitly present in the text.
Respond as a JSON array only.

Text:
{text}
"""

# ---------------------------------------------------------------------------
# Concept synthesis (cross-source)
# ---------------------------------------------------------------------------

CONCEPT_SYNTHESIS_PROMPT = """Write a structured concept article that synthesizes
information about "{concept_name}" from the provided sources.

Requirements:
- Start with a one-paragraph definition based only on the source material.
- Follow with sections that explore different aspects found across the sources.
- Cite sources inline using [source:{source_id}] notation.
- Use second-level Markdown headings (##) for each section.
- Include a "## Contradictions or Gaps" section if the sources disagree or leave
  important questions unanswered.
- Do NOT add background knowledge from outside the provided sources.

Related entities to link (use [[entities/{slug}]] wikilinks where relevant):
{entity_list}

Sources:
{sources_block}
"""

# ---------------------------------------------------------------------------
# Translation (EN → target language)
# ---------------------------------------------------------------------------

TRANSLATION_PROMPT = """Translate the following text from {source_language} to {target_language}.

Requirements:
- Preserve all Markdown formatting (headings, bullet points, bold, italics, links).
- Preserve all wikilinks [[like this]] and frontmatter keys unchanged.
- Preserve technical terms and proper nouns in their original form unless a
  widely accepted translation exists in {target_language}.
- Preserve timestamps in [HH:MM:SS] format unchanged.
- Do NOT add explanations, annotations, or translator notes.

Text:
{text}
"""

# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------

CONTRADICTION_DETECTION_PROMPT = """Analyse the following source excerpts and identify
any contradictory or conflicting claims between them.

For each contradiction provide a JSON object with:
  - claim_a:     the first claim (exact quote or close paraphrase)
  - source_a:    source_id of the first claim
  - claim_b:     the conflicting claim (exact quote or close paraphrase)
  - source_b:    source_id of the second claim
  - topic:       one-word or short phrase naming the topic in dispute
  - severity:    one of: critical | significant | minor

Only report genuine contradictions — differences in emphasis or perspective
that do not actually conflict should be omitted.
Respond as a JSON array only. Return [] if no contradictions found.

Sources:
{sources_block}
"""
