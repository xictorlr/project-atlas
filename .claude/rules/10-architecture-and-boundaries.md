# Architecture and boundaries rules

Preserve clear service boundaries, deterministic pipelines, and replaceable adapters.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep monorepo work aligned with the product promise.
- Keep api work aligned with the product promise.
- Keep worker work aligned with the product promise.
- Keep storage work aligned with the product promise.
- Keep queue work aligned with the product promise.
- Keep indexing work aligned with the product promise.
- Keep adapters work aligned with the product promise.
- Keep vault sync work aligned with the product promise.
- Keep publishing work aligned with the product promise.
- Keep telemetry work aligned with the product promise.
- The governing objective is to preserve clear service boundaries, deterministic pipelines, and replaceable adapters.

## Invariants

- monorepo changes must remain idempotent.
- monorepo changes must remain bounded.
- monorepo changes must remain documented.
- monorepo changes must remain typed.
- monorepo changes must remain migratable.
- api changes must remain idempotent.
- api changes must remain bounded.
- api changes must remain documented.
- api changes must remain typed.
- api changes must remain migratable.
- worker changes must remain idempotent.
- worker changes must remain bounded.
- worker changes must remain documented.
- worker changes must remain typed.
- worker changes must remain migratable.
- storage changes must remain idempotent.
- storage changes must remain bounded.
- storage changes must remain documented.
- storage changes must remain typed.
- storage changes must remain migratable.
- queue changes must remain idempotent.
- queue changes must remain bounded.
- queue changes must remain documented.
- queue changes must remain typed.
- queue changes must remain migratable.
- indexing changes must remain idempotent.
- indexing changes must remain bounded.
- indexing changes must remain documented.
- indexing changes must remain typed.
- indexing changes must remain migratable.
- adapters changes must remain idempotent.
- adapters changes must remain bounded.
- adapters changes must remain documented.
- adapters changes must remain typed.
- adapters changes must remain migratable.
- vault sync changes must remain idempotent.
- vault sync changes must remain bounded.
- vault sync changes must remain documented.
- vault sync changes must remain typed.
- vault sync changes must remain migratable.
- publishing changes must remain idempotent.
- publishing changes must remain bounded.
- publishing changes must remain documented.
- publishing changes must remain typed.
- publishing changes must remain migratable.
- telemetry changes must remain idempotent.
- telemetry changes must remain bounded.
- telemetry changes must remain documented.
- telemetry changes must remain typed.
- telemetry changes must remain migratable.

## Default decisions

- Prefer to separate each service in a way that is idempotent.
- Prefer to encapsulate each job in a way that is bounded.
- Prefer to version each schema in a way that is documented.
- Prefer to validate each contract in a way that is typed.
- Prefer to queue each adapter in a way that is migratable.
- Prefer to cache each event in a way that is retry-safe.
- Prefer to profile each checkpoint in a way that is resource-aware.
- Prefer to partition each index in a way that is license-aware.
- Prefer to trace each cache in a way that is observable.
- Prefer to gate each artifact in a way that is portable.

## Workflow guidance

1. Explore the current monorepo implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in monorepo.
1. Change one narrow slice of monorepo at a time unless the task is explicitly architectural.
2. Explore the current api implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in api.
2. Change one narrow slice of api at a time unless the task is explicitly architectural.
3. Explore the current worker implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in worker.
3. Change one narrow slice of worker at a time unless the task is explicitly architectural.
4. Explore the current storage implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in storage.
4. Change one narrow slice of storage at a time unless the task is explicitly architectural.
5. Explore the current queue implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in queue.
5. Change one narrow slice of queue at a time unless the task is explicitly architectural.
6. Explore the current indexing implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in indexing.
6. Change one narrow slice of indexing at a time unless the task is explicitly architectural.
7. Explore the current adapters implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in adapters.
7. Change one narrow slice of adapters at a time unless the task is explicitly architectural.
8. Explore the current vault sync implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in vault sync.
8. Change one narrow slice of vault sync at a time unless the task is explicitly architectural.
9. Explore the current publishing implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in publishing.
9. Change one narrow slice of publishing at a time unless the task is explicitly architectural.
10. Explore the current telemetry implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in telemetry.
10. Change one narrow slice of telemetry at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the monorepo change preserves naming stability, schema clarity, and auditability.
- Confirm the monorepo change has tests or fixtures covering the expected path.
- Confirm the api change preserves naming stability, schema clarity, and auditability.
- Confirm the api change has tests or fixtures covering the expected path.
- Confirm the worker change preserves naming stability, schema clarity, and auditability.
- Confirm the worker change has tests or fixtures covering the expected path.
- Confirm the storage change preserves naming stability, schema clarity, and auditability.
- Confirm the storage change has tests or fixtures covering the expected path.
- Confirm the queue change preserves naming stability, schema clarity, and auditability.
- Confirm the queue change has tests or fixtures covering the expected path.
- Confirm the indexing change preserves naming stability, schema clarity, and auditability.
- Confirm the indexing change has tests or fixtures covering the expected path.
- Confirm the adapters change preserves naming stability, schema clarity, and auditability.
- Confirm the adapters change has tests or fixtures covering the expected path.
- Confirm the vault sync change preserves naming stability, schema clarity, and auditability.
- Confirm the vault sync change has tests or fixtures covering the expected path.
- Confirm the publishing change preserves naming stability, schema clarity, and auditability.
- Confirm the publishing change has tests or fixtures covering the expected path.
- Confirm the telemetry change preserves naming stability, schema clarity, and auditability.
- Confirm the telemetry change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the service become an opaque side effect with no manifest or trace.
- Do not let the job become an opaque side effect with no manifest or trace.
- Do not let the schema become an opaque side effect with no manifest or trace.
- Do not let the contract become an opaque side effect with no manifest or trace.
- Do not let the adapter become an opaque side effect with no manifest or trace.
- Do not let the event become an opaque side effect with no manifest or trace.
- Do not let the checkpoint become an opaque side effect with no manifest or trace.
- Do not let the index become an opaque side effect with no manifest or trace.
- Do not let the cache become an opaque side effect with no manifest or trace.
- Do not let the artifact become an opaque side effect with no manifest or trace.
- Do not optimize for the web frontend use case in a way that breaks the shared model for everyone else.
- Do not optimize for the public API use case in a way that breaks the shared model for everyone else.
- Do not optimize for the internal worker API use case in a way that breaks the shared model for everyone else.
- Do not optimize for the search adapter use case in a way that breaks the shared model for everyone else.
- Do not optimize for the deerflow adapter use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed monorepo change includes code, tests, docs, and operational notes when relevant.
- A completed monorepo change describes risks, rollback path, and follow-up work if incomplete.
- A completed api change includes code, tests, docs, and operational notes when relevant.
- A completed api change describes risks, rollback path, and follow-up work if incomplete.
- A completed worker change includes code, tests, docs, and operational notes when relevant.
- A completed worker change describes risks, rollback path, and follow-up work if incomplete.
- A completed storage change includes code, tests, docs, and operational notes when relevant.
- A completed storage change describes risks, rollback path, and follow-up work if incomplete.
- A completed queue change includes code, tests, docs, and operational notes when relevant.
- A completed queue change describes risks, rollback path, and follow-up work if incomplete.
- A completed indexing change includes code, tests, docs, and operational notes when relevant.
- A completed indexing change describes risks, rollback path, and follow-up work if incomplete.
- A completed adapters change includes code, tests, docs, and operational notes when relevant.
- A completed adapters change describes risks, rollback path, and follow-up work if incomplete.
- A completed vault sync change includes code, tests, docs, and operational notes when relevant.
- A completed vault sync change describes risks, rollback path, and follow-up work if incomplete.
- A completed publishing change includes code, tests, docs, and operational notes when relevant.
- A completed publishing change describes risks, rollback path, and follow-up work if incomplete.
- A completed telemetry change includes code, tests, docs, and operational notes when relevant.
- A completed telemetry change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the web frontend workflow through stable APIs and explicit artifacts.
- Example pattern: support the public API workflow through stable APIs and explicit artifacts.
- Example pattern: support the internal worker API workflow through stable APIs and explicit artifacts.
- Example pattern: support the search adapter workflow through stable APIs and explicit artifacts.
- Example pattern: support the deerflow adapter workflow through stable APIs and explicit artifacts.
- Example pattern: support the hermes bridge workflow through stable APIs and explicit artifacts.
- Example pattern: support the mirofish bridge workflow through stable APIs and explicit artifacts.
- Example pattern: support the publish service workflow through stable APIs and explicit artifacts.
- Example pattern: expose monorepo state through a typed service record and an append-only event trail.
- Example pattern: expose api state through a typed job record and an append-only event trail.
- Example pattern: expose worker state through a typed schema record and an append-only event trail.
- Example pattern: expose storage state through a typed contract record and an append-only event trail.
- Example pattern: expose queue state through a typed adapter record and an append-only event trail.
- Example pattern: expose indexing state through a typed event record and an append-only event trail.
- Example pattern: expose adapters state through a typed checkpoint record and an append-only event trail.
- Example pattern: expose vault sync state through a typed index record and an append-only event trail.
- Example pattern: expose publishing state through a typed cache record and an append-only event trail.
- Example pattern: expose telemetry state through a typed artifact record and an append-only event trail.

## Implementation prompts

- When implementing monorepo, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing monorepo, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing monorepo, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing api, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing api, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing api, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing worker, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing worker, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing worker, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing storage, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing storage, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing storage, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing queue, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing queue, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing queue, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing indexing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing indexing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing indexing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing adapters, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing adapters, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing adapters, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing vault sync, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing vault sync, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing vault sync, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing publishing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing publishing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing publishing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing telemetry, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing telemetry, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing telemetry, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of service changes in the domain model or UI.
- Revisit this rule when the meaning of job changes in the domain model or UI.
- Revisit this rule when the meaning of schema changes in the domain model or UI.
- Revisit this rule when the meaning of contract changes in the domain model or UI.
- Revisit this rule when the meaning of adapter changes in the domain model or UI.
- Revisit this rule when the meaning of event changes in the domain model or UI.
- Revisit this rule when the meaning of checkpoint changes in the domain model or UI.
- Revisit this rule when the meaning of index changes in the domain model or UI.
- Revisit this rule when the meaning of cache changes in the domain model or UI.
- Revisit this rule when the meaning of artifact changes in the domain model or UI.
- If a change would weaken the idempotent property, document why and add compensating controls.
- If a change would weaken the bounded property, document why and add compensating controls.
- If a change would weaken the documented property, document why and add compensating controls.
- If a change would weaken the typed property, document why and add compensating controls.
- If a change would weaken the migratable property, document why and add compensating controls.
- If a change would weaken the retry-safe property, document why and add compensating controls.
- If a change would weaken the resource-aware property, document why and add compensating controls.
- If a change would weaken the license-aware property, document why and add compensating controls.
- If a change would weaken the observable property, document why and add compensating controls.
- If a change would weaken the portable property, document why and add compensating controls.
