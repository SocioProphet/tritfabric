from __future__ import annotations

import pytest

import atlas.serve.autoscaler as autoscaler_mod
from atlas.serve.autoscaler import RouterAutoscalerCore


def test_autoscaler_shifts_weight_from_hot_to_cool_backend():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=2, inflight_weight=0.1)
    status = {
        "weights": {"blue": 10, "green": 10},
        "lat_p95": {"blue": 250.0, "green": 50.0},
        "inflight": {"blue": 5, "green": 0},
    }

    decision = autoscaler.decide(status)

    assert decision.changed is True
    assert decision.reason == "shift-hot-to-cool"
    assert decision.weights == {"blue": 8, "green": 12}
    assert decision.adjusted_backend == "blue"
    assert decision.pressure["blue"] > decision.pressure["green"]


def test_autoscaler_does_not_change_when_within_target():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=2, inflight_weight=0.1)
    status = {
        "weights": {"blue": 10, "green": 10},
        "lat_p95": {"blue": 80.0, "green": 50.0},
        "inflight": {"blue": 0, "green": 0},
    }

    decision = autoscaler.decide(status)

    assert decision.changed is False
    assert decision.reason == "within-target"
    assert decision.adjusted_backend is None
    assert decision.weights == {"blue": 10, "green": 10}


def test_autoscaler_respects_min_weight():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=3, step=5, inflight_weight=0.0)
    status = {
        "weights": {"blue": 4, "green": 10},
        "lat_p95": {"blue": 500.0, "green": 10.0},
        "inflight": {"blue": 0, "green": 0},
    }

    decision = autoscaler.decide(status)

    assert decision.changed is True
    assert decision.weights["blue"] == 3
    assert decision.weights["green"] == 11


def test_autoscaler_single_backend_is_noop():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0)
    decision = autoscaler.decide({"weights": {"blue": 10}, "lat_p95": {"blue": 500.0}, "inflight": {"blue": 10}})

    assert decision.changed is False
    assert decision.reason == "insufficient-backends"
    assert decision.weights == {"blue": 10}


def test_step_from_status_returns_router_update_payload():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=1)
    out = autoscaler.step_from_status(
        {
            "weights": {"blue": 10, "green": 10},
            "lat_p95": {"blue": 200.0, "green": 50.0},
            "inflight": {"blue": 0, "green": 0},
            "shadow": True,
        },
        record_metrics=False,
    )

    assert out["ok"] is True
    assert out["changed"] is True
    assert out["weights"] == {"blue": 9, "green": 11}
    assert out["adjusted_backend"] == "blue"
    assert out["shadow"] is True


def test_step_from_status_records_observability_decision(monkeypatch):
    calls = []

    def fake_record_autoscale_decision(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(autoscaler_mod, "record_autoscale_decision", fake_record_autoscale_decision)
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=1, step=1)

    out = autoscaler.step_from_status(
        {
            "weights": {"blue": 10, "green": 10},
            "lat_p95": {"blue": 200.0, "green": 50.0},
            "inflight": {"blue": 1, "green": 0},
        }
    )

    assert out["changed"] is True
    assert len(calls) == 1
    assert calls[0]["reason"] == "shift-hot-to-cool"
    assert calls[0]["changed"] is True
    assert calls[0]["adjusted_backend"] == "blue"
    assert calls[0]["pressure"]["blue"] > calls[0]["pressure"]["green"]


def test_autoscaler_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="target_p95_ms"):
        RouterAutoscalerCore(target_p95_ms=0)
    with pytest.raises(ValueError, match="min_weight"):
        RouterAutoscalerCore(target_p95_ms=100, min_weight=-1)
    with pytest.raises(ValueError, match="step"):
        RouterAutoscalerCore(target_p95_ms=100, step=0)


def test_reconfigure_updates_parameters():
    autoscaler = RouterAutoscalerCore(target_p95_ms=100.0)
    out = autoscaler.reconfigure(target_p95_ms=120.0, min_weight=2, step=3, inflight_weight=0.2)

    assert out["target_p95_ms"] == 120.0
    assert out["min_weight"] == 2
    assert out["step"] == 3
    assert out["inflight_weight"] == 0.2
