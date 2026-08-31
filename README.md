# Liquipedia Match Scraper

Standalone Home Assistant custom integration for upcoming match + score extraction from Liquipedia.

## What it does

- Reads a team page such as `https://liquipedia.net/mobilelegends/RRQ_Hoshi`
- Extracts upcoming match data from the team page
- Derives the score/result page automatically from the upcoming match row
- Exposes one sensor that feeds `custom_cards/match-card.js`

## Files

- `custom_components/liquipedia_match_scraper`
- `hacs.json`
- `custom_components/liquipedia_match_scraper/brand/icon.png`
- `custom_components/liquipedia_match_scraper/brand/logo.png`

## HACS / install

This folder is ready to be copied into a separate GitHub repository and published as its own HACS integration.
The integration includes local brand assets, so Home Assistant and HACS can show an icon/logo without waiting for the central brands repository.

If you want to test it locally first, copy `custom_components/liquipedia_match_scraper` into your Home Assistant `custom_components` folder, then restart Home Assistant.

## Example config

Use only the team URL:

```text
team_url: https://liquipedia.net/mobilelegends/RRQ_Hoshi
```

You can also set the match timezone offset from the integration options. The
`date` attribute is converted into ISO-8601 using that GMT offset.

The sensor will expose fields like:

```yaml
state: PRE
team_name: RRQ Hoshi
opponent_name: Geek Fam ID
team_score: null
opponent_score: null
score_url: https://liquipedia.net/mobilelegends/MPL/Indonesia/Season_18/Regular_Season#RS:_Week_2
score_section: RS: Week 2
```

Because Liquipedia layouts vary, this integration should be treated as experimental.

## Sensor response

Sensor state is taken from `status`, so the primary state can be one of:

- `PRE` — match is upcoming or the score page does not yet contain final scores
- `POST` — match result was found and both team scores were parsed
- `NOT_FOUND` — Liquipedia page could not be fetched or no match data was found

The sensor also exposes attributes such as:

- `team_name`, `opponent_name`
- `team_score`, `opponent_score`
- `date`, `venue`, `tournament`
- `score_url`, `score_section`, `match_url`
- `entity_picture` and `image` for card compatibility
- `upcoming_match` and `upcoming_matches`
- `error` when fetch/parsing fails

By default, the sensor refreshes every 5 minutes.

Example response:

```yaml
state: PRE
attributes:
  team_name: RRQ Hoshi
  opponent_name: Geek Fam ID
  team_score: null
  opponent_score: null
  score_url: https://liquipedia.net/mobilelegends/MPL/Indonesia/Season_18/Regular_Season#RS:_Week_2
  score_section: RS: Week 2
  error: null
```
