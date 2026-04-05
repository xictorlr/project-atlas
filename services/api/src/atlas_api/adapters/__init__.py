"""External integration adapters.

Each adapter follows the Protocol/interface pattern so the implementation can be
swapped or disabled independently. Adapters are feature-flagged via env vars;
failure in any adapter must not affect the core pipeline.

Adapters:
  DeerFlowAdapter   — agent orchestration (ATLAS_DEERFLOW_ENABLED)
  HermesAdapter     — memory/context bridge (ATLAS_HERMES_ENABLED)
  MiroFishAdapter   — simulation gateway   (ATLAS_MIROFISH_ENABLED)
"""
