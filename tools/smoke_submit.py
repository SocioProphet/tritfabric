from __future__ import annotations

import os
import requests
import json


def main() -> None:
    api = os.getenv("ATLAS_HTTP", "http://127.0.0.1:8000")
    token = os.getenv("ATLAS_OPT_IN_TOKEN", "")
    headers = {}
    if token:
        headers["X-Opt-In-Token"] = token

    req = {
        "tenant": "default",
        "task": "demo",
        "entrypoint": "toy",
        "metric": "val_score",
        "mode": "max",
        "resources": {"CPU": 1, "GPU": 0, "MEM": 0.1},
        "export": {"onnx": {"runtime_check": False}},
    }

    r = requests.post(f"{api}/v1/tune", headers=headers, json=req, timeout=10)
    r.raise_for_status()
    job_id = r.json()["id"]
    print("submitted", job_id)

    for _ in range(40):
        st = requests.get(f"{api}/v1/jobs/{job_id}/status", headers=headers, timeout=10).json()
        print("status", st)
        if st.get("state") in ("SUCCEEDED", "FAILED"):
            break

    # Attempt promotion (may be blocked by opt-in token / SHACL etc)
    pr = requests.post(f"{api}/v1/jobs/{job_id}/promote", headers=headers, timeout=10)
    print("promote", pr.status_code)
    print(pr.text)


if __name__ == "__main__":
    main()
