"""Download and cache multi-season history from football-data.co.uk."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from epl_predictor.leagues.base import LeagueConfig
from epl_predictor.results import SCHEMA_COLS, _http_get, _looks_like_results_csv, normalize_football_data

HISTORY_START = 2000  # 2000/01
HISTORY_END = 2025  # through 2025/26 (live 2026/27 fetched separately)


def season_code(start_year: int) -> str:
    """2000 -> '0001', 2025 -> '2526'."""
    end = (start_year + 1) % 100
    return f"{start_year % 100:02d}{end:02d}"


def season_label(start_year: int) -> str:
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def season_url(fd_code: str, start_year: int) -> str:
    return f"https://www.football-data.co.uk/mmz4281/{season_code(start_year)}/{fd_code}.csv"


def history_covers_through(path: Path, through_season: str = "2025/26") -> bool:
    if not path.exists() or path.stat().st_size < 200:
        return False
    try:
        seasons = pd.read_csv(path, usecols=["Season"])["Season"].astype(str)
    except (OSError, ValueError, KeyError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return False
    return through_season in set(seasons)


def fetch_season_csv(fd_code: str, start_year: int, timeout: float = 25.0) -> pd.DataFrame:
    url = season_url(fd_code, start_year)
    label = season_label(start_year)
    try:
        raw = _http_get(url, timeout=timeout)
    except Exception:  # noqa: BLE001 — network / HTTP failures skip the season
        return pd.DataFrame(columns=SCHEMA_COLS)
    if not raw or len(raw) < 40 or not _looks_like_results_csv(raw):
        return pd.DataFrame(columns=SCHEMA_COLS)
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except (ValueError, pd.errors.ParserError):
        return pd.DataFrame(columns=SCHEMA_COLS)
    return normalize_football_data(df, season=label, aliases=None)


def build_history(
    league: LeagueConfig,
    *,
    force: bool = False,
    start_year: int = HISTORY_START,
    end_year: int = HISTORY_END,
) -> tuple[pd.DataFrame, dict]:
    """Ensure a local history CSV exists (2000/01–2025/26) and return it.

    EPL uses the bundled epl_final.csv. Other leagues download from football-data.co.uk.
    """
    path = league.history_path
    status = {
        "ok": False,
        "path": str(path),
        "n_matches": 0,
        "message": "",
        "downloaded": False,
        "seasons_ok": 0,
        "seasons_missing": [],
    }

    if league.use_bundled_history:
        if not path.exists():
            status["message"] = f"Bundled history missing: {path}"
            return pd.DataFrame(columns=SCHEMA_COLS), status
        df = pd.read_csv(path)
        for col in SCHEMA_COLS:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[SCHEMA_COLS]
        status.update(
            ok=True,
            n_matches=len(df),
            message=f"Using bundled history ({len(df):,} matches).",
        )
        return df, status

    path.parent.mkdir(parents=True, exist_ok=True)
    if not force and history_covers_through(path):
        df = pd.read_csv(path)
        for col in SCHEMA_COLS:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[SCHEMA_COLS]
        status.update(
            ok=True,
            n_matches=len(df),
            message=f"Cached history through 2025/26 ({len(df):,} matches).",
        )
        return df, status

    frames: list[pd.DataFrame] = []
    missing: list[str] = []
    for year in range(start_year, end_year + 1):
        frame = fetch_season_csv(league.fd_code, year)
        label = season_label(year)
        if frame.empty:
            missing.append(label)
            continue
        frames.append(frame)

    if not frames:
        status["message"] = f"No seasons downloaded for {league.fd_code}."
        status["seasons_missing"] = missing
        return pd.DataFrame(columns=SCHEMA_COLS), status

    merged = pd.concat(frames, ignore_index=True)
    if "MatchDate" in merged.columns:
        merged["MatchDate"] = pd.to_datetime(merged["MatchDate"], dayfirst=True, errors="coerce")
    merged = merged.dropna(subset=["MatchDate", "HomeTeam", "AwayTeam"], how="any")
    merged = merged.drop_duplicates(subset=["MatchDate", "HomeTeam", "AwayTeam"], keep="last")
    merged = merged.sort_values(["MatchDate", "HomeTeam", "AwayTeam"]).reset_index(drop=True)
    merged = merged[SCHEMA_COLS]
    # Persist dates as ISO so reloads stay unambiguous.
    to_save = merged.copy()
    to_save["MatchDate"] = pd.to_datetime(to_save["MatchDate"]).dt.strftime("%Y-%m-%d")
    to_save.to_csv(path, index=False)

    status.update(
        ok=True,
        n_matches=len(merged),
        downloaded=True,
        seasons_ok=len(frames),
        seasons_missing=missing,
        message=(
            f"Downloaded {len(frames)} seasons ({len(merged):,} matches) for {league.name}."
            + (f" Missing: {', '.join(missing)}." if missing else "")
        ),
    )
    return merged, status


def ensure_history(league: LeagueConfig, force: bool = False) -> Path:
    """Download history if needed; return the CSV path."""
    build_history(league, force=force)
    return league.history_path
