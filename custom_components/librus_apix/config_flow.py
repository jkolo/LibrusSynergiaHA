"""Config flow for Librus APIX integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from librus_apix.client import new_client

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    try:
        loop = asyncio.get_running_loop()
        client = await loop.run_in_executor(None, new_client)
        token = await loop.run_in_executor(None, client.get_token, username, password)

        if not token:
            raise ValueError("Authentication failed")

        return {"title": f"Librus APIX ({username})"}

    except Exception as ex:
        _LOGGER.exception("Authentication error during config flow")
        raise ValueError("Cannot connect") from ex


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Librus APIX."""

    VERSION = 1

    # ---------- Initial setup (user-initiated add) ----------

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Zapobiegamy duplikatom config entry dla tego samego loginu.
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    # ---------- Reauthentication (HA-initiated after auth fail) ----------

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Trigger reauth flow when credentials no longer work."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Ask the user for the new password and update the entry."""
        errors: dict[str, str] = {}
        existing_entry = self._get_reauth_entry()
        username = existing_entry.data[CONF_USERNAME]

        if user_input is not None:
            try:
                await validate_input(
                    self.hass,
                    {CONF_USERNAME: username, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    existing_entry,
                    data={**existing_entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            description_placeholders={"username": username},
            errors=errors,
        )

    # ---------- Reconfigure (user wants to change credentials) ----------

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Allow the user to change username/password without removing entry."""
        errors: dict[str, str] = {}
        existing_entry = self._get_reconfigure_entry()

        if user_input is not None:
            new_username = user_input[CONF_USERNAME].lower()

            # Pozwol zmienic haslo dla tego samego loginu, ale jesli login
            # zmieniany — sprawdz czy nie kolidujemy z innym entry.
            await self.async_set_unique_id(new_username)
            self._abort_if_unique_id_mismatch(reason="account_mismatch")

            try:
                await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reconfigure")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    existing_entry,
                    data=user_input,
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=existing_entry.data.get(CONF_USERNAME, ""),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
