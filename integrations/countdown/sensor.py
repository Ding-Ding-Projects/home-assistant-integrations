"""Sensors for Countdown."""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_DATE, CONF_YEARLY, DOMAIN
from .logic import days_until, next_occurrence, years_marked

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DaysUntilSensor(entry), NextDateSensor(entry)])


class _CountdownSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        settings = {**entry.data, **entry.options}
        self._target: date = date.fromisoformat(settings[CONF_DATE])
        self._yearly: bool = bool(settings[CONF_YEARLY])
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Home Assistant Integrations",
        )

    @staticmethod
    def _today() -> date:
        return dt_util.now().date()


class DaysUntilSensor(_CountdownSensor):
    """Days until the next occurrence."""

    _attr_native_unit_of_measurement = "d"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "days_until")

    @property
    def native_value(self) -> int | None:
        return days_until(self._target, self._yearly, self._today())

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {"yearly": self._yearly, "original_date": self._target.isoformat()}
        if self._yearly:
            attrs["years"] = years_marked(self._target, self._today())
        return attrs


class NextDateSensor(_CountdownSensor):
    """Date of the next occurrence."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_date")

    @property
    def native_value(self) -> date | None:
        return next_occurrence(self._target, self._yearly, self._today())
