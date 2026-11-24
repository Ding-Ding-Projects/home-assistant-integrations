"""Talk to edge-tts. No Home Assistant imports, so it can be tested with a fake."""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable


class EdgeTTSError(Exception):
    """Raised when the online service cannot be reached or returns no audio."""


async def synthesize(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
    communicate_cls: Any = None,
) -> bytes:
    """Stream Communicate output into mp3 bytes."""
    if communicate_cls is None:
        import edge_tts

        communicate_cls = edge_tts.Communicate
    try:
        communicate = communicate_cls(text, voice, rate=rate, pitch=pitch, volume=volume)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio.extend(chunk["data"])
    except Exception as err:  # noqa: BLE001 - network, websocket and service errors vary
        raise EdgeTTSError(f"Edge TTS request failed: {err}") from err
    if not audio:
        raise EdgeTTSError("Edge TTS returned no audio")
    return bytes(audio)


class VoiceCache:
    """Holds the voice list and refreshes it at most once per max_age seconds."""

    def __init__(
        self,
        fetcher: Callable[[], Awaitable[list[dict[str, Any]]]] | None = None,
        max_age: float = 24 * 60 * 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetcher = fetcher
        self._max_age = max_age
        self._clock = clock
        self.voices: list[dict[str, Any]] = []
        self._fetched_at: float | None = None

    async def _fetch(self) -> list[dict[str, Any]]:
        if self._fetcher is not None:
            return await self._fetcher()
        import edge_tts

        return await edge_tts.list_voices()

    @property
    def is_stale(self) -> bool:
        return self._fetched_at is None or self._clock() - self._fetched_at >= self._max_age

    async def async_get(self) -> list[dict[str, Any]]:
        """Return voices, refreshing when stale. Falls back to the old list on failure."""
        if not self.is_stale:
            return self.voices
        try:
            voices = await self._fetch()
        except Exception as err:  # noqa: BLE001
            if self.voices:
                return self.voices
            raise EdgeTTSError(f"Could not fetch the voice list: {err}") from err
        if not voices:
            if self.voices:
                return self.voices
            raise EdgeTTSError("The voice list was empty")
        self.voices = list(voices)
        self._fetched_at = self._clock()
        return self.voices
