"""Config flow for Seed Tray."""

from __future__ import annotations

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

from .const import CONF_GERMINATION_DAYS, CONF_SOW_DATE, CONF_TRANSPLANT_DAYS, DOMAIN
from .logic import validate

_DAYS = selector.NumberSelector(
    selector.NumberSelectorConfig(min=1, max=365, step=1, mode=selector.NumberSelectorMode.BOX)
)


def _check(user_input: dict[str, Any]) -> dict[str, str]:
    try:
        validate(int(user_input[CONF_GERMINATION_DAYS]), int(user_input[CONF_TRANSPLANT_DAYS]))
    except ValueError:
        return {CONF_TRANSPLANT_DAYS: "transplant_before_germination"}
    return {}


class SeedTrayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one tray of one crop."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _check(user_input)
            if not errors:
                name = user_input["name"].strip()
                await self.async_set_unique_id(name.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        "name": name,
                        CONF_SOW_DATE: user_input[CONF_SOW_DATE],
                        CONF_GERMINATION_DAYS: int(user_input[CONF_GERMINATION_DAYS]),
                        CONF_TRANSPLANT_DAYS: int(user_input[CONF_TRANSPLANT_DAYS]),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(),
                vol.Required(CONF_SOW_DATE): selector.DateSelector(),
                vol.Required(CONF_GERMINATION_DAYS, default=7): _DAYS,
                vol.Required(CONF_TRANSPLANT_DAYS, default=28): _DAYS,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SeedTrayOptionsFlow()


class SeedTrayOptionsFlow(OptionsFlow):
    """Adjust the sow date or the stage lengths."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _check(user_input)
            if not errors:
                return self.async_create_entry(
                    data={
                        CONF_SOW_DATE: user_input[CONF_SOW_DATE],
                        CONF_GERMINATION_DAYS: int(user_input[CONF_GERMINATION_DAYS]),
                        CONF_TRANSPLANT_DAYS: int(user_input[CONF_TRANSPLANT_DAYS]),
                    }
                )
        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_SOW_DATE, default=current[CONF_SOW_DATE]): selector.DateSelector(),
                vol.Required(
                    CONF_GERMINATION_DAYS, default=current[CONF_GERMINATION_DAYS]
                ): _DAYS,
                vol.Required(
                    CONF_TRANSPLANT_DAYS, default=current[CONF_TRANSPLANT_DAYS]
                ): _DAYS,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
