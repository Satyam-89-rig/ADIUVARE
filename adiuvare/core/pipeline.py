from ..core.gate import run_trackA
from ..core.scorer import compute_score
from ..core.verdict import compute_verdict
from ..signals.payload import PayloadSignal
from ..state.identity_store import IdentityStore


class Pipeline:
    def __init__(self, id_store: IdentityStore, soft_signals: list | None = None) -> None:
        self._id_store = id_store
        self._soft_signals = soft_signals or [PayloadSignal()]

    async def process(self, ctx):
        gate = run_trackA(ctx, self._id_store)
        if not gate.passed:
            return gate, None

        sig_res = {}
        for sig in self._soft_signals:
            sig_res[sig.name] = await sig.extract(ctx)

        score, breakdown = compute_score(sig_res)
        verdict = compute_verdict(score)
        return gate, (score, verdict, breakdown)

