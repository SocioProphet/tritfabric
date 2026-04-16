# Atlas v1 — TriTRPC Contract (Canonical)

This directory is the canonical Atlas service contract expressed in TriTRPC schemas.

Status:
- v0 placeholders committed to freeze direction: TriTRPC is canonical.
- gRPC/proto remains as compatibility surface during migration.

Next:
- define message types for: SubmitTune, SubmitTrain, CancelJob, GetJobStatus, ListArtifacts, GetLedger, PromoteArtifact
- define Serve plane contract (Deploy/Scale/List/Router config)
- define Autopilot extension contract as separate module (mirrors `api/atlas/v1/autopilot.proto` intent)
- add conformance fixtures to compare TriTRPC ↔ gRPC semantics
