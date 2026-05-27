#!/usr/bin/env python3
"""Validate recovered knowledge-framework contract files.

This script intentionally avoids optional runtime services. It checks that:
- JSON-LD context files are parseable JSON and contain required terms;
- Avro schema files are parseable JSON and expose required fields;
- SHACL Turtle files are parseable by rdflib;
- community fixtures exercise the consent/rubric/license/lineage eligibility boundary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CONTEXT_TERMS = {
    "api/jsonld/community_context.jsonld": ["HFEvent", "CurationRecord", "CreditRecord", "Curriculum", "consent", "license", "lineage", "rubric"],
    "api/jsonld/math_context.jsonld": ["ModelCard", "Model", "mathType", "calcOps", "ledgerRef", "artifactRef"],
}

REQUIRED_AVRO_FIELDS = {
    "community/schemas/HFEvent.avsc": ["event_id", "agent_id", "user_id", "rubric", "score", "consent", "license", "lineage", "ts"],
    "community/schemas/CurationRecord.avsc": ["record_id", "submitter_id", "artifact_uri", "checksum", "license", "lineage", "consent", "ts"],
    "community/schemas/CreditRecord.avsc": ["credit_id", "contributor_id", "source_event_id", "credit", "credit_basis", "accepted", "ts"],
    "community/schemas/Curriculum.avsc": ["curriculum_id", "title", "description", "rubric", "license", "lineage", "ts"],
}

SHACL_FILES = [
    "api/shapes/community_shapes.ttl",
    "api/shapes/model_shapes.ttl",
]


def load_json(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_contexts() -> None:
    for path, terms in REQUIRED_CONTEXT_TERMS.items():
        doc = load_json(path)
        ctx = doc.get("@context")
        if not isinstance(ctx, dict):
            raise AssertionError(f"{path} missing @context object")
        missing = [term for term in terms if term not in ctx]
        if missing:
            raise AssertionError(f"{path} missing context terms: {missing}")


def validate_avro_schemas() -> None:
    for path, fields in REQUIRED_AVRO_FIELDS.items():
        doc = load_json(path)
        if doc.get("type") != "record":
            raise AssertionError(f"{path} is not an Avro record")
        names = {field.get("name") for field in doc.get("fields", [])}
        missing = [field for field in fields if field not in names]
        if missing:
            raise AssertionError(f"{path} missing Avro fields: {missing}")


def validate_shacl_turtle() -> None:
    for path in SHACL_FILES:
        graph = Graph()
        graph.parse(str(ROOT / path), format="turtle")
        if len(graph) == 0:
            raise AssertionError(f"{path} parsed to an empty graph")


def eligible_hf_event(event: dict) -> bool:
    return (
        event.get("type") == "HFEvent"
        and event.get("consent") is True
        and bool(event.get("rubric"))
        and bool(event.get("license"))
        and bool(event.get("lineage"))
    )


def validate_fixtures() -> None:
    valid = load_json("community/fixtures/hf_event_valid.json")
    invalid = load_json("community/fixtures/hf_event_invalid_no_consent.json")
    if not eligible_hf_event(valid):
        raise AssertionError("valid HF event fixture did not pass eligibility check")
    if eligible_hf_event(invalid):
        raise AssertionError("invalid HF event fixture unexpectedly passed eligibility check")


def main() -> int:
    validate_contexts()
    validate_avro_schemas()
    validate_shacl_turtle()
    validate_fixtures()
    print("recovered framework contracts: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
