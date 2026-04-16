# TriTRPC Alignment

## Canonical contract
TriTRPC is the contract-of-record for TritFabric/Atlas services in the SocioProphet stack.

## Compatibility surfaces
Protocol Buffers / gRPC exist as an external compatibility surface for:
- Kubernetes ecosystem integration (Argo, Rollouts, Gatekeeper workflows)
- generic tooling expectations

Proto files in this repo are treated as a **compatibility layer** during migration, not the canonical standard.

## Migration plan
1) Define Atlas services in TriTRPC schemas (canonical).
2) Provide a bridge that serves both TriTRPC and the existing gRPC endpoints.
3) Move internal callers to TriTRPC first.
4) Keep gRPC only as long as required for external tooling.
