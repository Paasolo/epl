"""Premier League 2026/27 configuration (existing EPL overlay)."""

from __future__ import annotations

from epl_predictor.context import (
    CSV_NAME,
    LAST_SEASON_POSITION,
    PROMOTED_TEAMS,
    TEAM_CONTEXT,
)
from epl_predictor.leagues.base import LeagueConfig

# Club-specific shocks already encoded inside context_adjustment for EPL;
# keep shocks empty here and let the legacy EPL branch in context.py handle them.
_CTX = {k: {**v, "shocks": v.get("shocks", [])} for k, v in TEAM_CONTEXT.items()}

NAME_ALIASES = {
    "Man Utd": "Man United",
    "Spurs": "Tottenham",
    "Man City": "Man City",
    "Nott'm Forest": "Nott'm Forest",
    "Bournemouth": "Bournemouth",
    "Brighton": "Brighton",
    "Newcastle": "Newcastle",
    "Hull": "Hull",
    "Ipswich": "Ipswich",
    "Coventry": "Coventry",
    "Leeds": "Leeds",
    "AFC Bournemouth": "Bournemouth",
    "Brighton & Hove Albion": "Brighton",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "Crystal Palace": "Crystal Palace",
    "Aston Villa": "Aston Villa",
    "West Ham": "West Ham",
    "Wolves": "Wolves",
}

CONFIG = LeagueConfig(
    id="epl",
    name="Premier League",
    fd_code="E0",
    index_url="https://www.football-data.co.uk/englandm.php",
    currency="£",
    second_tier_label="Championship",
    fixture_feed_slug="epl-2026",
    matchweek_count=38,
    csv_name=dict(CSV_NAME),
    last_season_position=dict(LAST_SEASON_POSITION),
    promoted=frozenset(PROMOTED_TEAMS),
    team_context=_CTX,
    name_aliases=NAME_ALIASES,
    use_bundled_history=True,
    bundled_history_name="epl_final.csv",
    season_start="2026-08-21",
    context_as_of="20 Aug 2026",
)
