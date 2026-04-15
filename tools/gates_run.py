from __future__ import annotations

import argparse
import json
import os

from atlas.autopilot.promotion_controller import PromotionController


def main() -> None:
    p = argparse.ArgumentParser(description="Run promotion gates for a job_id")
    p.add_argument("job_id")
    p.add_argument("--artifacts", default=os.getenv("ATLAS_ARTIFACTS", "artifacts"))
    p.add_argument("--onnx-thr", type=float, default=float(os.getenv("ATLAS_ONNX_COS_THR", "0.995")))
    p.add_argument("--eval-thr", type=float, default=float(os.getenv("ATLAS_EVAL_DELTA_THR", "0.01")))
    args = p.parse_args()

    pc = PromotionController(
        artifacts_root=args.artifacts,
        onnx_cosine_threshold=args.onnx_thr,
        eval_delta_threshold=args.eval_thr,
        shacl_enforce=True,
    )
    report = pc.run_gates(args.job_id, req={}, best={})
    print(json.dumps(report, indent=2))
    if not report.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
