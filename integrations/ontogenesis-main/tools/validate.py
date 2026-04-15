#!/usr/bin/env python3
"""Ontogenesis repo validation.

Runs:
- SHACL conformance (pyshacl) over the merged ontology + examples
- SPARQL invariant checks for tests/*.rq (expects 0 rows)

Dependencies: rdflib + pyshacl
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from rdflib import Graph
from rdflib.query import Result


ROOT = Path(__file__).resolve().parents[1]

TTL_GLOBS = [
    "ontogenesis.ttl",
    "skos/*.ttl",
    "mappings/*.ttl",
    "examples/*.ttl",
]

SHAPES_PATH = ROOT / "shapes" / "ontogenesis.shacl.ttl"
TESTS_DIR = ROOT / "tests"


def load_merged_graph() -> Graph:
    g = Graph()
    loaded = 0
    for pat in TTL_GLOBS:
        for p in ROOT.glob(pat):
            if p.is_file():
                g.parse(p, format="turtle")
                loaded += 1
    if loaded == 0:
        raise RuntimeError("No Turtle files loaded; repo layout unexpected.")
    return g


def run_shacl(g: Graph) -> None:
    try:
        from pyshacl import validate
    except Exception as e:
        raise RuntimeError("pyshacl import failed; install requirements.txt") from e

    if not SHAPES_PATH.exists():
        raise FileNotFoundError(f"Missing SHACL shapes: {SHAPES_PATH}")

    conforms, _report_graph, report_text = validate(
        data_graph=g,
        shacl_graph=str(SHAPES_PATH),
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        debug=False,
    )

    if not conforms:
        sys.stderr.write("ERR: SHACL validation failed.\n")
        sys.stderr.write(report_text + "\n")
        raise SystemExit(2)

    print("OK: SHACL conforms.")


def run_sparql_tests(g: Graph) -> None:
    if not TESTS_DIR.exists():
        print("WARN: no tests/ directory present; skipping SPARQL tests.")
        return

    rq_files = sorted(TESTS_DIR.glob("*.rq"))
    if not rq_files:
        print("WARN: no SPARQL tests (*.rq) found; skipping.")
        return

    failed = 0
    for rq in rq_files:
        q = rq.read_text(encoding="utf-8")
        res = g.query(q)

        rows = list(res) if isinstance(res, Result) else list(res)
        if rows:
            failed += 1
            sys.stderr.write(f"ERR: SPARQL test produced {len(rows)} row(s): {rq.name}\n")
            for i, row in enumerate(rows[:20], start=1):
                sys.stderr.write(f"  {i:02d}: {row}\n")
            if len(rows) > 20:
                sys.stderr.write("  ... (truncated)\n")
        else:
            print(f"OK: {rq.name} returned 0 rows.")

    if failed:
        raise SystemExit(3)

    print("OK: SPARQL tests passed.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shacl", action="store_true", help="run SHACL validation")
    ap.add_argument("--sparql", action="store_true", help="run SPARQL invariant tests")
    args = ap.parse_args()

    if not args.shacl and not args.sparql:
        args.shacl = True
        args.sparql = True

    g = load_merged_graph()

    if args.shacl:
        run_shacl(g)
    if args.sparql:
        run_sparql_tests(g)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
