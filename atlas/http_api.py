from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from atlas.rpc.server import OptInGuard  # reuse guard logic
from atlas.observability.metrics import record_request


def create_app(daemon) -> FastAPI:
    app = FastAPI(title="Atlas OS Service", version="0.1")

    guard = OptInGuard(
        opt_in_required=bool(daemon.policy.get("security", "opt_in_required", default=True)),
        opt_in_token_sha256=str(daemon.policy.get("security", "opt_in_token_sha256", default="") or ""),
    )

    def check(token: Optional[str]) -> None:
        # mimic gRPC metadata name
        md = [("x-opt-in-token", token or "")]
        try:
            guard.check(md)
        except Exception as e:
            raise HTTPException(status_code=403, detail=str(e))

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.post("/v1/tune")
    def submit_tune(req: Dict[str, Any], x_opt_in_token: Optional[str] = Header(default=None)):
        check(x_opt_in_token)
        tenant = str(req.get("tenant", "default"))
        record_request("HTTP/POST /v1/tune", tenant, "TRUE")
        job_id = daemon.submit_job(req)
        return {"id": job_id}

    @app.get("/v1/jobs/{job_id}/status")
    def job_status(job_id: str, x_opt_in_token: Optional[str] = Header(default=None)):
        check(x_opt_in_token)
        st = daemon.get_status(job_id)
        tenant = str((st.get("info") or {}).get("tenant", "default"))
        record_request("HTTP/GET /v1/jobs/{id}/status", tenant, "TRUE")
        return st

    @app.post("/v1/jobs/{job_id}/promote")
    def promote(job_id: str, x_opt_in_token: Optional[str] = Header(default=None)):
        check(x_opt_in_token)
        try:
            out = daemon.promote(job_id)
            record_request("HTTP/POST /v1/jobs/{id}/promote", "default", "TRUE")
            return out
        except ValueError as e:
            record_request("HTTP/POST /v1/jobs/{id}/promote", "default", "FALSE")
            raise HTTPException(status_code=412, detail=str(e))

    @app.get("/v1/registry")
    def list_registry(x_opt_in_token: Optional[str] = Header(default=None)):
        check(x_opt_in_token)
        record_request("HTTP/GET /v1/registry", "default", "TRUE")
        return daemon.registry.list_artifacts()

    return app
