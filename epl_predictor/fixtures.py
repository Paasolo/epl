"""Official 2026/27 Premier League matchweek fixtures.

Source: Premier League fixture release / club and broadcast listings.
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
    2: {
        "label": "Matchweek 2 (28-31 Aug 2026)",
        "fixtures": [
            ("Crystal Palace", "Manchester City"),
            ("Liverpool", "Nottingham Forest"),
            ("Coventry City", "Hull City"),
            ("AFC Bournemouth", "Everton"),
            ("Tottenham Hotspur", "Newcastle United"),
            ("Leeds United", "Brentford"),
            ("Chelsea", "Brighton & Hove Albion"),
            ("Sunderland", "Fulham"),
            ("Manchester United", "Ipswich Town"),
            ("Aston Villa", "Arsenal"),
        ],
    },
    3: {
        "label": "Matchweek 3 (4-6 Sep 2026)",
        "fixtures": [
            ("Ipswich Town", "Liverpool"),
            ("Newcastle United", "AFC Bournemouth"),
            ("Brentford", "Sunderland"),
            ("Brighton & Hove Albion", "Leeds United"),
            ("Fulham", "Crystal Palace"),
            ("Manchester City", "Coventry City"),
            ("Nottingham Forest", "Tottenham Hotspur"),
            ("Hull City", "Aston Villa"),
            ("Everton", "Manchester United"),
            ("Arsenal", "Chelsea"),
        ],
    },
    4: {
        "label": "Matchweek 4 (12-14 Sep 2026)",
        "fixtures": [
            ("AFC Bournemouth", "Brentford"),
            ("Aston Villa", "Nottingham Forest"),
            ("Chelsea", "Hull City"),
            ("Crystal Palace", "Ipswich Town"),
            ("Liverpool", "Fulham"),
            ("Tottenham Hotspur", "Everton"),
            ("Sunderland", "Arsenal"),
            ("Coventry City", "Brighton & Hove Albion"),
            ("Manchester United", "Manchester City"),
            ("Leeds United", "Newcastle United"),
        ],
    },
}


def matchweek_options() -> dict[str, int]:
    """Label -> matchweek number for UI selectboxes."""
    return {info["label"]: gw for gw, info in sorted(MATCHWEEKS.items())}


def fixtures_for(gw: int) -> list[tuple[str, str]]:
    return list(MATCHWEEKS[gw]["fixtures"])
