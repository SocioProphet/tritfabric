from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

try:
    import ray  # type: ignore
    from ray import serve  # type: ignore
except Exception:  # pragma: no cover
    ray = None
    serve = None


@dataclass(frozen=True)
class AutoscaleDecision:
    """Pure autoscaler decision result for RouterCore-compatible status payloads."""

    weights: Dict[str, int]
    pressure: Dict[str, float]
    changed: bool
    reason: str


class RouterAutoscalerCore:
    """Pressure-aware router weight adjuster.

    This class has no hard Ray dependency and no side effects. It consumes a
    status payload shaped like RouterCore.status():

    {
      "weights": {backend: int},
      "lat_p95": {backend: float_ms},
      "inflight": {backend: int}
    }

    Higher p95 latency and inflight load increase pressure. The autoscaler moves
    weight away from the highest-pressure backend toward the lowest-pressure
    backend while preserving a minimum weight for every backend.
    """

    def __init__(
        self,
        router_name: str = "Router",
        target_p95_ms: float = 80.0,
        min_weight: int = 1,
        period_s: float = 5.0,
        step: int = 1,
        inflight_weight: float = 0.1,
    ):
        if target_p95_ms <= 0:
            raise ValueError("target_p95_ms must be positive")
        if min_weight < 0:
            raise ValueError("min_weight must be non-negative")
        if period_s <= 0:
            raise ValueError("period_s must be positive")
        if step <= 0:
            raise ValueError("step must be positive")
        if inflight_weight < 0:
            raise ValueError("inflight_weight must be non-negative")
        self.router_name = router_name
        self.target_p95 = float(target_p95_ms)
        self.min_w = int(min_weight)
        self.period_s = float(period_s)
        self.step = int(step)
        self.inflight_weight = float(inflight_weight)
        self.running = False

    def reconfigure(
        self,
        target_p95_ms: Optional[float] = None,
        min_weight: Optional[int] = None,
        period_s: Optional[float] = None,
        step: Optional[int] = None,
        inflight_weight: Optional[float] = None,
    ) -> Dict[str, Any]:
        if target_p95_ms is not None:
            if target_p95_ms <= 0:
                raise ValueError("target_p95_ms must be positive")
            self.target_p95 = float(target_p95_ms)
        if min_weight is not None:
            if min_weight < 0:
                raise ValueError("min_weight must be non-negative")
            self.min_w = int(min_weight)
        if period_s is not None:
            if period_s <= 0:
                raise ValueError("period_s must be positive")
            self.period_s = float(period_s)
        if step is not None:
            if step <= 0:
                raise ValueError("step must be positive")
            self.step = int(step)
        if inflight_weight is not None:
            if inflight_weight < 0:
                raise ValueError("inflight_weight must be non-negative")
            self.inflight_weight = float(inflight_weight)
        return {
            "ok": True,
            "target_p95_ms": self.target_p95,
            "min_weight": self.min_w,
            "period_s": self.period_s,
            "step": self.step,
            "inflight_weight": self.inflight_weight,
        }

    def stop(self) -> None:
        self.running = False

    def pressure(self, status: Mapping[str, Any]) -> Dict[str, float]:
        weights = {str(k): int(v) for k, v in (status.get("weights") or {}).items()}
        lat_p95 = {str(k): float(v) for k, v in (status.get("lat_p95") or {}).items()}
        inflight = {str(k): int(v) for k, v in (status.get("inflight") or {}).items()}
        out: Dict[str, float] = {}
        for backend in weights:
            latency_pressure = lat_p95.get(backend, 0.0) / self.target_p95
            inflight_pressure = inflight.get(backend, 0) * self.inflight_weight
            out[backend] = latency_pressure + inflight_pressure
        return out

    def decide(self, status: Mapping[str, Any]) -> AutoscaleDecision:
        weights = {str(k): max(0, int(v)) for k, v in (status.get("weights") or {}).items()}
        pressure = self.pressure(status)
        if len(weights) < 2:
            return AutoscaleDecision(weights=weights, pressure=pressure, changed=False, reason="insufficient-backends")
        if not pressure:
            return AutoscaleDecision(weights=weights, pressure=pressure, changed=False, reason="no-pressure")

        hottest = max(pressure, key=pressure.get)
        coolest = min(pressure, key=pressure.get)
        if hottest == coolest:
            return AutoscaleDecision(weights=weights, pressure=pressure, changed=False, reason="flat-pressure")
        if pressure[hottest] <= 1.0:
            return AutoscaleDecision(weights=weights, pressure=pressure, changed=False, reason="within-target")
        if weights[hottest] <= self.min_w:
            return AutoscaleDecision(weights=weights, pressure=pressure, changed=False, reason="hottest-at-min-weight")

        delta = min(self.step, max(0, weights[hottest] - self.min_w))
        new_weights = dict(weights)
        new_weights[hottest] -= delta
        new_weights[coolest] += delta
        return AutoscaleDecision(weights=new_weights, pressure=pressure, changed=new_weights != weights, reason="shift-hot-to-cool")

    def step_from_status(self, st: Dict[str, Any]) -> Dict[str, Any]:
        decision = self.decide(st)
        return {
            "ok": True,
            "weights": decision.weights,
            "pressure": decision.pressure,
            "changed": decision.changed,
            "reason": decision.reason,
            "shadow": bool(st.get("shadow", False)),
        }


if ray and serve:  # pragma: no cover
    @ray.remote(num_cpus=0.1)
    class RouterAutoscaler(RouterAutoscalerCore):
        def step(self):
            rh = serve.get_deployment(self.router_name).get_handle()
            st = ray.get(rh.status.remote())
            out = self.step_from_status(st)

            if out.get("ok") and out.get("changed") and out.get("weights"):
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
    # Fallback: keep the symbol available for import; this is not runnable without Ray.
    RouterAutoscaler = None
