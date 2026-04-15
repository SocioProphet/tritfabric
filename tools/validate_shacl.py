from __future__ import annotations

import argparse
import json
import os

from atlas.semantics.shacl_validate import validate_trial_graph_turtle


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ttl", required=True, help="Path to turtle file")
    p.add_argument("--shapes", default="api/shapes/model_shapes.ttl")
    p.add_argument("--ontology", default=None)
    args = p.parse_args()

    with open(args.ttl, "r", encoding="utf-8") as f:
        turtle = f.read()

    ok, report = validate_trial_graph_turtle(turtle=turtle, shapes_path=args.shapes, ontology_path=args.ontology)
    print(json.dumps({"ok": ok}, indent=2))
    if not ok:
        print(report)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
