"""Drift guard: the local autonomy-ladder config must match the canonical export.

The single source of truth is SocioProphet/prophet-mesh
(specs/ai-driven-development.yaml -> ai-driven-development.ladder.json). We
vendor that export as configs/autonomy-ladder.canonical.json and assert the
hand-readable configs/autonomy-ladder.yaml the gate consumes never drifts from
it. Re-vendor with: prophet-mesh export-autonomy-ladder --out, then copy.
"""

from __future__ import annotations

import json
import os

import yaml

HERE = os.path.dirname(__file__)
CONFIG = os.path.join(HERE, "..", "configs", "autonomy-ladder.yaml")
CANONICAL = os.path.join(HERE, "..", "configs", "autonomy-ladder.canonical.json")


def test_config_matches_canonical():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(CANONICAL, encoding="utf-8") as f:
        canon = json.load(f)

    assert cfg["trust_kernel_gate_order"] == canon["trust_kernel_gate_order"]

    cfg_levels = cfg["levels"]
    canon_levels = {lvl["level"]: lvl for lvl in canon["levels"]}
    assert set(cfg_levels) == set(canon_levels), "level set drifted from canonical"

    for name, c in canon_levels.items():
        local = cfg_levels[name]
        assert local["gate"] == c["gate"], f"{name} gate drifted"
        assert local["evidence_required"] == c["evidence_required"], f"{name} evidence drifted"
