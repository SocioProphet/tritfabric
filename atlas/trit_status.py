from __future__ import annotations

from typing import Any, Dict, Optional

TRIT_TRUE = "TRUE"
TRIT_MID = "MID"
TRIT_FALSE = "FALSE"


def trit_status(code: str, reason: str, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a small transport-neutral Trit status envelope."""
    return {
        "code": code,
        "reason": reason,
        "info": {k: str(v) for k, v in (info or {}).items()},
    }


def status_reply(
    *,
    code: str,
    reason: str,
    state: str,
    info: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a TritRPC-style structured status reply for HTTP compatibility surfaces."""
    return {
        "trit": trit_status(code, reason, info),
        "status": {
            "state": state,
            "info": {k: str(v) for k, v in (info or {}).items()},
        },
        "payload": payload or {},
    }
