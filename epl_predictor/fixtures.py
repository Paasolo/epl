"""Official matchweek fixtures — openfootball primary, fixturedownload fallback."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from epl_predictor.leagues.base import CACHE_DIR, LeagueConfig
from epl_predictor.leagues.epl import CONFIG as EPL_CONFIG

# openfootball/football.json paths (GitHub raw — fast & reliable).
# Prefer 2026-27; fall back to 2025-26 when a league file is missing.
_OPENFOOTBALL_FILES: dict[str, list[tuple[str, str]]] = {
    "epl": [("2026-27", "en.1.json"), ("2025-26", "en.1.json")],
    "laliga": [("2026-27", "es.1.json"), ("2025-26", "es.1.json")],
    "bundesliga": [("2026-27", "de.1.json"), ("2025-26", "de.1.json")],
    "ligue1": [("2026-27", "fr.1.json"), ("2025-26", "fr.1.json")],
    "seriea": [("2026-27", "it.1.json"), ("2025-26", "it.1.json")],
    "eredivisie": [("2026-27", "nl.1.json"), ("2025-26", "nl.1.json")],
    "portugal": [("2026-27", "pt.1.json"), ("2025-26", "pt.1.json")],
    # Turkey / Belgium 2026-27 not published on openfootball yet — avoid stale prior season.
}

_OPENFOOTBALL_RAW = (
    "https://raw.githubusercontent.com/openfootball/football.json/master/{season}/{file}"
)

# In-memory success cache only (never permanently cache empty/failed loads).
_MEMORY: dict[str, dict[int, dict]] = {}
_PLAYED_MEMORY: dict[str, set[tuple[str, str]]] = {}
_FETCH_ERRORS: dict[str, str] = {}

_ROUND_RE = re.compile(r"(?:matchday|matchweek|round|spieltag|jornada|journée|giornata)\s*(\d+)", re.I)
_SUFFIX_RE = re.compile(
    r"\s+(?:FC|CF|AFC|SC|AC|AS|SSC|FK|SK|BK|IF|IK|SV|BV|TSV|UD|CD|RC|RCD|SD|CA)$",
    re.I,
)


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


def next_unplayed_matchweek(
    matches,
    league: LeagueConfig | None = None,
    season: str = "2026/27",
) -> int | None:
    """Smallest official matchweek that still has at least one unplayed fixture."""
    from epl_predictor.results import played_fixture_keys

    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    if not weeks:
        return None
    played = played_fixture_keys(matches, season=season)
    last_gw: int | None = None
    for gw in sorted(weeks):
        last_gw = gw
        remaining = False
        for home_d, away_d in weeks[gw]["fixtures"]:
            home_csv = league.csv_name.get(home_d, home_d)
            away_csv = league.csv_name.get(away_d, away_d)
            if (home_csv, away_csv) not in played:
                remaining = True
                break
        if remaining:
            return gw
    return last_gw


def next_unplayed_matchweek_fast(league: LeagueConfig | None = None) -> int | None:
    """Next unplayed week using openfootball scores only (no full history load)."""
    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    if not weeks:
        return None
    played = _openfootball_played_keys(league)
    last_gw: int | None = None
    for gw in sorted(weeks):
        last_gw = gw
        remaining = False
        for home_d, away_d in weeks[gw]["fixtures"]:
            home_csv = league.csv_name.get(home_d, home_d)
            away_csv = league.csv_name.get(away_d, away_d)
            if (home_csv, away_csv) not in played:
                remaining = True
                break
        if remaining:
            return gw
    return last_gw


def validate_matchweeks(league: LeagueConfig | None = None) -> list[str]:
    """Return human-readable problems, or [] if the slate looks usable."""
    league = league or EPL_CONFIG
    weeks = matchweeks_for(league)
    if not weeks:
        err = _FETCH_ERRORS.get(league.id)
        if league.fixture_feed_slug or league.id in _OPENFOOTBALL_FILES:
            msg = f"Could not load matchweek fixtures for {league.name}."
            if err:
                msg += f" ({err})"
            return [msg]
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


def fixture_load_error(league: LeagueConfig | None = None) -> str | None:
    league = league or EPL_CONFIG
    if matchweeks_for(league):
        return None
    return _FETCH_ERRORS.get(league.id)


def clear_fixture_cache(league_id: str | None = None) -> None:
    """Drop memory (+ optional disk) fixture cache so the next load retries the network."""
    if league_id:
        _MEMORY.pop(league_id, None)
        _PLAYED_MEMORY.pop(league_id, None)
        _FETCH_ERRORS.pop(league_id, None)
        for path in (_disk_path(league_id), _played_disk_path(league_id)):
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
        return
    _MEMORY.clear()
    _PLAYED_MEMORY.clear()
    _FETCH_ERRORS.clear()
    if CACHE_DIR.exists():
        for path in CACHE_DIR.glob("fixtures_*.json"):
            try:
                path.unlink()
            except OSError:
                pass


def matchweeks_for(league: LeagueConfig) -> dict[int, dict]:
    league = league or EPL_CONFIG
    cached = _MEMORY.get(league.id)
    if cached:
        return cached

    disk = _read_disk(league.id)
    if disk:
        _MEMORY[league.id] = disk
        return disk

    loaded = _fetch_and_parse(league)
    if loaded:
        _MEMORY[league.id] = loaded
        _write_disk(league.id, loaded)
        _FETCH_ERRORS.pop(league.id, None)
        return loaded

    return {}


def _disk_path(league_id: str) -> Path:
    return CACHE_DIR / f"fixtures_{league_id}.json"


def _played_disk_path(league_id: str) -> Path:
    return CACHE_DIR / f"fixtures_{league_id}_played.json"


def _read_played_disk(league_id: str) -> set[tuple[str, str]] | None:
    path = _played_disk_path(league_id)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {(str(a), str(b)) for a, b in (raw or [])}
    except Exception:  # noqa: BLE001
        return None


def _write_played_disk(league_id: str, played: set[tuple[str, str]]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = sorted([list(pair) for pair in played])
        _played_disk_path(league_id).write_text(json.dumps(payload), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _played_from_openfootball_payload(payload, league: LeagueConfig) -> set[tuple[str, str]]:
    played: set[tuple[str, str]] = set()
    matches = payload.get("matches") if isinstance(payload, dict) else None
    if not isinstance(matches, list):
        return played
    for match in matches:
        score = match.get("score") or {}
        ft = score.get("ft") if isinstance(score, dict) else None
        if not isinstance(ft, (list, tuple)) or len(ft) < 2:
            continue
        home_d = resolve_feed_team(league, str(match.get("team1") or ""))
        away_d = resolve_feed_team(league, str(match.get("team2") or ""))
        if home_d is None or away_d is None:
            continue
        played.add(
            (
                league.csv_name.get(home_d, home_d),
                league.csv_name.get(away_d, away_d),
            )
        )
    return played


def _openfootball_played_keys(league: LeagueConfig) -> set[tuple[str, str]]:
    """Completed (home_csv, away_csv) pairs from the openfootball JSON for this league."""
    cached = _PLAYED_MEMORY.get(league.id)
    if cached is not None:
        return cached
    disk = _read_played_disk(league.id)
    if disk is not None:
        _PLAYED_MEMORY[league.id] = disk
        return disk

    played: set[tuple[str, str]] = set()
    for season, filename in _OPENFOOTBALL_FILES.get(league.id, []):
        url = _OPENFOOTBALL_RAW.format(season=season, file=filename)
        try:
            raw = _http_get_bytes(url, timeout=8.0, retries=1)
            payload = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        played = _played_from_openfootball_payload(payload, league)
        # Cache even empty — means season started with no scores yet.
        _PLAYED_MEMORY[league.id] = played
        _write_played_disk(league.id, played)
        return played
    _PLAYED_MEMORY[league.id] = played
    return played


def _read_disk(league_id: str) -> dict[int, dict]:
    path = _disk_path(league_id)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        out: dict[int, dict] = {}
        for key, info in (raw or {}).items():
            gw = int(key)
            fixtures = [tuple(pair) for pair in info.get("fixtures", [])]
            out[gw] = {"label": info.get("label") or f"Matchweek {gw}", "fixtures": fixtures}
        return out
    except Exception:  # noqa: BLE001
        return {}


def _write_disk(league_id: str, weeks: dict[int, dict]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            str(gw): {
                "label": info["label"],
                "fixtures": [list(pair) for pair in info["fixtures"]],
            }
            for gw, info in weeks.items()
        }
        _disk_path(league_id).write_text(json.dumps(payload), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _http_get_bytes(url: str, timeout: float = 8.0, retries: int = 2) -> bytes:
    """Fetch URL with short timeout and light retries (httpx preferred)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    }
    last_exc: Exception | None = None
    try:
        import httpx

        for attempt in range(max(1, retries)):
            try:
                resp = httpx.get(url, timeout=timeout, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                return resp.content
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt + 1 < retries:
                    time.sleep(0.35 * (attempt + 1))
    except ImportError:
        from epl_predictor.results import _http_get

        try:
            return _http_get(url, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
    raise RuntimeError(str(last_exc) if last_exc else f"Failed to fetch {url}")


def _fetch_and_parse(league: LeagueConfig) -> dict[int, dict]:
    errors: list[str] = []

    # 1) openfootball (primary)
    for season, filename in _OPENFOOTBALL_FILES.get(league.id, []):
        url = _OPENFOOTBALL_RAW.format(season=season, file=filename)
        try:
            raw = _http_get_bytes(url, timeout=10.0, retries=2)
            payload = json.loads(raw.decode("utf-8"))
            parsed = _parse_openfootball(payload, league)
            if parsed:
                played = _played_from_openfootball_payload(payload, league)
                _PLAYED_MEMORY[league.id] = played
                _write_played_disk(league.id, played)
                return parsed
            errors.append(f"openfootball {season}/{filename}: no mapped fixtures")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"openfootball {season}/{filename}: {exc}")

    # 2) fixturedownload (short timeout — currently often unreachable)
    slug = league.fixture_feed_slug
    if slug:
        url = f"https://fixturedownload.com/feed/json/{slug}"
        try:
            raw = _http_get_bytes(url, timeout=5.0, retries=1)
            payload = json.loads(raw.decode("utf-8"))
            parsed = _parse_fixturedownload(payload, league)
            if parsed:
                return parsed
            errors.append("fixturedownload: empty after parse")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"fixturedownload: {exc}")

    _FETCH_ERRORS[league.id] = "; ".join(errors[:2]) if errors else "unknown error"
    return {}


def _parse_round_number(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        pass
    m = _ROUND_RE.search(text)
    if m:
        return int(m.group(1))
    digits = re.search(r"(\d+)", text)
    return int(digits.group(1)) if digits else None


def _name_candidates(raw: str) -> list[str]:
    raw = str(raw or "").strip()
    if not raw:
        return []
    cands = [raw]
    stripped = _SUFFIX_RE.sub("", raw).strip()
    if stripped and stripped not in cands:
        cands.append(stripped)
    # Hull City AFC / Sunderland AFC style
    stripped2 = re.sub(r"\s+AFC$", "", raw, flags=re.I).strip()
    if stripped2 and stripped2 not in cands:
        cands.append(stripped2)
    no_city = re.sub(r"\s+City$", "", stripped, flags=re.I).strip()
    if no_city and no_city not in cands:
        cands.append(no_city)
    return cands


def resolve_feed_team(league: LeagueConfig, raw: str) -> str | None:
    """Map a feed team name onto a display club name for this league."""
    inv_csv = {csv: display for display, csv in league.csv_name.items()}
    for cand in _name_candidates(raw):
        if cand in league.csv_name:
            return cand
        csv = league.canon_team(cand)
        if csv in inv_csv:
            return inv_csv[csv]
        # alias map may return display already
        if csv in league.csv_name:
            return csv
    # Fuzzy contains (prefer longest club name match)
    low = str(raw).lower()
    best = None
    best_len = 0
    for display in league.csv_name:
        dlow = display.lower()
        if dlow in low or low in dlow:
            if len(dlow) > best_len:
                best = display
                best_len = len(dlow)
    return best


def _build_weeks(by_round: dict[int, list[tuple[str, str]]]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for rnd, fixtures in sorted(by_round.items()):
        seen: set[tuple[str, str]] = set()
        unique: list[tuple[str, str]] = []
        for pair in fixtures:
            if pair in seen:
                continue
            seen.add(pair)
            unique.append(pair)
        if unique:
            out[rnd] = {"label": f"Matchweek {rnd}", "fixtures": unique}
    return out


def _parse_openfootball(payload, league: LeagueConfig) -> dict[int, dict]:
    if not isinstance(payload, dict):
        return {}
    matches = payload.get("matches")
    if not isinstance(matches, list):
        return {}
    by_round: dict[int, list[tuple[str, str]]] = {}
    for match in matches:
        rnd = _parse_round_number(match.get("round"))
        if rnd is None:
            continue
        home_d = resolve_feed_team(league, str(match.get("team1") or ""))
        away_d = resolve_feed_team(league, str(match.get("team2") or ""))
        if home_d is None or away_d is None:
            continue
        by_round.setdefault(rnd, []).append((home_d, away_d))
    return _build_weeks(by_round)


def _parse_fixturedownload(payload, league: LeagueConfig) -> dict[int, dict]:
    if not isinstance(payload, list):
        return {}
    by_round: dict[int, list[tuple[str, str]]] = {}
    for match in payload:
        rnd = _parse_round_number(match.get("RoundNumber"))
        if rnd is None:
            continue
        home_d = resolve_feed_team(league, str(match.get("HomeTeam") or ""))
        away_d = resolve_feed_team(league, str(match.get("AwayTeam") or ""))
        if home_d is None or away_d is None:
            continue
        by_round.setdefault(rnd, []).append((home_d, away_d))
    return _build_weeks(by_round)


def __getattr__(name: str):
    """Lazy MATCHWEEKS for older imports (EPL only)."""
    if name == "MATCHWEEKS":
        return matchweeks_for(EPL_CONFIG)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
