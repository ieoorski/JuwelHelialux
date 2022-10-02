from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ATTRIBUTION, CONF_ID, DEVICE_CLASS_TIMESTAMP

from . import AquariumEntity, AquariumDataUpdateCoordinator

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    AQUARIUM_SWITCH_LIST,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Garmin Connect sensor based on a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities = []
    for (
        switch_type,
        (name,  icon)
    ) in AQUARIUM_SWITCH_LIST.items():
        entities.append(
            AquariumSwitch(
                coordinator,
                switch_type,
                name,
                icon,

            )
        )
    async_add_entities(entities)

class AquariumSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(
        self,
        coordinator,
        switch_type,
        name,
        icon,
    ):
        super().__init__(coordinator)
        self._type = switch_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{self._type}"
        self._attr_is_on = self.coordinator.data[self._type]
        self._attr_available = (super().available and self.coordinator.data and self._type in self.coordinator.data)


    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self.coordinator.aquarium.set_manual_colour('True' )
    def turn_off(self, **kwargs):
        self.coordinator.aquarium.set_manual_colour('False')
        """Turn the entity off."""