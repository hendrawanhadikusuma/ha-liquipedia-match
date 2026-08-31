from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

from aiohttp import ClientSession
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    ),
}


@dataclass
class LiquipediaMatchData:
    status: str
    team_name: str
    team_url: str
    score_url: str
    score_section: str | None
    team_logo: str | None = None
    opponent_name: str | None = None
    opponent_logo: str | None = None
    team_score: str | None = None
    opponent_score: str | None = None
    date: str | None = None
    venue: str | None = None
    tournament: str | None = None
    summary: str | None = None
    match_url: str | None = None
    upcoming_matches: list[dict[str, Any]] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class LiquipediaMatchScraper:
    def __init__(self, session: ClientSession, team_url: str, score_url: str | None = None) -> None:
        self.session = session
        self.team_url = team_url.strip()
        self.team_location = self._parse_url(self.team_url)
        self.score_location = self._parse_url(score_url.strip()) if score_url else None

    async def async_fetch(self) -> LiquipediaMatchData:
        team_html = None
        score_html = None
        last_error: Exception | None = None

        for candidate in (self._api_url(self.team_location["page_slug"], self.team_location["game_slug"]), self.team_location["page_url"]):
            try:
                team_html = await self._fetch_html(candidate)
                if team_html:
                    break
            except Exception as err:  # pragma: no cover - defensive fallback path
                last_error = err
                _LOGGER.debug("Liquipedia team fetch failed for %s: %s", candidate, err)

        if not team_html:
            return LiquipediaMatchData(
                status="NOT_FOUND",
                team_name=self.team_location["page_title"],
                team_url=self.team_location["page_url"],
                score_url=self.score_location["page_url"] if self.score_location else self.team_location["page_url"],
                score_section=self.score_location["section_hint"] if self.score_location else None,
                error=str(last_error) if last_error else "Unable to fetch Liquipedia pages",
            )

        team_soup = BeautifulSoup(team_html or "", "html.parser") if team_html else None

        team_name = self._extract_page_title(team_soup) if team_soup else self.team_location["page_title"]
        team_name = team_name or self.team_location["page_title"]
        team_logo = self._extract_logo_url(team_soup, self.team_location["page_url"]) if team_soup else None
        upcoming_matches = self._extract_upcoming_matches(team_soup, team_name, self.team_location["page_url"]) if team_soup else []
        selected_upcoming = upcoming_matches[0] if upcoming_matches else None

        score_url = self.score_location["page_url"] if self.score_location else None
        score_location = self.score_location

        if not score_location and selected_upcoming and selected_upcoming.get("score_url"):
            try:
                score_location = self._parse_url(selected_upcoming["score_url"])
                score_url = score_location["page_url"]
            except ValueError:
                score_location = None

        if score_location:
            for candidate in (
                self._api_url(score_location["page_slug"], score_location["game_slug"]),
                score_location["page_url"],
            ):
                try:
                    score_html = await self._fetch_html(candidate)
                    if score_html:
                        break
                except Exception as err:  # pragma: no cover - defensive fallback path
                    last_error = err
                    _LOGGER.debug("Liquipedia score fetch failed for %s: %s", candidate, err)

        score_soup = BeautifulSoup(score_html or "", "html.parser") if score_html else None

        score_match = self._extract_score_match(
            score_soup,
            team_name,
            selected_upcoming.get("opponent") if selected_upcoming else None,
            score_location["section_hint"] if score_location else None,
            score_location["page_url"] if score_location else self.team_location["page_url"],
            team_logo,
        ) if score_soup else None

        if score_match and score_match.get("opponent_name"):
            status = score_match.get("status") or "PRE"
        elif selected_upcoming:
            status = "PRE"
        else:
            status = "NOT_FOUND"

        merged = {
            "status": status,
            "team_name": team_name,
            "team_logo": team_logo,
            "opponent_name": None,
            "opponent_logo": None,
            "team_score": None,
            "opponent_score": None,
            "date": None,
            "venue": None,
            "tournament": None,
            "summary": None,
            "match_url": None,
            "score_section": self.score_location["section_hint"] or None,
        }

        if selected_upcoming:
            merged.update(
                {
                    "opponent_name": selected_upcoming.get("opponent"),
                    "opponent_logo": selected_upcoming.get("opponent_logo"),
                    "date": selected_upcoming.get("datetime_text"),
                    "venue": selected_upcoming.get("venue"),
                    "tournament": selected_upcoming.get("tournament"),
                    "summary": selected_upcoming.get("summary"),
                }
            )

        if score_match:
            merged.update({key: value for key, value in score_match.items() if value is not None})

        return LiquipediaMatchData(
            status=merged["status"],
            team_name=merged["team_name"],
            team_url=self.team_location["page_url"],
            score_url=score_url or (selected_upcoming.get("score_url") if selected_upcoming else self.team_location["page_url"]),
            score_section=merged.get("score_section"),
            team_logo=merged.get("team_logo"),
            opponent_name=merged.get("opponent_name"),
            opponent_logo=merged.get("opponent_logo"),
            team_score=merged.get("team_score"),
            opponent_score=merged.get("opponent_score"),
            date=merged.get("date"),
            venue=merged.get("venue"),
            tournament=merged.get("tournament"),
            summary=merged.get("summary"),
            match_url=merged.get("match_url"),
            upcoming_matches=upcoming_matches,
            attributes={
                "team": self.team_location,
                "score": score_location,
                "selected_upcoming": selected_upcoming,
                "score_match": score_match,
            },
            error=str(last_error) if last_error else None,
        )

    async def _fetch_html(self, url: str) -> str:
        async with self.session.get(url, headers=_REQUEST_HEADERS, timeout=30) as response:
            response.raise_for_status()
            if "api.php" in url:
                payload = await response.json(content_type=None)
                html = self._extract_parse_html(payload)
                if not html:
                    raise ValueError("Liquipedia API parse returned no HTML")
                return html
            return await response.text()

    @staticmethod
    def _api_url(page_slug: str, game_slug: str) -> str:
        page_title = quote(page_slug, safe="")
        return f"https://liquipedia.net/{game_slug}/api.php?action=parse&page={page_title}&prop=text|sections&format=json&formatversion=2"

    @staticmethod
    def _extract_parse_html(payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None

        parse = payload.get("parse") or {}
        text = parse.get("text")
        if isinstance(text, dict):
            return text.get("*") or text.get("content")
        if isinstance(text, str):
            return text

        raw_html = parse.get("html")
        if isinstance(raw_html, str):
            return raw_html

        return None

    @staticmethod
    def _parse_url(url: str) -> dict[str, str]:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("invalid_domain")

        host = parsed.netloc.lower()
        if host not in {"liquipedia.net", "www.liquipedia.net"}:
            raise ValueError("invalid_domain")

        parts = [unquote(segment) for segment in parsed.path.split("/") if segment]
        if not parts:
            raise ValueError("invalid_liquipedia_url")

        if len(parts) >= 2 and parts[1].lower() == "index.php":
            game_slug = parts[0]
            page_title = parse_qs(parsed.query).get("title", [""])[0].strip()
            if not page_title:
                raise ValueError("invalid_liquipedia_url")
            page_slug = page_title.replace(" ", "_")
        else:
            if len(parts) < 2:
                raise ValueError("invalid_liquipedia_url")
            game_slug = parts[0]
            page_slug = "/".join(parts[1:]).strip("/")

        if not game_slug or not page_slug:
            raise ValueError("invalid_liquipedia_url")

        section_hint = parsed.fragment.strip().replace("_", " ")
        game_name = re.sub(r"\s+", " ", game_slug.replace("_", " ").replace("-", " ")).strip().title()

        return {
            "game_slug": game_slug,
            "game_name": game_name or game_slug,
            "page_slug": page_slug,
            "page_title": page_slug.replace("_", " ").replace("-", " ").strip(),
            "page_url": f"https://liquipedia.net/{game_slug}/{page_slug}",
            "section_hint": section_hint,
        }

    @classmethod
    def _clean_text(cls, value: str | None) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @classmethod
    def _normalize_key(cls, value: str | None) -> str:
        return re.sub(r"[^a-z0-9]+", "", cls._clean_text(value).casefold())

    @classmethod
    def _text(cls, node) -> str:
        return cls._clean_text(node.get_text(" ", strip=True))

    @classmethod
    def _extract_page_title(cls, soup: BeautifulSoup | None) -> str | None:
        if not soup:
            return None

        heading = soup.select_one("h1#firstHeading")
        if heading:
            text = cls._text(heading)
            if text:
                return re.split(r"\s(?:-?|\|)\sLiquipedia", text, maxsplit=1)[0].strip() or text

        meta_title = soup.select_one('meta[property="og:title"]')
        if meta_title and meta_title.get("content"):
            text = cls._clean_text(meta_title.get("content"))
            if text:
                return re.split(r"\s(?:-?|\|)\sLiquipedia", text, maxsplit=1)[0].strip() or text

        return None

    def _extract_logo_url(self, soup: BeautifulSoup | None, base_url: str) -> str | None:
        if not soup:
            return None

        meta = soup.select_one('meta[property="og:image"]')
        if meta and meta.get("content"):
            return urljoin(base_url, meta.get("content"))

        image = soup.select_one("table img[src]") or soup.select_one("aside img[src]")
        if image and image.get("src"):
            return urljoin(base_url, image.get("src"))

        return None

    @classmethod
    def _section_table(cls, soup: BeautifulSoup, heading_text: str):
        target = cls._normalize_key(heading_text)
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if target in cls._normalize_key(heading.get_text(" ", strip=True)):
                table = heading.find_next("table")
                if table:
                    return table
        return None

    @classmethod
    def _extract_table_rows(cls, table) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        headers: list[str] | None = None

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells or not row.find_all("td", recursive=False):
                continue

            values = [cls._text(cell) for cell in cells]
            if not any(values):
                continue

            if headers is None and row.find("th"):
                headers = [cls._normalize_key(value) for value in values]
                continue

            item: dict[str, str] = {}
            if headers:
                for index, value in enumerate(values):
                    key = headers[index] if index < len(headers) else f"col_{index}"
                    if value:
                        item[key] = value
            else:
                for index, value in enumerate(values):
                    if value:
                        item[f"col_{index}"] = value

            images: list[str] = []
            for image in row.find_all("img"):
                image_src = image.get("src")
                if image_src:
                    images.append(image_src)

            links: list[dict[str, str]] = []
            for link in row.find_all("a", href=True):
                href = link.get("href")
                if not href:
                    continue

                links.append(
                    {
                        "href": href,
                        "title": cls._clean_text(link.get("title") or link.get_text(" ", strip=True)),
                    }
                )

            if images:
                item["__images"] = ",".join(images)

            if links:
                item["__links"] = links

            if item:
                rows.append(item)

        return rows

    def _extract_upcoming_matches(self, soup: BeautifulSoup, team_name: str, base_url: str) -> list[dict[str, Any]]:
        table = self._section_table(soup, "Upcoming Matches")
        if not table:
            return []

        upcoming_matches: list[dict[str, Any]] = []
        for row in self._extract_table_rows(table):
            values = self._row_values(row)
            if not values:
                continue

            datetime_text = row.get("date") or row.get("time") or row.get("datetime") or row.get("col_0")
            tournament = row.get("tournament") or row.get("event") or row.get("col_1") or row.get("col_2")
            opponent = row.get("opponent") or row.get("away") or row.get("col_3") or row.get("col_2")
            opponent_logo = self._extract_first_image_url(row, base_url)

            if opponent and self._normalize_key(team_name) in self._normalize_key(opponent):
                opponent = None

            if not opponent:
                for value in values:
                    if self._normalize_key(team_name) in self._normalize_key(value):
                        continue
                    if value == tournament or value == datetime_text:
                        continue
                    if self._looks_like_score(value):
                        continue
                    opponent = value
                    break

            score_url = self._select_score_url_from_row(row, base_url, team_name, opponent)

            upcoming_matches.append(
                {
                    "datetime_text": datetime_text,
                    "tournament": tournament,
                    "venue": tournament,
                    "opponent": opponent,
                    "opponent_logo": opponent_logo,
                    "score_url": score_url,
                    "summary": " | ".join(values),
                    "raw": row,
                }
            )

        return upcoming_matches

    def _extract_score_match(
        self,
        soup: BeautifulSoup,
        team_name: str,
        opponent_hint: str | None,
        section_hint: str | None,
        base_url: str,
        team_logo: str | None,
    ) -> dict[str, Any] | None:
        heading_candidates = [section_hint, "Results", "Played Matches", "Match History", "Recent Matches"]
        for heading in [candidate for candidate in heading_candidates if candidate]:
            table = self._section_table(soup, heading)
            if not table:
                continue

            for row in self._extract_table_rows(table):
                row_text = self._clean_text(" | ".join(self._row_values(row))).casefold()
                if self._normalize_key(team_name) not in self._normalize_key(row_text):
                    continue
                if opponent_hint and self._normalize_key(opponent_hint) not in self._normalize_key(row_text):
                    continue

                values = self._row_values(row)
                scores = self._extract_scores(values)
                opponent = self._extract_row_opponent(row, team_name)
                if not opponent and opponent_hint:
                    opponent = opponent_hint

                if not opponent:
                    continue

                team_score, opponent_score = self._map_scores_to_teams(values, team_name, opponent, scores)
                status = "POST" if team_score is not None and opponent_score is not None else "PRE"

                return {
                    "status": status,
                    "team_name": team_name,
                    "team_logo": team_logo,
                    "opponent_name": opponent,
                    "opponent_logo": self._extract_first_image_url(row, base_url),
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "date": row.get("date") or row.get("time") or row.get("datetime") or row.get("col_0"),
                    "venue": row.get("venue") or row.get("stage") or row.get("tournament") or section_hint,
                    "tournament": row.get("tournament") or section_hint,
                    "summary": " | ".join(values),
                    "match_url": None,
                }

        return None

    def _extract_row_opponent(self, row: dict[str, str], team_name: str) -> str | None:
        values = self._row_values(row)
        team_key = self._normalize_key(team_name)
        for value in values:
            if team_key in self._normalize_key(value):
                continue
            if self._looks_like_score(value):
                continue
            return value
        return None

    @classmethod
    def _row_values(cls, row: dict[str, str]) -> list[str]:
        return [
            value
            for key, value in row.items()
            if not key.startswith("__") and isinstance(value, str) and value
        ]

    def _extract_scores(self, values: list[str]) -> list[str]:
        scores: list[str] = []
        for value in values:
            match = re.search(r"\b(\d+)\b", value)
            if match and self._looks_like_score(value):
                scores.append(match.group(1))
            else:
                compact = self._clean_text(value)
                if compact.isdigit():
                    scores.append(compact)
        return scores

    def _map_scores_to_teams(self, values: list[str], team_name: str, opponent_name: str, scores: list[str]) -> tuple[str | None, str | None]:
        if len(scores) >= 2:
            return scores[0], scores[1]

        text = self._clean_text(" | ".join(values))
        m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", text)
        if m:
            return m.group(1), m.group(2)

        return None, None

    def _extract_first_image_url(self, row: dict[str, str], base_url: str) -> str | None:
        images = row.get("__images")
        if not images:
            return None

        candidates = [candidate.strip() for candidate in images.split(",") if candidate.strip()]
        if not candidates:
            return None

        return urljoin(base_url, candidates[-1])

    def _select_score_url_from_row(
        self,
        row: dict[str, str],
        base_url: str,
        team_name: str,
        opponent_name: str | None,
    ) -> str | None:
        links = row.get("__links")
        if not isinstance(links, list) or not links:
            return None

        team_key = self._normalize_key(team_name)
        opponent_key = self._normalize_key(opponent_name)
        scored_candidates: list[tuple[int, str]] = []

        for link in links:
            if not isinstance(link, dict):
                continue

            href = link.get("href")
            if not href:
                continue

            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            if parsed.scheme not in {"http", "https"}:
                continue

            lower_url = absolute_url.casefold()
            if any(token in lower_url for token in ["special:", "file:", "category:", "help:", "action=edit"]):
                continue

            label = self._normalize_key(link.get("title") or absolute_url)
            if team_key and team_key in label:
                continue
            if opponent_key and opponent_key in label:
                continue

            score = 0
            if any(token in lower_url for token in ["regular_season", "regularseason", "season", "week", "match", "results", "playoffs", "bracket", "stage"]):
                score += 2
            if parsed.fragment:
                score += 1
            if "/" in parsed.path.strip("/"):
                score += 1

            scored_candidates.append((score, absolute_url))

        if not scored_candidates:
            return None

        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        return scored_candidates[0][1]

    @staticmethod
    def _looks_like_score(value: str | None) -> bool:
        if not value:
            return False
        return bool(re.search(r"^\s*\d+\s*[:\-]\s*\d+\s*$", value))
