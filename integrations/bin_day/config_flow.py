"""Config flow for Bin Day."""

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

from .const import (
    CONF_EVENING_HOUR,
    CONF_INTERVAL_WEEKS,
    CONF_START_DATE,
    DEFAULT_EVENING_HOUR,
    DOMAIN,
)

_INTERVAL = selector.NumberSelector(
    selector.NumberSelectorConfig(min=1, max=52, step=1, mode=selector.NumberSelectorMode.BOX)
)
_HOUR = selector.NumberSelector(
    selector.NumberSelectorConfig(min=0, max=23, step=1, mode=selector.NumberSelectorMode.BOX)
)


class BinDayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one collection stream (for example general waste or recycling)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            name = user_input["name"].strip()
            await self.async_set_unique_id(name.lower())
            self._abort_if_unique_id_configured()
            data = {
                "name": name,
                CONF_START_DATE: user_input[CONF_START_DATE],
                CONF_INTERVAL_WEEKS: int(user_input[CONF_INTERVAL_WEEKS]),
            }
            return self.async_create_entry(title=name, data=data)

        schema = vol.Schema(
            {
                vol.Required("name"): selector.TextSelector(),
                vol.Required(CONF_START_DATE): selector.DateSelector(),
                vol.Required(CONF_INTERVAL_WEEKS, default=1): _INTERVAL,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BinDayOptionsFlow()


class BinDayOptionsFlow(OptionsFlow):
    """Change the interval or the evening reminder hour."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_INTERVAL_WEEKS: int(user_input[CONF_INTERVAL_WEEKS]),
                    CONF_EVENING_HOUR: int(user_input[CONF_EVENING_HOUR]),
                }
            )
        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_INTERVAL_WEEKS, default=current[CONF_INTERVAL_WEEKS]
                ): _INTERVAL,
                vol.Required(
                    CONF_EVENING_HOUR,
                    default=current.get(CONF_EVENING_HOUR, DEFAULT_EVENING_HOUR),
                ): _HOUR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
