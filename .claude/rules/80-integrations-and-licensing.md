---
paths:
  - "packages/adapters/**"
  - "services/api/**"
  - "services/worker/**"
  - "docs/**"
---

# Integrations and licensing rules

Integrate external agent frameworks and connectors without letting them define the core product contract.

## How to use this rule

Read this file before changing the area it governs.
If this rule conflicts with a more specific path-scoped rule, the more specific rule wins.
When in doubt, preserve portability, provenance, and reviewability.

## Intent

- Keep DeerFlow work aligned with the product promise.
- Keep Hermes work aligned with the product promise.
- Keep MiroFish work aligned with the product promise.
- Keep MCP work aligned with the product promise.
- Keep web connectors work aligned with the product promise.
- Keep CLI bridges work aligned with the product promise.
- Keep plugin packaging work aligned with the product promise.
- Keep licensing work aligned with the product promise.
- Keep feature flags work aligned with the product promise.
- Keep self-hosting work aligned with the product promise.
- The governing objective is to integrate external agent frameworks and connectors without letting them define the core product contract.

## Invariants

- DeerFlow changes must remain replaceable.
- DeerFlow changes must remain thin.
- DeerFlow changes must remain documented.
- DeerFlow changes must remain optional.
- DeerFlow changes must remain license-aware.
- Hermes changes must remain replaceable.
- Hermes changes must remain thin.
- Hermes changes must remain documented.
- Hermes changes must remain optional.
- Hermes changes must remain license-aware.
- MiroFish changes must remain replaceable.
- MiroFish changes must remain thin.
- MiroFish changes must remain documented.
- MiroFish changes must remain optional.
- MiroFish changes must remain license-aware.
- MCP changes must remain replaceable.
- MCP changes must remain thin.
- MCP changes must remain documented.
- MCP changes must remain optional.
- MCP changes must remain license-aware.
- web connectors changes must remain replaceable.
- web connectors changes must remain thin.
- web connectors changes must remain documented.
- web connectors changes must remain optional.
- web connectors changes must remain license-aware.
- CLI bridges changes must remain replaceable.
- CLI bridges changes must remain thin.
- CLI bridges changes must remain documented.
- CLI bridges changes must remain optional.
- CLI bridges changes must remain license-aware.
- plugin packaging changes must remain replaceable.
- plugin packaging changes must remain thin.
- plugin packaging changes must remain documented.
- plugin packaging changes must remain optional.
- plugin packaging changes must remain license-aware.
- licensing changes must remain replaceable.
- licensing changes must remain thin.
- licensing changes must remain documented.
- licensing changes must remain optional.
- licensing changes must remain license-aware.
- feature flags changes must remain replaceable.
- feature flags changes must remain thin.
- feature flags changes must remain documented.
- feature flags changes must remain optional.
- feature flags changes must remain license-aware.
- self-hosting changes must remain replaceable.
- self-hosting changes must remain thin.
- self-hosting changes must remain documented.
- self-hosting changes must remain optional.
- self-hosting changes must remain license-aware.

## Default decisions

- Prefer to wrap each adapter in a way that is replaceable.
- Prefer to adapt each bridge in a way that is thin.
- Prefer to feature-flag each connector in a way that is documented.
- Prefer to version each license boundary in a way that is optional.
- Prefer to license-check each feature flag in a way that is license-aware.
- Prefer to isolate each provider in a way that is observable.
- Prefer to fallback each sandbox in a way that is time-bounded.
- Prefer to degrade each runtime in a way that is self-hostable.
- Prefer to document each transport in a way that is recoverable.
- Prefer to replace each manifest in a way that is user-consent-driven.

## Workflow guidance

1. Explore the current DeerFlow implementation before proposing a replacement.
1. Map the key inputs, outputs, storage effects, and user-visible behavior in DeerFlow.
1. Change one narrow slice of DeerFlow at a time unless the task is explicitly architectural.
2. Explore the current Hermes implementation before proposing a replacement.
2. Map the key inputs, outputs, storage effects, and user-visible behavior in Hermes.
2. Change one narrow slice of Hermes at a time unless the task is explicitly architectural.
3. Explore the current MiroFish implementation before proposing a replacement.
3. Map the key inputs, outputs, storage effects, and user-visible behavior in MiroFish.
3. Change one narrow slice of MiroFish at a time unless the task is explicitly architectural.
4. Explore the current MCP implementation before proposing a replacement.
4. Map the key inputs, outputs, storage effects, and user-visible behavior in MCP.
4. Change one narrow slice of MCP at a time unless the task is explicitly architectural.
5. Explore the current web connectors implementation before proposing a replacement.
5. Map the key inputs, outputs, storage effects, and user-visible behavior in web connectors.
5. Change one narrow slice of web connectors at a time unless the task is explicitly architectural.
6. Explore the current CLI bridges implementation before proposing a replacement.
6. Map the key inputs, outputs, storage effects, and user-visible behavior in CLI bridges.
6. Change one narrow slice of CLI bridges at a time unless the task is explicitly architectural.
7. Explore the current plugin packaging implementation before proposing a replacement.
7. Map the key inputs, outputs, storage effects, and user-visible behavior in plugin packaging.
7. Change one narrow slice of plugin packaging at a time unless the task is explicitly architectural.
8. Explore the current licensing implementation before proposing a replacement.
8. Map the key inputs, outputs, storage effects, and user-visible behavior in licensing.
8. Change one narrow slice of licensing at a time unless the task is explicitly architectural.
9. Explore the current feature flags implementation before proposing a replacement.
9. Map the key inputs, outputs, storage effects, and user-visible behavior in feature flags.
9. Change one narrow slice of feature flags at a time unless the task is explicitly architectural.
10. Explore the current self-hosting implementation before proposing a replacement.
10. Map the key inputs, outputs, storage effects, and user-visible behavior in self-hosting.
10. Change one narrow slice of self-hosting at a time unless the task is explicitly architectural.

## Review checklist

- Confirm the DeerFlow change preserves naming stability, schema clarity, and auditability.
- Confirm the DeerFlow change has tests or fixtures covering the expected path.
- Confirm the Hermes change preserves naming stability, schema clarity, and auditability.
- Confirm the Hermes change has tests or fixtures covering the expected path.
- Confirm the MiroFish change preserves naming stability, schema clarity, and auditability.
- Confirm the MiroFish change has tests or fixtures covering the expected path.
- Confirm the MCP change preserves naming stability, schema clarity, and auditability.
- Confirm the MCP change has tests or fixtures covering the expected path.
- Confirm the web connectors change preserves naming stability, schema clarity, and auditability.
- Confirm the web connectors change has tests or fixtures covering the expected path.
- Confirm the CLI bridges change preserves naming stability, schema clarity, and auditability.
- Confirm the CLI bridges change has tests or fixtures covering the expected path.
- Confirm the plugin packaging change preserves naming stability, schema clarity, and auditability.
- Confirm the plugin packaging change has tests or fixtures covering the expected path.
- Confirm the licensing change preserves naming stability, schema clarity, and auditability.
- Confirm the licensing change has tests or fixtures covering the expected path.
- Confirm the feature flags change preserves naming stability, schema clarity, and auditability.
- Confirm the feature flags change has tests or fixtures covering the expected path.
- Confirm the self-hosting change preserves naming stability, schema clarity, and auditability.
- Confirm the self-hosting change has tests or fixtures covering the expected path.

## Failure modes to avoid

- Do not let the adapter become an opaque side effect with no manifest or trace.
- Do not let the bridge become an opaque side effect with no manifest or trace.
- Do not let the connector become an opaque side effect with no manifest or trace.
- Do not let the license boundary become an opaque side effect with no manifest or trace.
- Do not let the feature flag become an opaque side effect with no manifest or trace.
- Do not let the provider become an opaque side effect with no manifest or trace.
- Do not let the sandbox become an opaque side effect with no manifest or trace.
- Do not let the runtime become an opaque side effect with no manifest or trace.
- Do not let the transport become an opaque side effect with no manifest or trace.
- Do not let the manifest become an opaque side effect with no manifest or trace.
- Do not optimize for the deerflow orchestration adapter use case in a way that breaks the shared model for everyone else.
- Do not optimize for the hermes memory bridge use case in a way that breaks the shared model for everyone else.
- Do not optimize for the mirofish simulation gateway use case in a way that breaks the shared model for everyone else.
- Do not optimize for the obsidian file watcher use case in a way that breaks the shared model for everyone else.
- Do not optimize for the publish target use case in a way that breaks the shared model for everyone else.

## Acceptance expectations

- A completed DeerFlow change includes code, tests, docs, and operational notes when relevant.
- A completed DeerFlow change describes risks, rollback path, and follow-up work if incomplete.
- A completed Hermes change includes code, tests, docs, and operational notes when relevant.
- A completed Hermes change describes risks, rollback path, and follow-up work if incomplete.
- A completed MiroFish change includes code, tests, docs, and operational notes when relevant.
- A completed MiroFish change describes risks, rollback path, and follow-up work if incomplete.
- A completed MCP change includes code, tests, docs, and operational notes when relevant.
- A completed MCP change describes risks, rollback path, and follow-up work if incomplete.
- A completed web connectors change includes code, tests, docs, and operational notes when relevant.
- A completed web connectors change describes risks, rollback path, and follow-up work if incomplete.
- A completed CLI bridges change includes code, tests, docs, and operational notes when relevant.
- A completed CLI bridges change describes risks, rollback path, and follow-up work if incomplete.
- A completed plugin packaging change includes code, tests, docs, and operational notes when relevant.
- A completed plugin packaging change describes risks, rollback path, and follow-up work if incomplete.
- A completed licensing change includes code, tests, docs, and operational notes when relevant.
- A completed licensing change describes risks, rollback path, and follow-up work if incomplete.
- A completed feature flags change includes code, tests, docs, and operational notes when relevant.
- A completed feature flags change describes risks, rollback path, and follow-up work if incomplete.
- A completed self-hosting change includes code, tests, docs, and operational notes when relevant.
- A completed self-hosting change describes risks, rollback path, and follow-up work if incomplete.

## Examples and patterns

- Example pattern: support the deerflow orchestration adapter workflow through stable APIs and explicit artifacts.
- Example pattern: support the hermes memory bridge workflow through stable APIs and explicit artifacts.
- Example pattern: support the mirofish simulation gateway workflow through stable APIs and explicit artifacts.
- Example pattern: support the obsidian file watcher workflow through stable APIs and explicit artifacts.
- Example pattern: support the publish target workflow through stable APIs and explicit artifacts.
- Example pattern: expose DeerFlow state through a typed adapter record and an append-only event trail.
- Example pattern: expose Hermes state through a typed bridge record and an append-only event trail.
- Example pattern: expose MiroFish state through a typed connector record and an append-only event trail.
- Example pattern: expose MCP state through a typed license boundary record and an append-only event trail.
- Example pattern: expose web connectors state through a typed feature flag record and an append-only event trail.
- Example pattern: expose CLI bridges state through a typed provider record and an append-only event trail.
- Example pattern: expose plugin packaging state through a typed sandbox record and an append-only event trail.
- Example pattern: expose licensing state through a typed runtime record and an append-only event trail.
- Example pattern: expose feature flags state through a typed transport record and an append-only event trail.
- Example pattern: expose self-hosting state through a typed manifest record and an append-only event trail.

## Implementation prompts

- When implementing DeerFlow, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing DeerFlow, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing DeerFlow, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing Hermes, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing Hermes, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing Hermes, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing MiroFish, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing MiroFish, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing MiroFish, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing MCP, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing MCP, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing MCP, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing web connectors, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing web connectors, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing web connectors, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing CLI bridges, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing CLI bridges, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing CLI bridges, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing plugin packaging, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing plugin packaging, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing plugin packaging, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing licensing, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing licensing, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing licensing, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing feature flags, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing feature flags, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing feature flags, ask: what should be visible in the vault, API, logs, and admin UI?
- When implementing self-hosting, ask: what is the source of truth, who owns it, and how does it fail?
- When implementing self-hosting, ask: what part should be deterministic and what part benefits from LLM synthesis?
- When implementing self-hosting, ask: what should be visible in the vault, API, logs, and admin UI?

## Maintenance notes

- Revisit this rule when the meaning of adapter changes in the domain model or UI.
- Revisit this rule when the meaning of bridge changes in the domain model or UI.
- Revisit this rule when the meaning of connector changes in the domain model or UI.
- Revisit this rule when the meaning of license boundary changes in the domain model or UI.
- Revisit this rule when the meaning of feature flag changes in the domain model or UI.
- Revisit this rule when the meaning of provider changes in the domain model or UI.
- Revisit this rule when the meaning of sandbox changes in the domain model or UI.
- Revisit this rule when the meaning of runtime changes in the domain model or UI.
- Revisit this rule when the meaning of transport changes in the domain model or UI.
- Revisit this rule when the meaning of manifest changes in the domain model or UI.
- If a change would weaken the replaceable property, document why and add compensating controls.
- If a change would weaken the thin property, document why and add compensating controls.
- If a change would weaken the documented property, document why and add compensating controls.
- If a change would weaken the optional property, document why and add compensating controls.
- If a change would weaken the license-aware property, document why and add compensating controls.
- If a change would weaken the observable property, document why and add compensating controls.
- If a change would weaken the time-bounded property, document why and add compensating controls.
- If a change would weaken the self-hostable property, document why and add compensating controls.
- If a change would weaken the recoverable property, document why and add compensating controls.
- If a change would weaken the user-consent-driven property, document why and add compensating controls.
