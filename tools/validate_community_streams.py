#!/usr/bin/env python3
"""Validate Community Learning Plane event stream contracts.

This checks topic declarations and fixtures without requiring a broker or storage
runtime. The stream layer is contract-only until a later runtime tranche.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
TOPICS = ROOT / "community/streams/topics.json"
FIXTURES = ROOT / "community/streams/fixtures"

REQUIRED_TOPIC_FIELDS = {"name", "record_type", "schema", "required_gates", "retention", "side_effects"}
REQUIRED_TOPIC_GATES = {"license-present", "lineage-present"}
KNOWN_RECORD_TYPES = {"HFEvent", "CurationRecord", "Curriculum", "CreditRecord"}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_topics() -> set[str]:
    doc = _load_json(TOPICS)
    if not doc.get("claim_boundary"):
        raise AssertionError("topics contract must include claim_boundary")
    topics = doc.get("topics")
    if not isinstance(topics, list) or not topics:
        raise AssertionError("topics must be a non-empty list")
    names: set[str] = set()
    for topic in topics:
        missing = REQUIRED_TOPIC_FIELDS - set(topic)
        if missing:
            raise AssertionError(f"topic missing fields: {sorted(missing)}")
        name = topic["name"]
        if name in names:
            raise AssertionError(f"duplicate topic: {name}")
        names.add(name)
        if topic["record_type"] not in KNOWN_RECORD_TYPES:
            raise AssertionError(f"{name} unknown record_type: {topic['record_type']}")
        schema_path = ROOT / topic["schema"]
        if not schema_path.exists():
            raise AssertionError(f"{name} schema path does not exist: {topic['schema']}")
        gates = set(topic["required_gates"])
        if topic["record_type"] != "CreditRecord" and not REQUIRED_TOPIC_GATES.issubset(gates):
            raise AssertionError(f"{name} missing required gates: {sorted(REQUIRED_TOPIC_GATES - gates)}")
        if topic["side_effects"] != ["none"]:
            raise AssertionError(f"{name} must declare side_effects ['none'] in contract-only tranche")
    return names


def validate_fixtures(topic_names: set[str]) -> None:
    fixture_files = sorted(FIXTURES.glob("*.json"))
    if not fixture_files:
        raise AssertionError("no stream fixtures found")
    for path in fixture_files:
        doc = _load_json(path)
        topic = doc.get("topic")
        if topic not in topic_names:
            raise AssertionError(f"{path} references unknown topic: {topic}")
        if doc.get("side_effects") != ["none"]:
            raise AssertionError(f"{path} must declare side_effects ['none']")
        if not doc.get("claim_boundary"):
            raise AssertionError(f"{path} must include claim_boundary")
        if topic == "atlas.community.credit.recorded":
            if doc.get("non_transferable") is not True:
                raise AssertionError(f"{path} credit fixture must be non_transferable")
            if doc.get("economic_obligation") is not False:
                raise AssertionError(f"{path} credit fixture must not create economic obligation")


def main() -> int:
    names = validate_topics()
    validate_fixtures(names)
    print("community streams: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
