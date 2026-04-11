import asyncio

from adiuvare.core.models import RequestContext
from adiuvare.signals.payload import PayloadSignal


async def _score(text: str) -> float:
    ctx = RequestContext(
        identity="u1",
        payload=text,
        url="/form",
        method="POST",
        headers={},
        ip="127.0.0.1",
        endpoint="/form",
    )
    res = await PayloadSignal().extract(ctx)
    return res.score


def test_benign_matrix_stays_clean():
    cases = [
        "please select an option",
        "drop by later if you can",
        "the union hall opens at six",
        "javascript is disabled in this browser",
        "we benchmarked the service last week",
    ]

    for text in cases:
        score = asyncio.run(_score(text))
        assert score == 0.0, text
