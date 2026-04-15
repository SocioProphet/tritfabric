from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import os
import yaml


@dataclass
class Policy:
    """Thin wrapper around a policy document.

    We keep this intentionally boring. Policy is loaded once at daemon start and
    treated as configuration, not as an executable language.
    """

    doc: Dict[str, Any]

    @classmethod
    def from_file(cls, path: str) -> "Policy":
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {})

    @classmethod
    def from_env_or_default(cls, default_path: str) -> "Policy":
        path = os.getenv("ATLAS_POLICY", default_path)
        return cls.from_file(path)

    def get(self, *keys: str, default: Any = None) -> Any:
        cur: Any = self.doc
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur
