"""Sensors for GitHub Releases."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReleasesCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = ReleasesCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([LatestTagSensor(coordinator, entry), PublishedSensor(coordinator, entry)])


class _ReleaseSensor(CoordinatorEntity[ReleasesCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ReleasesCoordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="GitHub",
        )


class LatestTagSensor(_ReleaseSensor):
    """Latest release tag."""

    def __init__(self, coordinator: ReleasesCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "latest_release")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.tag

    @property
    def extra_state_attributes(self) -> dict:
        return {"repository": self.coordinator.repo, "url": self.coordinator.data.url}


class PublishedSensor(_ReleaseSensor):
    """When the latest release was published."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ReleasesCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "published")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.published_at
