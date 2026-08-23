"""Live Premier League results: fetch, merge, and matchweek filtering.

Completed 2026/27 scores are pulled from football-data.co.uk (same provider
lineage as epl_final.csv) and merged into the training history.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from .context import CSV_NAME
from .fixtures import fixtures_for

LIVE_SEASON = "2026/27"
# football-data season folder is YY next-YY, e.g. 2627 for 2026/27.
# Try https then http; the file appears once the season page lists Premier League.
LIVE_SEASON_URLS = {
    "2026/27": [
        "https://www.football-data.co.uk/mmz4281/2627/E0.csv",
        "http://www.football-data.co.uk/mmz4281/2627/E0.csv",
    ],
}

ENGLAND_INDEX_URL = "https://www.football-data.co.uk/englandm.php"

# football-data.co.uk short names -> epl_final schema
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


def _looks_like_results_csv(raw: bytes) -> bool:
    head = raw.lstrip(b"\xef\xbb\xbf")[:200].decode("utf-8", errors="ignore").lower()
    return "hometeam" in head and ("fthg" in head or "fulltimehomegoals" in head)


def _discover_e0_url(season_code: str = "2627") -> str | None:
    """Parse englandm.php for an E0.csv link matching the season folder."""
    try:
        req = Request(
            ENGLAND_INDEX_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; epl-predictor/1.0)"},
        )
        with urlopen(req, timeout=20.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError, OSError):
        return None
    # Prefer absolute or relative links containing mmz4281/{code}/E0.csv
    pattern = rf'https?://[^"\']*mmz4281/{season_code}/E0\.csv|mmz4281/{season_code}/E0\.csv'
    m = re.search(pattern, html, flags=re.I)
    if not m:
        return None
    href = m.group(0)
    if href.startswith("http"):
        return href
    return "https://www.football-data.co.uk/" + href.lstrip("/")


def fetch_season_results(
    season: str = LIVE_SEASON,
    timeout: float = 20.0,
) -> tuple[pd.DataFrame, dict]:
    """Download completed matches for a season. On failure returns empty + status."""
    urls = list(LIVE_SEASON_URLS.get(season) or [])
    status: dict = {
        "ok": False,
        "season": season,
        "url": urls[0] if urls else None,
        "n_live": 0,
        "message": "",
    }
    if not urls:
        status["message"] = f"No live URL configured for season {season}."
        return pd.DataFrame(columns=SCHEMA_COLS), status

    # Season folder is first two digits of each year: 2026/27 -> 2627
    parts = season.split("/")
    if len(parts) == 2 and len(parts[0]) >= 2 and len(parts[1]) >= 2:
        code = parts[0][-2:] + parts[1][-2:]
        discovered = _discover_e0_url(code)
        if discovered and discovered not in urls:
            urls.insert(0, discovered)

    errors: list[str] = []
    for url in urls:
        status["url"] = url
        try:
            req = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; epl-predictor/1.0)"},
            )
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            if not raw or len(raw) < 40 or not _looks_like_results_csv(raw):
                errors.append(f"{url}: not a results CSV")
                continue
            df = pd.read_csv(io.BytesIO(raw))
            live = normalize_football_data(df, season=season)
            status["ok"] = True
            status["n_live"] = int(len(live))
            status["message"] = (
                f"Fetched {len(live)} completed {season} match(es) from football-data.co.uk."
                if len(live)
                else f"No completed {season} matches in the live file yet."
            )
            return live, status
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, pd.errors.ParserError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    status["message"] = (
        "Could not fetch live results"
        + (f" ({errors[0]})" if errors else "")
        + ". Using historical CSV only."
    )
    return pd.DataFrame(columns=SCHEMA_COLS), status


def normalize_football_data(df: pd.DataFrame, season: str = LIVE_SEASON) -> pd.DataFrame:
    """Map football-data E0 columns onto the epl_final.csv schema; keep completed only."""
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
    out["MatchDate"] = pd.to_datetime(out["MatchDate"], dayfirst=True, errors="coerce")
    out = out.dropna(subset=["MatchDate", "HomeTeam", "AwayTeam"])
    for col in ("FullTimeHomeGoals", "FullTimeAwayGoals"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["FullTimeHomeGoals", "FullTimeAwayGoals"])
    out["HomeTeam"] = out["HomeTeam"].astype(str).str.strip()
    out["AwayTeam"] = out["AwayTeam"].astype(str).str.strip()
    return out[SCHEMA_COLS].reset_index(drop=True)


def merge_history_and_live(base_df: pd.DataFrame, live_df: pd.DataFrame) -> pd.DataFrame:
    """Concatenate history + live rows; drop duplicate date/home/away."""
    frames = [f for f in (base_df, live_df) if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLS)
    merged = pd.concat(frames, ignore_index=True)
    if "MatchDate" in merged.columns:
        merged["MatchDate"] = pd.to_datetime(merged["MatchDate"], dayfirst=True, errors="coerce")
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


def training_meta(df: pd.DataFrame, live_status: dict | None = None) -> dict:
    """Summary used by the UI and model cache."""
    n = 0 if df is None or df.empty else len(df)
    through = None
    if df is not None and not df.empty and "MatchDate" in df.columns:
        dates = pd.to_datetime(df["MatchDate"], errors="coerce").dropna()
        if not dates.empty:
            through = pd.Timestamp(dates.max())
    live_n = 0
    if df is not None and not df.empty and "Season" in df.columns:
        live_n = int((df["Season"].astype(str) == LIVE_SEASON).sum())
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


def score_lookup(df: pd.DataFrame, season: str = LIVE_SEASON) -> dict[tuple[str, str], tuple[int, int]]:
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
    season: str = LIVE_SEASON,
) -> tuple[list[tuple[str, str]], list[dict]]:
    """Split official GW fixtures into unplayed display pairs and excluded score rows."""
    pairs = fixtures_for(gw)
    played = played_fixture_keys(matches, season=season)
    scores = score_lookup(matches, season=season)
    remaining: list[tuple[str, str]] = []
    excluded: list[dict] = []
    for home_d, away_d in pairs:
        home_csv = CSV_NAME.get(home_d, home_d)
        away_csv = CSV_NAME.get(away_d, away_d)
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
    """Raw read of epl_final.csv (pre-clean)."""
    df = pd.read_csv(path)
    # Align column set for merge; cleaning happens in engine.load_matches.
    for col in SCHEMA_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[SCHEMA_COLS]
