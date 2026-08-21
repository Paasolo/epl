"""Official 2026/27 Premier League matchweek fixtures.

Source: Premier League fixture release / club and broadcast listings.
Home and away use the same display names as PREMIER_LEAGUE_2026_27.
"""

from __future__ import annotations

from epl_predictor.context import PREMIER_LEAGUE_2026_27

# Each entry is (home_display, away_display).
MATCHWEEKS: dict[int, dict] = {
    1: {
        "label": "Matchweek 1 (21 Aug–24 Aug 2026)",
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
        "label": "Matchweek 2 (29 Aug 2026)",
        "fixtures": [
            ("Aston Villa", "Arsenal"),
            ("AFC Bournemouth", "Everton"),
            ("Chelsea", "Brighton & Hove Albion"),
            ("Coventry City", "Hull City"),
            ("Crystal Palace", "Manchester City"),
            ("Leeds United", "Brentford"),
            ("Liverpool", "Nottingham Forest"),
            ("Manchester United", "Ipswich Town"),
            ("Sunderland", "Fulham"),
            ("Tottenham Hotspur", "Newcastle United"),
        ],
    },
    3: {
        "label": "Matchweek 3 (5 Sep 2026)",
        "fixtures": [
            ("Arsenal", "Chelsea"),
            ("Brentford", "Sunderland"),
            ("Brighton & Hove Albion", "Leeds United"),
            ("Everton", "Manchester United"),
            ("Fulham", "Crystal Palace"),
            ("Hull City", "Aston Villa"),
            ("Ipswich Town", "Liverpool"),
            ("Manchester City", "Coventry City"),
            ("Newcastle United", "AFC Bournemouth"),
            ("Nottingham Forest", "Tottenham Hotspur"),
        ],
    },
    4: {
        "label": "Matchweek 4 (12 Sep 2026)",
        "fixtures": [
            ("Aston Villa", "Nottingham Forest"),
            ("AFC Bournemouth", "Brentford"),
            ("Chelsea", "Hull City"),
            ("Coventry City", "Brighton & Hove Albion"),
            ("Crystal Palace", "Ipswich Town"),
            ("Leeds United", "Newcastle United"),
            ("Liverpool", "Fulham"),
            ("Manchester United", "Manchester City"),
            ("Sunderland", "Arsenal"),
            ("Tottenham Hotspur", "Everton"),
        ],
    },
    5: {
        "label": "Matchweek 5 (19 Sep 2026)",
        "fixtures": [
            ("AFC Bournemouth", "Liverpool"),
            ("Brentford", "Chelsea"),
            ("Brighton & Hove Albion", "Arsenal"),
            ("Everton", "Ipswich Town"),
            ("Fulham", "Manchester United"),
            ("Leeds United", "Crystal Palace"),
            ("Manchester City", "Sunderland"),
            ("Newcastle United", "Hull City"),
            ("Nottingham Forest", "Coventry City"),
            ("Tottenham Hotspur", "Aston Villa"),
        ],
    },
    6: {
        "label": "Matchweek 6 (10 Oct 2026)",
        "fixtures": [
            ("Arsenal", "Leeds United"),
            ("Aston Villa", "Brentford"),
            ("Chelsea", "AFC Bournemouth"),
            ("Coventry City", "Newcastle United"),
            ("Crystal Palace", "Nottingham Forest"),
            ("Hull City", "Everton"),
            ("Ipswich Town", "Fulham"),
            ("Liverpool", "Manchester City"),
            ("Manchester United", "Tottenham Hotspur"),
            ("Sunderland", "Brighton & Hove Albion"),
        ],
    },
    7: {
        "label": "Matchweek 7 (17 Oct 2026)",
        "fixtures": [
            ("AFC Bournemouth", "Sunderland"),
            ("Brentford", "Liverpool"),
            ("Brighton & Hove Albion", "Crystal Palace"),
            ("Everton", "Chelsea"),
            ("Fulham", "Hull City"),
            ("Leeds United", "Manchester United"),
            ("Manchester City", "Ipswich Town"),
            ("Newcastle United", "Aston Villa"),
            ("Nottingham Forest", "Arsenal"),
            ("Tottenham Hotspur", "Coventry City"),
        ],
    },
    8: {
        "label": "Matchweek 8 (24 Oct 2026)",
        "fixtures": [
            ("Arsenal", "Everton"),
            ("Aston Villa", "Manchester City"),
            ("Chelsea", "Tottenham Hotspur"),
            ("Coventry City", "Fulham"),
            ("Crystal Palace", "Newcastle United"),
            ("Hull City", "Brentford"),
            ("Ipswich Town", "Nottingham Forest"),
            ("Liverpool", "Brighton & Hove Albion"),
            ("Manchester United", "AFC Bournemouth"),
            ("Sunderland", "Leeds United"),
        ],
    },
    9: {
        "label": "Matchweek 9 (31 Oct 2026)",
        "fixtures": [
            ("Aston Villa", "Fulham"),
            ("AFC Bournemouth", "Leeds United"),
            ("Brentford", "Nottingham Forest"),
            ("Chelsea", "Manchester United"),
            ("Coventry City", "Sunderland"),
            ("Hull City", "Ipswich Town"),
            ("Liverpool", "Arsenal"),
            ("Manchester City", "Brighton & Hove Albion"),
            ("Newcastle United", "Everton"),
            ("Tottenham Hotspur", "Crystal Palace"),
        ],
    },
    10: {
        "label": "Matchweek 10 (7 Nov 2026)",
        "fixtures": [
            ("Arsenal", "Hull City"),
            ("Brighton & Hove Albion", "Brentford"),
            ("Crystal Palace", "Liverpool"),
            ("Everton", "Coventry City"),
            ("Fulham", "Newcastle United"),
            ("Ipswich Town", "AFC Bournemouth"),
            ("Leeds United", "Tottenham Hotspur"),
            ("Manchester United", "Aston Villa"),
            ("Nottingham Forest", "Manchester City"),
            ("Sunderland", "Chelsea"),
        ],
    },
    11: {
        "label": "Matchweek 11 (21 Nov 2026)",
        "fixtures": [
            ("Aston Villa", "Sunderland"),
            ("AFC Bournemouth", "Nottingham Forest"),
            ("Brentford", "Everton"),
            ("Chelsea", "Leeds United"),
            ("Coventry City", "Crystal Palace"),
            ("Hull City", "Brighton & Hove Albion"),
            ("Liverpool", "Manchester United"),
            ("Manchester City", "Fulham"),
            ("Newcastle United", "Arsenal"),
            ("Tottenham Hotspur", "Ipswich Town"),
        ],
    },
    12: {
        "label": "Matchweek 12 (28 Nov 2026)",
        "fixtures": [
            ("Arsenal", "Manchester City"),
            ("Brighton & Hove Albion", "Newcastle United"),
            ("Crystal Palace", "Hull City"),
            ("Everton", "Liverpool"),
            ("Fulham", "AFC Bournemouth"),
            ("Ipswich Town", "Aston Villa"),
            ("Leeds United", "Coventry City"),
            ("Manchester United", "Brentford"),
            ("Nottingham Forest", "Chelsea"),
            ("Sunderland", "Tottenham Hotspur"),
        ],
    },
    13: {
        "label": "Matchweek 13 (2 Dec 2026)",
        "fixtures": [
            ("Aston Villa", "Everton"),
            ("AFC Bournemouth", "Brighton & Hove Albion"),
            ("Brentford", "Arsenal"),
            ("Chelsea", "Crystal Palace"),
            ("Coventry City", "Ipswich Town"),
            ("Hull City", "Nottingham Forest"),
            ("Liverpool", "Sunderland"),
            ("Manchester City", "Leeds United"),
            ("Newcastle United", "Manchester United"),
            ("Tottenham Hotspur", "Fulham"),
        ],
    },
    14: {
        "label": "Matchweek 14 (5 Dec 2026)",
        "fixtures": [
            ("Aston Villa", "Crystal Palace"),
            ("AFC Bournemouth", "Hull City"),
            ("Brentford", "Manchester City"),
            ("Chelsea", "Liverpool"),
            ("Everton", "Fulham"),
            ("Leeds United", "Ipswich Town"),
            ("Manchester United", "Coventry City"),
            ("Newcastle United", "Sunderland"),
            ("Nottingham Forest", "Brighton & Hove Albion"),
            ("Tottenham Hotspur", "Arsenal"),
        ],
    },
    15: {
        "label": "Matchweek 15 (12 Dec 2026)",
        "fixtures": [
            ("Arsenal", "AFC Bournemouth"),
            ("Brighton & Hove Albion", "Everton"),
            ("Coventry City", "Aston Villa"),
            ("Crystal Palace", "Manchester United"),
            ("Fulham", "Brentford"),
            ("Hull City", "Tottenham Hotspur"),
            ("Ipswich Town", "Newcastle United"),
            ("Liverpool", "Leeds United"),
            ("Manchester City", "Chelsea"),
            ("Sunderland", "Nottingham Forest"),
        ],
    },
    16: {
        "label": "Matchweek 16 (19 Dec 2026)",
        "fixtures": [
            ("Arsenal", "Manchester United"),
            ("AFC Bournemouth", "Coventry City"),
            ("Brentford", "Newcastle United"),
            ("Brighton & Hove Albion", "Ipswich Town"),
            ("Chelsea", "Aston Villa"),
            ("Leeds United", "Fulham"),
            ("Liverpool", "Tottenham Hotspur"),
            ("Manchester City", "Hull City"),
            ("Nottingham Forest", "Everton"),
            ("Sunderland", "Crystal Palace"),
        ],
    },
    17: {
        "label": "Matchweek 17 (26 Dec 2026)",
        "fixtures": [
            ("Aston Villa", "Leeds United"),
            ("Coventry City", "Chelsea"),
            ("Crystal Palace", "Arsenal"),
            ("Everton", "Sunderland"),
            ("Fulham", "Brighton & Hove Albion"),
            ("Hull City", "Liverpool"),
            ("Ipswich Town", "Brentford"),
            ("Manchester United", "Nottingham Forest"),
            ("Newcastle United", "Manchester City"),
            ("Tottenham Hotspur", "AFC Bournemouth"),
        ],
    },
    18: {
        "label": "Matchweek 18 (30 Dec 2026)",
        "fixtures": [
            ("Aston Villa", "Liverpool"),
            ("Coventry City", "Brentford"),
            ("Crystal Palace", "AFC Bournemouth"),
            ("Everton", "Manchester City"),
            ("Fulham", "Arsenal"),
            ("Hull City", "Leeds United"),
            ("Ipswich Town", "Chelsea"),
            ("Manchester United", "Sunderland"),
            ("Newcastle United", "Nottingham Forest"),
            ("Tottenham Hotspur", "Brighton & Hove Albion"),
        ],
    },
    19: {
        "label": "Matchweek 19 (2 Jan 2027)",
        "fixtures": [
            ("Arsenal", "Ipswich Town"),
            ("AFC Bournemouth", "Aston Villa"),
            ("Brentford", "Crystal Palace"),
            ("Brighton & Hove Albion", "Manchester United"),
            ("Chelsea", "Newcastle United"),
            ("Leeds United", "Everton"),
            ("Liverpool", "Coventry City"),
            ("Manchester City", "Tottenham Hotspur"),
            ("Nottingham Forest", "Fulham"),
            ("Sunderland", "Hull City"),
        ],
    },
    20: {
        "label": "Matchweek 20 (6 Jan 2027)",
        "fixtures": [
            ("Arsenal", "Brentford"),
            ("Brighton & Hove Albion", "AFC Bournemouth"),
            ("Crystal Palace", "Chelsea"),
            ("Everton", "Aston Villa"),
            ("Fulham", "Tottenham Hotspur"),
            ("Ipswich Town", "Coventry City"),
            ("Leeds United", "Manchester City"),
            ("Manchester United", "Newcastle United"),
            ("Nottingham Forest", "Hull City"),
            ("Sunderland", "Liverpool"),
        ],
    },
    21: {
        "label": "Matchweek 21 (16 Jan 2027)",
        "fixtures": [
            ("Aston Villa", "Manchester United"),
            ("AFC Bournemouth", "Ipswich Town"),
            ("Brentford", "Brighton & Hove Albion"),
            ("Chelsea", "Sunderland"),
            ("Coventry City", "Everton"),
            ("Hull City", "Arsenal"),
            ("Liverpool", "Crystal Palace"),
            ("Manchester City", "Nottingham Forest"),
            ("Newcastle United", "Fulham"),
            ("Tottenham Hotspur", "Leeds United"),
        ],
    },
    22: {
        "label": "Matchweek 22 (23 Jan 2027)",
        "fixtures": [
            ("Arsenal", "Newcastle United"),
            ("Brighton & Hove Albion", "Manchester City"),
            ("Crystal Palace", "Tottenham Hotspur"),
            ("Everton", "Brentford"),
            ("Fulham", "Aston Villa"),
            ("Ipswich Town", "Hull City"),
            ("Leeds United", "Chelsea"),
            ("Manchester United", "Liverpool"),
            ("Nottingham Forest", "AFC Bournemouth"),
            ("Sunderland", "Coventry City"),
        ],
    },
    23: {
        "label": "Matchweek 23 (30 Jan 2027)",
        "fixtures": [
            ("Aston Villa", "Ipswich Town"),
            ("AFC Bournemouth", "Fulham"),
            ("Brentford", "Manchester United"),
            ("Chelsea", "Nottingham Forest"),
            ("Coventry City", "Leeds United"),
            ("Hull City", "Crystal Palace"),
            ("Liverpool", "Everton"),
            ("Manchester City", "Arsenal"),
            ("Newcastle United", "Brighton & Hove Albion"),
            ("Tottenham Hotspur", "Sunderland"),
        ],
    },
    24: {
        "label": "Matchweek 24 (6 Feb 2027)",
        "fixtures": [
            ("Arsenal", "Liverpool"),
            ("Brighton & Hove Albion", "Hull City"),
            ("Crystal Palace", "Coventry City"),
            ("Everton", "Newcastle United"),
            ("Fulham", "Manchester City"),
            ("Ipswich Town", "Tottenham Hotspur"),
            ("Leeds United", "AFC Bournemouth"),
            ("Manchester United", "Chelsea"),
            ("Nottingham Forest", "Brentford"),
            ("Sunderland", "Aston Villa"),
        ],
    },
    25: {
        "label": "Matchweek 25 (10 Feb 2027)",
        "fixtures": [
            ("Aston Villa", "AFC Bournemouth"),
            ("Coventry City", "Liverpool"),
            ("Crystal Palace", "Brentford"),
            ("Everton", "Leeds United"),
            ("Fulham", "Nottingham Forest"),
            ("Hull City", "Sunderland"),
            ("Ipswich Town", "Arsenal"),
            ("Manchester United", "Brighton & Hove Albion"),
            ("Newcastle United", "Chelsea"),
            ("Tottenham Hotspur", "Manchester City"),
        ],
    },
    26: {
        "label": "Matchweek 26 (20 Feb 2027)",
        "fixtures": [
            ("Arsenal", "Fulham"),
            ("AFC Bournemouth", "Crystal Palace"),
            ("Brentford", "Coventry City"),
            ("Brighton & Hove Albion", "Tottenham Hotspur"),
            ("Chelsea", "Ipswich Town"),
            ("Leeds United", "Aston Villa"),
            ("Liverpool", "Hull City"),
            ("Manchester City", "Newcastle United"),
            ("Nottingham Forest", "Manchester United"),
            ("Sunderland", "Everton"),
        ],
    },
    27: {
        "label": "Matchweek 27 (27 Feb 2027)",
        "fixtures": [
            ("Aston Villa", "Chelsea"),
            ("Coventry City", "AFC Bournemouth"),
            ("Crystal Palace", "Sunderland"),
            ("Everton", "Nottingham Forest"),
            ("Fulham", "Leeds United"),
            ("Hull City", "Manchester City"),
            ("Ipswich Town", "Brighton & Hove Albion"),
            ("Manchester United", "Arsenal"),
            ("Newcastle United", "Brentford"),
            ("Tottenham Hotspur", "Liverpool"),
        ],
    },
    28: {
        "label": "Matchweek 28 (3 Mar 2027)",
        "fixtures": [
            ("Arsenal", "Crystal Palace"),
            ("AFC Bournemouth", "Tottenham Hotspur"),
            ("Brentford", "Ipswich Town"),
            ("Brighton & Hove Albion", "Fulham"),
            ("Chelsea", "Coventry City"),
            ("Leeds United", "Hull City"),
            ("Liverpool", "Aston Villa"),
            ("Manchester City", "Everton"),
            ("Nottingham Forest", "Newcastle United"),
            ("Sunderland", "Manchester United"),
        ],
    },
    29: {
        "label": "Matchweek 29 (13 Mar 2027)",
        "fixtures": [
            ("Aston Villa", "Hull City"),
            ("AFC Bournemouth", "Newcastle United"),
            ("Chelsea", "Arsenal"),
            ("Coventry City", "Manchester City"),
            ("Crystal Palace", "Fulham"),
            ("Leeds United", "Brighton & Hove Albion"),
            ("Liverpool", "Ipswich Town"),
            ("Manchester United", "Everton"),
            ("Sunderland", "Brentford"),
            ("Tottenham Hotspur", "Nottingham Forest"),
        ],
    },
    30: {
        "label": "Matchweek 30 (20 Mar 2027)",
        "fixtures": [
            ("Arsenal", "Sunderland"),
            ("Brentford", "AFC Bournemouth"),
            ("Brighton & Hove Albion", "Coventry City"),
            ("Everton", "Tottenham Hotspur"),
            ("Fulham", "Liverpool"),
            ("Hull City", "Chelsea"),
            ("Ipswich Town", "Crystal Palace"),
            ("Manchester City", "Manchester United"),
            ("Newcastle United", "Leeds United"),
            ("Nottingham Forest", "Aston Villa"),
        ],
    },
    31: {
        "label": "Matchweek 31 (10 Apr 2027)",
        "fixtures": [
            ("Aston Villa", "Brighton & Hove Albion"),
            ("AFC Bournemouth", "Manchester City"),
            ("Chelsea", "Fulham"),
            ("Coventry City", "Arsenal"),
            ("Crystal Palace", "Everton"),
            ("Leeds United", "Nottingham Forest"),
            ("Liverpool", "Newcastle United"),
            ("Manchester United", "Hull City"),
            ("Sunderland", "Ipswich Town"),
            ("Tottenham Hotspur", "Brentford"),
        ],
    },
    32: {
        "label": "Matchweek 32 (17 Apr 2027)",
        "fixtures": [
            ("Arsenal", "Aston Villa"),
            ("Brentford", "Leeds United"),
            ("Brighton & Hove Albion", "Chelsea"),
            ("Everton", "AFC Bournemouth"),
            ("Fulham", "Sunderland"),
            ("Hull City", "Coventry City"),
            ("Ipswich Town", "Manchester United"),
            ("Manchester City", "Crystal Palace"),
            ("Newcastle United", "Tottenham Hotspur"),
            ("Nottingham Forest", "Liverpool"),
        ],
    },
    33: {
        "label": "Matchweek 33 (24 Apr 2027)",
        "fixtures": [
            ("Aston Villa", "Coventry City"),
            ("AFC Bournemouth", "Arsenal"),
            ("Brentford", "Fulham"),
            ("Chelsea", "Manchester City"),
            ("Everton", "Brighton & Hove Albion"),
            ("Leeds United", "Liverpool"),
            ("Manchester United", "Crystal Palace"),
            ("Newcastle United", "Ipswich Town"),
            ("Nottingham Forest", "Sunderland"),
            ("Tottenham Hotspur", "Hull City"),
        ],
    },
    34: {
        "label": "Matchweek 34 (1 May 2027)",
        "fixtures": [
            ("Arsenal", "Tottenham Hotspur"),
            ("Brighton & Hove Albion", "Nottingham Forest"),
            ("Coventry City", "Manchester United"),
            ("Crystal Palace", "Aston Villa"),
            ("Fulham", "Everton"),
            ("Hull City", "AFC Bournemouth"),
            ("Ipswich Town", "Leeds United"),
            ("Liverpool", "Chelsea"),
            ("Manchester City", "Brentford"),
            ("Sunderland", "Newcastle United"),
        ],
    },
    35: {
        "label": "Matchweek 35 (8 May 2027)",
        "fixtures": [
            ("AFC Bournemouth", "Manchester United"),
            ("Brentford", "Aston Villa"),
            ("Brighton & Hove Albion", "Sunderland"),
            ("Everton", "Hull City"),
            ("Fulham", "Ipswich Town"),
            ("Leeds United", "Arsenal"),
            ("Manchester City", "Liverpool"),
            ("Newcastle United", "Coventry City"),
            ("Nottingham Forest", "Crystal Palace"),
            ("Tottenham Hotspur", "Chelsea"),
        ],
    },
    36: {
        "label": "Matchweek 36 (15 May 2027)",
        "fixtures": [
            ("Arsenal", "Nottingham Forest"),
            ("Aston Villa", "Newcastle United"),
            ("Chelsea", "Everton"),
            ("Coventry City", "Tottenham Hotspur"),
            ("Crystal Palace", "Brighton & Hove Albion"),
            ("Hull City", "Fulham"),
            ("Ipswich Town", "Manchester City"),
            ("Liverpool", "Brentford"),
            ("Manchester United", "Leeds United"),
            ("Sunderland", "AFC Bournemouth"),
        ],
    },
    37: {
        "label": "Matchweek 37 (23 May 2027)",
        "fixtures": [
            ("AFC Bournemouth", "Chelsea"),
            ("Brentford", "Hull City"),
            ("Brighton & Hove Albion", "Liverpool"),
            ("Everton", "Arsenal"),
            ("Fulham", "Coventry City"),
            ("Leeds United", "Sunderland"),
            ("Manchester City", "Aston Villa"),
            ("Newcastle United", "Crystal Palace"),
            ("Nottingham Forest", "Ipswich Town"),
            ("Tottenham Hotspur", "Manchester United"),
        ],
    },
    38: {
        "label": "Matchweek 38 (30 May 2027)",
        "fixtures": [
            ("Arsenal", "Brighton & Hove Albion"),
            ("Aston Villa", "Tottenham Hotspur"),
            ("Chelsea", "Brentford"),
            ("Coventry City", "Nottingham Forest"),
            ("Crystal Palace", "Leeds United"),
            ("Hull City", "Newcastle United"),
            ("Ipswich Town", "Everton"),
            ("Liverpool", "AFC Bournemouth"),
            ("Manchester United", "Fulham"),
            ("Sunderland", "Manchester City"),
        ],
    },
}


def matchweek_options() -> dict[str, int]:
    """Label -> matchweek number for UI selectboxes."""
    return {info["label"]: gw for gw, info in sorted(MATCHWEEKS.items())}


def fixtures_for(gw: int) -> list[tuple[str, str]]:
    if gw not in MATCHWEEKS:
        raise KeyError(f"Unknown matchweek {gw}; valid: 1–{max(MATCHWEEKS)}")
    return list(MATCHWEEKS[gw]["fixtures"])


def validate_matchweeks() -> list[str]:
    """Return human-readable problems, or [] if all weeks look valid."""
    expected = set(PREMIER_LEAGUE_2026_27)
    problems: list[str] = []
    for gw, info in sorted(MATCHWEEKS.items()):
        fixtures = info["fixtures"]
        if len(fixtures) != 10:
            problems.append(f"GW{gw}: expected 10 fixtures, got {len(fixtures)}")
        teams = [t for pair in fixtures for t in pair]
        if len(teams) != 20:
            problems.append(f"GW{gw}: expected 20 team slots, got {len(teams)}")
        if len(set(teams)) != 20:
            problems.append(f"GW{gw}: duplicate team(s) in slate")
        unknown = set(teams) - expected
        if unknown:
            problems.append(f"GW{gw}: unknown teams {sorted(unknown)}")
        missing = expected - set(teams)
        if missing:
            problems.append(f"GW{gw}: missing teams {sorted(missing)}")
    return problems

