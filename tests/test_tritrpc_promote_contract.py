from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_proto_declares_statusreply_promote_contract():
    proto = (ROOT / "api/atlas/v1/atlas.proto").read_text(encoding="utf-8")

    assert "message TritStatus" in proto
    assert "message StatusReply" in proto
    assert "rpc Promote(JobId) returns (StatusReply)" in proto
    assert 'post: "/v1/promote/{id}"' in proto


def test_canonical_contract_declares_statusreply_promote_semantics():
    contract = (ROOT / "tritrpc/atlas/v1/atlas.contract.md").read_text(encoding="utf-8")

    assert "Promote (Trit-visible status projection returning StatusReply)" in contract
    assert "StatusReply.trit.code = TRUE" in contract
    assert "StatusReply.trit.code = FALSE" in contract
    assert "PROMOTION_GATE_FAILED" in contract
