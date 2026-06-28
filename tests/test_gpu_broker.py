"""Proofs for the GPU broker that feeds the Ray training substrate."""
from atlas.gpu_broker import broker_compute, plan_cheapest, plan_ray_cluster, NEOCLOUDS


def test_h100_brokers_to_cheapest_neocloud():
    r = broker_compute({"gpu": {"type": "H100", "count": 1}, "hours": 100, "exclude_local": True})
    assert r["best"] is not None
    assert r["best"]["sku"]["provider"] in NEOCLOUDS  # cheapest H100 is a neocloud
    assert r["best"]["per_hr"] <= 2.0
    assert r["savings_pct"] > 0


def test_sovereign_only_restriction():
    r = broker_compute({"gpu": {"count": 1}, "hours": 5, "providers": list(NEOCLOUDS)})
    assert r["best"]["sku"]["provider"] in NEOCLOUDS
    assert all(q["sku"]["provider"] in NEOCLOUDS for q in r["ranked"])


def test_non_nvidia_ascend_is_brokerable():
    r = broker_compute({"gpu": {"type": "Ascend", "count": 1}, "hours": 10})
    assert r["best"] is not None
    assert r["best"]["sku"]["provider"] == "huawei"
    assert r["best"]["sku"].get("nvidia") is False


def test_plan_cheapest_renders_kuberay_spec():
    spec = plan_cheapest({"gpu": {"type": "H100", "count": 1}, "hours": 10, "exclude_local": True})
    assert spec is not None
    assert spec["kind"] == "RayCluster"
    assert spec["worker_group"]["gpu"]["count"] == 1
    assert "H100" in spec["worker_group"]["gpu"]["type"]


def test_no_satisfying_gpu_returns_none():
    assert plan_cheapest({"gpu": {"type": "NONEXISTENT", "count": 99}, "hours": 1}) is None


def test_spot_pricing_is_cheaper():
    od = broker_compute({"gpu": {"type": "A100", "count": 1}, "hours": 10})
    spot = broker_compute({"gpu": {"type": "A100", "count": 1}, "hours": 10, "spot": True})
    assert spot["best"]["per_hr"] <= od["best"]["per_hr"]
