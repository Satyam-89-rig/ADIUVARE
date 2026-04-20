import os
from collections import deque


class UnixSocketEventStream:
    def __init__(self, name: str = "adiuvare") -> None:
        self.name = name
        self.path = os.path.join(os.getenv("TEMP", "/tmp"), f"{name}.sock")
        self._recent = deque(maxlen=100)
        self._cmd = None

    async def emit(self, event) -> None:
        self._recent.append(event)

    def recent(self) -> list:
        return list(self._recent)

    def set_command_handler(self, handler) -> None:
        self._cmd = handler

    async def command(self, name: str, args: dict | None = None) -> dict:
        if self._cmd is None:
            raise RuntimeError("stream_command_unbound")
        return await self._cmd(name, args or {})
