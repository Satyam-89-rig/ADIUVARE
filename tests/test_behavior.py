import adiuvare.signals.behavior as behavior

from adiuvare.signals.behavior import BehaviorSignal
from adiuvare.state.identity_store import IdentityStore


def test_behavior_falls_back_without_ua_parser(monkeypatch):
    monkeypatch.setattr(behavior, "_load_ua_parser", lambda: None)
    sig = BehaviorSignal(IdentityStore())

    assert sig.ua_score("curl/8.0") == 0.45


def test_behavior_flags_headless_without_ua_parser(monkeypatch):
    monkeypatch.setattr(behavior, "_load_ua_parser", lambda: None)
    sig = BehaviorSignal(IdentityStore())

    assert sig.ua_score("Mozilla/5.0 HeadlessChrome/124.0") == 0.65


def test_behavior_falls_back_when_parser_breaks(monkeypatch):
    class BrokenParser:
        @staticmethod
        def ParseUserAgent(_ua: str):
            raise RuntimeError("parser broke")

    monkeypatch.setattr(behavior, "_load_ua_parser", lambda: BrokenParser)
    sig = BehaviorSignal(IdentityStore())

    assert sig.ua_score("curl/8.0") == 0.45
