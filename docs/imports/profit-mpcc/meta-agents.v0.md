# Profit MPCC meta-agents intake (v0)

## Purpose

This document stages the fabric-facing agent decomposition emerging from `mdheller/profit-mpcc`.

## Why this matters to TritFabric

`tritfabric` is the consolidated fabric / bridge / runtime-and-governance working tree. The `profit-mpcc` line is upstream semantic/archive work, but its agent decomposition has direct implications for:
- canonicalization,
- provenance extraction,
- planner/executor guards,
- policy/capability mediation,
- anomaly tracking,
- and archive-to-runtime handoff.

## Candidate imported surfaces

The upstream `profit-mpcc` line currently distinguishes at least:
- message statistics agent,
- canonicalization agent,
- discourse / speech-act agent,
- entity / claim / provenance agent,
- branch / merge / rebase agent,
- policy / capability agent,
- planner / executor guard,
- memory / compaction agent,
- evaluation / anomaly agent.

## Intake stance

This is an intake copy for review inside the fabric/runtime lane. It is not the canonical upstream source of truth.

Only stabilized fabric-facing portions should eventually influence TritFabric runtime design.
