from __future__ import annotations

import argparse
import json
import os
import sys
import requests


def _headers() -> dict:
    token = os.getenv("ATLAS_OPT_IN_TOKEN", "")
    return {"X-Opt-In-Token": token} if token else {}


def cmd_submit(args: argparse.Namespace) -> None:
    api = args.api
    with open(args.req, "r", encoding="utf-8") as f:
        req = json.load(f)
    r = requests.post(f"{api}/v1/tune", headers=_headers(), json=req, timeout=30)
    print(r.status_code, r.text)
    r.raise_for_status()


def cmd_status(args: argparse.Namespace) -> None:
    api = args.api
    r = requests.get(f"{api}/v1/jobs/{args.job_id}/status", headers=_headers(), timeout=30)
    print(r.status_code, r.text)
    r.raise_for_status()


def cmd_promote(args: argparse.Namespace) -> None:
    api = args.api
    r = requests.post(f"{api}/v1/jobs/{args.job_id}/promote", headers=_headers(), timeout=30)
    print(r.status_code, r.text)
    if r.status_code >= 400:
        sys.exit(1)


def cmd_registry(args: argparse.Namespace) -> None:
    api = args.api
    r = requests.get(f"{api}/v1/registry", headers=_headers(), timeout=30)
    print(json.dumps(r.json(), indent=2))


def main() -> None:
    p = argparse.ArgumentParser(prog="tritfabricctl")
    p.add_argument("--api", default=os.getenv("ATLAS_HTTP", "http://127.0.0.1:8000"))

    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("submit", help="submit a tune job")
    s.add_argument("--req", required=True, help="path to JSON request")
    s.set_defaults(func=cmd_submit)

    s = sub.add_parser("status", help="job status")
    s.add_argument("job_id")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("promote", help="promote job artifact (runs gates)")
    s.add_argument("job_id")
    s.set_defaults(func=cmd_promote)

    s = sub.add_parser("registry", help="list registry")
    s.set_defaults(func=cmd_registry)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
