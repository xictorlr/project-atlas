"""Vault compiler package.

Pipeline order:
  1. source_notes         — generate Markdown source notes from ingested sources
  2. summarizer           — LLM-generated 3–5 paragraph summaries per source
  3. meeting_minutes      — structured minutes from audio transcripts (LLM)
  4. entity_extraction    — extract entities and generate entity notes + wikilinks
  5. reference_extractor  — bibliography / citation extraction (LLM)
  6. concept_synthesizer  — cross-source concept articles (LLM)
  7. tracker              — decision log + action item tracker (cross-source)
  8. translator           — EN→ES translation of vault content (LLM, optional)
  9. index_generator      — rebuild index notes (sources-index, entities-index, tags-index)
  10. backlinks           — verify [[wikilinks]] and log broken targets
"""
