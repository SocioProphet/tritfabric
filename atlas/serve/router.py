from __future__ import annotations

import asyncio
import collections
import random
import time
from typing import Any, Dict, Optional

import numpy as np

# Optional Ray Serve integration: if ray isn't installed, the Router class can still be imported,
# but deployment decorators won't exist.
try:
    from ray import serve  # type: ignore
except Exception:  # pragma: no cover
    serve = None


def _choose_weighted(weights: Dict[str, int], sticky: bool, user_key: Optional[str]) -> Optional[str]:
    names = list(weights.keys())
    if not names:
        return None
    if len(names) == 1:
        return names[0]
    tot = max(1, sum(max(0, int(w)) for w in weights.values()))
    if sticky and user_key:
        slot = (hash(user_key) % tot) + 1
        csum = 0
        for k, w in weights.items():
            csum += max(0, int(w))
            if slot <= csum:
                return k
        return names[0]
    r = random.randint(1, tot)
    csum = 0
    for k, w in weights.items():
        csum += max(0, int(w))
        if r <= csum:
            return k
    return names[0]


class RouterCore:
    """Router core (usable without Ray Serve).

    Provides:
    - weighted routing
    - optional sticky routing
    - optional shadow mirroring (hook point)
    - p95 latency window per backend
    - inflight counters per backend
    """

    def __init__(self, weights: Optional[Dict[str, int]] = None, shadow: bool = False, sticky: bool = False, window_size: int = 200):
        self.weights: Dict[str, int] = dict(weights or {})
        self.shadow = bool(shadow)
        self.sticky = bool(sticky)
        self.win_size = int(window_size)

        self._lat_win: Dict[str, collections.deque] = {n: collections.deque(maxlen=self.win_size) for n in self.weights}
        self._inflight: Dict[str, int] = collections.defaultdict(int)

        # Serve handles (populated only when ray serve is available)
        self._handles: Dict[str, Any] = {}

    def _refresh_handles(self) -> None:
        if not serve:
            return
        self._handles = {n: serve.get_deployment(n).get_handle() for n in self.weights}

    async def route(self, body: Any, user_key: Optional[str] = None) -> Any:
        chosen = _choose_weighted(self.weights, self.sticky, user_key)
        if not chosen:
            raise RuntimeError("no backends configured")

        self._inflight[chosen] += 1
        t0 = time.perf_counter()
        try:
            if serve:
                if not self._handles:
                    self._refresh_handles()
                res = await self._handles[chosen].remote(body)
            else:
                # No serve: we cannot call real backends. Echo for dev.
                res = {"backend": chosen, "echo": body}
            return res
        finally:
            dur_ms = (time.perf_counter() - t0) * 1000.0
            self._inflight[chosen] = max(0, self._inflight[chosen] - 1)
            self._lat_win.setdefault(chosen, collections.deque(maxlen=self.win_size)).append(dur_ms)

            if self.shadow and serve and self._handles:
                for k, h in self._handles.items():
                    if k != chosen:
                        asyncio.create_task(h.remote(body))

    def status(self) -> Dict[str, Any]:
        lat_p95: Dict[str, float] = {}
        for k, win in self._lat_win.items():
            lat_p95[k] = float(np.percentile(list(win), 95)) if win else 0.0
        return {
            "weights": dict(self.weights),
            "shadow": self.shadow,
            "sticky": self.sticky,
            "lat_p95": lat_p95,
            "inflight": dict(self._inflight),
        }

    def update(self, weights: Dict[str, int], shadow: bool = False, sticky: Optional[bool] = None) -> Dict[str, Any]:
        self.weights = dict(weights or {})
        self.shadow = bool(shadow)
        if sticky is not None:
            self.sticky = bool(sticky)
        # refresh latency windows
        for name in self.weights:
            self._lat_win.setdefault(name, collections.deque(maxlen=self.win_size))
        for name in list(self._lat_win.keys()):
            if name not in self.weights:
                self._lat_win.pop(name, None)
                self._inflight.pop(name, None)
        self._refresh_handles()
        return {"ok": True, "weights": dict(self.weights), "shadow": self.shadow, "sticky": self.sticky}


# If Ray Serve exists, export a deployment wrapper for RouterCore.
if serve:  # pragma: no cover
    from starlette.responses import JSONResponse

    @serve.deployment(name="Router", route_prefix="/infer", num_replicas=1)
    class Router(RouterCore):
        async def __call__(self, request):
            body = await request.json()
            user_key = request.headers.get("X-User-Id") or request.cookies.get("atlas_stick")
            res = await self.route(body, user_key=user_key)

            # Set sticky cookie if enabled and missing
            if self.sticky and not request.cookies.get("atlas_stick"):
                resp = JSONResponse(res)
                resp.set_cookie("atlas_stick", user_key or f"u{hash(time.time())}")
                return resp
            return res
