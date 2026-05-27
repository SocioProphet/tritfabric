#!/usr/bin/env python3
"""Validate Community Learning Plane workflow stubs.

The validator avoids external JSON Schema and OPA dependencies. It checks the
contract properties that matter for recovered workflow capture: required fields,
known step kinds, explicit gates, outputs, and mandatory claim boundaries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "community/workflows"
POLICY = ROOT / "community/opa/community-policy.rego"

REQUIRED = {"id", "version", "purpose", "inputs", "gates", "steps", "outputs", "claim_boundary"}
STEP_REQUIRED = {"id", "kind", "description"}
STEP_KINDS = {"ingest", "policy_check", "curate", "evaluate", "distill", "ab_test", "credit", "emit", "manual_review"}
REQUIRED_GATES = {"license-present", "lineage-present"}


def _require_nonempty_list(doc: Dict[str, Any], key: str) -> None:
    value = doc.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise AssertionError(f"{doc.get('id', '<unknown>')} field {key!r} must be a non-empty list of strings")


def validate_workflow(path: Path) -> None:
    with path.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    missing = REQUIRED - set(doc)
    if missing:
        raise AssertionError(f"{path} missing fields: {sorted(missing)}")
    for key in ("inputs", "gates", "outputs"):
        _require_nonempty_list(doc, key)
    gates = set(doc["gates"])
    missing_gates = REQUIRED_GATES - gates
    if missing_gates:
        raise AssertionError(f"{path} missing required gates: {sorted(missing_gates)}")
    if "manual-review-before-promotion" not in gates:
        raise AssertionError(f"{path} must require manual-review-before-promotion")
    steps = doc.get("steps")
    if not isinstance(steps, list) or not steps:
        raise AssertionError(f"{path} steps must be a non-empty list")
    seen_policy_check = False
    for step in steps:
        missing_step = STEP_REQUIRED - set(step)
        if missing_step:
            raise AssertionError(f"{path} step missing fields: {sorted(missing_step)}")
        if step["kind"] not in STEP_KINDS:
            raise AssertionError(f"{path} invalid step kind: {step['kind']}")
        seen_policy_check = seen_policy_check or step["kind"] == "policy_check"
    if not seen_policy_check:
        raise AssertionError(f"{path} must include a policy_check step")
    if not isinstance(doc["claim_boundary"], str) or not doc["claim_boundary"]:
        raise AssertionError(f"{path} claim_boundary must be non-empty")


def validate_policy_stub() -> None:
    text = POLICY.read_text(encoding="utf-8")
    for needle in ("allow_training_use", "input.consent == true", "input.license", "input.lineage", "input.rubric_present"):
        if needle not in text:
            raise AssertionError(f"policy stub missing {needle}")


def main() -> int:
    workflow_files = sorted(p for p in WORKFLOWS.glob("*.json") if p.name != "schema.json")
    if not workflow_files:
        raise AssertionError("no community workflow files found")
    for path in workflow_files:
        validate_workflow(path)
    validate_policy_stub()
    print("community workflows: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
