# Profit MPCC fabric routing and provenance intake (v0)

## Purpose

This note stages a narrow fabric-facing slice from `mdheller/profit-mpcc` for review inside `tritfabric`.

## Why this matters to TritFabric

The upstream MPCC line treats conversational and agentic state as a partially ordered event fabric with:
- authority context,
- provenance links,
- requested / approved / actual effect separation,
- and policy-constrained transitions.

Those ideas matter here because `tritfabric` is the bridge/runtime lane where event routing and runtime governance meet.

## Candidate intake surfaces

The strongest fabric-facing implications are:
- bridge-facing conversational event routing semantics,
- planner / executor guard boundaries,
- provenance hook requirements at routing boundaries,
- and policy-aware effect handoff between event fabric and runtime fabric.

## Intake stance

This is a review copy for alignment. It is not the canonical upstream source of truth.

Only stabilized fabric-facing portions should influence TritFabric runtime design.
