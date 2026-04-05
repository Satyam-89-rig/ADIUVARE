import asyncio
import threading

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from ..core.gate import run_trackA
from ..core.models import RequestContext


class AdiuvareMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, guard) -> None:
        super().__init__(app)
        self._guard = guard

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        ctx = RequestContext(
            identity=request.headers.get("x-user-id", request.client.host if request.client else "anon"),
            payload=body.decode() if body else None,
            url=str(request.url.path),
            method=request.method,
            headers=dict(request.headers),
            ip=request.client.host if request.client else "127.0.0.1",
            endpoint=request.url.path,
        )
        if ctx.snapshot is None:
            ctx.snapshot = self._guard._cfg_snap

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

    async def _run_trackB(self, ctx: RequestContext) -> None:
        event = await self._guard._pipeline.trackB(ctx)
        if event is not None:
            self._guard.hooks.emit_event(event)
