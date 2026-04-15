from __future__ import annotations

import argparse
import os
import threading

import uvicorn

from atlas.policy import Policy
from atlas.daemon import Daemon
from atlas.http_api import create_app
from atlas.observability.metrics import start_metrics_server
from atlas.observability.logs import configure_json_logging


def main() -> None:
    parser = argparse.ArgumentParser(prog="atlasd", description="Atlas OS Service (TritFabric runtime)")
    parser.add_argument("--config", default=os.getenv("ATLAS_POLICY", "configs/policy.yaml"), help="Path to policy/config YAML")
    parser.add_argument("--host", default=os.getenv("ATLAS_HTTP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("ATLAS_HTTP_PORT", "8000")))
    parser.add_argument("--metrics-port", type=int, default=int(os.getenv("ATLAS_METRICS_PORT", "9108")))
    parser.add_argument(
        "--shacl-enforce",
        default=os.getenv("ATLAS_SHACL_ENFORCE", "true"),
        help="true|false: block promotion on SHACL violations (default true)",
    )
    parser.add_argument("--grpc", action="store_true", help="Also start gRPC server (requires generated stubs)")
    parser.add_argument("--grpc-host", default=os.getenv("ATLAS_GRPC_HOST", "127.0.0.1"))
    parser.add_argument("--grpc-port", type=int, default=int(os.getenv("ATLAS_GRPC_PORT", "50051")))
    args = parser.parse_args()

    configure_json_logging(os.getenv("ATLAS_LOG_LEVEL", "INFO"))
    start_metrics_server(args.metrics_port)

    shacl_enforce = str(args.shacl_enforce).lower() in ("1", "true", "yes", "on")
    policy = Policy.from_file(args.config)
    artifacts_root = policy.get("artifacts", "root", default=os.getenv("ATLAS_ARTIFACTS", "artifacts"))

    daemon = Daemon(policy, artifacts_root, shacl_enforce=shacl_enforce)
    daemon.start()

    if args.grpc:
        from atlas.rpc.server import serve_grpc

        th = threading.Thread(target=serve_grpc, args=(daemon, args.grpc_host, args.grpc_port), daemon=True)
        th.start()

    app = create_app(daemon)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
