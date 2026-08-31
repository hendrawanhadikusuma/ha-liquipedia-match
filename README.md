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

## HACS / install

This folder is ready to be copied into a separate GitHub repository and published as its own HACS integration.

If you want to test it locally first, copy `custom_components/liquipedia_match_scraper` into your Home Assistant `custom_components` folder, then restart Home Assistant.

## Example config

Use only the team URL:

```text
team_url: https://liquipedia.net/mobilelegends/RRQ_Hoshi
```

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
