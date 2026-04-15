# Autogen policy

- Files matching docs/ui/*.auto.md are canonical snapshots and may be committed.
- Any build outputs (dist/, node_modules/, .venv/, caches) are ignored.
- Generators must be deterministic; CI may verify regeneration matches committed snapshots.
