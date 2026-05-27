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
    def __init__(self, fail: bool = False):
        self.policy = _Policy()
        self.registry = _Registry()
        self.fail = fail

    def get_status(self, job_id):
        return {"state": "SUCCEEDED", "info": {"tenant": "tenant-a"}}

    def submit_job(self, req):
        return "job-1"

    def promote(self, job_id):
        if self.fail:
            raise ValueError("SHACL validation failed")
        return {"card": {"model": {"id": job_id}}, "report": {"ok": True}}


def test_promote_status_returns_trit_true():
    client = TestClient(create_app(_Daemon(fail=False)))

    res = client.post("/v1/promote/job-1")

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "TRUE"
    assert body["trit"]["reason"] == "PROMOTED"
    assert body["status"]["state"] == "SUCCEEDED"
    assert body["payload"]["card"]["model"]["id"] == "job-1"


def test_promote_status_returns_trit_false_without_http_error():
    client = TestClient(create_app(_Daemon(fail=True)))

    res = client.post("/v1/promote/job-1")

    assert res.status_code == 200
    body = res.json()
    assert body["trit"]["code"] == "FALSE"
    assert body["trit"]["reason"] == "PROMOTION_GATE_FAILED"
    assert body["status"]["state"] == "FAILED"
    assert "SHACL validation failed" in body["status"]["info"]["error"]


def test_compat_promote_still_returns_failed_precondition():
    client = TestClient(create_app(_Daemon(fail=True)))

    res = client.post("/v1/jobs/job-1/promote")

    assert res.status_code == 412
    assert "SHACL validation failed" in res.json()["detail"]
