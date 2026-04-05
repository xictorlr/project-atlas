---
paths:
  - "services/api/**"
  - "services/worker/**"
  - "packages/search/**"
  - "packages/prompts/**"
---

# Search and answering rules

Make retrieval and answering transparent, citation-backed, and tunable without trapping knowledge in opaque chat state.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep query parsing work aligned with the product promise.
- Keep search ranking work aligned with the product promise.
- Keep citation assembly work aligned with the product promise.
- Keep answer plans work aligned with the product promise.
- Keep evidence packs work aligned with the product promise.
- Keep report generation work aligned with the product promise.
- Keep slide generation work aligned with the product promise.
- Keep follow-up questions work aligned with the product promise.
- Keep cache work aligned with the product promise.
- Keep evaluation work aligned with the product promise.
- The governing objective is to make retrieval and answering transparent, citation-backed, and tunable without trapping knowledge in opaque chat state.

## Invariants

- query parsing changes must remain grounded.
- query parsing changes must remain non-fabricated.
- query parsing changes must remain source-attributed.
- query parsing changes must remain user-visible.
- query parsing changes must remain auditable.
- search ranking changes must remain grounded.
- search ranking changes must remain non-fabricated.
- search ranking changes must remain source-attributed.
- search ranking changes must remain user-visible.
- search ranking changes must remain auditable.
- citation assembly changes must remain grounded.
- citation assembly changes must remain non-fabricated.
- citation assembly changes must remain source-attributed.
- citation assembly changes must remain user-visible.
- citation assembly changes must remain auditable.
- answer plans changes must remain grounded.
- answer plans changes must remain non-fabricated.
- answer plans changes must remain source-attributed.
- answer plans changes must remain user-visible.
- answer plans changes must remain auditable.
- evidence packs changes must remain grounded.
- evidence packs changes must remain non-fabricated.
- evidence packs changes must remain source-attributed.
- evidence packs changes must remain user-visible.
- evidence packs changes must remain auditable.
- report generation changes must remain grounded.
- report generation changes must remain non-fabricated.
- report generation changes must remain source-attributed.
- report generation changes must remain user-visible.
- report generation changes must remain auditable.
- slide generation changes must remain grounded.
- slide generation changes must remain non-fabricated.
- slide generation changes must remain source-attributed.
- slide generation changes must remain user-visible.
- slide generation changes must remain auditable.
- follow-up questions changes must remain grounded.
- follow-up questions changes must remain non-fabricated.
- follow-up questions changes must remain source-attributed.
- follow-up questions changes must remain user-visible.
- follow-up questions changes must remain auditable.
- cache changes must remain grounded.
- cache changes must remain non-fabricated.
- cache changes must remain source-attributed.
- cache changes must remain user-visible.
- cache changes must remain auditable.
- evaluation changes must remain grounded.
- evaluation changes must remain non-fabricated.
- evaluation changes must remain source-attributed.
- evaluation changes must remain user-visible.
- evaluation changes must remain auditable.

## Default decisions

- Prefer to ground each query in a way that is grounded.
- Prefer to cite each result set in a way that is non-fabricated.
- Prefer to re-rank each evidence chunk in a way that is source-attributed.
- Prefer to cluster each citation in a way that is user-visible.
- Prefer to summarize each answer in a way that is auditable.
- Prefer to compare each brief in a way that is reproducible.
- Prefer to quote each deck in a way that is cache-aware.
- Prefer to attribute each view model in a way that is latency-bounded.
- Prefer to cache each quality score in a way that is eval-driven.
- Prefer to score each coverage score in a way that is opt-in web-aware.

## Workflow guidance

1. Explore the current query parsing implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in query parsing.
1. Change one narrow slice of query parsing at a time unless the task is explicitly architectural.
2. Explore the current search ranking implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in search ranking.
2. Change one narrow slice of search ranking at a time unless the task is explicitly architectural.
3. Explore the current citation assembly implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in citation assembly.
3. Change one narrow slice of citation assembly at a time unless the task is explicitly architectural.
4. Explore the current answer plans implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in answer plans.
4. Change one narrow slice of answer plans at a time unless the task is explicitly architectural.
5. Explore the current evidence packs implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in evidence packs.
5. Change one narrow slice of evidence packs at a time unless the task is explicitly architectural.
6. Explore the current report generation implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in report generation.
6. Change one narrow slice of report generation at a time unless the task is explicitly architectural.
7. Explore the current slide generation implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in slide generation.
7. Change one narrow slice of slide generation at a time unless the task is explicitly architectural.
8. Explore the current follow-up questions implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in follow-up questions.
8. Change one narrow slice of follow-up questions at a time unless the task is explicitly architectural.
9. Explore the current cache implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in cache.
9. Change one narrow slice of cache at a time unless the task is explicitly architectural.
10. Explore the current evaluation implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in evaluation.
10. Change one narrow slice of evaluation at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the query parsing change preserves naming stability, schema clarity, and auditability.
- Confirm the query parsing change has tests or fixtures covering the expected path.
- Confirm the search ranking change preserves naming stability, schema clarity, and auditability.
- Confirm the search ranking change has tests or fixtures covering the expected path.
- Confirm the citation assembly change preserves naming stability, schema clarity, and auditability.
- Confirm the citation assembly change has tests or fixtures covering the expected path.
- Confirm the answer plans change preserves naming stability, schema clarity, and auditability.
- Confirm the answer plans change has tests or fixtures covering the expected path.
- Confirm the evidence packs change preserves naming stability, schema clarity, and auditability.
- Confirm the evidence packs change has tests or fixtures covering the expected path.
- Confirm the report generation change preserves naming stability, schema clarity, and auditability.
- Confirm the report generation change has tests or fixtures covering the expected path.
- Confirm the slide generation change preserves naming stability, schema clarity, and auditability.
- Confirm the slide generation change has tests or fixtures covering the expected path.
- Confirm the follow-up questions change preserves naming stability, schema clarity, and auditability.
- Confirm the follow-up questions change has tests or fixtures covering the expected path.
- Confirm the cache change preserves naming stability, schema clarity, and auditability.
- Confirm the cache change has tests or fixtures covering the expected path.
- Confirm the evaluation change preserves naming stability, schema clarity, and auditability.
- Confirm the evaluation change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the query become an opaque side effect with no manifest or trace.
- Do not let the result set become an opaque side effect with no manifest or trace.
- Do not let the evidence chunk become an opaque side effect with no manifest or trace.
- Do not let the citation become an opaque side effect with no manifest or trace.
- Do not let the answer become an opaque side effect with no manifest or trace.
- Do not let the brief become an opaque side effect with no manifest or trace.
- Do not let the deck become an opaque side effect with no manifest or trace.
- Do not let the view model become an opaque side effect with no manifest or trace.
- Do not let the quality score become an opaque side effect with no manifest or trace.
- Do not let the coverage score become an opaque side effect with no manifest or trace.
- Do not optimize for the workspace question use case in a way that breaks the shared model for everyone else.
- Do not optimize for the compare two sources use case in a way that breaks the shared model for everyone else.
- Do not optimize for the timeline synthesis use case in a way that breaks the shared model for everyone else.
- Do not optimize for the contradiction report use case in a way that breaks the shared model for everyone else.
- Do not optimize for the executive brief use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed query parsing change includes code, tests, docs, and operational notes when relevant.
- A completed query parsing change describes risks, rollback path, and follow-up work if incomplete.
- A completed search ranking change includes code, tests, docs, and operational notes when relevant.
- A completed search ranking change describes risks, rollback path, and follow-up work if incomplete.
- A completed citation assembly change includes code, tests, docs, and operational notes when relevant.
- A completed citation assembly change describes risks, rollback path, and follow-up work if incomplete.
- A completed answer plans change includes code, tests, docs, and operational notes when relevant.
- A completed answer plans change describes risks, rollback path, and follow-up work if incomplete.
- A completed evidence packs change includes code, tests, docs, and operational notes when relevant.
- A completed evidence packs change describes risks, rollback path, and follow-up work if incomplete.
- A completed report generation change includes code, tests, docs, and operational notes when relevant.
- A completed report generation change describes risks, rollback path, and follow-up work if incomplete.
- A completed slide generation change includes code, tests, docs, and operational notes when relevant.
- A completed slide generation change describes risks, rollback path, and follow-up work if incomplete.
- A completed follow-up questions change includes code, tests, docs, and operational notes when relevant.
- A completed follow-up questions change describes risks, rollback path, and follow-up work if incomplete.
- A completed cache change includes code, tests, docs, and operational notes when relevant.
- A completed cache change describes risks, rollback path, and follow-up work if incomplete.
- A completed evaluation change includes code, tests, docs, and operational notes when relevant.
- A completed evaluation change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the workspace question workflow through stable APIs and explicit artifacts.
- Example pattern: support the compare two sources workflow through stable APIs and explicit artifacts.
- Example pattern: support the timeline synthesis workflow through stable APIs and explicit artifacts.
- Example pattern: support the contradiction report workflow through stable APIs and explicit artifacts.
- Example pattern: support the executive brief workflow through stable APIs and explicit artifacts.
- Example pattern: support the slide outline workflow through stable APIs and explicit artifacts.
- Example pattern: expose query parsing state through a typed query record and an append-only event trail.
- Example pattern: expose search ranking state through a typed result set record and an append-only event trail.
- Example pattern: expose citation assembly state through a typed evidence chunk record and an append-only event trail.
- Example pattern: expose answer plans state through a typed citation record and an append-only event trail.
- Example pattern: expose evidence packs state through a typed answer record and an append-only event trail.
- Example pattern: expose report generation state through a typed brief record and an append-only event trail.
- Example pattern: expose slide generation state through a typed deck record and an append-only event trail.
- Example pattern: expose follow-up questions state through a typed view model record and an append-only event trail.
- Example pattern: expose cache state through a typed quality score record and an append-only event trail.
- Example pattern: expose evaluation state through a typed coverage score record and an append-only event trail.

## Implementation prompts

- When implementing query parsing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing query parsing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing query parsing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing search ranking, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing search ranking, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing search ranking, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing citation assembly, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing citation assembly, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing citation assembly, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing answer plans, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing answer plans, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing answer plans, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing evidence packs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing evidence packs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing evidence packs, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing report generation, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing report generation, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing report generation, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing slide generation, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing slide generation, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing slide generation, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing follow-up questions, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing follow-up questions, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing follow-up questions, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing cache, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing cache, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing cache, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing evaluation, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing evaluation, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing evaluation, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of query changes in the domain model or UI.
- Revisit this rule when the meaning of result set changes in the domain model or UI.
- Revisit this rule when the meaning of evidence chunk changes in the domain model or UI.
- Revisit this rule when the meaning of citation changes in the domain model or UI.
- Revisit this rule when the meaning of answer changes in the domain model or UI.
- Revisit this rule when the meaning of brief changes in the domain model or UI.
- Revisit this rule when the meaning of deck changes in the domain model or UI.
- Revisit this rule when the meaning of view model changes in the domain model or UI.
- Revisit this rule when the meaning of quality score changes in the domain model or UI.
- Revisit this rule when the meaning of coverage score changes in the domain model or UI.
- If a change would weaken the grounded property, document why and add compensating controls.
- If a change would weaken the non-fabricated property, document why and add compensating controls.
- If a change would weaken the source-attributed property, document why and add compensating controls.
- If a change would weaken the user-visible property, document why and add compensating controls.
- If a change would weaken the auditable property, document why and add compensating controls.
- If a change would weaken the reproducible property, document why and add compensating controls.
- If a change would weaken the cache-aware property, document why and add compensating controls.
- If a change would weaken the latency-bounded property, document why and add compensating controls.
- If a change would weaken the eval-driven property, document why and add compensating controls.
- If a change would weaken the opt-in web-aware property, document why and add compensating controls.
