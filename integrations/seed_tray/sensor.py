"""Sensors for Seed Tray."""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_GERMINATION_DAYS, CONF_SOW_DATE, CONF_TRANSPLANT_DAYS, DOMAIN
from .logic import (
    STAGE_GERMINATING,
    STAGE_GROWING,
    STAGE_PLANNED,
    STAGE_READY,
    days_to_transplant,
    germination_date,
    stage,
    transplant_date,
)

SCAN_INTERVAL = timedelta(minutes=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([StageSensor(entry), DaysToTransplantSensor(entry)])


class _TraySensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        settings = {**entry.data, **entry.options}
        self._sow: date = date.fromisoformat(settings[CONF_SOW_DATE])
        self._germ: int = int(settings[CONF_GERMINATION_DAYS])
        self._transplant: int = int(settings[CONF_TRANSPLANT_DAYS])
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

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "sow_date": self._sow.isoformat(),
            "germination_date": germination_date(self._sow, self._germ).isoformat(),
            "transplant_date": transplant_date(self._sow, self._transplant).isoformat(),
        }


class StageSensor(_TraySensor):
    """Current stage of the tray."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [STAGE_PLANNED, STAGE_GERMINATING, STAGE_GROWING, STAGE_READY]

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "stage")

    @property
    def native_value(self) -> str:
        return stage(self._sow, self._germ, self._transplant, self._today())


class DaysToTransplantSensor(_TraySensor):
    """Days until the tray is ready to transplant."""

    _attr_native_unit_of_measurement = "d"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "days_to_transplant")

    @property
    def native_value(self) -> int:
        return days_to_transplant(self._sow, self._transplant, self._today())
