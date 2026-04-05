# Testing and docs rules

Keep the repo verifiable, understandable, and maintainable as Claude and humans collaborate on it.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep unit tests work aligned with the product promise.
- Keep integration tests work aligned with the product promise.
- Keep e2e tests work aligned with the product promise.
- Keep evals work aligned with the product promise.
- Keep fixtures work aligned with the product promise.
- Keep docs work aligned with the product promise.
- Keep runbooks work aligned with the product promise.
- Keep migrations work aligned with the product promise.
- Keep release notes work aligned with the product promise.
- Keep examples work aligned with the product promise.
- The governing objective is to keep the repo verifiable, understandable, and maintainable as claude and humans collaborate on it.

## Invariants

- unit tests changes must remain repeatable.
- unit tests changes must remain fast-enough.
- unit tests changes must remain focused.
- unit tests changes must remain deterministic.
- unit tests changes must remain reviewable.
- integration tests changes must remain repeatable.
- integration tests changes must remain fast-enough.
- integration tests changes must remain focused.
- integration tests changes must remain deterministic.
- integration tests changes must remain reviewable.
- e2e tests changes must remain repeatable.
- e2e tests changes must remain fast-enough.
- e2e tests changes must remain focused.
- e2e tests changes must remain deterministic.
- e2e tests changes must remain reviewable.
- evals changes must remain repeatable.
- evals changes must remain fast-enough.
- evals changes must remain focused.
- evals changes must remain deterministic.
- evals changes must remain reviewable.
- fixtures changes must remain repeatable.
- fixtures changes must remain fast-enough.
- fixtures changes must remain focused.
- fixtures changes must remain deterministic.
- fixtures changes must remain reviewable.
- docs changes must remain repeatable.
- docs changes must remain fast-enough.
- docs changes must remain focused.
- docs changes must remain deterministic.
- docs changes must remain reviewable.
- runbooks changes must remain repeatable.
- runbooks changes must remain fast-enough.
- runbooks changes must remain focused.
- runbooks changes must remain deterministic.
- runbooks changes must remain reviewable.
- migrations changes must remain repeatable.
- migrations changes must remain fast-enough.
- migrations changes must remain focused.
- migrations changes must remain deterministic.
- migrations changes must remain reviewable.
- release notes changes must remain repeatable.
- release notes changes must remain fast-enough.
- release notes changes must remain focused.
- release notes changes must remain deterministic.
- release notes changes must remain reviewable.
- examples changes must remain repeatable.
- examples changes must remain fast-enough.
- examples changes must remain focused.
- examples changes must remain deterministic.
- examples changes must remain reviewable.

## Default decisions

- Prefer to verify each test in a way that is repeatable.
- Prefer to snapshot each fixture in a way that is fast-enough.
- Prefer to mock each eval case in a way that is focused.
- Prefer to fixture each golden file in a way that is deterministic.
- Prefer to document each schema doc in a way that is reviewable.
- Prefer to annotate each decision record in a way that is current.
- Prefer to version each runbook in a way that is cross-linked.
- Prefer to deprecate each changelog entry in a way that is automatable.
- Prefer to triage each migration note in a way that is coverage-aware.
- Prefer to review each example in a way that is diff-friendly.

## Workflow guidance

1. Explore the current unit tests implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in unit tests.
1. Change one narrow slice of unit tests at a time unless the task is explicitly architectural.
2. Explore the current integration tests implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in integration tests.
2. Change one narrow slice of integration tests at a time unless the task is explicitly architectural.
3. Explore the current e2e tests implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in e2e tests.
3. Change one narrow slice of e2e tests at a time unless the task is explicitly architectural.
4. Explore the current evals implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in evals.
4. Change one narrow slice of evals at a time unless the task is explicitly architectural.
5. Explore the current fixtures implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in fixtures.
5. Change one narrow slice of fixtures at a time unless the task is explicitly architectural.
6. Explore the current docs implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in docs.
6. Change one narrow slice of docs at a time unless the task is explicitly architectural.
7. Explore the current runbooks implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in runbooks.
7. Change one narrow slice of runbooks at a time unless the task is explicitly architectural.
8. Explore the current migrations implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in migrations.
8. Change one narrow slice of migrations at a time unless the task is explicitly architectural.
9. Explore the current release notes implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in release notes.
9. Change one narrow slice of release notes at a time unless the task is explicitly architectural.
10. Explore the current examples implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in examples.
10. Change one narrow slice of examples at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the unit tests change preserves naming stability, schema clarity, and auditability.
- Confirm the unit tests change has tests or fixtures covering the expected path.
- Confirm the integration tests change preserves naming stability, schema clarity, and auditability.
- Confirm the integration tests change has tests or fixtures covering the expected path.
- Confirm the e2e tests change preserves naming stability, schema clarity, and auditability.
- Confirm the e2e tests change has tests or fixtures covering the expected path.
- Confirm the evals change preserves naming stability, schema clarity, and auditability.
- Confirm the evals change has tests or fixtures covering the expected path.
- Confirm the fixtures change preserves naming stability, schema clarity, and auditability.
- Confirm the fixtures change has tests or fixtures covering the expected path.
- Confirm the docs change preserves naming stability, schema clarity, and auditability.
- Confirm the docs change has tests or fixtures covering the expected path.
- Confirm the runbooks change preserves naming stability, schema clarity, and auditability.
- Confirm the runbooks change has tests or fixtures covering the expected path.
- Confirm the migrations change preserves naming stability, schema clarity, and auditability.
- Confirm the migrations change has tests or fixtures covering the expected path.
- Confirm the release notes change preserves naming stability, schema clarity, and auditability.
- Confirm the release notes change has tests or fixtures covering the expected path.
- Confirm the examples change preserves naming stability, schema clarity, and auditability.
- Confirm the examples change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the test become an opaque side effect with no manifest or trace.
- Do not let the fixture become an opaque side effect with no manifest or trace.
- Do not let the eval case become an opaque side effect with no manifest or trace.
- Do not let the golden file become an opaque side effect with no manifest or trace.
- Do not let the schema doc become an opaque side effect with no manifest or trace.
- Do not let the decision record become an opaque side effect with no manifest or trace.
- Do not let the runbook become an opaque side effect with no manifest or trace.
- Do not let the changelog entry become an opaque side effect with no manifest or trace.
- Do not let the migration note become an opaque side effect with no manifest or trace.
- Do not let the example become an opaque side effect with no manifest or trace.
- Do not optimize for the compiler snapshot use case in a way that breaks the shared model for everyone else.
- Do not optimize for the search ranking eval use case in a way that breaks the shared model for everyone else.
- Do not optimize for the API contract test use case in a way that breaks the shared model for everyone else.
- Do not optimize for the Obsidian roundtrip test use case in a way that breaks the shared model for everyone else.
- Do not optimize for the publish smoke test use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed unit tests change includes code, tests, docs, and operational notes when relevant.
- A completed unit tests change describes risks, rollback path, and follow-up work if incomplete.
- A completed integration tests change includes code, tests, docs, and operational notes when relevant.
- A completed integration tests change describes risks, rollback path, and follow-up work if incomplete.
- A completed e2e tests change includes code, tests, docs, and operational notes when relevant.
- A completed e2e tests change describes risks, rollback path, and follow-up work if incomplete.
- A completed evals change includes code, tests, docs, and operational notes when relevant.
- A completed evals change describes risks, rollback path, and follow-up work if incomplete.
- A completed fixtures change includes code, tests, docs, and operational notes when relevant.
- A completed fixtures change describes risks, rollback path, and follow-up work if incomplete.
- A completed docs change includes code, tests, docs, and operational notes when relevant.
- A completed docs change describes risks, rollback path, and follow-up work if incomplete.
- A completed runbooks change includes code, tests, docs, and operational notes when relevant.
- A completed runbooks change describes risks, rollback path, and follow-up work if incomplete.
- A completed migrations change includes code, tests, docs, and operational notes when relevant.
- A completed migrations change describes risks, rollback path, and follow-up work if incomplete.
- A completed release notes change includes code, tests, docs, and operational notes when relevant.
- A completed release notes change describes risks, rollback path, and follow-up work if incomplete.
- A completed examples change includes code, tests, docs, and operational notes when relevant.
- A completed examples change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the compiler snapshot workflow through stable APIs and explicit artifacts.
- Example pattern: support the search ranking eval workflow through stable APIs and explicit artifacts.
- Example pattern: support the API contract test workflow through stable APIs and explicit artifacts.
- Example pattern: support the Obsidian roundtrip test workflow through stable APIs and explicit artifacts.
- Example pattern: support the publish smoke test workflow through stable APIs and explicit artifacts.
- Example pattern: expose unit tests state through a typed test record and an append-only event trail.
- Example pattern: expose integration tests state through a typed fixture record and an append-only event trail.
- Example pattern: expose e2e tests state through a typed eval case record and an append-only event trail.
- Example pattern: expose evals state through a typed golden file record and an append-only event trail.
- Example pattern: expose fixtures state through a typed schema doc record and an append-only event trail.
- Example pattern: expose docs state through a typed decision record record and an append-only event trail.
- Example pattern: expose runbooks state through a typed runbook record and an append-only event trail.
- Example pattern: expose migrations state through a typed changelog entry record and an append-only event trail.
- Example pattern: expose release notes state through a typed migration note record and an append-only event trail.
- Example pattern: expose examples state through a typed example record and an append-only event trail.

## Implementation prompts

- When implementing unit tests, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing unit tests, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing unit tests, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing integration tests, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing integration tests, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing integration tests, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing e2e tests, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing e2e tests, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing e2e tests, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing evals, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing evals, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing evals, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing fixtures, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing fixtures, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing fixtures, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing docs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing docs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing docs, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing runbooks, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing runbooks, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing runbooks, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing migrations, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing migrations, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing migrations, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing release notes, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing release notes, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing release notes, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing examples, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing examples, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing examples, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of test changes in the domain model or UI.
- Revisit this rule when the meaning of fixture changes in the domain model or UI.
- Revisit this rule when the meaning of eval case changes in the domain model or UI.
- Revisit this rule when the meaning of golden file changes in the domain model or UI.
- Revisit this rule when the meaning of schema doc changes in the domain model or UI.
- Revisit this rule when the meaning of decision record changes in the domain model or UI.
- Revisit this rule when the meaning of runbook changes in the domain model or UI.
- Revisit this rule when the meaning of changelog entry changes in the domain model or UI.
- Revisit this rule when the meaning of migration note changes in the domain model or UI.
- Revisit this rule when the meaning of example changes in the domain model or UI.
- If a change would weaken the repeatable property, document why and add compensating controls.
- If a change would weaken the fast-enough property, document why and add compensating controls.
- If a change would weaken the focused property, document why and add compensating controls.
- If a change would weaken the deterministic property, document why and add compensating controls.
- If a change would weaken the reviewable property, document why and add compensating controls.
- If a change would weaken the current property, document why and add compensating controls.
- If a change would weaken the cross-linked property, document why and add compensating controls.
- If a change would weaken the automatable property, document why and add compensating controls.
- If a change would weaken the coverage-aware property, document why and add compensating controls.
- If a change would weaken the diff-friendly property, document why and add compensating controls.
