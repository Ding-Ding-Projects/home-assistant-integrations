"""Sensors for Sun Hours."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .logic import change_vs_yesterday, daylight_minutes

SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            DaylightSensor(hass, entry, "daylight_today"),
            DaylightSensor(hass, entry, "daylight_change"),
        ]
    )


class DaylightSensor(SensorEntity):
    """Daylight length or its change since yesterday, in minutes."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_native_unit_of_measurement = "min"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str) -> None:
        self._hass = hass
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Home Assistant Integrations",
        )

    @property
    def native_value(self) -> float:
        cfg = self._hass.config
        tz = dt_util.get_time_zone(cfg.time_zone) or dt_util.UTC
        today = dt_util.now(tz).date()
        if self._key == "daylight_today":
            return daylight_minutes(cfg.latitude, cfg.longitude, today, tz)
        return change_vs_yesterday(cfg.latitude, cfg.longitude, today, tz)
