"""Polite polling of the unauthenticated GitHub releases API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, CONF_REPO, DOMAIN, USER_AGENT
from .logic import BASE_INTERVAL_HOURS, backoff_hours, is_rate_limited, parse_release

_LOGGER = logging.getLogger(__name__)


@dataclass
class ReleaseData:
    """Latest release information."""

    tag: str | None
    published_at: datetime | None
    url: str | None


class ReleasesCoordinator(DataUpdateCoordinator[ReleaseData]):
    """Fetch the latest release every six hours, backing off when rate limited."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_REPO]}",
            update_interval=timedelta(hours=BASE_INTERVAL_HOURS),
        )
        self.repo: str = entry.data[CONF_REPO]
        self._failures = 0

    async def _async_update_data(self) -> ReleaseData:
        session = async_get_clientsession(self.hass)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        }
        try:
            async with session.get(
                API_URL.format(repo=self.repo), headers=headers, timeout=30
            ) as response:
                status = response.status
                if is_rate_limited(status, response.headers.get("X-RateLimit-Remaining")):
                    self._failures += 1
                    self.update_interval = timedelta(hours=backoff_hours(self._failures))
                    raise UpdateFailed(
                        f"GitHub rate limit reached; next try in {self.update_interval}"
                    )
                if status == 404:
                    self._reset_backoff()
                    return ReleaseData(None, None, None)
                if status != 200:
                    raise UpdateFailed(f"GitHub returned HTTP {status}")
                payload = await response.json()
        except UpdateFailed:
            raise
        except Exception as err:  # network and decoding problems
            raise UpdateFailed(f"Could not reach GitHub: {err}") from err

        self._reset_backoff()
        tag, published = parse_release(payload)
        return ReleaseData(tag, published, payload.get("html_url"))

    def _reset_backoff(self) -> None:
        self._failures = 0
        self.update_interval = timedelta(hours=BASE_INTERVAL_HOURS)
