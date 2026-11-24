"""Config and options flow for Edge TTS."""

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
    CONF_PITCH,
    CONF_RATE,
    CONF_VOICE,
    CONF_VOLUME,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    DOMAIN,
    PITCH_RANGE,
    RATE_RANGE,
    VOLUME_RANGE,
)
from .engine import EdgeTTSError, VoiceCache
from .logic import voice_options


def _voice_selector(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
            sort=False,
        )
    )


def _fallback_options(current: str = DEFAULT_VOICE) -> list[dict[str, str]]:
    options = [{"value": DEFAULT_VOICE, "label": "English (United States), Aria, Female"}]
    if current != DEFAULT_VOICE:
        options.append({"value": current, "label": current})
    return options


def _number(bounds: tuple[int, int], unit: str) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=bounds[0],
            max=bounds[1],
            step=1,
            unit_of_measurement=unit,
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )


class EdgeTTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Choose the default voice."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return EdgeTTSOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Edge TTS", data={CONF_VOICE: user_input[CONF_VOICE]}
            )

        errors: dict[str, str] = {}
        try:
            cache = VoiceCache()
            options = voice_options(await cache.async_get())
        except EdgeTTSError:
            errors["base"] = "cannot_connect"
            options = _fallback_options()

        schema = vol.Schema(
            {vol.Required(CONF_VOICE, default=DEFAULT_VOICE): _voice_selector(options)}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class EdgeTTSOptionsFlow(OptionsFlow):
    """Default voice, rate, pitch and volume."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        current = entry.options.get(CONF_VOICE) or entry.data.get(CONF_VOICE, DEFAULT_VOICE)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        cache: VoiceCache | None = getattr(entry, "runtime_data", None)
        try:
            options = voice_options(await (cache or VoiceCache()).async_get())
        except EdgeTTSError:
            options = _fallback_options(current)
        if not any(option["value"] == current for option in options):
            options.append({"value": current, "label": current})

        def default(key: str, fallback: int) -> int:
            return int(entry.options.get(key, fallback))

        schema = vol.Schema(
            {
                vol.Required(CONF_VOICE, default=current): _voice_selector(options),
                vol.Required(CONF_RATE, default=default(CONF_RATE, DEFAULT_RATE)): _number(
                    RATE_RANGE, "%"
                ),
                vol.Required(CONF_PITCH, default=default(CONF_PITCH, DEFAULT_PITCH)): _number(
                    PITCH_RANGE, "Hz"
                ),
                vol.Required(
                    CONF_VOLUME, default=default(CONF_VOLUME, DEFAULT_VOLUME)
                ): _number(VOLUME_RANGE, "%"),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
