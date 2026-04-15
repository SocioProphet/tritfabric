from __future__ import annotations

import base64
import hmac
import hashlib
from typing import Optional


def load_key_b64(b64: str) -> bytes:
    return base64.b64decode(b64.encode("utf-8"))


def hmac_sign(payload: bytes, key: bytes) -> str:
    """Return hex HMAC-SHA256."""
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def hmac_verify(payload: bytes, key: bytes, sig_hex: str) -> bool:
    expected = hmac_sign(payload, key)
    return hmac.compare_digest(expected, (sig_hex or "").lower())
