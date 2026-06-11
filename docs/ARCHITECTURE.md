# Architecture overview

TritFabric is designed as a **contract-first** runtime:

- **TritRPC/TritFabric envelope discipline**:
  - explicit schema/context identifiers
  - deterministic framing
  - cryptographic integrity lane (HMAC today, AEAD upgrade path)

- **Atlas OS Service**:
  - orchestrator: accepts training/tuning submissions
  - scheduler: fairness (DRF) + admission
  - runner: executes locally or via Ray (optional)
  - registry: produces model cards + ledgers; promotion is gated
  - serve plane: optional router/autoscaler (Ray Serve) for online A/B and sticky routing

- **Promotion**:
  - fail-closed by default (SHACL + ONNX cosine + eval delta)
  - compatible with Argo Rollouts analysis for canary gating

- **SourceOS integration**:
  - opt-in by default
  - local socket mode preferred
  - secrets never shipped; pulled from vault/agent when enabled

- **SocioProphet training platform**:
  - standards and governance live outside SourceOS
  - training/eval pipelines can target Atlas or run standalone

- **Cainpath mesh integration** *(planned — see `docs/cainpath/CAINPATH_MESH.md`)*:
  - every Atlas job transition emits a CairnStep into a CairnLine
  - the Cairnlog is the append-only promotion evidence trail
  - promotion requires a complete, replayable CairnLine — not just file checks
  - substrate schemas: `SocioProphet/cairnpath-mesh`

- **Five-layer spine** *(see `docs/atlas/ATLAS_SPINE.md`)*:
  - Layer 1: Network Atlas (model zoo taxonomy, composable IR, shape contracts)
  - Layer 2: atlasd (implemented)
  - Layer 3: Framework Catalog (governed adapter intake)
  - Layer 4: Calculus Contracts (`math_type` + `calc_ops` + SHACL gate)
  - Layer 5: Devine Intelligence War Games (defensive validation plane)

See `docs/NAMING_LEDGER.md` for frozen terminology.
