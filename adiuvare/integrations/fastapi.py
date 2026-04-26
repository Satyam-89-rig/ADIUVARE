import asyncio
import threading

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ..core.gate import run_trackA
from . import build_http_ctx


class AdiuvareMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, guard) -> None:
        super().__init__(app)
        self._guard = guard

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        raw_ip = request.headers.get("x-forwarded-for", "")
        ip = raw_ip.split(",", 1)[0].strip()
        if not ip:
            ip = request.client.host if request.client else "127.0.0.1"
        ctx = build_http_ctx(
            identity=request.headers.get("x-user-id", request.client.host if request.client else "anon"),
            payload=body.decode() if body else None,
            url=str(request.url.path),
            method=request.method,
            headers=dict(request.headers),
            ip=ip,
            endpoint=request.url.path,
            snapshot=self._guard._cfg_snap,
        )

        gate = run_trackA(ctx, self._guard._id_store)
        if not gate.passed:
            self._guard.hooks.emit_block(gate)
            return JSONResponse(
                {"detail": gate.block_reason or "blocked"},
                status_code=gate.status_code,
            )

        res = await call_next(request)
        threading.Thread(
            target=lambda: asyncio.run(self._run_trackB(ctx)),
            daemon=True,
        ).start()
        return res

    async def _run_trackB(self, ctx) -> None:
        event = await self._guard._pipeline.trackB(ctx)
        if event is not None:
            await self._guard.event_stream.emit(event)
            self._guard._audit.write(event)
            self._guard.hooks.emit_event(event)
