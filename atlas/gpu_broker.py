"""GPU broker for the Ray training substrate.

Picks the cheapest GPU that satisfies a training job across the multi-polar supply — NeoClouds (CoreWeave/Lambda/
Nebius/Crusoe), Western hyperscalers, NON-NVIDIA silicon (Huawei Ascend), and the local mesh — and renders a KubeRay
RayCluster placement for it. This is the cost layer under ``RayRunner._run_with_ray``: Ray is portable + cloud-agnostic,
so the SAME training fabric lands on whatever GPU is cheapest/compliant — the sovereignty + cost edge the
hyperscalers' lock-in MLOps can't match.

Prices are illustrative list rates (USD/hr) for ranking; swap in a live billing adapter without changing the API.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

# CANONICAL catalog (prophet-core-contracts/contracts/gpu-catalog.v1.json), vendored next to this module + shared with
# noetica's cloud-broker. Single source of truth — edit the canonical file + re-vendor; don't hand-edit rows here.
_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "gpu-catalog.v1.json")


def _load_catalog() -> List[Dict[str, Any]]:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        raw = json.load(f).get("skus", [])
    out: List[Dict[str, Any]] = []
    for s in raw:
        g = s.get("gpu")
        if not g:  # GPU broker → GPU rows only
            continue
        row: Dict[str, Any] = {
            "provider": s["provider"], "sku": s["name"], "gpu": g["type"], "gpu_mem": g.get("memGiB", 0),
            "vcpus": s["vcpus"], "mem_gib": s["memGiB"], "usd_hr": s["usdPerHour"],
        }
        if "spotPerHour" in s:
            row["spot_hr"] = s["spotPerHour"]
        if s.get("neocloud"):
            row["neocloud"] = True
        if s.get("nvidia") is False:
            row["nvidia"] = False
        out.append(row)
    return out


GPU_CATALOG: List[Dict[str, Any]] = _load_catalog()

NEOCLOUDS = ("coreweave", "lambda", "nebius", "crusoe")


def _satisfies(sku: Dict[str, Any], req: Dict[str, Any]) -> bool:
    gpu = req.get("gpu") or {}
    if gpu:
        want = str(gpu.get("type") or "")
        if want and want.lower() not in str(sku["gpu"]).lower():
            return False
        if gpu.get("min_mem_gib") and sku["gpu_mem"] < gpu["min_mem_gib"]:
            return False
    if req.get("vcpus") and sku["vcpus"] < req["vcpus"]:
        return False
    if req.get("mem_gib") and sku["mem_gib"] < req["mem_gib"]:
        return False
    return True


def broker_compute(req: Dict[str, Any], catalog: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Rank satisfying SKUs by effective price; return best + ranked + savings.

    req: {gpu:{type,count,min_mem_gib}, vcpus, mem_gib, hours, spot, providers:[...], exclude_local}
    """
    cat = catalog or GPU_CATALOG
    allow = set(req["providers"]) if req.get("providers") else None
    hours = max(0.0, float(req.get("hours") or 0))
    quotes = []
    for sku in cat:
        if allow and sku["provider"] not in allow:
            continue
        if req.get("exclude_local") and sku["provider"] == "local":
            continue
        if not _satisfies(sku, req):
            continue
        use_spot = bool(req.get("spot")) and sku.get("spot_hr") is not None
        per_hr = sku["spot_hr"] if use_spot else sku["usd_hr"]
        quotes.append({"sku": sku, "per_hr": per_hr, "total_usd": round(per_hr * hours, 2), "spot": use_spot})
    quotes.sort(key=lambda q: (q["total_usd"], q["per_hr"]))
    best = quotes[0] if quotes else None
    savings = 0
    if len(quotes) >= 2 and quotes[-1]["total_usd"] > 0:
        savings = round((quotes[-1]["total_usd"] - quotes[0]["total_usd"]) / quotes[-1]["total_usd"] * 100)
    return {"best": best, "ranked": quotes, "considered": len(quotes), "savings_pct": savings}


def plan_ray_cluster(best: Dict[str, Any], image: str = "ghcr.io/socioprophet/ray-train:tritfabric", gpu_count: int = 1) -> Dict[str, Any]:
    """Render a KubeRay RayCluster placement for the chosen SKU (Ray Train/Tune lands here)."""
    sku = best["sku"]
    return {
        "apiVersion": "ray.io/v1",
        "kind": "RayCluster",
        "provider": sku["provider"],
        "image": image,
        "head": {"cpu": 4, "mem_gib": 16},
        "worker_group": {
            "replicas": 1,
            "cpu": sku["vcpus"],
            "mem_gib": sku["mem_gib"],
            "gpu": {"type": sku["gpu"], "count": gpu_count},
        },
        "est_usd_per_hour": best["per_hr"],
    }


def plan_cheapest(req: Dict[str, Any], image: str = "ghcr.io/socioprophet/ray-train:tritfabric") -> Optional[Dict[str, Any]]:
    """Convenience: broker + plan in one call. Returns the RayCluster placement, or None if nothing satisfies."""
    result = broker_compute(req)
    if not result["best"]:
        return None
    count = int((req.get("gpu") or {}).get("count") or 1)
    return plan_ray_cluster(result["best"], image=image, gpu_count=count)
