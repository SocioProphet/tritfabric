from atlas.serve.autoscaler import RouterAutoscalerCore


def test_autoscaler_step_from_status_prefers_fast_backend():
    ra = RouterAutoscalerCore(target_p95_ms=100.0, min_weight=5, max_gain=1.5, min_gain=0.5)
    st = {
        "weights": {"A": 50, "B": 50},
        "lat_p95": {"A": 200.0, "B": 60.0},
        "inflight": {"A": 2, "B": 1},
        "shadow": False,
    }
    out = ra.step_from_status(st)
    assert out["ok"]
    w = out["weights"]
    # B is faster; should gain weight relative to A
    assert w["B"] > w["A"]
    assert w["A"] >= ra.min_w
