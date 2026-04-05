---
paths:
  - "vault/**"
  - "packages/vault/**"
  - "services/worker/**"
---

# Vault and Obsidian rules

Preserve a stable Markdown vault that remains pleasant to browse in Obsidian and safe to sync.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep frontmatter work aligned with the product promise.
- Keep filenames work aligned with the product promise.
- Keep links work aligned with the product promise.
- Keep backlinks work aligned with the product promise.
- Keep embeds work aligned with the product promise.
- Keep images work aligned with the product promise.
- Keep index notes work aligned with the product promise.
- Keep daily notes work aligned with the product promise.
- Keep exports work aligned with the product promise.
- Keep conflict resolution work aligned with the product promise.
- The governing objective is to preserve a stable markdown vault that remains pleasant to browse in obsidian and safe to sync.

## Invariants

- frontmatter changes must remain portable.
- frontmatter changes must remain deterministic.
- frontmatter changes must remain human-readable.
- frontmatter changes must remain obsidian-friendly.
- frontmatter changes must remain stable.
- filenames changes must remain portable.
- filenames changes must remain deterministic.
- filenames changes must remain human-readable.
- filenames changes must remain obsidian-friendly.
- filenames changes must remain stable.
- links changes must remain portable.
- links changes must remain deterministic.
- links changes must remain human-readable.
- links changes must remain obsidian-friendly.
- links changes must remain stable.
- backlinks changes must remain portable.
- backlinks changes must remain deterministic.
- backlinks changes must remain human-readable.
- backlinks changes must remain obsidian-friendly.
- backlinks changes must remain stable.
- embeds changes must remain portable.
- embeds changes must remain deterministic.
- embeds changes must remain human-readable.
- embeds changes must remain obsidian-friendly.
- embeds changes must remain stable.
- images changes must remain portable.
- images changes must remain deterministic.
- images changes must remain human-readable.
- images changes must remain obsidian-friendly.
- images changes must remain stable.
- index notes changes must remain portable.
- index notes changes must remain deterministic.
- index notes changes must remain human-readable.
- index notes changes must remain obsidian-friendly.
- index notes changes must remain stable.
- daily notes changes must remain portable.
- daily notes changes must remain deterministic.
- daily notes changes must remain human-readable.
- daily notes changes must remain obsidian-friendly.
- daily notes changes must remain stable.
- exports changes must remain portable.
- exports changes must remain deterministic.
- exports changes must remain human-readable.
- exports changes must remain obsidian-friendly.
- exports changes must remain stable.
- conflict resolution changes must remain portable.
- conflict resolution changes must remain deterministic.
- conflict resolution changes must remain human-readable.
- conflict resolution changes must remain obsidian-friendly.
- conflict resolution changes must remain stable.

## Default decisions

- Prefer to slugify each note in a way that is portable.
- Prefer to link each folder in a way that is deterministic.
- Prefer to embed each frontmatter field in a way that is human-readable.
- Prefer to namespace each tag in a way that is obsidian-friendly.
- Prefer to preserve each alias in a way that is stable.
- Prefer to merge each backlink in a way that is lossless.
- Prefer to append each index note in a way that is round-trippable.
- Prefer to diff each asset in a way that is asset-safe.
- Prefer to rebuild each attachment in a way that is utf8-safe.
- Prefer to publish each conflict marker in a way that is cacheable.

## Workflow guidance

1. Explore the current frontmatter implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in frontmatter.
1. Change one narrow slice of frontmatter at a time unless the task is explicitly architectural.
2. Explore the current filenames implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in filenames.
2. Change one narrow slice of filenames at a time unless the task is explicitly architectural.
3. Explore the current links implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in links.
3. Change one narrow slice of links at a time unless the task is explicitly architectural.
4. Explore the current backlinks implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in backlinks.
4. Change one narrow slice of backlinks at a time unless the task is explicitly architectural.
5. Explore the current embeds implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in embeds.
5. Change one narrow slice of embeds at a time unless the task is explicitly architectural.
6. Explore the current images implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in images.
6. Change one narrow slice of images at a time unless the task is explicitly architectural.
7. Explore the current index notes implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in index notes.
7. Change one narrow slice of index notes at a time unless the task is explicitly architectural.
8. Explore the current daily notes implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in daily notes.
8. Change one narrow slice of daily notes at a time unless the task is explicitly architectural.
9. Explore the current exports implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in exports.
9. Change one narrow slice of exports at a time unless the task is explicitly architectural.
10. Explore the current conflict resolution implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in conflict resolution.
10. Change one narrow slice of conflict resolution at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the frontmatter change preserves naming stability, schema clarity, and auditability.
- Confirm the frontmatter change has tests or fixtures covering the expected path.
- Confirm the filenames change preserves naming stability, schema clarity, and auditability.
- Confirm the filenames change has tests or fixtures covering the expected path.
- Confirm the links change preserves naming stability, schema clarity, and auditability.
- Confirm the links change has tests or fixtures covering the expected path.
- Confirm the backlinks change preserves naming stability, schema clarity, and auditability.
- Confirm the backlinks change has tests or fixtures covering the expected path.
- Confirm the embeds change preserves naming stability, schema clarity, and auditability.
- Confirm the embeds change has tests or fixtures covering the expected path.
- Confirm the images change preserves naming stability, schema clarity, and auditability.
- Confirm the images change has tests or fixtures covering the expected path.
- Confirm the index notes change preserves naming stability, schema clarity, and auditability.
- Confirm the index notes change has tests or fixtures covering the expected path.
- Confirm the daily notes change preserves naming stability, schema clarity, and auditability.
- Confirm the daily notes change has tests or fixtures covering the expected path.
- Confirm the exports change preserves naming stability, schema clarity, and auditability.
- Confirm the exports change has tests or fixtures covering the expected path.
- Confirm the conflict resolution change preserves naming stability, schema clarity, and auditability.
- Confirm the conflict resolution change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the note become an opaque side effect with no manifest or trace.
- Do not let the folder become an opaque side effect with no manifest or trace.
- Do not let the frontmatter field become an opaque side effect with no manifest or trace.
- Do not let the tag become an opaque side effect with no manifest or trace.
- Do not let the alias become an opaque side effect with no manifest or trace.
- Do not let the backlink become an opaque side effect with no manifest or trace.
- Do not let the index note become an opaque side effect with no manifest or trace.
- Do not let the asset become an opaque side effect with no manifest or trace.
- Do not let the attachment become an opaque side effect with no manifest or trace.
- Do not let the conflict marker become an opaque side effect with no manifest or trace.
- Do not optimize for the source note use case in a way that breaks the shared model for everyone else.
- Do not optimize for the concept article use case in a way that breaks the shared model for everyone else.
- Do not optimize for the entity profile use case in a way that breaks the shared model for everyone else.
- Do not optimize for the report note use case in a way that breaks the shared model for everyone else.
- Do not optimize for the slide deck source use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed frontmatter change includes code, tests, docs, and operational notes when relevant.
- A completed frontmatter change describes risks, rollback path, and follow-up work if incomplete.
- A completed filenames change includes code, tests, docs, and operational notes when relevant.
- A completed filenames change describes risks, rollback path, and follow-up work if incomplete.
- A completed links change includes code, tests, docs, and operational notes when relevant.
- A completed links change describes risks, rollback path, and follow-up work if incomplete.
- A completed backlinks change includes code, tests, docs, and operational notes when relevant.
- A completed backlinks change describes risks, rollback path, and follow-up work if incomplete.
- A completed embeds change includes code, tests, docs, and operational notes when relevant.
- A completed embeds change describes risks, rollback path, and follow-up work if incomplete.
- A completed images change includes code, tests, docs, and operational notes when relevant.
- A completed images change describes risks, rollback path, and follow-up work if incomplete.
- A completed index notes change includes code, tests, docs, and operational notes when relevant.
- A completed index notes change describes risks, rollback path, and follow-up work if incomplete.
- A completed daily notes change includes code, tests, docs, and operational notes when relevant.
- A completed daily notes change describes risks, rollback path, and follow-up work if incomplete.
- A completed exports change includes code, tests, docs, and operational notes when relevant.
- A completed exports change describes risks, rollback path, and follow-up work if incomplete.
- A completed conflict resolution change includes code, tests, docs, and operational notes when relevant.
- A completed conflict resolution change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the source note workflow through stable APIs and explicit artifacts.
- Example pattern: support the concept article workflow through stable APIs and explicit artifacts.
- Example pattern: support the entity profile workflow through stable APIs and explicit artifacts.
- Example pattern: support the report note workflow through stable APIs and explicit artifacts.
- Example pattern: support the slide deck source workflow through stable APIs and explicit artifacts.
- Example pattern: support the simulation report workflow through stable APIs and explicit artifacts.
- Example pattern: support the lint report workflow through stable APIs and explicit artifacts.
- Example pattern: expose frontmatter state through a typed note record and an append-only event trail.
- Example pattern: expose filenames state through a typed folder record and an append-only event trail.
- Example pattern: expose links state through a typed frontmatter field record and an append-only event trail.
- Example pattern: expose backlinks state through a typed tag record and an append-only event trail.
- Example pattern: expose embeds state through a typed alias record and an append-only event trail.
- Example pattern: expose images state through a typed backlink record and an append-only event trail.
- Example pattern: expose index notes state through a typed index note record and an append-only event trail.
- Example pattern: expose daily notes state through a typed asset record and an append-only event trail.
- Example pattern: expose exports state through a typed attachment record and an append-only event trail.
- Example pattern: expose conflict resolution state through a typed conflict marker record and an append-only event trail.

## Implementation prompts

- When implementing frontmatter, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing frontmatter, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing frontmatter, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing filenames, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing filenames, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing filenames, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing links, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing links, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing links, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing backlinks, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing backlinks, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing backlinks, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing embeds, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing embeds, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing embeds, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing images, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing images, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing images, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing index notes, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing index notes, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing index notes, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing daily notes, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing daily notes, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing daily notes, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing exports, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing exports, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing exports, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing conflict resolution, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing conflict resolution, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing conflict resolution, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of note changes in the domain model or UI.
- Revisit this rule when the meaning of folder changes in the domain model or UI.
- Revisit this rule when the meaning of frontmatter field changes in the domain model or UI.
- Revisit this rule when the meaning of tag changes in the domain model or UI.
- Revisit this rule when the meaning of alias changes in the domain model or UI.
- Revisit this rule when the meaning of backlink changes in the domain model or UI.
- Revisit this rule when the meaning of index note changes in the domain model or UI.
- Revisit this rule when the meaning of asset changes in the domain model or UI.
- Revisit this rule when the meaning of attachment changes in the domain model or UI.
- Revisit this rule when the meaning of conflict marker changes in the domain model or UI.
- If a change would weaken the portable property, document why and add compensating controls.
- If a change would weaken the deterministic property, document why and add compensating controls.
- If a change would weaken the human-readable property, document why and add compensating controls.
- If a change would weaken the obsidian-friendly property, document why and add compensating controls.
- If a change would weaken the stable property, document why and add compensating controls.
- If a change would weaken the lossless property, document why and add compensating controls.
- If a change would weaken the round-trippable property, document why and add compensating controls.
- If a change would weaken the asset-safe property, document why and add compensating controls.
- If a change would weaken the utf8-safe property, document why and add compensating controls.
- If a change would weaken the cacheable property, document why and add compensating controls.
