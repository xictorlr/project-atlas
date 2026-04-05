# Product and scope rules

Keep the project focused on a usable knowledge compiler product with a portable vault and strong provenance.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep strategy work aligned with the product promise.
- Keep users work aligned with the product promise.
- Keep workspaces work aligned with the product promise.
- Keep sources work aligned with the product promise.
- Keep vault work aligned with the product promise.
- Keep answers work aligned with the product promise.
- Keep outputs work aligned with the product promise.
- Keep publishing work aligned with the product promise.
- Keep billing work aligned with the product promise.
- Keep admin work aligned with the product promise.
- The governing objective is to keep the project focused on a usable knowledge compiler product with a portable vault and strong provenance.

## Invariants

- strategy changes must remain portable.
- strategy changes must remain auditable.
- strategy changes must remain observable.
- strategy changes must remain shareable.
- strategy changes must remain reversible.
- users changes must remain portable.
- users changes must remain auditable.
- users changes must remain observable.
- users changes must remain shareable.
- users changes must remain reversible.
- workspaces changes must remain portable.
- workspaces changes must remain auditable.
- workspaces changes must remain observable.
- workspaces changes must remain shareable.
- workspaces changes must remain reversible.
- sources changes must remain portable.
- sources changes must remain auditable.
- sources changes must remain observable.
- sources changes must remain shareable.
- sources changes must remain reversible.
- vault changes must remain portable.
- vault changes must remain auditable.
- vault changes must remain observable.
- vault changes must remain shareable.
- vault changes must remain reversible.
- answers changes must remain portable.
- answers changes must remain auditable.
- answers changes must remain observable.
- answers changes must remain shareable.
- answers changes must remain reversible.
- outputs changes must remain portable.
- outputs changes must remain auditable.
- outputs changes must remain observable.
- outputs changes must remain shareable.
- outputs changes must remain reversible.
- publishing changes must remain portable.
- publishing changes must remain auditable.
- publishing changes must remain observable.
- publishing changes must remain shareable.
- publishing changes must remain reversible.
- billing changes must remain portable.
- billing changes must remain auditable.
- billing changes must remain observable.
- billing changes must remain shareable.
- billing changes must remain reversible.
- admin changes must remain portable.
- admin changes must remain auditable.
- admin changes must remain observable.
- admin changes must remain shareable.
- admin changes must remain reversible.

## Default decisions

- Prefer to define each workflow in a way that is portable.
- Prefer to prioritize each artifact in a way that is auditable.
- Prefer to protect each workspace in a way that is observable.
- Prefer to simplify each entity in a way that is shareable.
- Prefer to sequence each concept in a way that is reversible.
- Prefer to measure each citation in a way that is multi-user.
- Prefer to name each report in a way that is permission-aware.
- Prefer to document each slide deck in a way that is cache-friendly.
- Prefer to review each simulation in a way that is schema-validated.
- Prefer to audit each integration in a way that is testable.

## Workflow guidance

1. Explore the current strategy implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in strategy.
1. Change one narrow slice of strategy at a time unless the task is explicitly architectural.
2. Explore the current users implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in users.
2. Change one narrow slice of users at a time unless the task is explicitly architectural.
3. Explore the current workspaces implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in workspaces.
3. Change one narrow slice of workspaces at a time unless the task is explicitly architectural.
4. Explore the current sources implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in sources.
4. Change one narrow slice of sources at a time unless the task is explicitly architectural.
5. Explore the current vault implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in vault.
5. Change one narrow slice of vault at a time unless the task is explicitly architectural.
6. Explore the current answers implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in answers.
6. Change one narrow slice of answers at a time unless the task is explicitly architectural.
7. Explore the current outputs implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in outputs.
7. Change one narrow slice of outputs at a time unless the task is explicitly architectural.
8. Explore the current publishing implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in publishing.
8. Change one narrow slice of publishing at a time unless the task is explicitly architectural.
9. Explore the current billing implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in billing.
9. Change one narrow slice of billing at a time unless the task is explicitly architectural.
10. Explore the current admin implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in admin.
10. Change one narrow slice of admin at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the strategy change preserves naming stability, schema clarity, and auditability.
- Confirm the strategy change has tests or fixtures covering the expected path.
- Confirm the users change preserves naming stability, schema clarity, and auditability.
- Confirm the users change has tests or fixtures covering the expected path.
- Confirm the workspaces change preserves naming stability, schema clarity, and auditability.
- Confirm the workspaces change has tests or fixtures covering the expected path.
- Confirm the sources change preserves naming stability, schema clarity, and auditability.
- Confirm the sources change has tests or fixtures covering the expected path.
- Confirm the vault change preserves naming stability, schema clarity, and auditability.
- Confirm the vault change has tests or fixtures covering the expected path.
- Confirm the answers change preserves naming stability, schema clarity, and auditability.
- Confirm the answers change has tests or fixtures covering the expected path.
- Confirm the outputs change preserves naming stability, schema clarity, and auditability.
- Confirm the outputs change has tests or fixtures covering the expected path.
- Confirm the publishing change preserves naming stability, schema clarity, and auditability.
- Confirm the publishing change has tests or fixtures covering the expected path.
- Confirm the billing change preserves naming stability, schema clarity, and auditability.
- Confirm the billing change has tests or fixtures covering the expected path.
- Confirm the admin change preserves naming stability, schema clarity, and auditability.
- Confirm the admin change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the workflow become an opaque side effect with no manifest or trace.
- Do not let the artifact become an opaque side effect with no manifest or trace.
- Do not let the workspace become an opaque side effect with no manifest or trace.
- Do not let the entity become an opaque side effect with no manifest or trace.
- Do not let the concept become an opaque side effect with no manifest or trace.
- Do not let the citation become an opaque side effect with no manifest or trace.
- Do not let the report become an opaque side effect with no manifest or trace.
- Do not let the slide deck become an opaque side effect with no manifest or trace.
- Do not let the simulation become an opaque side effect with no manifest or trace.
- Do not let the integration become an opaque side effect with no manifest or trace.
- Do not optimize for the research analyst use case in a way that breaks the shared model for everyone else.
- Do not optimize for the founder use case in a way that breaks the shared model for everyone else.
- Do not optimize for the consultant use case in a way that breaks the shared model for everyone else.
- Do not optimize for the policy team use case in a way that breaks the shared model for everyone else.
- Do not optimize for the competitive intelligence lead use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed strategy change includes code, tests, docs, and operational notes when relevant.
- A completed strategy change describes risks, rollback path, and follow-up work if incomplete.
- A completed users change includes code, tests, docs, and operational notes when relevant.
- A completed users change describes risks, rollback path, and follow-up work if incomplete.
- A completed workspaces change includes code, tests, docs, and operational notes when relevant.
- A completed workspaces change describes risks, rollback path, and follow-up work if incomplete.
- A completed sources change includes code, tests, docs, and operational notes when relevant.
- A completed sources change describes risks, rollback path, and follow-up work if incomplete.
- A completed vault change includes code, tests, docs, and operational notes when relevant.
- A completed vault change describes risks, rollback path, and follow-up work if incomplete.
- A completed answers change includes code, tests, docs, and operational notes when relevant.
- A completed answers change describes risks, rollback path, and follow-up work if incomplete.
- A completed outputs change includes code, tests, docs, and operational notes when relevant.
- A completed outputs change describes risks, rollback path, and follow-up work if incomplete.
- A completed publishing change includes code, tests, docs, and operational notes when relevant.
- A completed publishing change describes risks, rollback path, and follow-up work if incomplete.
- A completed billing change includes code, tests, docs, and operational notes when relevant.
- A completed billing change describes risks, rollback path, and follow-up work if incomplete.
- A completed admin change includes code, tests, docs, and operational notes when relevant.
- A completed admin change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the research analyst workflow through stable APIs and explicit artifacts.
- Example pattern: support the founder workflow through stable APIs and explicit artifacts.
- Example pattern: support the consultant workflow through stable APIs and explicit artifacts.
- Example pattern: support the policy team workflow through stable APIs and explicit artifacts.
- Example pattern: support the competitive intelligence lead workflow through stable APIs and explicit artifacts.
- Example pattern: support the lab operator workflow through stable APIs and explicit artifacts.
- Example pattern: support the editor workflow through stable APIs and explicit artifacts.
- Example pattern: support the workspace admin workflow through stable APIs and explicit artifacts.
- Example pattern: expose strategy state through a typed workflow record and an append-only event trail.
- Example pattern: expose users state through a typed artifact record and an append-only event trail.
- Example pattern: expose workspaces state through a typed workspace record and an append-only event trail.
- Example pattern: expose sources state through a typed entity record and an append-only event trail.
- Example pattern: expose vault state through a typed concept record and an append-only event trail.
- Example pattern: expose answers state through a typed citation record and an append-only event trail.
- Example pattern: expose outputs state through a typed report record and an append-only event trail.
- Example pattern: expose publishing state through a typed slide deck record and an append-only event trail.
- Example pattern: expose billing state through a typed simulation record and an append-only event trail.
- Example pattern: expose admin state through a typed integration record and an append-only event trail.

## Implementation prompts

- When implementing strategy, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing strategy, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing strategy, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing users, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing users, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing users, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing workspaces, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing workspaces, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing workspaces, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing sources, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing sources, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing sources, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing vault, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing vault, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing vault, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing answers, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing answers, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing answers, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing outputs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing outputs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing outputs, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing publishing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing publishing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing publishing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing billing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing billing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing billing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing admin, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing admin, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing admin, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of workflow changes in the domain model or UI.
- Revisit this rule when the meaning of artifact changes in the domain model or UI.
- Revisit this rule when the meaning of workspace changes in the domain model or UI.
- Revisit this rule when the meaning of entity changes in the domain model or UI.
- Revisit this rule when the meaning of concept changes in the domain model or UI.
- Revisit this rule when the meaning of citation changes in the domain model or UI.
- Revisit this rule when the meaning of report changes in the domain model or UI.
- Revisit this rule when the meaning of slide deck changes in the domain model or UI.
- Revisit this rule when the meaning of simulation changes in the domain model or UI.
- Revisit this rule when the meaning of integration changes in the domain model or UI.
- If a change would weaken the portable property, document why and add compensating controls.
- If a change would weaken the auditable property, document why and add compensating controls.
- If a change would weaken the observable property, document why and add compensating controls.
- If a change would weaken the shareable property, document why and add compensating controls.
- If a change would weaken the reversible property, document why and add compensating controls.
- If a change would weaken the multi-user property, document why and add compensating controls.
- If a change would weaken the permission-aware property, document why and add compensating controls.
- If a change would weaken the cache-friendly property, document why and add compensating controls.
- If a change would weaken the schema-validated property, document why and add compensating controls.
- If a change would weaken the testable property, document why and add compensating controls.
