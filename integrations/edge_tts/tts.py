"""Text to speech entity for Edge TTS."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.tts import TextToSpeechEntity, TtsAudioType, Voice
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EdgeTTSConfigEntry
from .const import (
    CONF_PITCH,
    CONF_RATE,
    CONF_VOICE,
    CONF_VOLUME,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    DOMAIN,
)
from .engine import EdgeTTSError, synthesize
from .logic import (
    choose_voice,
    default_language_for,
    find_voice,
    locales_from_voices,
    resolve_call_options,
    voice_label,
    voices_for_language,
)

_LOGGER = logging.getLogger(__name__)

OPTION_VOICE = "voice"
OPTION_RATE = "rate"
OPTION_PITCH = "pitch"
OPTION_VOLUME = "volume"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EdgeTTSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the Edge TTS entity."""
    entity = EdgeTTSEntity(entry)
    # Load the voice list now so the supported languages are known when the entity is added.
    try:
        await entry.runtime_data.async_get()
    except EdgeTTSError as err:
        _LOGGER.warning("Edge TTS voice list not available yet: %s", err)
    async_add_entities([entity])


class EdgeTTSEntity(TextToSpeechEntity):
    """Speech from Microsoft Edge's online voices."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_options = [OPTION_VOICE, OPTION_RATE, OPTION_PITCH, OPTION_VOLUME]

    def __init__(self, entry: EdgeTTSConfigEntry) -> None:
        self._entry = entry
        self._cache = entry.runtime_data
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Edge TTS",
            manufacturer="Microsoft",
            model="Edge read-aloud voices",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _default_voice(self) -> str:
        options = self._entry.options
        return options.get(CONF_VOICE) or self._entry.data.get(CONF_VOICE, DEFAULT_VOICE)

    @property
    def _defaults(self) -> dict[str, Any]:
        options = self._entry.options
        return {
            "rate": options.get(CONF_RATE, DEFAULT_RATE),
            "pitch": options.get(CONF_PITCH, DEFAULT_PITCH),
            "volume": options.get(CONF_VOLUME, DEFAULT_VOLUME),
        }

    @property
    def default_language(self) -> str:
        return default_language_for(self._cache.voices, self._default_voice)

    @property
    def supported_languages(self) -> list[str]:
        locales = locales_from_voices(self._cache.voices)
        return locales or [self.default_language]

    async def _voices(self) -> list[dict[str, Any]]:
        try:
            return await self._cache.async_get()
        except EdgeTTSError:
            return self._cache.voices

    async def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Voices for a language, for the voice picker."""
        voices = voices_for_language(await self._voices(), language)
        if not voices:
            return None
        return [Voice(voice["ShortName"], voice_label(voice)) for voice in voices]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Generate mp3 audio for a message."""
        voices = await self._voices()
        requested = options.get(OPTION_VOICE)
        if requested and voices and find_voice(voices, str(requested)) is None:
            raise HomeAssistantError(f"Unknown Edge TTS voice: {requested}")
        voice = choose_voice(voices, language, requested, self._default_voice)
        try:
            formatted = resolve_call_options(options, self._defaults)
        except ValueError as err:
            raise HomeAssistantError(f"Invalid Edge TTS option: {err}") from err
        try:
            audio = await synthesize(message, voice, **formatted)
        except EdgeTTSError as err:
            raise HomeAssistantError(
                f"Edge TTS could not generate speech. Check the internet connection. ({err})"
            ) from err
        return "mp3", audio
