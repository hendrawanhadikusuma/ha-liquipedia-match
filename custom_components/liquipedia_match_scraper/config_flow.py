from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import CONF_TEAM_URL, DOMAIN


def parse_liquipedia_url(url: str) -> dict[str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("invalid_domain")

    host = parsed.netloc.lower()
    if host not in {"liquipedia.net", "www.liquipedia.net"}:
        raise ValueError("invalid_domain")

    parts = [segment for segment in parsed.path.split("/") if segment]
    if len(parts) < 2:
        raise ValueError("invalid_liquipedia_url")

    if parts[1].lower() == "index.php":
        game_slug = parts[0]
        page_title = parse_qs(parsed.query).get("title", [""])[0].strip()
        if not page_title:
            raise ValueError("invalid_liquipedia_url")
        page_slug = page_title.replace(" ", "_")
    else:
        game_slug = parts[0]
        page_slug = "/".join(parts[1:]).strip("/")

    if not game_slug or not page_slug:
        raise ValueError("invalid_liquipedia_url")

    game_name = re.sub(r"\s+", " ", game_slug.replace("_", " ").replace("-", " ")).strip().title()
    section_hint = parsed.fragment.strip()

    return {
        "game_slug": game_slug,
        "game_name": game_name or game_slug,
        "page_slug": page_slug,
        "page_title": page_slug.replace("_", " ").replace("-", " ").strip(),
        "page_url": f"https://liquipedia.net/{game_slug}/{page_slug}",
        "section_hint": section_hint,
    }


class LiquipediaMatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                team = parse_liquipedia_url(user_input[CONF_TEAM_URL])
            except ValueError as err:
                errors["base"] = str(err)
            else:
                unique_id = team["page_url"]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = user_input.get(CONF_NAME) or team["page_title"]

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_NAME: title,
                        CONF_TEAM_URL: user_input[CONF_TEAM_URL].strip(),
                        "team": team,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TEAM_URL): str,
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
