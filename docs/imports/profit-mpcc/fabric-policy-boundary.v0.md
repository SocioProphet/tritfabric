# Profit MPCC fabric policy boundary intake (v0)

## Purpose

This note stages a narrow policy-boundary slice from `mdheller/profit-mpcc` for review inside `tritfabric`.

## Why this matters to TritFabric

The upstream MPCC line distinguishes:
- requested effects,
- approved effects,
- actual effects,
- and policy-aware handoff between semantic state and runtime execution.

For the fabric/runtime lane, this implies explicit boundary checks at:
- ingress,
- bridge routing,
- execution handoff,
- and provenance-preserving return paths.

## Candidate fabric-facing implications

- deny-by-default routing when authority context is incomplete,
- preservation of upstream provenance links across bridge hops,
- explicit policy labels at ingress and egress,
- no silent collapse of approval and execution state.

## Intake stance

This is a review copy for alignment inside the fabric lane. It is not the canonical upstream source of truth.
