# ADR-0002: Freeze Cainpath / Cairn / Atlas naming

**Status:** accepted
**Date:** 2026-06-11
**Deciders:** Michael Heller

---

## Context

Multiple names for the same concepts have accumulated across the SocioProphet estate: Cainpath vs. Cairnpath, Atlas vs. Network Atlas vs. Zoo Slate, Cairnlog vs. Cainpath audit trail, Divine vs. Devine Intelligence War Games. This drift is visible in docs, issues, and code.

Naming drift causes: incorrect repo targeting, duplicate implementations, and integration failures where two components reference the same concept by different names.

---

## Decision

The names are frozen as defined in `docs/NAMING_LEDGER.md`. No new name may be introduced in code or docs without a PR updating the ledger first.

Key decisions:

| What | Frozen name | Deprecated name(s) |
|---|---|---|
| Product/system name for mesh pathing | **Cainpath** | Cairnpath (acceptable alias only) |
| Primitive checkpoint object | **Cairn** / **CairnContext** / **CairnStep** / **CairnLine** | "checkpoint", "state node" |
| Append-only audit trail | **Cairnlog** | "audit log", "ledger" (in Cainpath context) |
| Model zoo + IR layer | **Network Atlas** | Zoo Slate |
| Validation layer | **Devine Intelligence War Games** | "Divine Intelligence War Games" |

---

## Rationale

Frozen names prevent: implementation splitting across repos that use different names for the same thing, confusion in issues and code review, and the silent accumulation of aliases that no one remembers are aliases.

The Naming Ledger (`docs/NAMING_LEDGER.md`) is the single source of truth. It records drift that has already occurred as an audit record, so future contributors know what names are deprecated and why.

---

## Consequences

- All new code and docs use the frozen names.
- Existing code using deprecated names (e.g. "Zoo Slate") is corrected on next touch, not en masse refactored.
- Pull requests that introduce new names without a ledger entry are rejected at review.
- The Naming Ledger is maintained as a living document: when a new term is genuinely needed, it is added to the ledger before it appears anywhere else.
