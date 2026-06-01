# Atlas README Preservation v0.1

This note preserves the durable architecture vocabulary extracted from the thin Atlas bundle repositories before any future archive or retirement decision.

Source repositories:

- `SocioProphet/atlas_master_bundle_complete`
- `SocioProphet/atlas_master_bundle_autopilot_fullorchestration`
- `SocioProphet/atlas_os_service_full`

The Atlas repositories remain only partially confirmed: README content exists, one orchestration README exists, and representative implementation-path probes did not confirm full implementation files. This note does not make the Atlas repositories authoritative. It preserves their reusable concepts inside TritFabric, which is the canonical implementation and immediate contract authority for the recovered Atlas / TritFabric lineage.

## Preserved TritFabric concepts

### 1. TritRPC service and daemon scaffold

Atlas names an `atlas_service` surface with TritRPC v1 proto, daemon, gRPC server scaffold, observability, and Grafana starter material. TritFabric should preserve this as the historical origin of the service/daemon vocabulary, while TriTRPC remains the protocol authority.

Canonical disposition:

- TritFabric owns recovered Atlas implementation lineage and service readiness posture.
- TriTRPC owns protocol mechanics and protocol contract evolution.
- SocioSphere records architecture and estate propagation, not implementation.

### 2. Autopilot promotion and rollout

Atlas names Autopilot promotion and rollout behavior. TritFabric should retain this as a governance-facing runtime concept, but promotion authority must remain governed by policy and model-governance ledgers rather than by a bundle README.

Canonical disposition:

- TritFabric may model rollout/promotion intent and runtime readiness.
- Policy Fabric governs admission and authorization.
- Model Governance Ledger owns lifecycle, promotion, consent, revocation, and governance evidence.

### 3. Observability and alert vocabulary

Atlas names Grafana dashboards, per-tenant alert policies, Prometheus exporter, and Loki logs. TritFabric should preserve these as observability vocabulary for runtime/readiness integration.

Canonical disposition:

- TritFabric owns fabric/runtime observability vocabulary where it is tied to Atlas lineage.
- Platform observability and DevSecOps lanes may later absorb common metrics and alert contracts.

### 4. OS daemon, scheduler, Ray runner, and registry

Atlas OS Service names an OS daemon scaffold with admission, DRF scheduler, Ray runner, and registry. TritFabric should preserve this as compute-mesh/runtime placement vocabulary.

Canonical disposition:

- TritFabric preserves the Atlas-side runtime vocabulary.
- `svc.platform.compute-mesh` owns distributed execution placement semantics.
- AgentPlane owns execution/evidence-control surfaces.

### 5. ServeService, router, autoscaler, and sticky routing

Atlas OS Service names ServeService stubs, router autoscaler, and sticky routing. TritFabric already contains router/autoscaler work; this note records the Atlas README source as preserved vocabulary.

Canonical disposition:

- TritFabric owns recovered Serve/router/autoscaler lineage.
- Model Router owns runtime model routing decisions when model selection is involved.
- Policy Fabric gates privileged routing side effects.

## Non-authority boundary

This document does not promote Atlas bundle repositories back to canonical implementation authority.

Atlas bundle repositories remain candidates for archive or reference retention after direct tree confirmation and after all extraction rows are discharged in SocioSphere.
