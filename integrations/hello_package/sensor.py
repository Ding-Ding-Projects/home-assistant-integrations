"""Sensor platform for the Hello Package integration."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


def _read_version() -> str:
    """Read the integration version from manifest.json."""
    manifest = Path(__file__).parent / "manifest.json"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Package demo sensor."""
    version = await hass.async_add_executor_job(_read_version)
    async_add_entities([PackageDemoSensor(entry, version)])


class PackageDemoSensor(SensorEntity):
    """Sensor whose state is the integration version."""

    _attr_has_entity_name = True
    _attr_name = "Package demo"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, version: str) -> None:
        """Initialize the sensor."""
        self._attr_unique_id = f"{entry.entry_id}_package_demo"
        self._attr_native_value = version
