---
paths:
  - "services/api/**"
  - "services/worker/**"
  - "packages/shared/**/*.py"
---

# Backend and jobs rules

Make backend work schema-first, retry-safe, and explicit about side effects.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep api handlers work aligned with the product promise.
- Keep domain services work aligned with the product promise.
- Keep job orchestration work aligned with the product promise.
- Keep indexing work aligned with the product promise.
- Keep file IO work aligned with the product promise.
- Keep auth work aligned with the product promise.
- Keep permissions work aligned with the product promise.
- Keep billing hooks work aligned with the product promise.
- Keep exports work aligned with the product promise.
- Keep simulation runs work aligned with the product promise.
- The governing objective is to make backend work schema-first, retry-safe, and explicit about side effects.

## Invariants

- api handlers changes must remain typed.
- api handlers changes must remain idempotent.
- api handlers changes must remain traceable.
- api handlers changes must remain secure.
- api handlers changes must remain least-privilege.
- domain services changes must remain typed.
- domain services changes must remain idempotent.
- domain services changes must remain traceable.
- domain services changes must remain secure.
- domain services changes must remain least-privilege.
- job orchestration changes must remain typed.
- job orchestration changes must remain idempotent.
- job orchestration changes must remain traceable.
- job orchestration changes must remain secure.
- job orchestration changes must remain least-privilege.
- indexing changes must remain typed.
- indexing changes must remain idempotent.
- indexing changes must remain traceable.
- indexing changes must remain secure.
- indexing changes must remain least-privilege.
- file IO changes must remain typed.
- file IO changes must remain idempotent.
- file IO changes must remain traceable.
- file IO changes must remain secure.
- file IO changes must remain least-privilege.
- auth changes must remain typed.
- auth changes must remain idempotent.
- auth changes must remain traceable.
- auth changes must remain secure.
- auth changes must remain least-privilege.
- permissions changes must remain typed.
- permissions changes must remain idempotent.
- permissions changes must remain traceable.
- permissions changes must remain secure.
- permissions changes must remain least-privilege.
- billing hooks changes must remain typed.
- billing hooks changes must remain idempotent.
- billing hooks changes must remain traceable.
- billing hooks changes must remain secure.
- billing hooks changes must remain least-privilege.
- exports changes must remain typed.
- exports changes must remain idempotent.
- exports changes must remain traceable.
- exports changes must remain secure.
- exports changes must remain least-privilege.
- simulation runs changes must remain typed.
- simulation runs changes must remain idempotent.
- simulation runs changes must remain traceable.
- simulation runs changes must remain secure.
- simulation runs changes must remain least-privilege.

## Default decisions

- Prefer to validate each request in a way that is typed.
- Prefer to normalize each response in a way that is idempotent.
- Prefer to enqueue each job in a way that is traceable.
- Prefer to checkpoint each run in a way that is secure.
- Prefer to deduplicate each task in a way that is least-privilege.
- Prefer to timeout each snapshot in a way that is transactional.
- Prefer to backoff each manifest in a way that is retry-aware.
- Prefer to archive each delta in a way that is documented.
- Prefer to notify each workspace in a way that is metricized.
- Prefer to audit each token budget in a way that is rollbackable.

## Workflow guidance

1. Explore the current api handlers implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in api handlers.
1. Change one narrow slice of api handlers at a time unless the task is explicitly architectural.
2. Explore the current domain services implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in domain services.
2. Change one narrow slice of domain services at a time unless the task is explicitly architectural.
3. Explore the current job orchestration implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in job orchestration.
3. Change one narrow slice of job orchestration at a time unless the task is explicitly architectural.
4. Explore the current indexing implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in indexing.
4. Change one narrow slice of indexing at a time unless the task is explicitly architectural.
5. Explore the current file IO implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in file IO.
5. Change one narrow slice of file IO at a time unless the task is explicitly architectural.
6. Explore the current auth implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in auth.
6. Change one narrow slice of auth at a time unless the task is explicitly architectural.
7. Explore the current permissions implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in permissions.
7. Change one narrow slice of permissions at a time unless the task is explicitly architectural.
8. Explore the current billing hooks implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in billing hooks.
8. Change one narrow slice of billing hooks at a time unless the task is explicitly architectural.
9. Explore the current exports implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in exports.
9. Change one narrow slice of exports at a time unless the task is explicitly architectural.
10. Explore the current simulation runs implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in simulation runs.
10. Change one narrow slice of simulation runs at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the api handlers change preserves naming stability, schema clarity, and auditability.
- Confirm the api handlers change has tests or fixtures covering the expected path.
- Confirm the domain services change preserves naming stability, schema clarity, and auditability.
- Confirm the domain services change has tests or fixtures covering the expected path.
- Confirm the job orchestration change preserves naming stability, schema clarity, and auditability.
- Confirm the job orchestration change has tests or fixtures covering the expected path.
- Confirm the indexing change preserves naming stability, schema clarity, and auditability.
- Confirm the indexing change has tests or fixtures covering the expected path.
- Confirm the file IO change preserves naming stability, schema clarity, and auditability.
- Confirm the file IO change has tests or fixtures covering the expected path.
- Confirm the auth change preserves naming stability, schema clarity, and auditability.
- Confirm the auth change has tests or fixtures covering the expected path.
- Confirm the permissions change preserves naming stability, schema clarity, and auditability.
- Confirm the permissions change has tests or fixtures covering the expected path.
- Confirm the billing hooks change preserves naming stability, schema clarity, and auditability.
- Confirm the billing hooks change has tests or fixtures covering the expected path.
- Confirm the exports change preserves naming stability, schema clarity, and auditability.
- Confirm the exports change has tests or fixtures covering the expected path.
- Confirm the simulation runs change preserves naming stability, schema clarity, and auditability.
- Confirm the simulation runs change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the request become an opaque side effect with no manifest or trace.
- Do not let the response become an opaque side effect with no manifest or trace.
- Do not let the job become an opaque side effect with no manifest or trace.
- Do not let the run become an opaque side effect with no manifest or trace.
- Do not let the task become an opaque side effect with no manifest or trace.
- Do not let the snapshot become an opaque side effect with no manifest or trace.
- Do not let the manifest become an opaque side effect with no manifest or trace.
- Do not let the delta become an opaque side effect with no manifest or trace.
- Do not let the workspace become an opaque side effect with no manifest or trace.
- Do not let the token budget become an opaque side effect with no manifest or trace.
- Do not optimize for the ingest source use case in a way that breaks the shared model for everyone else.
- Do not optimize for the compile batch use case in a way that breaks the shared model for everyone else.
- Do not optimize for the reindex workspace use case in a way that breaks the shared model for everyone else.
- Do not optimize for the publish export use case in a way that breaks the shared model for everyone else.
- Do not optimize for the answer generation use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed api handlers change includes code, tests, docs, and operational notes when relevant.
- A completed api handlers change describes risks, rollback path, and follow-up work if incomplete.
- A completed domain services change includes code, tests, docs, and operational notes when relevant.
- A completed domain services change describes risks, rollback path, and follow-up work if incomplete.
- A completed job orchestration change includes code, tests, docs, and operational notes when relevant.
- A completed job orchestration change describes risks, rollback path, and follow-up work if incomplete.
- A completed indexing change includes code, tests, docs, and operational notes when relevant.
- A completed indexing change describes risks, rollback path, and follow-up work if incomplete.
- A completed file IO change includes code, tests, docs, and operational notes when relevant.
- A completed file IO change describes risks, rollback path, and follow-up work if incomplete.
- A completed auth change includes code, tests, docs, and operational notes when relevant.
- A completed auth change describes risks, rollback path, and follow-up work if incomplete.
- A completed permissions change includes code, tests, docs, and operational notes when relevant.
- A completed permissions change describes risks, rollback path, and follow-up work if incomplete.
- A completed billing hooks change includes code, tests, docs, and operational notes when relevant.
- A completed billing hooks change describes risks, rollback path, and follow-up work if incomplete.
- A completed exports change includes code, tests, docs, and operational notes when relevant.
- A completed exports change describes risks, rollback path, and follow-up work if incomplete.
- A completed simulation runs change includes code, tests, docs, and operational notes when relevant.
- A completed simulation runs change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the ingest source workflow through stable APIs and explicit artifacts.
- Example pattern: support the compile batch workflow through stable APIs and explicit artifacts.
- Example pattern: support the reindex workspace workflow through stable APIs and explicit artifacts.
- Example pattern: support the publish export workflow through stable APIs and explicit artifacts.
- Example pattern: support the answer generation workflow through stable APIs and explicit artifacts.
- Example pattern: support the simulation launch workflow through stable APIs and explicit artifacts.
- Example pattern: support the health check run workflow through stable APIs and explicit artifacts.
- Example pattern: expose api handlers state through a typed request record and an append-only event trail.
- Example pattern: expose domain services state through a typed response record and an append-only event trail.
- Example pattern: expose job orchestration state through a typed job record and an append-only event trail.
- Example pattern: expose indexing state through a typed run record and an append-only event trail.
- Example pattern: expose file IO state through a typed task record and an append-only event trail.
- Example pattern: expose auth state through a typed snapshot record and an append-only event trail.
- Example pattern: expose permissions state through a typed manifest record and an append-only event trail.
- Example pattern: expose billing hooks state through a typed delta record and an append-only event trail.
- Example pattern: expose exports state through a typed workspace record and an append-only event trail.
- Example pattern: expose simulation runs state through a typed token budget record and an append-only event trail.

## Implementation prompts

- When implementing api handlers, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing api handlers, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing api handlers, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing domain services, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing domain services, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing domain services, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing job orchestration, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing job orchestration, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing job orchestration, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing indexing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing indexing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing indexing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing file IO, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing file IO, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing file IO, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing auth, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing auth, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing auth, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing permissions, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing permissions, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing permissions, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing billing hooks, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing billing hooks, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing billing hooks, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing exports, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing exports, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing exports, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing simulation runs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing simulation runs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing simulation runs, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of request changes in the domain model or UI.
- Revisit this rule when the meaning of response changes in the domain model or UI.
- Revisit this rule when the meaning of job changes in the domain model or UI.
- Revisit this rule when the meaning of run changes in the domain model or UI.
- Revisit this rule when the meaning of task changes in the domain model or UI.
- Revisit this rule when the meaning of snapshot changes in the domain model or UI.
- Revisit this rule when the meaning of manifest changes in the domain model or UI.
- Revisit this rule when the meaning of delta changes in the domain model or UI.
- Revisit this rule when the meaning of workspace changes in the domain model or UI.
- Revisit this rule when the meaning of token budget changes in the domain model or UI.
- If a change would weaken the typed property, document why and add compensating controls.
- If a change would weaken the idempotent property, document why and add compensating controls.
- If a change would weaken the traceable property, document why and add compensating controls.
- If a change would weaken the secure property, document why and add compensating controls.
- If a change would weaken the least-privilege property, document why and add compensating controls.
- If a change would weaken the transactional property, document why and add compensating controls.
- If a change would weaken the retry-aware property, document why and add compensating controls.
- If a change would weaken the documented property, document why and add compensating controls.
- If a change would weaken the metricized property, document why and add compensating controls.
- If a change would weaken the rollbackable property, document why and add compensating controls.
