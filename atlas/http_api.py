from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException

from atlas.community_api import router as community_router
from atlas.rpc.server import OptInGuard  # reuse guard logic
from atlas.observability.metrics import record_request
from atlas.trit_status import TRIT_FALSE, TRIT_TRUE, status_reply


def create_app(daemon) -> FastAPI:
    app = FastAPI(title="Atlas OS Service", version="0.1")
    app.include_router(community_router)

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

    def tenant_for_job(job_id: str) -> str:
        st = daemon.get_status(job_id)
        return str((st.get("info") or {}).get("tenant", "default"))

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
        """Compatibility promotion route: preserves existing HTTP error behavior."""
        check(x_opt_in_token)
        tenant = tenant_for_job(job_id)
        try:
            out = daemon.promote(job_id)
            record_request("HTTP/POST /v1/jobs/{id}/promote", tenant, "TRUE")
            return out
        except ValueError as e:
            record_request("HTTP/POST /v1/jobs/{id}/promote", tenant, "FALSE")
            raise HTTPException(status_code=412, detail=str(e))

    @app.post("/v1/promote/{job_id}")
    def promote_status(job_id: str, x_opt_in_token: Optional[str] = Header(default=None)):
        """TritRPC-style promotion route: always returns a structured status envelope."""
        check(x_opt_in_token)
        tenant = tenant_for_job(job_id)
        try:
            out = daemon.promote(job_id)
            record_request("HTTP/POST /v1/promote", tenant, "TRUE")
            return status_reply(
                code=TRIT_TRUE,
                reason="PROMOTED",
                state="SUCCEEDED",
                info={"job_id": job_id, "tenant": tenant},
                payload=out,
            )
        except ValueError as e:
            record_request("HTTP/POST /v1/promote", tenant, "FALSE")
            return status_reply(
                code=TRIT_FALSE,
                reason="PROMOTION_GATE_FAILED",
                state="FAILED",
                info={"job_id": job_id, "tenant": tenant, "error": str(e)},
            )
        except Exception as e:
            record_request("HTTP/POST /v1/promote", tenant, "FALSE")
            return status_reply(
                code=TRIT_FALSE,
                reason="PROMOTION_ERROR",
                state="FAILED",
                info={"job_id": job_id, "tenant": tenant, "error": str(e)},
            )

    @app.get("/v1/registry")
    def list_registry(x_opt_in_token: Optional[str] = Header(default=None)):
        check(x_opt_in_token)
        record_request("HTTP/GET /v1/registry", "default", "TRUE")
        return daemon.registry.list_artifacts()

    return app
