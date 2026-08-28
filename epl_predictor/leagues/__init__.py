"""Registry of supported football leagues."""

from __future__ import annotations

from epl_predictor.leagues.base import LeagueConfig
from epl_predictor.leagues.belgium import CONFIG as BELGIUM
from epl_predictor.leagues.bundesliga import CONFIG as BUNDESLIGA
from epl_predictor.leagues.epl import CONFIG as EPL
from epl_predictor.leagues.eredivisie import CONFIG as EREDIVISIE
from epl_predictor.leagues.laliga import CONFIG as LALIGA
from epl_predictor.leagues.ligue1 import CONFIG as LIGUE1
from epl_predictor.leagues.portugal import CONFIG as PORTUGAL
from epl_predictor.leagues.seriea import CONFIG as SERIEA
from epl_predictor.leagues.turkey import CONFIG as TURKEY

LEAGUES: dict[str, LeagueConfig] = {
    EPL.id: EPL,
    LALIGA.id: LALIGA,
    BUNDESLIGA.id: BUNDESLIGA,
    LIGUE1.id: LIGUE1,
    SERIEA.id: SERIEA,
    EREDIVISIE.id: EREDIVISIE,
    PORTUGAL.id: PORTUGAL,
    TURKEY.id: TURKEY,
    BELGIUM.id: BELGIUM,
}

LEAGUE_ORDER = list(LEAGUES.keys())


def get_league(league_id: str) -> LeagueConfig:
    try:
        return LEAGUES[league_id]
    except KeyError as exc:
        raise KeyError(f"Unknown league {league_id!r}. Valid: {', '.join(LEAGUE_ORDER)}") from exc


def league_options() -> dict[str, str]:
    """Display label -> league id for UI selectboxes."""
    return {cfg.name: cfg.id for cfg in (LEAGUES[i] for i in LEAGUE_ORDER)}
