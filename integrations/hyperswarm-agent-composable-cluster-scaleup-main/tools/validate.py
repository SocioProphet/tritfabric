#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "LICENSE",
    "NOTICE.md",
    "docs/UPSTREAMS.md",
    "tools/upstreams.env",
    "tools/fetch_upstreams.sh",
]

ALLOW_MASTER = {"HEROKU_BUILDPACK_APT_REF"}  # explicit exception: upstream has no releases

def fail(msg: str) -> None:
    print(f"ERR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.exists():
            fail(f"missing {rel}")

    # Ensure we don't accidentally commit vendored upstreams
    # (we fetch into third_party/, but do not track it in git)
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    if "third_party/" not in gitignore:
        fail("'.gitignore' must include 'third_party/' to prevent vendoring upstream code")

    env = (ROOT / "tools/upstreams.env").read_text(encoding="utf-8", errors="replace")
    for key in ["KUBESPRAY_URL", "KUBESPRAY_REF", "KREW_URL", "KREW_REF", "FYBRIK_URL", "FYBRIK_REF", "HEROKU_BUILDPACK_APT_URL", "HEROKU_BUILDPACK_APT_REF"]:
        if key not in env:
            fail(f"tools/upstreams.env missing {key}")

    # Validate refs are pinned (tags/commits) and not floating, except explicit allowlist.
    for m in re.finditer(r'^([A-Z0-9_]+_REF)="([^"]+)"\s*$', env, flags=re.M):
        k, v = m.group(1), m.group(2)
        if v in {"main", "master", "HEAD"} and k not in ALLOW_MASTER:
            fail(f"{k} must not be floating ref ({v}); pin a tag or commit")

    # Basic doc hygiene: prevent placeholder ellipses in core docs
    for rel in ["README.md", "docs/UPSTREAMS.md"]:
        s = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if re.search(r"\n\.\.\.\n", s):
            fail(f"{rel} contains placeholder ellipses")

    print("OK: validate passed (wrapper docs present, refs pinned, third_party gitignored)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
