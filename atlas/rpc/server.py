from __future__ import annotations

import hashlib
import os
from concurrent import futures
from typing import Any, Dict, Iterable, Optional, Tuple

try:
    import grpc  # type: ignore
except Exception:  # pragma: no cover
    grpc = None

try:
    from google.protobuf.json_format import MessageToDict  # type: ignore
except Exception:  # pragma: no cover
    MessageToDict = None  # type: ignore

from atlas.observability.metrics import record_request

# Generated modules (via `make proto` / buf generate).
# We keep imports inside functions where possible so tools can import this file without protoc output.
# Expected paths (buf): gen/python/atlas/v1/atlas_pb2.py etc.


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _metadata_get(md: Iterable[Tuple[str, str]], key: str) -> Optional[str]:
    key = key.lower()
    for k, v in md:
        if str(k).lower() == key:
            return str(v)
    return None


class AuthError(Exception):
    pass


class OptInGuard:
    def __init__(self, opt_in_required: bool, opt_in_token_sha256: str):
        self.required = bool(opt_in_required)
        self.token_sha256 = (opt_in_token_sha256 or "").strip().lower()

    def check(self, metadata: Iterable[Tuple[str, str]]) -> None:
        if not self.required:
            return
        if not self.token_sha256:
            # If required but no token configured, deny all remote usage.
            raise AuthError("opt-in required but no opt-in token configured")

        token = _metadata_get(metadata, "x-opt-in-token") or _metadata_get(metadata, "X-Opt-In-Token")
        if not token:
            raise AuthError("missing X-Opt-In-Token")
        if _sha256_hex(token) != self.token_sha256:
            raise AuthError("invalid opt-in token")


def _pb_to_dict(msg: Any) -> Dict[str, Any]:
    if MessageToDict is None:
        return {}
    return MessageToDict(msg, preserving_proto_field_name=True)


def serve_grpc(daemon: Any, host: str = "127.0.0.1", port: int = 50051) -> None:
    """Start a gRPC server for the Atlas API.

    Requires:
    - grpcio installed
    - generated protobuf modules present (make proto)
    """
    if grpc is None:
        raise RuntimeError("grpcio is not installed")

    from gen.python.atlas.v1 import atlas_pb2  # type: ignore
    from gen.python.atlas.v1 import atlas_pb2_grpc  # type: ignore

    guard = OptInGuard(
        opt_in_required=bool(daemon.policy.get("security", "opt_in_required", default=True)),
        opt_in_token_sha256=str(daemon.policy.get("security", "opt_in_token_sha256", default="") or ""),
    )

    class OrchestratorServicer(atlas_pb2_grpc.OrchestratorServiceServicer):  # type: ignore
        def SubmitTuneStudy(self, req, ctx):
            endpoint = "OrchestratorService/SubmitTuneStudy"
            tenant = getattr(req, "tenant", "") or "default"
            try:
                guard.check(ctx.invocation_metadata())
                job_id = daemon.submit_job(_pb_to_dict(req))
                record_request(endpoint, tenant, "TRUE")
                return atlas_pb2.JobId(id=job_id)
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            except Exception as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.INTERNAL, str(e))

        def GetJobStatus(self, req, ctx):
            endpoint = "OrchestratorService/GetJobStatus"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                st = daemon.get_status(req.id)
                record_request(endpoint, tenant, "TRUE")
                return atlas_pb2.Status(state=st.get("state", ""), info={k: str(v) for k, v in (st.get("info") or {}).items()})
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            except Exception as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.INTERNAL, str(e))

        def CancelJob(self, req, ctx):
            endpoint = "OrchestratorService/CancelJob"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                st = daemon.cancel(req.id)
                record_request(endpoint, tenant, "TRUE")
                return atlas_pb2.Status(state=st.get("state", ""), info={k: str(v) for k, v in (st.get("info") or {}).items()})
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            except Exception as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.INTERNAL, str(e))

    class RegistryServicer(atlas_pb2_grpc.RegistryServiceServicer):  # type: ignore
        def ListArtifacts(self, req, ctx):
            endpoint = "RegistryService/ListArtifacts"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                record_request(endpoint, tenant, "TRUE")
                for job_id, meta in daemon.registry.list_artifacts().items():
                    yield atlas_pb2.Artifact(
                        id=job_id,
                        uri=meta.get("dir", ""),
                        task="",
                        family="",
                        dataset="",
                        metrics={},
                        onnx_uri=os.path.join(meta.get("dir", ""), "model.onnx"),
                        ledger_uri=os.path.join(meta.get("dir", ""), "ledger.json"),
                    )
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))

        def GetLedger(self, req, ctx):
            endpoint = "RegistryService/GetLedger"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                led = daemon.registry.read_ledger(req.id) or {}
                record_request(endpoint, tenant, "TRUE")
                return atlas_pb2.Ledger(json=str(led))
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            except Exception as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.INTERNAL, str(e))

        def PromoteArtifact(self, req, ctx):
            endpoint = "RegistryService/PromoteArtifact"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                art = daemon.promote(req.id)
                record_request(endpoint, tenant, "TRUE")
                return atlas_pb2.Artifact(
                    id=req.id,
                    uri=os.path.join(daemon.registry.root, req.id),
                    task=str(art.get("model", {}).get("task", "")),
                    family=str(art.get("model", {}).get("family", "")),
                    dataset=str(art.get("data", {}).get("train_uri", "")),
                    metrics={k: float(v) for k, v in (art.get("metrics") or {}).items() if isinstance(v, (int, float))},
                    onnx_uri=str(art.get("onnx", {}).get("path", "")),
                    ledger_uri=os.path.join(daemon.registry.root, req.id, "ledger.json"),
                )
            except ValueError as e:
                # promotion gate failure; treat as failed precondition
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
            except Exception as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.INTERNAL, str(e))

    # ServeService is optional; implemented only if ray serve is installed.
    class ServeServicer(atlas_pb2_grpc.ServeServiceServicer):  # type: ignore
        def GetRouter(self, req, ctx):
            endpoint = "ServeService/GetRouter"
            tenant = "default"
            try:
                guard.check(ctx.invocation_metadata())
                record_request(endpoint, tenant, "TRUE")
                try:
                    from ray import serve  # type: ignore
                    import ray  # type: ignore
                    router = serve.get_deployment("Router").get_handle()
                    st = ray.get(router.status.remote())
                    return atlas_pb2.RouterStatus(
                        weights={k: int(v) for k, v in (st.get("weights") or {}).items()},
                        shadow=bool(st.get("shadow", False)),
                        sticky=bool(st.get("sticky", False)),
                    )
                except Exception as e:
                    ctx.abort(grpc.StatusCode.UNIMPLEMENTED, f"router not available: {e}")
            except AuthError as e:
                record_request(endpoint, tenant, "FALSE")
                ctx.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(os.getenv("ATLAS_GRPC_WORKERS", "16"))))
    atlas_pb2_grpc.add_OrchestratorServiceServicer_to_server(OrchestratorServicer(), server)
    atlas_pb2_grpc.add_RegistryServiceServicer_to_server(RegistryServicer(), server)
    atlas_pb2_grpc.add_ServeServiceServicer_to_server(ServeServicer(), server)

    bind = f"{host}:{port}"
    server.add_insecure_port(bind)
    server.start()
    server.wait_for_termination()
