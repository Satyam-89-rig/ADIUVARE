import asyncio

from adiuvare.core.models import RequestContext
from adiuvare.core.pipeline import Pipeline
from adiuvare.state.identity_store import IdentityStore


def test_pipeline_runs_end_to_end():
    ctx = RequestContext(
        identity="u1",
        payload="select * from users",
        url="/login",
        method="POST",
        headers={},
        ip="127.0.0.1",
        endpoint="/login",
    )

    gate, out = asyncio.run(Pipeline(IdentityStore()).process(ctx))
    assert gate.passed is True
    assert out is not None
    assert out[1] == "flag"


def test_pipeline_stops_when_gate_fails():
    store = IdentityStore()
    store.block("u1")

    ctx = RequestContext(
        identity="u1",
        payload="select * from users",
        url="/login",
        method="POST",
        headers={},
        ip="127.0.0.1",
        endpoint="/login",
    )

    gate, out = asyncio.run(Pipeline(store).process(ctx))
    assert gate.passed is False
    assert out is None

