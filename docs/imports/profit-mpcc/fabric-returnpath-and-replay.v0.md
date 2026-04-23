# Profit MPCC fabric return-path and replay intake (v0)

## Purpose

This note stages a narrow return-path/replay slice from `mdheller/profit-mpcc` for review inside `tritfabric`.

## Why this matters to TritFabric

The upstream MPCC line keeps provenance-preserving, policy-constrained state transitions. For the fabric/runtime lane, that implies not only controlled ingress and routing, but also controlled return paths for:
- execution receipts,
- replay evidence,
- compensating actions,
- and post-execution provenance closure.

## Candidate fabric-facing implications

- return-path events should preserve upstream provenance links,
- replay receipts should not collapse approval and execution state,
- compensating actions should append rather than overwrite prior history,
- runtime-to-archive handoff should preserve branch/workspace identity.

## Intake stance

This is a review copy for alignment inside the fabric lane. It is not the canonical upstream source of truth.
