from __future__ import annotations

from fastapi.testclient import TestClient

from atlas.http_api import create_app


class _Policy:
    def get(self, *keys, default=None):
        if keys == ("security", "opt_in_required"):
            return False
        return default


class _Registry:
    def list_artifacts(self):
        return {}


class _Daemon:
    policy = _Policy()
    registry = _Registry()

    def get_status(self, job_id):
        return {"state": "UNKNOWN", "info": {"tenant": "default"}}

    def submit_job(self, req):
        return "job-1"

    def promote(self, job_id):
        return {"card": {"model": {"id": job_id}}, "report": {"ok": True}}


def _client():
    return TestClient(create_app(_Daemon()))


def test_feedback_accepts_eligible_event_without_mutation():
    res = _client().post(
        "/v1/community/feedback",
        json={
            "event_id": "hf-1",
            "consent": True,
            "license": "CC-BY-4.0",
            "lineage": ["source-a"],
            "rubric": {"helpfulness": 1.0},
            "score": 0.9,
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "TRUE"
    assert body["payload"]["mutates_model"] is False
    assert body["payload"]["promotes_artifact"] is False


def test_feedback_rejects_missing_consent():
    res = _client().post(
        "/v1/community/feedback",
        json={"event_id": "hf-2", "license": "CC-BY-4.0", "lineage": ["source-a"], "rubric": {"helpfulness": 1.0}, "score": 0.9},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "FALSE"
    assert body["trit"]["reason"] == "COMMUNITY_EVENT_REJECTED"
    assert "consent=true" in body["trit"]["info"]["missing"]


def test_curation_rejects_missing_lineage():
    res = _client().post(
        "/v1/community/curation",
        json={"record_id": "cur-1", "artifact_uri": "s3://example/data", "checksum": "sha256:abc", "license": "CC-BY-4.0", "consent": True},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "FALSE"
    assert "lineage" in body["trit"]["info"]["missing"]


def test_proposal_accepts_review_only():
    res = _client().post("/v1/community/proposals", json={"proposal_id": "prop-1", "title": "Review new curriculum", "lineage": ["source-a"]})

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "TRUE"
    assert body["payload"]["requires_manual_review"] is True
    assert body["payload"]["mutates_model"] is False


def test_reputation_placeholder_is_non_economic():
    res = _client().get("/v1/community/reputation/user-1")

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "TRUE"
    assert body["payload"]["non_transferable"] is True
    assert body["payload"]["economic_obligation"] is False
