"""Autonomy promotion gate for Atlas/TritFabric.

TritFabric is the promotion-discipline runtime. This gate enforces the
Prophet Mesh AI-driven-development autonomy ladder at promotion time: an
artifact may only be promoted to operate at a requested autonomy level if the
evidence token that level's gate requires is present. It is intentionally
boring and fail-closed, in the same spirit as the SHACL/ONNX gates.

The ladder definition is treated as configuration (see
``configs/autonomy-ladder.yaml``), which mirrors the canonical contract in
SocioProphet/prophet-mesh (``specs/ai-driven-development.yaml``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional
import os

import yaml

_NO_GATE = frozenset({"none", "", None})

DEFAULT_LADDER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "configs", "autonomy-ladder.yaml"
)


def _level_rank(level: str) -> int:
    try:
        return int(str(level).lstrip("Ll"))
    except (ValueError, TypeError):
        return -1


@dataclass
class AutonomyDecision:
    ok: bool
    requested_level: str
    granted_level: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "requested_level": self.requested_level,
            "granted_level": self.granted_level,
            "reason": self.reason,
        }


class AutonomyGate:
    """Promotion-time evidence gate over the autonomy ladder."""

    def __init__(self, levels: Dict[str, Dict[str, Any]]) -> None:
        # rank -> (name, evidence_required, gate)
        self._by_rank: Dict[int, Dict[str, Any]] = {}
        for name, spec in (levels or {}).items():
            rank = _level_rank(name)
            if rank < 0:
                continue
            self._by_rank[rank] = {
                "level": name,
                "evidence_required": str((spec or {}).get("evidence_required", "none")),
                "gate": str((spec or {}).get("gate", "none")),
            }
        if 0 not in self._by_rank:
            # L0 is always grantable, even if the config omits it.
            self._by_rank[0] = {"level": "L0", "evidence_required": "none", "gate": "none"}

    @classmethod
    def from_file(cls, path: Optional[str] = None) -> "AutonomyGate":
        path = path or os.getenv("ATLAS_AUTONOMY_LADDER", DEFAULT_LADDER_PATH)
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        return cls(doc.get("levels", {}))

    def _satisfied(self, rank: int, evidence: Iterable[str]) -> bool:
        required = self._by_rank[rank]["evidence_required"]
        return required in _NO_GATE or required in set(evidence)

    def max_admissible(self, evidence: Iterable[str]) -> int:
        evidence = set(evidence)
        best = 0
        for rank in sorted(self._by_rank):
            if self._satisfied(rank, evidence):
                best = rank
            else:
                break
        return best

    def evaluate(self, requested_level: str, evidence: Iterable[str]) -> AutonomyDecision:
        """Fail-closed: requested level is admitted only if its evidence is present.

        Unlike the runtime engine (which demotes), promotion BLOCKS when the
        requested level cannot be met — silently promoting at a lower level
        would ship an over-claimed artifact. The reason reports the highest
        level the evidence actually supports.
        """
        evidence = set(evidence)
        requested_rank = _level_rank(requested_level)
        if requested_rank < 0:
            return AutonomyDecision(
                ok=False,
                requested_level=str(requested_level),
                granted_level="L0",
                reason=f"unparseable autonomy level {requested_level!r}",
            )
        if requested_rank not in self._by_rank:
            return AutonomyDecision(
                ok=False,
                requested_level=f"L{requested_rank}",
                granted_level="L0",
                reason=f"L{requested_rank} not defined in ladder",
            )
        if self._satisfied(requested_rank, evidence):
            return AutonomyDecision(
                ok=True,
                requested_level=f"L{requested_rank}",
                granted_level=f"L{requested_rank}",
                reason=f"evidence satisfies gate '{self._by_rank[requested_rank]['gate']}'",
            )
        ceiling = self.max_admissible(evidence)
        need = self._by_rank[requested_rank]["evidence_required"]
        return AutonomyDecision(
            ok=False,
            requested_level=f"L{requested_rank}",
            granted_level=f"L{ceiling}",
            reason=(
                f"L{requested_rank} gate '{self._by_rank[requested_rank]['gate']}' needs "
                f"evidence '{need}' (absent); evidence supports up to L{ceiling}"
            ),
        )


def check_promotion_autonomy(
    req: Dict[str, Any], ladder_path: Optional[str] = None
) -> Optional[AutonomyDecision]:
    """Gate a promotion request that declares an ``autonomy`` block.

    Returns ``None`` when the request makes no autonomy claim (so existing
    promotion paths are unaffected), otherwise a fail-closed decision.

    Expected shape::

        req["autonomy"] = {"requested_level": "L4", "evidence": ["conductor_response_envelope"]}
    """
    block = req.get("autonomy")
    if not isinstance(block, dict):
        return None
    gate = AutonomyGate.from_file(ladder_path)
    requested = block.get("requested_level", "L0")
    evidence = block.get("evidence", []) or []
    return gate.evaluate(requested, evidence)
