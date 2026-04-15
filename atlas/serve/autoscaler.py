from __future__ import annotations

import time
from typing import Any, Dict, Optional

import numpy as np

try:
    import ray  # type: ignore
    from ray import serve  # type: ignore
except Exception:  # pragma: no cover
    ray = None
    serve = None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class RouterAutoscalerCore:
    def __init__(
        self,
        router_name: str = "Router",
        target_p95_ms: float = 80.0,
        min_weight: int = 5,
        period_s: float = 5.0,
        max_gain: float = 1.5,
        min_gain: float = 0.5,
    ):
        self.router_name = router_name
        self.target_p95 = float(target_p95_ms)
        self.min_w = int(min_weight)
        self.period_s = float(period_s)
        self.max_gain = float(max_gain)
        self.min_gain = float(min_gain)
        self.running = False

    def reconfigure(self, target_p95_ms: Optional[float] = None, min_weight: Optional[int] = None, period_s: Optional[float] = None) -> Dict[str, Any]:
        if target_p95_ms is not None:
            self.target_p95 = float(target_p95_ms)
        if min_weight is not None:
            self.min_w = int(min_weight)
        if period_s is not None:
            self.period_s = float(period_s)
        return {"ok": True, "target_p95_ms": self.target_p95, "min_weight": self.min_w, "period_s": self.period_s}

    def stop(self) -> None:
        self.running = False

    def step_from_status(self, st: Dict[str, Any]) -> Dict[str, Any]:
        w = st.get("weights", {}) or {}
        if not w:
            return {"ok": False, "reason": "no backends"}

        lat = st.get("lat_p95", {}) or {}
        infl = st.get("inflight", {}) or {}

        total_old = sum(max(0, int(v)) for v in w.values()) or 1
        new_w: Dict[str, int] = {}

        for k, old in w.items():
            p95 = float(lat.get(k, self.target_p95))
            press = max(1.0, float(infl.get(k, 0)))
            raw_gain = (self.target_p95 / max(1e-3, p95))
            gain = _clamp(raw_gain / np.log1p(press), self.min_gain, self.max_gain)
            cand = max(self.min_w, int(int(old) * float(gain)))
            new_w[k] = cand

        # Normalize to keep sum stable
        total_new = sum(new_w.values()) or 1
        norm = total_old / float(total_new)
        for k in list(new_w.keys()):
            new_w[k] = max(self.min_w, int(new_w[k] * norm))

        return {"ok": True, "weights": new_w, "shadow": bool(st.get("shadow", False))}


if ray and serve:  # pragma: no cover
    @ray.remote(num_cpus=0.1)
    class RouterAutoscaler(RouterAutoscalerCore):
        def step(self):
            rh = serve.get_deployment(self.router_name).get_handle()
            st = ray.get(rh.status.remote())
            out = self.step_from_status(st)

            if out.get("ok") and out.get("weights") and out["weights"] != st.get("weights", {}):
                return ray.get(rh.update.remote(out["weights"], out.get("shadow", False)))
            return out

        def run(self):
            self.running = True
            while self.running:
                try:
                    self.step()
                except Exception:
                    pass
                time.sleep(self.period_s)
else:
    # Fallback: keep the symbol available for import; this isn't runnable without Ray.
    RouterAutoscaler = None
