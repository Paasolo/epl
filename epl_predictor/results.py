"""Live results: fetch, merge, and matchweek filtering (multi-league)."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from epl_predictor.leagues.base import LeagueConfig

LIVE_SEASON = "2026/27"

_FD_TO_INTERNAL = {
    "Date": "MatchDate",
    "HomeTeam": "HomeTeam",
    "AwayTeam": "AwayTeam",
    "FTHG": "FullTimeHomeGoals",
    "FTAG": "FullTimeAwayGoals",
    "FTR": "FullTimeResult",
    "HTHG": "HalfTimeHomeGoals",
    "HTAG": "HalfTimeAwayGoals",
    "HTR": "HalfTimeResult",
    "HS": "HomeShots",
    "AS": "AwayShots",
    "HST": "HomeShotsOnTarget",
    "AST": "AwayShotsOnTarget",
    "HC": "HomeCorners",
    "AC": "AwayCorners",
    "HF": "HomeFouls",
    "AF": "AwayFouls",
    "HY": "HomeYellowCards",
    "AY": "AwayYellowCards",
    "HR": "HomeRedCards",
    "AR": "AwayRedCards",
}

SCHEMA_COLS = [
    "Season",
    "MatchDate",
    "HomeTeam",
    "AwayTeam",
    "FullTimeHomeGoals",
    "FullTimeAwayGoals",
    "FullTimeResult",
    "HalfTimeHomeGoals",
    "HalfTimeAwayGoals",
    "HalfTimeResult",
    "HomeShots",
    "AwayShots",
    "HomeShotsOnTarget",
    "AwayShotsOnTarget",
    "HomeCorners",
    "AwayCorners",
    "HomeFouls",
    "AwayFouls",
    "HomeYellowCards",
    "AwayYellowCards",
    "HomeRedCards",
    "AwayRedCards",
]


def _http_get(url: str, timeout: float = 20.0) -> bytes:
    req = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; multi-league-predictor/1.0)"},
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _looks_like_results_csv(raw: bytes) -> bool:
    head = raw.lstrip(b"\xef\xbb\xbf")[:200].decode("utf-8", errors="ignore").lower()
    return "hometeam" in head and ("fthg" in head or "fulltimehomegoals" in head)


def _empty_status(season: str, url: str | None = None) -> dict:
    return {
        "ok": False,
        "season": season,
        "url": url,
        "source": None,
        "n_live": 0,
        "message": "",
        "soft": False,
    }


def _season_folder(season: str = LIVE_SEASON) -> str:
    parts = season.split("/")
    if len(parts) == 2 and len(parts[0]) >= 2 and len(parts[1]) >= 2:
        return parts[0][-2:] + parts[1][-2:]
    return "2627"


def live_urls(league: LeagueConfig, season: str = LIVE_SEASON) -> list[str]:
    code = _season_folder(season)
    base = f"https://www.football-data.co.uk/mmz4281/{code}/{league.fd_code}.csv"
    http = f"http://www.football-data.co.uk/mmz4281/{code}/{league.fd_code}.csv"
    return [base, http]


def _discover_league_url(league: LeagueConfig, season_code: str = "2627") -> str | None:
    """Parse the league index page for a CSV link matching the season folder."""
    try:
        html = _http_get(league.index_url).decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError, OSError):
        return None
    pattern = (
        rf'https?://[^"\']*mmz4281/{season_code}/{league.fd_code}\.csv|'
        rf'mmz4281/{season_code}/{league.fd_code}\.csv'
    )
    m = re.search(pattern, html, flags=re.I)
    if not m:
        return None
    href = m.group(0)
    if href.startswith("http"):
        return href
    return "https://www.football-data.co.uk/" + href.lstrip("/")


def _canon_with_aliases(name: str, aliases: dict[str, str] | None) -> str:
    name = str(name).strip()
    if not aliases:
        return name
    return aliases.get(name, name)


def normalize_football_data(
    df: pd.DataFrame,
    season: str = LIVE_SEASON,
    aliases: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Map football-data columns onto the shared schema; keep completed only."""
    if df is None or df.empty:
        return pd.DataFrame(columns=SCHEMA_COLS)

    df = df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    rename = {src: dst for src, dst in _FD_TO_INTERNAL.items() if src in df.columns}
    out = df.rename(columns=rename).copy()
    for col in SCHEMA_COLS:
        if col not in out.columns and col != "Season":
            out[col] = pd.NA
    out["Season"] = season
    out["MatchDate"] = _parse_match_dates(out["MatchDate"])
    out = out.dropna(subset=["MatchDate", "HomeTeam", "AwayTeam"])
    for col in ("FullTimeHomeGoals", "FullTimeAwayGoals"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["FullTimeHomeGoals", "FullTimeAwayGoals"])
    out["HomeTeam"] = out["HomeTeam"].map(lambda n: _canon_with_aliases(n, aliases))
    out["AwayTeam"] = out["AwayTeam"].map(lambda n: _canon_with_aliases(n, aliases))
    return out[SCHEMA_COLS].reset_index(drop=True)


def _fetch_football_data(
    league: LeagueConfig,
    season: str,
    timeout: float,
) -> tuple[pd.DataFrame, dict]:
    urls = live_urls(league, season)
    status = _empty_status(season, urls[0] if urls else None)
    code = _season_folder(season)
    discovered = _discover_league_url(league, code)
    if discovered and discovered not in urls:
        urls.insert(0, discovered)

    errors: list[str] = []
    for url in urls:
        status["url"] = url
        try:
            raw = _http_get(url, timeout=timeout)
            if not raw or len(raw) < 40 or not _looks_like_results_csv(raw):
                errors.append(f"{url}: not a results CSV yet")
                status["soft"] = True
                continue
            df = pd.read_csv(io.BytesIO(raw))
            live = normalize_football_data(df, season=season, aliases=league.name_aliases)
            status["ok"] = True
            status["source"] = "football-data.co.uk"
            status["n_live"] = int(len(live))
            status["message"] = (
                f"Fetched {len(live)} completed {season} match(es) from football-data.co.uk."
                if len(live)
                else f"football-data.co.uk has no completed {season} matches yet."
            )
            return live, status
        except HTTPError as exc:
            if exc.code in {300, 404}:
                errors.append(f"{url}: HTTP {exc.code} (season file not published yet)")
                status["soft"] = True
            else:
                errors.append(f"{url}: HTTPError: {exc}")
        except (URLError, TimeoutError, OSError, ValueError, pd.errors.ParserError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    status["message"] = errors[0] if errors else "football-data.co.uk unavailable."
    return pd.DataFrame(columns=SCHEMA_COLS), status


def _fetch_fixturedownload(
    league: LeagueConfig,
    season: str,
    timeout: float,
) -> tuple[pd.DataFrame, dict]:
    slug = league.fixture_feed_slug
    status = _empty_status(season, None)
    if not slug:
        status["message"] = f"No fixturedownload feed configured for {league.name}."
        status["soft"] = True
        return pd.DataFrame(columns=SCHEMA_COLS), status

    url = f"https://fixturedownload.com/feed/json/{slug}"
    status["url"] = url
    try:
        raw = _http_get(url, timeout=timeout)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, list):
            status["message"] = "fixturedownload feed was not a JSON list."
            return pd.DataFrame(columns=SCHEMA_COLS), status
        rows = []
        for match in payload:
            hg = match.get("HomeTeamScore")
            ag = match.get("AwayTeamScore")
            if hg is None or ag is None:
                continue
            home = league.canon_team(match.get("HomeTeam", ""))
            away = league.canon_team(match.get("AwayTeam", ""))
            if not home or not away:
                continue
            try:
                hg_i, ag_i = int(hg), int(ag)
            except (TypeError, ValueError):
                continue
            date = pd.to_datetime(match.get("DateUtc"), utc=True, errors="coerce")
            if pd.isna(date):
                continue
            date = date.tz_convert(None).normalize()
            rows.append(
                {
                    "Season": season,
                    "MatchDate": date,
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FullTimeHomeGoals": hg_i,
                    "FullTimeAwayGoals": ag_i,
                    "FullTimeResult": "H" if hg_i > ag_i else "A" if hg_i < ag_i else "D",
                }
            )
        live = pd.DataFrame(rows)
        if live.empty:
            live = pd.DataFrame(columns=SCHEMA_COLS)
        else:
            for col in SCHEMA_COLS:
                if col not in live.columns:
                    live[col] = pd.NA
            live = live[SCHEMA_COLS].reset_index(drop=True)
        status["ok"] = True
        status["source"] = "fixturedownload.com"
        status["n_live"] = int(len(live))
        status["message"] = (
            f"Fetched {len(live)} completed {season} match(es) from fixturedownload.com"
            f" ({league.name} football-data file not published yet)."
            if len(live)
            else f"No completed {season} scores in the fixturedownload feed yet."
        )
        return live, status
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        status["message"] = f"fixturedownload.com: {type(exc).__name__}: {exc}"
        return pd.DataFrame(columns=SCHEMA_COLS), status


def fetch_season_results(
    league: LeagueConfig,
    season: str = LIVE_SEASON,
    timeout: float = 20.0,
) -> tuple[pd.DataFrame, dict]:
    """Download completed matches for a season. On failure returns empty + status."""
    live, status = _fetch_football_data(league, season, timeout=timeout)
    if status.get("ok") and status.get("n_live", 0) > 0:
        return live, status

    alt, alt_status = _fetch_fixturedownload(league, season, timeout=timeout)
    if alt_status.get("ok"):
        return alt, alt_status

    combined = _empty_status(season, status.get("url"))
    if status.get("soft") and not alt_status.get("ok"):
        combined["soft"] = True
        combined["message"] = (
            f"Live {season} results are not published on football-data.co.uk yet "
            f"({league.name} CSV still missing). Using historical CSV only until scores appear."
        )
    else:
        combined["message"] = (
            status.get("message")
            or alt_status.get("message")
            or "Could not fetch live results. Using historical CSV only."
        )
    return pd.DataFrame(columns=SCHEMA_COLS), combined


def _parse_match_dates(series: pd.Series) -> pd.Series:
    """Parse football-data dates (dd/mm/yy) and ISO dates from our cached CSVs."""
    as_str = series.astype(str)
    iso_mask = as_str.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(series.loc[iso_mask], errors="coerce")
    rest = ~iso_mask & series.notna()
    if rest.any():
        parsed.loc[rest] = pd.to_datetime(series.loc[rest], dayfirst=True, errors="coerce")
        still_missing = rest & parsed.isna()
        if still_missing.any():
            parsed.loc[still_missing] = pd.to_datetime(series.loc[still_missing], errors="coerce")
    return parsed


def merge_history_and_live(base_df: pd.DataFrame, live_df: pd.DataFrame) -> pd.DataFrame:
    """Concatenate history + live rows; drop duplicate date/home/away."""
    frames = [f for f in (base_df, live_df) if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLS)
    merged = pd.concat(frames, ignore_index=True)
    if "MatchDate" in merged.columns:
        merged["MatchDate"] = _parse_match_dates(merged["MatchDate"])
    merged = merged.dropna(subset=["MatchDate", "HomeTeam", "AwayTeam"], how="any")
    merged = merged.drop_duplicates(subset=["MatchDate", "HomeTeam", "AwayTeam"], keep="last")
    return merged.sort_values(["MatchDate", "HomeTeam", "AwayTeam"]).reset_index(drop=True)


def results_fingerprint(df: pd.DataFrame) -> str:
    """Stable cache key: row count + latest match date."""
    if df is None or df.empty or "MatchDate" not in df.columns:
        return "0|none"
    dates = pd.to_datetime(df["MatchDate"], errors="coerce").dropna()
    if dates.empty:
        return f"{len(df)}|none"
    latest = pd.Timestamp(dates.max()).strftime("%Y-%m-%d")
    return f"{len(df)}|{latest}"


def training_meta(
    df: pd.DataFrame,
    live_status: dict | None = None,
    season: str = LIVE_SEASON,
) -> dict:
    """Summary used by the UI and model cache."""
    n = 0 if df is None or df.empty else len(df)
    through = None
    if df is not None and not df.empty and "MatchDate" in df.columns:
        dates = pd.to_datetime(df["MatchDate"], errors="coerce").dropna()
        if not dates.empty:
            through = pd.Timestamp(dates.max())
    live_n = 0
    if df is not None and not df.empty and "Season" in df.columns:
        live_n = int((df["Season"].astype(str) == season).sum())
    return {
        "fingerprint": results_fingerprint(df),
        "n_matches": n,
        "through": through,
        "n_live_season": live_n,
        "live_status": live_status or {},
    }


def played_fixture_keys(df: pd.DataFrame, season: str = LIVE_SEASON) -> set[tuple[str, str]]:
    """Set of (HomeTeam, AwayTeam) CSV names with a completed score in season."""
    if df is None or df.empty:
        return set()
    mask = df["Season"].astype(str) == season if "Season" in df.columns else slice(None)
    sub = df.loc[mask]
    if sub.empty:
        return set()
    keys: set[tuple[str, str]] = set()
    for home, away in zip(sub["HomeTeam"].astype(str), sub["AwayTeam"].astype(str)):
        keys.add((home, away))
    return keys


def score_lookup(
    df: pd.DataFrame,
    season: str = LIVE_SEASON,
) -> dict[tuple[str, str], tuple[int, int]]:
    """(home_csv, away_csv) -> (hg, ag) for completed matches in season."""
    if df is None or df.empty:
        return {}
    mask = df["Season"].astype(str) == season if "Season" in df.columns else slice(None)
    sub = df.loc[mask]
    out: dict[tuple[str, str], tuple[int, int]] = {}
    for _, row in sub.iterrows():
        try:
            hg = int(row["FullTimeHomeGoals"])
            ag = int(row["FullTimeAwayGoals"])
        except (TypeError, ValueError):
            continue
        out[(str(row["HomeTeam"]), str(row["AwayTeam"]))] = (hg, ag)
    return out


def split_matchweek_fixtures(
    gw: int,
    matches: pd.DataFrame,
    league: LeagueConfig,
    season: str = LIVE_SEASON,
) -> tuple[list[tuple[str, str]], list[dict]]:
    """Split official GW fixtures into unplayed display pairs and excluded score rows."""
    from epl_predictor.fixtures import fixtures_for

    pairs = fixtures_for(gw, league)
    played = played_fixture_keys(matches, season=season)
    scores = score_lookup(matches, season=season)
    remaining: list[tuple[str, str]] = []
    excluded: list[dict] = []
    for home_d, away_d in pairs:
        home_csv = league.csv_name.get(home_d, home_d)
        away_csv = league.csv_name.get(away_d, away_d)
        key = (home_csv, away_csv)
        if key in played:
            hg, ag = scores.get(key, (None, None))
            excluded.append(
                {
                    "home": home_d,
                    "away": away_d,
                    "home_csv": home_csv,
                    "away_csv": away_csv,
                    "hg": hg,
                    "ag": ag,
                    "score": f"{hg}-{ag}" if hg is not None and ag is not None else "FT",
                    "label": (
                        f"{home_d} {hg}-{ag} {away_d}"
                        if hg is not None and ag is not None
                        else f"{home_d} vs {away_d} (played)"
                    ),
                }
            )
        else:
            remaining.append((home_d, away_d))
    return remaining, excluded


def read_base_csv(path: Path) -> pd.DataFrame:
    """Raw read of a history CSV (pre-clean)."""
    df = pd.read_csv(path)
    for col in SCHEMA_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[SCHEMA_COLS]
