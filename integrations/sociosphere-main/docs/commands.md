# Commands (paste-safe rules)

## Rules
- We only use complete one-liners or complete heredocs. No trailing \\ continuations.
- Never paste mid-chain fragments starting with '&&' or ending with '\\'.

## Patterns
- Prefer: `cd <dir> && <cmd>`
- For diagnostics: `cmd || { echo ...; <debug>; }`
