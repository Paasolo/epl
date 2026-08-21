"""Official 2026/27 Premier League matchweek fixtures.

Source: Premier League / club announcements for opening weekends.
Home and away use the same display names as PREMIER_LEAGUE_2026_27.
"""

from __future__ import annotations

# Each entry is (home_display, away_display).
MATCHWEEKS: dict[int, dict] = {
    1: {
        "label": "Matchweek 1 (21-24 Aug 2026)",
        "fixtures": [
            ("Arsenal", "Coventry City"),
            ("Hull City", "Manchester United"),
            ("Everton", "Crystal Palace"),
            ("Ipswich Town", "Sunderland"),
            ("Nottingham Forest", "Leeds United"),
            ("Brentford", "Tottenham Hotspur"),
            ("Brighton & Hove Albion", "Aston Villa"),
            ("Manchester City", "AFC Bournemouth"),
            ("Newcastle United", "Liverpool"),
            ("Fulham", "Chelsea"),
        ],
    },
}


def matchweek_options() -> dict[str, int]:
    """Label -> matchweek number for UI selectboxes."""
    return {info["label"]: gw for gw, info in sorted(MATCHWEEKS.items())}


def fixtures_for(gw: int) -> list[tuple[str, str]]:
    return list(MATCHWEEKS[gw]["fixtures"])
