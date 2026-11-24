"""Text to speech through Microsoft Edge's online read-aloud voices."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import VOICE_CACHE_SECONDS
from .engine import VoiceCache

PLATFORMS: list[Platform] = [Platform.TTS]

type EdgeTTSConfigEntry = ConfigEntry[VoiceCache]


async def async_setup_entry(hass: HomeAssistant, entry: EdgeTTSConfigEntry) -> bool:
    """Set up Edge TTS from a config entry."""
    entry.runtime_data = VoiceCache(max_age=VOICE_CACHE_SECONDS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: EdgeTTSConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EdgeTTSConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
