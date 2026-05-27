#!/usr/bin/env python3
"""Validate the Network Atlas framework catalog.

The validator intentionally avoids external JSON Schema dependencies so it can run in the base dev environment.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog/frameworks/index.jsonl"
SCORECARDS = ROOT / "catalog/frameworks/scorecards"

CATALOG_REQUIRED = {
    "id",
    "name",
    "domain",
    "architecture_family",
    "adapter_status",
    "adapter_type",
    "license_status",
    "maintenance_status",
    "promotion_gates",
    "metrics",
    "math_type",
    "calc_ops",
    "source_docs",
    "claim_boundary",
}

ADAPTER_STATUS = {"raw_source", "candidate", "planned", "stubbed", "validated", "rejected", "superseded"}
ADAPTER_TYPE = {"none", "native", "wrapper", "converter", "dataset", "evaluation", "serve", "training", "catalog_only"}
LICENSE_STATUS = {"unknown", "compatible", "review_required", "restricted", "incompatible"}
MAINTENANCE_STATUS = {"unknown", "active", "stale", "archived", "internal", "n/a"}

SCORECARD_REQUIRED = {"framework_id", "scorecard_version", "authority", "adapter_scope", "readiness", "gates", "claim_boundary"}
AUTHORITY = {"catalog", "adapter", "runtime", "promotion", "deprecated"}
READINESS = {"not_started", "design_only", "stub", "smoke_tested", "validated", "blocked", "rejected"}


def _require_nonempty_list(entry: Dict[str, Any], key: str) -> None:
    value = entry.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
        raise AssertionError(f"{entry.get('id', '<unknown>')} field {key!r} must be a non-empty list of strings")


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{idx} is not valid JSON: {exc}") from exc


def validate_catalog() -> set[str]:
    ids: set[str] = set()
    entries = list(_load_jsonl(CATALOG))
    if not entries:
        raise AssertionError("framework catalog is empty")
    for entry in entries:
        missing = CATALOG_REQUIRED - set(entry)
        if missing:
            raise AssertionError(f"catalog entry missing fields: {sorted(missing)}")
        fid = entry["id"]
        if fid in ids:
            raise AssertionError(f"duplicate framework id: {fid}")
        ids.add(fid)
        if entry["adapter_status"] not in ADAPTER_STATUS:
            raise AssertionError(f"{fid} invalid adapter_status: {entry['adapter_status']}")
        if entry["adapter_type"] not in ADAPTER_TYPE:
            raise AssertionError(f"{fid} invalid adapter_type: {entry['adapter_type']}")
        if entry["license_status"] not in LICENSE_STATUS:
            raise AssertionError(f"{fid} invalid license_status: {entry['license_status']}")
        if entry["maintenance_status"] not in MAINTENANCE_STATUS:
            raise AssertionError(f"{fid} invalid maintenance_status: {entry['maintenance_status']}")
        for key in ("promotion_gates", "metrics", "math_type", "calc_ops", "source_docs"):
            _require_nonempty_list(entry, key)
        if not isinstance(entry["claim_boundary"], str) or not entry["claim_boundary"]:
            raise AssertionError(f"{fid} claim_boundary must be a non-empty string")
    return ids


def validate_scorecards(catalog_ids: set[str]) -> None:
    if not SCORECARDS.exists():
        return
    for path in sorted(SCORECARDS.glob("*.json")):
        with path.open("r", encoding="utf-8") as fh:
            card = json.load(fh)
        missing = SCORECARD_REQUIRED - set(card)
        if missing:
            raise AssertionError(f"{path} missing fields: {sorted(missing)}")
        fid = card["framework_id"]
        if fid not in catalog_ids:
            raise AssertionError(f"{path} references unknown framework_id: {fid}")
        if card["authority"] not in AUTHORITY:
            raise AssertionError(f"{path} invalid authority: {card['authority']}")
        if card["readiness"] not in READINESS:
            raise AssertionError(f"{path} invalid readiness: {card['readiness']}")
        gates = card["gates"]
        for gate in ("license", "provenance", "tests", "model_card", "runtime_safety"):
            if gate not in gates:
                raise AssertionError(f"{path} gates missing {gate}")


def main() -> int:
    ids = validate_catalog()
    validate_scorecards(ids)
    print("framework catalog: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
