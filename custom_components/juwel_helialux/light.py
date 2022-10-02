from __future__ import annotations

import logging

import math
from typing import cast
from homeassistant.components.light import  (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_RGBW_COLOR,
    ATTR_EFFECT,
    ColorMode,
    LightEntityFeature,)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from homeassistant.util import color
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    AQUARIUM_LIGHT_LIST,
)
DEFAULT_COLOR = 10
DEFAULT_BRIGHTNESS = 10
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
        light,
        (name,  icon, ),
    ) in AQUARIUM_LIGHT_LIST.items():


        entities.append(
            AquariumSensor(
                coordinator,
                light,
                name,
                icon,


            )
        )
    async_add_entities(entities)

class AquariumSensor(CoordinatorEntity, LightEntity):



    def __init__(
        self,
        coordinator,

        light,
        name,
        icon,

    ):
        super().__init__(coordinator)
        self._light = light
        self._attr_name = name
        self._available = True
        self._state = None
        self._attr_icon = icon

        self._attr_unique_id = f"{self._light}"
        self._brightness = DEFAULT_BRIGHTNESS
        self._rgbw_color = (DEFAULT_COLOR, DEFAULT_COLOR, DEFAULT_COLOR, DEFAULT_COLOR)
        self._white = DEFAULT_COLOR
        self._red = DEFAULT_COLOR
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._green = DEFAULT_COLOR
        self._blue = DEFAULT_COLOR
        self._attr_supported_color_modes = set()
        self._attr_supported_color_modes.add(ColorMode.RGBW )
        self._attr_supported_color_modes.add(ColorMode.HS )
        self._attr_supported_color_modes.add(ColorMode.WHITE )
        self._attr_effect_list = []

    @property
    def white_value  (self):
         return cast(int, self.coordinator.data['color']['white'])
    @property
    def hs_color  (self):
         return color.color_RGB_to_hs( self.coordinator.data['color']['red'],self.coordinator.data['color']['green'],self.coordinator.data['color']['blue'])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_brightness =  self.coordinator.data['brightness']
        self._attr_rgbw_color = (self.coordinator.data['color']['red'],self.coordinator.data['color']['green'],self.coordinator.data['color']['blue'],self.coordinator.data['color']['white'])
        self._attr_is_on = self.coordinator.data["state"]
        self._attr_effect = self.coordinator.data["profile"]
        self._attr_effect_list = self.coordinator.data['profile_list']
        self._attr_available = (super().available and self.coordinator.data)
        self.async_write_ha_state()


    def turn_on(self, **kwargs):
        _LOGGER.warning({**kwargs})
        if ATTR_RGBW_COLOR in kwargs:
            rgbw = kwargs[ATTR_RGBW_COLOR]
            self._white = int(rgbw[3]/2.55)
            self._red = int(rgbw[0]/2.55)
            self._blue = int(rgbw[2]/2.55)
            self._green = int(rgbw[1]/2.55)
            self.coordinator.aquarium.set( self._white,self._blue, self._red, self._green )
        elif ATTR_EFFECT in kwargs:
            self.coordinator.aquarium.set_profile( kwargs[ATTR_EFFECT] )
        elif ATTR_BRIGHTNESS in kwargs:
          brightness = kwargs[ATTR_BRIGHTNESS]
          if brightness > 95:
            self._white = 100
            self._white = 100
            self._red = 100
            self._blue = 100
            self.coordinator.aquarium.set( self._white,self._blue, self._red, self._green )
          else:
            if self._brightness != 0:
                brightness_Per = 1 + ((brightness - self._brightness) / self._brightness)
            else:
                brightness_Per =  (brightness/2.55)/100
                self._white =100
                self._red =100
                self._blue = 100
                self._green = 100
            self._white = math.ceil(self._white * brightness_Per )
            self._red = math.ceil(self._red * brightness_Per )
            self._green = math.ceil(self._green * brightness_Per )
            self._blue = math.ceil(self._blue * brightness_Per )
            if self._white >= 100:
              self._white = 100
            elif self._red >= 100:
              self._red = 100
            elif self._green >= 100:
              self._green = 100
            elif self._blue >=100:
              self._blue = 100
            self._brightness = brightness
            self.coordinator.aquarium.set( self._white,self._blue, self._red , self._green)

    def turn_off(self, **kwargs):
        self._white = 0
        self._red = 0
        self._green = 0
        self._blue = 0
        self._brightness = 0
        self.coordinator.aquarium.set( self._white,self._blue, self._red, self._green )

