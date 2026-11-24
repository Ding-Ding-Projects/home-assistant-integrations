"""Config flow for GitHub Releases."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import CONF_REPO, DOMAIN
from .logic import parse_repo


class GitHubReleasesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Watch one public GitHub repository."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                repo = parse_repo(user_input[CONF_REPO])
            except ValueError:
                errors[CONF_REPO] = "invalid_repo"
            else:
                await self.async_set_unique_id(repo.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=repo, data={CONF_REPO: repo})

        schema = vol.Schema({vol.Required(CONF_REPO): selector.TextSelector()})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
