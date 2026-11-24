"""Sensors for Bin Day."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import BinDayEntity
from .logic import days_until, next_collection

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([NextCollectionSensor(entry), DaysUntilSensor(entry)])


class NextCollectionSensor(BinDayEntity, SensorEntity):
    """Date of the next collection."""

    _attr_translation_key = "next_collection"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_collection")

    @property
    def native_value(self):
        return next_collection(self._start, self._interval, dt_util.now().date())


class DaysUntilSensor(BinDayEntity, SensorEntity):
    """Days until the next collection."""

    _attr_translation_key = "days_until"
    _attr_native_unit_of_measurement = "d"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "days_until")

    @property
    def native_value(self) -> int:
        return days_until(self._start, self._interval, dt_util.now().date())
