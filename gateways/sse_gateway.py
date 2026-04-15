from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from atlas.rpc.server import OptInGuard
from atlas.security.aead import load_key_b64, hmac_verify


app = FastAPI(title="TritFabric SSE Gateway", version="0.1")

# In SourceOS mode, SSE gateway should also be opt-in protected.
guard = OptInGuard(
    opt_in_required=(os.getenv("ATLAS_OPT_IN_REQUIRED", "true").lower() in ("1", "true", "yes", "on")),
    opt_in_token_sha256=os.getenv("ATLAS_OPT_IN_TOKEN_SHA256", ""),
)

# Optional integrity lane (HMAC today; AEAD upgrade path).
_HMAC_KEY_B64 = os.getenv("TRITFABRIC_HMAC_KEY_B64", "").strip()
_HMAC_KEY = load_key_b64(_HMAC_KEY_B64) if _HMAC_KEY_B64 else None


def _check_optin(token: Optional[str]) -> None:
    md = [("x-opt-in-token", token or "")]
    try:
        guard.check(md)
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


def _check_sig(body_bytes: bytes, sig_hex: Optional[str]) -> None:
    if _HMAC_KEY is None:
        return
    if not sig_hex:
        raise HTTPException(status_code=401, detail="missing X-Trit-Sig")
    if not hmac_verify(body_bytes, _HMAC_KEY, sig_hex):
        raise HTTPException(status_code=401, detail="invalid X-Trit-Sig")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/v1/sse/echo")
async def sse_echo(
    request: Request,
    x_opt_in_token: Optional[str] = Header(default=None),
    x_trit_sig: Optional[str] = Header(default=None),
):
    _check_optin(x_opt_in_token)

    body_bytes = await request.body()
    _check_sig(body_bytes, x_trit_sig)

    payload: Dict[str, Any] = json.loads(body_bytes.decode("utf-8") or "{}")
    text = str(payload.get("text", ""))

    async def gen():
        # toy streaming: emit one word at a time.
        for w in text.split():
            yield {"event": "token", "data": w}
            time.sleep(0.02)
        yield {"event": "done", "data": ""}

    return EventSourceResponse(gen())
