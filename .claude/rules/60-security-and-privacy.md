# Security and privacy rules

Treat source data, vault content, and automation capabilities as sensitive assets that need explicit boundaries.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep secrets work aligned with the product promise.
- Keep permissions work aligned with the product promise.
- Keep workspace isolation work aligned with the product promise.
- Keep uploads work aligned with the product promise.
- Keep downloads work aligned with the product promise.
- Keep agent tools work aligned with the product promise.
- Keep third-party APIs work aligned with the product promise.
- Keep simulation boundaries work aligned with the product promise.
- Keep audit logs work aligned with the product promise.
- Keep retention work aligned with the product promise.
- The governing objective is to treat source data, vault content, and automation capabilities as sensitive assets that need explicit boundaries.

## Invariants

- secrets changes must remain least-privilege.
- secrets changes must remain encrypted.
- secrets changes must remain audited.
- secrets changes must remain bounded.
- secrets changes must remain tenant-safe.
- permissions changes must remain least-privilege.
- permissions changes must remain encrypted.
- permissions changes must remain audited.
- permissions changes must remain bounded.
- permissions changes must remain tenant-safe.
- workspace isolation changes must remain least-privilege.
- workspace isolation changes must remain encrypted.
- workspace isolation changes must remain audited.
- workspace isolation changes must remain bounded.
- workspace isolation changes must remain tenant-safe.
- uploads changes must remain least-privilege.
- uploads changes must remain encrypted.
- uploads changes must remain audited.
- uploads changes must remain bounded.
- uploads changes must remain tenant-safe.
- downloads changes must remain least-privilege.
- downloads changes must remain encrypted.
- downloads changes must remain audited.
- downloads changes must remain bounded.
- downloads changes must remain tenant-safe.
- agent tools changes must remain least-privilege.
- agent tools changes must remain encrypted.
- agent tools changes must remain audited.
- agent tools changes must remain bounded.
- agent tools changes must remain tenant-safe.
- third-party APIs changes must remain least-privilege.
- third-party APIs changes must remain encrypted.
- third-party APIs changes must remain audited.
- third-party APIs changes must remain bounded.
- third-party APIs changes must remain tenant-safe.
- simulation boundaries changes must remain least-privilege.
- simulation boundaries changes must remain encrypted.
- simulation boundaries changes must remain audited.
- simulation boundaries changes must remain bounded.
- simulation boundaries changes must remain tenant-safe.
- audit logs changes must remain least-privilege.
- audit logs changes must remain encrypted.
- audit logs changes must remain audited.
- audit logs changes must remain bounded.
- audit logs changes must remain tenant-safe.
- retention changes must remain least-privilege.
- retention changes must remain encrypted.
- retention changes must remain audited.
- retention changes must remain bounded.
- retention changes must remain tenant-safe.

## Default decisions

- Prefer to sanitize each secret in a way that is least-privilege.
- Prefer to redact each token in a way that is encrypted.
- Prefer to scope each workspace in a way that is audited.
- Prefer to encrypt each role in a way that is bounded.
- Prefer to rotate each permission in a way that is tenant-safe.
- Prefer to expire each artifact in a way that is consent-aware.
- Prefer to deny each run log in a way that is redactable.
- Prefer to review each audit record in a way that is exportable.
- Prefer to notify each retention rule in a way that is compliant.
- Prefer to retain each review queue in a way that is revocable.

## Workflow guidance

1. Explore the current secrets implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in secrets.
1. Change one narrow slice of secrets at a time unless the task is explicitly architectural.
2. Explore the current permissions implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in permissions.
2. Change one narrow slice of permissions at a time unless the task is explicitly architectural.
3. Explore the current workspace isolation implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in workspace isolation.
3. Change one narrow slice of workspace isolation at a time unless the task is explicitly architectural.
4. Explore the current uploads implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in uploads.
4. Change one narrow slice of uploads at a time unless the task is explicitly architectural.
5. Explore the current downloads implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in downloads.
5. Change one narrow slice of downloads at a time unless the task is explicitly architectural.
6. Explore the current agent tools implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in agent tools.
6. Change one narrow slice of agent tools at a time unless the task is explicitly architectural.
7. Explore the current third-party APIs implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in third-party APIs.
7. Change one narrow slice of third-party APIs at a time unless the task is explicitly architectural.
8. Explore the current simulation boundaries implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in simulation boundaries.
8. Change one narrow slice of simulation boundaries at a time unless the task is explicitly architectural.
9. Explore the current audit logs implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in audit logs.
9. Change one narrow slice of audit logs at a time unless the task is explicitly architectural.
10. Explore the current retention implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in retention.
10. Change one narrow slice of retention at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the secrets change preserves naming stability, schema clarity, and auditability.
- Confirm the secrets change has tests or fixtures covering the expected path.
- Confirm the permissions change preserves naming stability, schema clarity, and auditability.
- Confirm the permissions change has tests or fixtures covering the expected path.
- Confirm the workspace isolation change preserves naming stability, schema clarity, and auditability.
- Confirm the workspace isolation change has tests or fixtures covering the expected path.
- Confirm the uploads change preserves naming stability, schema clarity, and auditability.
- Confirm the uploads change has tests or fixtures covering the expected path.
- Confirm the downloads change preserves naming stability, schema clarity, and auditability.
- Confirm the downloads change has tests or fixtures covering the expected path.
- Confirm the agent tools change preserves naming stability, schema clarity, and auditability.
- Confirm the agent tools change has tests or fixtures covering the expected path.
- Confirm the third-party APIs change preserves naming stability, schema clarity, and auditability.
- Confirm the third-party APIs change has tests or fixtures covering the expected path.
- Confirm the simulation boundaries change preserves naming stability, schema clarity, and auditability.
- Confirm the simulation boundaries change has tests or fixtures covering the expected path.
- Confirm the audit logs change preserves naming stability, schema clarity, and auditability.
- Confirm the audit logs change has tests or fixtures covering the expected path.
- Confirm the retention change preserves naming stability, schema clarity, and auditability.
- Confirm the retention change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the secret become an opaque side effect with no manifest or trace.
- Do not let the token become an opaque side effect with no manifest or trace.
- Do not let the workspace become an opaque side effect with no manifest or trace.
- Do not let the role become an opaque side effect with no manifest or trace.
- Do not let the permission become an opaque side effect with no manifest or trace.
- Do not let the artifact become an opaque side effect with no manifest or trace.
- Do not let the run log become an opaque side effect with no manifest or trace.
- Do not let the audit record become an opaque side effect with no manifest or trace.
- Do not let the retention rule become an opaque side effect with no manifest or trace.
- Do not let the review queue become an opaque side effect with no manifest or trace.
- Do not optimize for the private workspace use case in a way that breaks the shared model for everyone else.
- Do not optimize for the restricted source use case in a way that breaks the shared model for everyone else.
- Do not optimize for the admin override use case in a way that breaks the shared model for everyone else.
- Do not optimize for the signed export use case in a way that breaks the shared model for everyone else.
- Do not optimize for the external connector use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed secrets change includes code, tests, docs, and operational notes when relevant.
- A completed secrets change describes risks, rollback path, and follow-up work if incomplete.
- A completed permissions change includes code, tests, docs, and operational notes when relevant.
- A completed permissions change describes risks, rollback path, and follow-up work if incomplete.
- A completed workspace isolation change includes code, tests, docs, and operational notes when relevant.
- A completed workspace isolation change describes risks, rollback path, and follow-up work if incomplete.
- A completed uploads change includes code, tests, docs, and operational notes when relevant.
- A completed uploads change describes risks, rollback path, and follow-up work if incomplete.
- A completed downloads change includes code, tests, docs, and operational notes when relevant.
- A completed downloads change describes risks, rollback path, and follow-up work if incomplete.
- A completed agent tools change includes code, tests, docs, and operational notes when relevant.
- A completed agent tools change describes risks, rollback path, and follow-up work if incomplete.
- A completed third-party APIs change includes code, tests, docs, and operational notes when relevant.
- A completed third-party APIs change describes risks, rollback path, and follow-up work if incomplete.
- A completed simulation boundaries change includes code, tests, docs, and operational notes when relevant.
- A completed simulation boundaries change describes risks, rollback path, and follow-up work if incomplete.
- A completed audit logs change includes code, tests, docs, and operational notes when relevant.
- A completed audit logs change describes risks, rollback path, and follow-up work if incomplete.
- A completed retention change includes code, tests, docs, and operational notes when relevant.
- A completed retention change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the private workspace workflow through stable APIs and explicit artifacts.
- Example pattern: support the restricted source workflow through stable APIs and explicit artifacts.
- Example pattern: support the admin override workflow through stable APIs and explicit artifacts.
- Example pattern: support the signed export workflow through stable APIs and explicit artifacts.
- Example pattern: support the external connector workflow through stable APIs and explicit artifacts.
- Example pattern: support the sandboxed run workflow through stable APIs and explicit artifacts.
- Example pattern: expose secrets state through a typed secret record and an append-only event trail.
- Example pattern: expose permissions state through a typed token record and an append-only event trail.
- Example pattern: expose workspace isolation state through a typed workspace record and an append-only event trail.
- Example pattern: expose uploads state through a typed role record and an append-only event trail.
- Example pattern: expose downloads state through a typed permission record and an append-only event trail.
- Example pattern: expose agent tools state through a typed artifact record and an append-only event trail.
- Example pattern: expose third-party APIs state through a typed run log record and an append-only event trail.
- Example pattern: expose simulation boundaries state through a typed audit record record and an append-only event trail.
- Example pattern: expose audit logs state through a typed retention rule record and an append-only event trail.
- Example pattern: expose retention state through a typed review queue record and an append-only event trail.

## Implementation prompts

- When implementing secrets, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing secrets, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing secrets, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing permissions, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing permissions, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing permissions, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing workspace isolation, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing workspace isolation, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing workspace isolation, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing uploads, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing uploads, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing uploads, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing downloads, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing downloads, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing downloads, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing agent tools, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing agent tools, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing agent tools, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing third-party APIs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing third-party APIs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing third-party APIs, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing simulation boundaries, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing simulation boundaries, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing simulation boundaries, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing audit logs, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing audit logs, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing audit logs, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing retention, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing retention, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing retention, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of secret changes in the domain model or UI.
- Revisit this rule when the meaning of token changes in the domain model or UI.
- Revisit this rule when the meaning of workspace changes in the domain model or UI.
- Revisit this rule when the meaning of role changes in the domain model or UI.
- Revisit this rule when the meaning of permission changes in the domain model or UI.
- Revisit this rule when the meaning of artifact changes in the domain model or UI.
- Revisit this rule when the meaning of run log changes in the domain model or UI.
- Revisit this rule when the meaning of audit record changes in the domain model or UI.
- Revisit this rule when the meaning of retention rule changes in the domain model or UI.
- Revisit this rule when the meaning of review queue changes in the domain model or UI.
- If a change would weaken the least-privilege property, document why and add compensating controls.
- If a change would weaken the encrypted property, document why and add compensating controls.
- If a change would weaken the audited property, document why and add compensating controls.
- If a change would weaken the bounded property, document why and add compensating controls.
- If a change would weaken the tenant-safe property, document why and add compensating controls.
- If a change would weaken the consent-aware property, document why and add compensating controls.
- If a change would weaken the redactable property, document why and add compensating controls.
- If a change would weaken the exportable property, document why and add compensating controls.
- If a change would weaken the compliant property, document why and add compensating controls.
- If a change would weaken the revocable property, document why and add compensating controls.
