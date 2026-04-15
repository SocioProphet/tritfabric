from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional


def configure_json_logging(level: str = "INFO") -> None:
    """Configure a JSON-ish logger suitable for Loki ingestion.

    This is intentionally minimal. In production we'd typically use structlog or OpenTelemetry logging.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=lvl, format="%(message)s")


def log_event(
    event: str,
    level: str = "INFO",
    tenant: str = "default",
    job_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
        "level": level.upper(),
        "tenant": tenant,
        "job_id": job_id,
    }
    if extra:
        payload.update(extra)
    msg = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    getattr(logging, level.lower(), logging.info)(msg)
