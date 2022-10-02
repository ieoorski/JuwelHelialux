"""The Aquarium integration."""
from __future__ import annotations

from datetime import timedelta
import logging
import async_timeout
from .aquarium import (
    Aquarium,
    AquariumConnectionError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers import device_registry as dr
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    DATA_COORDINATOR,
)

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "light", "switch"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Aquarium  component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aquarium from a config entry."""
    coordinator = AquariumDataUpdateCoordinator(hass, entry=entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    await coordinator.async_config_entry_first_refresh()
    aquarium = Aquarium(entry.data[CONF_HOST])
    try:
        device_info = await hass.async_add_executor_job(aquarium.device_info)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, device_info["MAC adress"])},
        identifiers={(DOMAIN, device_info["MAC adress"])},
        sw_version=device_info["Software version"],
        hw_version=device_info["Hardware version"],
        name=device_info["Device type"],
        manufacturer="Juwel",
        model=device_info["Model"],
    )
    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class AquariumDataUpdateCoordinator(DataUpdateCoordinator):
    """Aquairum Data Update Coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Aquarium."""
        self.entry = entry
        self.hass = hass
        self.aquarium = Aquarium(entry.data[CONF_HOST])

        super().__init__(
            hass,
            _LOGGER,
            name=f"Update coordinator for {DOMAIN}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Aquairum"""
        try:
            async with async_timeout.timeout(30):
                data = await self.hass.async_add_executor_job(self.aquarium.status)
                await self.hass.async_add_executor_job(self.aquarium.statusvars)
                await self.hass.async_add_executor_job(self.aquarium.profile_list)
            return dict(data)
        except (
            AquariumConnectionError,
            Exception,
        ) as ex:  # pylint: disable=broad-except
            _LOGGER.exception("No aquarium found")
            _LOGGER.warning(str(ex))


class AquariumEntity(CoordinatorEntity[AquariumDataUpdateCoordinator]):
    """Defines a base Aquarium entity."""

    def __init__(self, *, coordinator: AquariumDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
