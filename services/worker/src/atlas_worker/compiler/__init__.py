"""Vault compiler package.

Pipeline order:
  1. source_notes    — generate Markdown source notes from ingested sources
  2. entity_extraction — extract entities and generate entity notes + wikilinks
  3. index_generator — rebuild index notes (sources-index, entities-index, tags-index)
  4. backlinks       — verify [[wikilinks]] and log broken targets
"""
