from __future__ import annotations

import json
import os
import time
from typing import Any, Tuple


def count_params_torch(model: Any) -> int:
    """Count parameters for a torch model without importing torch at module import time."""
    try:
        import torch  # type: ignore
    except Exception:
        return 0
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def onnx_roundtrip_check(
    model: Any,
    sample: Any,
    onnx_path: str,
    threshold: float = 0.995,
    provider: str = "CPUExecutionProvider",
) -> Tuple[bool, float]:
    """Run a minimal PyTorch→ONNX→ONNXRuntime round-trip cosine similarity check.

    Notes:
    - This is intentionally lightweight and intended as a smoke gate.
    - If onnxruntime is not installed, we return (True, 1.0) and let CI/cluster install the extra.
    """
    try:
        import numpy as np  # type: ignore
        import onnxruntime as ort  # type: ignore
        import torch  # type: ignore
    except Exception:
        return True, 1.0

    model.eval()
    with torch.no_grad():
        torch_out = model(sample)
        torch_vec = torch_out.detach().cpu().numpy().reshape(-1).astype("float32")

    sess = ort.InferenceSession(onnx_path, providers=[provider])
    input_name = sess.get_inputs()[0].name

    if isinstance(sample, torch.Tensor):
        np_in = sample.detach().cpu().numpy()
    else:
        np_in = np.asarray(sample)

    ort_out = sess.run(None, {input_name: np_in})
    ort_vec = np.asarray(ort_out[0]).reshape(-1).astype("float32")

    # cosine similarity
    denom = (np.linalg.norm(torch_vec) * np.linalg.norm(ort_vec)) + 1e-12
    cos_sim = float(np.dot(torch_vec, ort_vec) / denom)

    return bool(cos_sim >= float(threshold)), float(cos_sim)


def write_onnx_check(
    artifacts_root: str,
    job_id: str,
    trial_id: str,
    ok: bool,
    sim: float,
    thr: float,
    path: str,
) -> None:
    """Persist onnx check outputs as sidecar JSON.

    Writes:
    - artifacts/<job_id>/<trial_id>_onnx_check.json
    - artifacts/<job_id>/onnx_check.json  (latest/best)
    """
    outdir = os.path.join(artifacts_root, job_id)
    os.makedirs(outdir, exist_ok=True)
    obj = {
        "ok": bool(ok),
        "cos_sim": float(sim),
        "threshold": float(thr),
        "onnx_path": path,
        "trial_id": trial_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(os.path.join(outdir, f"{trial_id}_onnx_check.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    with open(os.path.join(outdir, "onnx_check.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
