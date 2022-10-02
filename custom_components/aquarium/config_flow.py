from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_ID

from .const import DOMAIN

from .aquarium import (
    Aquarium,
    AquariumConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FordPass."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._host: str | None = None

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}
        if user_input is None:
            return await self._show_setup_form()
        host = user_input[CONF_HOST]
        aquarium = Aquarium(host)

        try:
            device_info = await self.hass.async_add_executor_job(aquarium.device_info)
            unique_id = device_info["MAC adress"]
            name = device_info["Device type"]
        except AquariumConnectionError:
            errors["base"] = "Ivalid host"
            return await self._show_setup_form(errors)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
            return await self._show_setup_form(errors)

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=name,
            data={
                CONF_ID: unique_id,
                CONF_HOST: host,
            },
        )
