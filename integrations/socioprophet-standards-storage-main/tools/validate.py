#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys

def fail(msg: str) -> "None":
    print(f"ERR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def _safe_load_yaml(path: Path) -> "object":
    try:
        import yaml  # type: ignore
    except Exception:
        fail("missing dependency PyYAML (install with: python3 -m pip install pyyaml)")
    return yaml.safe_load(_read_text(path))

def main() -> int:
    root = Path(__file__).resolve().parents[1]

    lic = root / "LICENSE"
    if not lic.exists():
        fail("missing LICENSE")
    lic_txt = _read_text(lic).lower()
    if "placeholder" in lic_txt or "todo" in lic_txt:
        fail("LICENSE looks like a placeholder — replace with full license text before publish")

    # Workloads must parse where present (repo may omit benchmarks)
    for rel in ("benchmarks/workloads/workloads.yaml", "benchmarks/workloads/graph_workloads.yaml"):
        p = root / rel
        if p.exists():
            _safe_load_yaml(p)

    ds = list(root.rglob(".DS_Store"))
    if ds:
        fail(f"found .DS_Store files: {len(ds)} — remove and add to .gitignore")

    print("OK: validate passed (license non-placeholder, workloads parse where present, no .DS_Store)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
