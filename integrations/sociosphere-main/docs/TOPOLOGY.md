# Repo topology (canonical)

## Core repos
- **sociosphere**: workspace/orchestrator + integration surface (manifests, tooling, platform composition).
- **tritrpc**: protocol spec + fixtures + reference implementations (Go/Rust/Python).

## Notes / archival
- **tritrpc-notes-archive**: raw historical drafts (RTF/HTML/etc). Optional; may be archived/read-only.
- Curated narrative belongs in `tritrpc/docs/` as Markdown.

## Rules
1) Directionality: `sociosphere -> tritrpc` allowed; `tritrpc -> sociosphere` forbidden.
2) Repo identity is stable; versions are tags/releases.
3) Submodule pins are explicit + reviewed, not floating.
