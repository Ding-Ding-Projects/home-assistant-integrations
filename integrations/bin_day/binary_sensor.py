"""Binary sensor for Bin Day."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import BinDayEntity
from .logic import next_collection, put_bins_out

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([PutBinsOutSensor(entry)])


class PutBinsOutSensor(BinDayEntity, BinarySensorEntity):
    """On from the evening before a collection until the end of collection day."""

    _attr_translation_key = "put_bins_out"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "put_bins_out")

    @property
    def is_on(self) -> bool:
        return put_bins_out(dt_util.now(), self._start, self._interval, self._evening_hour)

    @property
    def extra_state_attributes(self) -> dict:
        due = next_collection(self._start, self._interval, dt_util.now().date())
        return {"next_collection": due.isoformat()}
