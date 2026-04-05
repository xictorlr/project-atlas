---
paths:
  - "apps/web/**"
  - "packages/ui/**"
---

# Frontend Next.js rules

Keep the UI legible, data-driven, accessible, and aligned with the vault mental model.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep routing work aligned with the product promise.
- Keep layout work aligned with the product promise.
- Keep tables work aligned with the product promise.
- Keep reader work aligned with the product promise.
- Keep workspace dashboard work aligned with the product promise.
- Keep job views work aligned with the product promise.
- Keep search work aligned with the product promise.
- Keep diff review work aligned with the product promise.
- Keep publish UI work aligned with the product promise.
- Keep admin UI work aligned with the product promise.
- The governing objective is to keep the ui legible, data-driven, accessible, and aligned with the vault mental model.

## Invariants

- routing changes must remain accessible.
- routing changes must remain responsive.
- routing changes must remain typed.
- routing changes must remain server-first.
- routing changes must remain cache-aware.
- layout changes must remain accessible.
- layout changes must remain responsive.
- layout changes must remain typed.
- layout changes must remain server-first.
- layout changes must remain cache-aware.
- tables changes must remain accessible.
- tables changes must remain responsive.
- tables changes must remain typed.
- tables changes must remain server-first.
- tables changes must remain cache-aware.
- reader changes must remain accessible.
- reader changes must remain responsive.
- reader changes must remain typed.
- reader changes must remain server-first.
- reader changes must remain cache-aware.
- workspace dashboard changes must remain accessible.
- workspace dashboard changes must remain responsive.
- workspace dashboard changes must remain typed.
- workspace dashboard changes must remain server-first.
- workspace dashboard changes must remain cache-aware.
- job views changes must remain accessible.
- job views changes must remain responsive.
- job views changes must remain typed.
- job views changes must remain server-first.
- job views changes must remain cache-aware.
- search changes must remain accessible.
- search changes must remain responsive.
- search changes must remain typed.
- search changes must remain server-first.
- search changes must remain cache-aware.
- diff review changes must remain accessible.
- diff review changes must remain responsive.
- diff review changes must remain typed.
- diff review changes must remain server-first.
- diff review changes must remain cache-aware.
- publish UI changes must remain accessible.
- publish UI changes must remain responsive.
- publish UI changes must remain typed.
- publish UI changes must remain server-first.
- publish UI changes must remain cache-aware.
- admin UI changes must remain accessible.
- admin UI changes must remain responsive.
- admin UI changes must remain typed.
- admin UI changes must remain server-first.
- admin UI changes must remain cache-aware.

## Default decisions

- Prefer to compose each route in a way that is accessible.
- Prefer to hydrate each component in a way that is responsive.
- Prefer to stream each panel in a way that is typed.
- Prefer to skeletonize each drawer in a way that is server-first.
- Prefer to paginate each timeline in a way that is cache-aware.
- Prefer to filter each table in a way that is suspense-friendly.
- Prefer to memoize each reader view in a way that is keyboard-friendly.
- Prefer to validate each diff card in a way that is state-light.
- Prefer to announce each empty state in a way that is observable.
- Prefer to instrument each mutation flow in a way that is theme-safe.

## Workflow guidance

1. Explore the current routing implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in routing.
1. Change one narrow slice of routing at a time unless the task is explicitly architectural.
2. Explore the current layout implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in layout.
2. Change one narrow slice of layout at a time unless the task is explicitly architectural.
3. Explore the current tables implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in tables.
3. Change one narrow slice of tables at a time unless the task is explicitly architectural.
4. Explore the current reader implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in reader.
4. Change one narrow slice of reader at a time unless the task is explicitly architectural.
5. Explore the current workspace dashboard implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in workspace dashboard.
5. Change one narrow slice of workspace dashboard at a time unless the task is explicitly architectural.
6. Explore the current job views implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in job views.
6. Change one narrow slice of job views at a time unless the task is explicitly architectural.
7. Explore the current search implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in search.
7. Change one narrow slice of search at a time unless the task is explicitly architectural.
8. Explore the current diff review implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in diff review.
8. Change one narrow slice of diff review at a time unless the task is explicitly architectural.
9. Explore the current publish UI implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in publish UI.
9. Change one narrow slice of publish UI at a time unless the task is explicitly architectural.
10. Explore the current admin UI implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in admin UI.
10. Change one narrow slice of admin UI at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the routing change preserves naming stability, schema clarity, and auditability.
- Confirm the routing change has tests or fixtures covering the expected path.
- Confirm the layout change preserves naming stability, schema clarity, and auditability.
- Confirm the layout change has tests or fixtures covering the expected path.
- Confirm the tables change preserves naming stability, schema clarity, and auditability.
- Confirm the tables change has tests or fixtures covering the expected path.
- Confirm the reader change preserves naming stability, schema clarity, and auditability.
- Confirm the reader change has tests or fixtures covering the expected path.
- Confirm the workspace dashboard change preserves naming stability, schema clarity, and auditability.
- Confirm the workspace dashboard change has tests or fixtures covering the expected path.
- Confirm the job views change preserves naming stability, schema clarity, and auditability.
- Confirm the job views change has tests or fixtures covering the expected path.
- Confirm the search change preserves naming stability, schema clarity, and auditability.
- Confirm the search change has tests or fixtures covering the expected path.
- Confirm the diff review change preserves naming stability, schema clarity, and auditability.
- Confirm the diff review change has tests or fixtures covering the expected path.
- Confirm the publish UI change preserves naming stability, schema clarity, and auditability.
- Confirm the publish UI change has tests or fixtures covering the expected path.
- Confirm the admin UI change preserves naming stability, schema clarity, and auditability.
- Confirm the admin UI change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the route become an opaque side effect with no manifest or trace.
- Do not let the component become an opaque side effect with no manifest or trace.
- Do not let the panel become an opaque side effect with no manifest or trace.
- Do not let the drawer become an opaque side effect with no manifest or trace.
- Do not let the timeline become an opaque side effect with no manifest or trace.
- Do not let the table become an opaque side effect with no manifest or trace.
- Do not let the reader view become an opaque side effect with no manifest or trace.
- Do not let the diff card become an opaque side effect with no manifest or trace.
- Do not let the empty state become an opaque side effect with no manifest or trace.
- Do not let the mutation flow become an opaque side effect with no manifest or trace.
- Do not optimize for the source list use case in a way that breaks the shared model for everyone else.
- Do not optimize for the wiki article page use case in a way that breaks the shared model for everyone else.
- Do not optimize for the citation drawer use case in a way that breaks the shared model for everyone else.
- Do not optimize for the job detail page use case in a way that breaks the shared model for everyone else.
- Do not optimize for the answer composer use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed routing change includes code, tests, docs, and operational notes when relevant.
- A completed routing change describes risks, rollback path, and follow-up work if incomplete.
- A completed layout change includes code, tests, docs, and operational notes when relevant.
- A completed layout change describes risks, rollback path, and follow-up work if incomplete.
- A completed tables change includes code, tests, docs, and operational notes when relevant.
- A completed tables change describes risks, rollback path, and follow-up work if incomplete.
- A completed reader change includes code, tests, docs, and operational notes when relevant.
- A completed reader change describes risks, rollback path, and follow-up work if incomplete.
- A completed workspace dashboard change includes code, tests, docs, and operational notes when relevant.
- A completed workspace dashboard change describes risks, rollback path, and follow-up work if incomplete.
- A completed job views change includes code, tests, docs, and operational notes when relevant.
- A completed job views change describes risks, rollback path, and follow-up work if incomplete.
- A completed search change includes code, tests, docs, and operational notes when relevant.
- A completed search change describes risks, rollback path, and follow-up work if incomplete.
- A completed diff review change includes code, tests, docs, and operational notes when relevant.
- A completed diff review change describes risks, rollback path, and follow-up work if incomplete.
- A completed publish UI change includes code, tests, docs, and operational notes when relevant.
- A completed publish UI change describes risks, rollback path, and follow-up work if incomplete.
- A completed admin UI change includes code, tests, docs, and operational notes when relevant.
- A completed admin UI change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the source list workflow through stable APIs and explicit artifacts.
- Example pattern: support the wiki article page workflow through stable APIs and explicit artifacts.
- Example pattern: support the citation drawer workflow through stable APIs and explicit artifacts.
- Example pattern: support the job detail page workflow through stable APIs and explicit artifacts.
- Example pattern: support the answer composer workflow through stable APIs and explicit artifacts.
- Example pattern: support the vault diff inspector workflow through stable APIs and explicit artifacts.
- Example pattern: support the workspace settings workflow through stable APIs and explicit artifacts.
- Example pattern: expose routing state through a typed route record and an append-only event trail.
- Example pattern: expose layout state through a typed component record and an append-only event trail.
- Example pattern: expose tables state through a typed panel record and an append-only event trail.
- Example pattern: expose reader state through a typed drawer record and an append-only event trail.
- Example pattern: expose workspace dashboard state through a typed timeline record and an append-only event trail.
- Example pattern: expose job views state through a typed table record and an append-only event trail.
- Example pattern: expose search state through a typed reader view record and an append-only event trail.
- Example pattern: expose diff review state through a typed diff card record and an append-only event trail.
- Example pattern: expose publish UI state through a typed empty state record and an append-only event trail.
- Example pattern: expose admin UI state through a typed mutation flow record and an append-only event trail.

## Implementation prompts

- When implementing routing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing routing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing routing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing layout, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing layout, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing layout, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing tables, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing tables, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing tables, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing reader, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing reader, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing reader, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing workspace dashboard, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing workspace dashboard, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing workspace dashboard, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing job views, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing job views, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing job views, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing search, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing search, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing search, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing diff review, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing diff review, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing diff review, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing publish UI, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing publish UI, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing publish UI, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing admin UI, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing admin UI, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing admin UI, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of route changes in the domain model or UI.
- Revisit this rule when the meaning of component changes in the domain model or UI.
- Revisit this rule when the meaning of panel changes in the domain model or UI.
- Revisit this rule when the meaning of drawer changes in the domain model or UI.
- Revisit this rule when the meaning of timeline changes in the domain model or UI.
- Revisit this rule when the meaning of table changes in the domain model or UI.
- Revisit this rule when the meaning of reader view changes in the domain model or UI.
- Revisit this rule when the meaning of diff card changes in the domain model or UI.
- Revisit this rule when the meaning of empty state changes in the domain model or UI.
- Revisit this rule when the meaning of mutation flow changes in the domain model or UI.
- If a change would weaken the accessible property, document why and add compensating controls.
- If a change would weaken the responsive property, document why and add compensating controls.
- If a change would weaken the typed property, document why and add compensating controls.
- If a change would weaken the server-first property, document why and add compensating controls.
- If a change would weaken the cache-aware property, document why and add compensating controls.
- If a change would weaken the suspense-friendly property, document why and add compensating controls.
- If a change would weaken the keyboard-friendly property, document why and add compensating controls.
- If a change would weaken the state-light property, document why and add compensating controls.
- If a change would weaken the observable property, document why and add compensating controls.
- If a change would weaken the theme-safe property, document why and add compensating controls.
