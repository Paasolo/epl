"""Official matchweek fixtures loaded from fixturedownload.com (all leagues)."""

from __future__ import annotations

import json
from functools import lru_cache

from epl_predictor.leagues.base import LeagueConfig
from epl_predictor.leagues.epl import CONFIG as EPL_CONFIG
from epl_predictor.results import _http_get


def matchweek_options(league: LeagueConfig | None = None) -> dict[str, int]:
    """Label -> matchweek number for UI selectboxes."""
    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    return {info["label"]: gw for gw, info in sorted(weeks.items())}


def fixtures_for(gw: int, league: LeagueConfig | None = None) -> list[tuple[str, str]]:
    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    if gw not in weeks:
        raise KeyError(f"Unknown matchweek {gw}; valid: 1–{max(weeks) if weeks else 0}")
    return list(weeks[gw]["fixtures"])


def fixtures_for_unplayed(
    gw: int,
    matches,
    league: LeagueConfig | None = None,
    season: str = "2026/27",
) -> tuple[list[tuple[str, str]], list[dict]]:
    """Official GW fixtures with completed games removed."""
    from epl_predictor.results import split_matchweek_fixtures

    league = league or EPL_CONFIG
    return split_matchweek_fixtures(gw, matches, league, season=season)


def validate_matchweeks(league: LeagueConfig | None = None) -> list[str]:
    """Return human-readable problems, or [] if the slate looks usable."""
    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    if not weeks:
        if league.fixture_feed_slug:
            return [f"Could not load matchweek fixtures for {league.name}."]
        return [f"No fixture feed configured for {league.name} — use a custom slate."]
    problems: list[str] = []
    expected = set(league.clubs)
    for gw, info in sorted(weeks.items()):
        fixtures = info["fixtures"]
        teams = [t for pair in fixtures for t in pair]
        unknown = set(teams) - expected
        if unknown:
            problems.append(f"GW{gw}: unknown teams {sorted(unknown)[:5]}")
        if len(set(teams)) != len(teams):
            problems.append(f"GW{gw}: duplicate team(s) in slate")
    return problems


def matchweeks_for(league: LeagueConfig) -> dict[int, dict]:
    return _cached_matchweeks(league.id, league.fixture_feed_slug)


@lru_cache(maxsize=16)
def _cached_matchweeks(league_id: str, slug: str | None) -> dict[int, dict]:
    from epl_predictor.leagues import get_league

    league = get_league(league_id)
    if not slug:
        return {}
    url = f"https://fixturedownload.com/feed/json/{slug}"
    try:
        raw = _http_get(url, timeout=20.0)
        payload = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001 — offline / feed missing
        return {}
    if not isinstance(payload, list):
        return {}

    inv_csv = {csv: display for display, csv in league.csv_name.items()}
    by_round: dict[int, list[tuple[str, str]]] = {}
    for match in payload:
        try:
            rnd = int(match.get("RoundNumber"))
        except (TypeError, ValueError):
            continue
        home_raw = str(match.get("HomeTeam") or "").strip()
        away_raw = str(match.get("AwayTeam") or "").strip()
        if not home_raw or not away_raw:
            continue
        home_csv = league.canon_team(home_raw)
        away_csv = league.canon_team(away_raw)
        home_d = inv_csv.get(home_csv)
        away_d = inv_csv.get(away_csv)
        if home_d is None or away_d is None:
            if home_raw in league.csv_name and away_raw in league.csv_name:
                home_d, away_d = home_raw, away_raw
            else:
                continue
        by_round.setdefault(rnd, []).append((home_d, away_d))

    out: dict[int, dict] = {}
    for rnd, fixtures in sorted(by_round.items()):
        seen: set[tuple[str, str]] = set()
        unique: list[tuple[str, str]] = []
        for pair in fixtures:
            if pair in seen:
                continue
            seen.add(pair)
            unique.append(pair)
        out[rnd] = {"label": f"Matchweek {rnd}", "fixtures": unique}
    return out


# Back-compat alias used by older imports / tests.
MATCHWEEKS = property  # placeholder replaced below


def __getattr__(name: str):
    if name == "MATCHWEEKS":
        return matchweeks_for(EPL_CONFIG)
    raise AttributeError(name)
