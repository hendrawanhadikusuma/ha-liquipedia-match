from __future__ import annotations

from datetime import timedelta

DOMAIN = "liquipedia_match_scraper"

CONF_TEAM_URL = "team_url"
CONF_SCORE_URL = "score_url"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)

ATTR_TEAM_NAME = "team_name"
ATTR_TEAM_LOGO = "team_logo"
ATTR_OPPONENT_NAME = "opponent_name"
ATTR_OPPONENT_LOGO = "opponent_logo"
ATTR_TEAM_SCORE = "team_score"
ATTR_OPPONENT_SCORE = "opponent_score"
ATTR_DATE = "date"
ATTR_VENUE = "venue"
ATTR_TOURNAMENT = "tournament"
ATTR_STATUS = "status"
ATTR_SUMMARY = "summary"
ATTR_MATCH_URL = "match_url"
ATTR_TEAM_URL = "team_url"
ATTR_SCORE_URL = "score_url"
ATTR_SCORE_SECTION = "score_section"
ATTR_UPCOMING_MATCHES = "upcoming_matches"
ATTR_UPCOMING_MATCH = "upcoming_match"
ATTR_ERROR = "error"
