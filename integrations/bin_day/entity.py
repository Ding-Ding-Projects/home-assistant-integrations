"""Shared base entity for Bin Day."""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_EVENING_HOUR,
    CONF_INTERVAL_WEEKS,
    CONF_START_DATE,
    DEFAULT_EVENING_HOUR,
    DOMAIN,
)

SCAN_INTERVAL = timedelta(minutes=15)


class BinDayEntity(Entity):
    """Base entity holding the stream settings."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        settings = {**entry.data, **entry.options}
        self._start: date = date.fromisoformat(settings[CONF_START_DATE])
        self._interval: int = int(settings[CONF_INTERVAL_WEEKS])
        self._evening_hour: int = int(settings.get(CONF_EVENING_HOUR, DEFAULT_EVENING_HOUR))
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Home Assistant Integrations",
            entry_type=None,
        )
