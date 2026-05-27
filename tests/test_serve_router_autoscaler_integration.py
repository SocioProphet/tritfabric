from __future__ import annotations

import collections

from atlas.serve.autoscaler import RouterAutoscalerCore
from atlas.serve.router import RouterCore


def _seed_latency(router: RouterCore, backend: str, values: list[float]) -> None:
    router._lat_win[backend] = collections.deque(values, maxlen=router.win_size)


def test_autoscaler_updates_routercore_weights_from_status_loop():
    router = RouterCore(weights={"blue": 10, "green": 10}, shadow=True, sticky=True, window_size=10)
    _seed_latency(router, "blue", [200.0, 220.0, 240.0, 260.0])
    _seed_latency(router, "green", [20.0, 30.0, 40.0, 50.0])
    router._inflight["blue"] = 2
    router._inflight["green"] = 0

    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=2, inflight_weight=0.1)
    out = autoscaler.step_from_status(router.status(), record_metrics=False)
    update = router.update(out["weights"], shadow=out["shadow"])

    assert out["changed"] is True
    assert out["adjusted_backend"] == "blue"
    assert update["weights"] == {"blue": 8, "green": 12}
    assert update["shadow"] is True
    assert update["sticky"] is True
    assert router.status()["weights"] == {"blue": 8, "green": 12}


def test_autoscaler_routercore_loop_noops_when_within_target():
    router = RouterCore(weights={"blue": 10, "green": 10}, shadow=False, sticky=False, window_size=10)
    _seed_latency(router, "blue", [50.0, 60.0, 70.0])
    _seed_latency(router, "green", [30.0, 40.0, 50.0])

    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=2, inflight_weight=0.1)
    out = autoscaler.step_from_status(router.status(), record_metrics=False)

    assert out["changed"] is False
    assert out["reason"] == "within-target"
    assert out["weights"] == {"blue": 10, "green": 10}


def test_router_update_removes_retired_backend_windows_and_inflight():
    router = RouterCore(weights={"blue": 10, "green": 10}, window_size=10)
    _seed_latency(router, "blue", [200.0, 220.0])
    _seed_latency(router, "green", [20.0, 30.0])
    router._inflight["green"] = 3

    update = router.update({"blue": 20}, shadow=False, sticky=True)

    assert update["weights"] == {"blue": 20}
    assert update["sticky"] is True
    assert "green" not in router._lat_win
    assert "green" not in router._inflight
    assert router.status()["weights"] == {"blue": 20}


def test_routercore_route_populates_status_without_ray(event_loop):
    router = RouterCore(weights={"blue": 1}, window_size=10)

    result = event_loop.run_until_complete(router.route({"x": 1}))
    status = router.status()

    assert result["backend"] == "blue"
    assert status["weights"] == {"blue": 1}
    assert status["inflight"].get("blue", 0) == 0
    assert status["lat_p95"]["blue"] >= 0.0
