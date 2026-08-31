from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCORE_URL, CONF_TEAM_URL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .scraper import LiquipediaMatchData, LiquipediaMatchScraper

_LOGGER = logging.getLogger(__name__)


class LiquipediaMatchCoordinator(DataUpdateCoordinator[LiquipediaMatchData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.scraper = LiquipediaMatchScraper(
            session=async_get_clientsession(hass),
            team_url=entry.data[CONF_TEAM_URL],
            score_url=entry.data.get(CONF_SCORE_URL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> LiquipediaMatchData:
        try:
            return await self.scraper.async_fetch()
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch Liquipedia match data: {err}") from err
