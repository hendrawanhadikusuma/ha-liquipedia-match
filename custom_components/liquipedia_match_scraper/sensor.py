from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATE,
    ATTR_ERROR,
    ATTR_MATCH_URL,
    ATTR_OPPONENT_LOGO,
    ATTR_OPPONENT_NAME,
    ATTR_OPPONENT_SCORE,
    ATTR_SCORE_SECTION,
    ATTR_SCORE_URL,
    ATTR_STATUS,
    ATTR_SUMMARY,
    ATTR_TEAM_LOGO,
    ATTR_TEAM_NAME,
    ATTR_TEAM_SCORE,
    ATTR_TEAM_URL,
    ATTR_TOURNAMENT,
    ATTR_UPCOMING_MATCH,
    ATTR_UPCOMING_MATCHES,
    ATTR_VENUE,
    DOMAIN,
)
from .coordinator import LiquipediaMatchCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LiquipediaMatchCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LiquipediaMatchSensor(coordinator, entry)])


class LiquipediaMatchSensor(CoordinatorEntity[LiquipediaMatchCoordinator], SensorEntity):
    def __init__(self, coordinator: LiquipediaMatchCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{entry.title} Match"
        self._attr_unique_id = f"{entry.entry_id}_match"
        self._attr_icon = "mdi:trophy-award"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Liquipedia {entry.title}",
            manufacturer="Liquipedia",
            model="Team + Score Page Scraper",
        )

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.status

    @property
    def entity_picture(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.opponent_logo or self.coordinator.data.team_logo

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        upcoming = data.upcoming_matches or []
        selected = upcoming[0] if upcoming else None

        return {
            ATTR_STATUS: data.status,
            ATTR_TEAM_NAME: data.team_name,
            ATTR_TEAM_LOGO: data.team_logo,
            ATTR_OPPONENT_NAME: data.opponent_name,
            ATTR_OPPONENT_LOGO: data.opponent_logo,
            ATTR_TEAM_SCORE: data.team_score,
            ATTR_OPPONENT_SCORE: data.opponent_score,
            ATTR_DATE: data.date,
            ATTR_VENUE: data.venue,
            ATTR_TOURNAMENT: data.tournament,
            ATTR_SUMMARY: data.summary,
            ATTR_MATCH_URL: data.match_url,
            ATTR_TEAM_URL: data.team_url,
            ATTR_SCORE_URL: data.score_url,
            ATTR_SCORE_SECTION: data.score_section,
            ATTR_UPCOMING_MATCHES: upcoming,
            ATTR_UPCOMING_MATCH: selected,
            ATTR_ERROR: data.error,
        }
