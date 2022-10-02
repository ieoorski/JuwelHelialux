from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (CoordinatorEntity, DataUpdateCoordinator,)

from .const import (DATA_COORDINATOR, DOMAIN, AQUARIUM_SENSOR_LIST,)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(  hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Juwel sensor based on a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][ DATA_COORDINATOR]
    entities = []
    for (sensor_type,(name, unit, icon, device_class, enabled_by_default),\
        ) in AQUARIUM_SENSOR_LIST.items():
        entities.append(
            AquariumSensor(
                coordinator,
                sensor_type,
                name,
                unit,
                icon,
                device_class,
                enabled_by_default,
            )
        )
    async_add_entities(entities)

class AquariumSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        sensor_type,
        name,
        unit,
        icon,
        device_class,
        enabled_default: bool = True,
    ):
        super().__init__(coordinator)
        self._type = sensor_type
        self._device_class = device_class
        self._enabled_default = enabled_default
        self._attr_name = name
        self._attr_device_class = self._device_class
        self._attr_icon = icon
        self._attr_unit_of_measurement = unit
        self._attr_unique_id = f"{self._type}"
        self._attr_native_value = self.coordinator.data[self._type]
        self._attr_entity_registry_enabled_default =  self._enabled_default
        self._attr_available =  (super().available and self.coordinator.data and self._type in self.coordinator.data)