"""Config flow for Countdown."""

from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_DATE, CONF_YEARLY, DOMAIN


class CountdownConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one named date."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input["name"].strip()
            try:
                date.fromisoformat(user_input[CONF_DATE])
            except ValueError:
                errors[CONF_DATE] = "invalid_date"
            if not name:
                errors["name"] = "empty_name"
            if not errors:
                await self.async_set_unique_id(name.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        "name": name,
                        CONF_DATE: user_input[CONF_DATE],
                        CONF_YEARLY: user_input[CONF_YEARLY],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(),
                vol.Required(CONF_DATE): selector.DateSelector(),
                vol.Required(CONF_YEARLY, default=True): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CountdownOptionsFlow()


class CountdownOptionsFlow(OptionsFlow):
    """Change the date or whether it repeats every year."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_DATE, default=current[CONF_DATE]): selector.DateSelector(),
                vol.Required(
                    CONF_YEARLY, default=current[CONF_YEARLY]
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
