# Relationship to Profit MPCC

## Purpose

This note records the current boundary between `SocioProphet/tritfabric` and `mdheller/profit-mpcc`.

## Current stance

- `tritfabric` is the consolidated fabric / bridge / runtime-and-governance working tree.
- `profit-mpcc` is the upstream semantic/archive drafting root for conversational event fabric, impulse archives, and tranche-based semantic extraction.

## What is not true

`profit-mpcc` has **not** been wholesale imported into `tritfabric`.

`tritfabric` should not silently absorb archive-native or still-moving semantic surfaces.

## Likely future import surfaces

When stable, the strongest candidate surfaces from `profit-mpcc` are:
- agent/fabric execution implications from `docs/meta-agents.md`,
- bridge-facing conversational event routing semantics,
- fabric-level provenance hooks.

## Governance rule

Treat `profit-mpcc` as an upstream drafting root and consume only narrow, stabilized tranches.
