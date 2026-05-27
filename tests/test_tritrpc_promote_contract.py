from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_proto_declares_statusreply_promote_contract():
    proto = (ROOT / "api/atlas/v1/atlas.proto").read_text(encoding="utf-8")

    assert "message TritStatus" in proto
    assert "message StatusReply" in proto
    assert "rpc Promote(JobId) returns (StatusReply)" in proto
    assert 'post: "/v1/promote/{id}"' in proto


def test_canonical_contract_mentions_promotion_status_semantics():
    contract = (ROOT / "tritrpc/atlas/v1/atlas.contract.md").read_text(encoding="utf-8")

    assert "Promote (Trit-visible status projection returning StatusReply)" in contract
    assert "Promotion MUST be protocol-visible" in contract
    assert "PROMOTION_GATE_FAILED" in contract


def test_grpc_server_implements_statusreply_promote_without_gate_abort():
    server = (ROOT / "atlas/rpc/server.py").read_text(encoding="utf-8")

    assert "def _status_reply" in server
    assert "def Promote(self, req, ctx):" in server
    assert 'reason="PROMOTED"' in server
    assert 'reason="PROMOTION_GATE_FAILED"' in server
    promote_impl = server.split("def Promote(self, req, ctx):", 1)[1].split("# ServeService is optional", 1)[0]
    assert "ctx.abort(grpc.StatusCode.FAILED_PRECONDITION" not in promote_impl
