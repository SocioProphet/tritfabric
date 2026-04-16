# Atlas v1 — TriTRPC Canonical Contract (v0)

This file is the contract-of-record for Atlas v1 on TriTRPC.

## Status
- Canonical contract: TriTRPC (this file + future schema DSL)
- Compatibility contract: protobuf/gRPC (`api/atlas/v1/atlas.proto` + `api/atlas/v1/autopilot.proto`)
- Migration: internal callers move to TriTRPC first; gRPC remains for Kubernetes ecosystem tooling.

## Canonical services (TriTRPC)
### Orchestrator
- SubmitTuneStudy
- SubmitTrainJob
- CancelJob
- GetJobStatus

### Registry
- ListArtifacts (stream)
- GetLedger
- PromoteArtifact

### Serve
- Deploy
- Scale
- ListDeployments
- ConfigureRouter
- GetRouter
- RouterSticky
- AutoScaleRouter

### Autopilot (extension)
- PauseRollout
- ResumeRollout
- SetLightsOut
- AlertWebhook

## Canonical message families
- JobId, Status, Artifact, Ledger
- SubmitTuneRequest (includes IRSpec, TuneGrid, DatasetSpec, OnnxExportSpec, LedgerSpec, PrecisionSpec, QuantSpec)
- Serve plane configs (RouterConfig, RouterStatus, StickyConfig, AutoScaleConfig)

## Determinism requirements
- Field ordering and encoding must follow TriTRPC fixtures and binding rules (see `~/dev/tritrpc` and SocioProphet standards).
- All responses MUST be reproducible under replay given the same inputs and policy.

## Compatibility mapping
The protobuf/gRPC surface is a compatibility projection for:
- Argo Rollouts analysis hooks
- Gatekeeper policy packs
- GitOps bootstrap tooling

Any divergence between the compat proto and this canonical contract is treated as a bug.
