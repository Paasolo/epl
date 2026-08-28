"""Belgian Pro League 2026/27 configuration."""

from epl_predictor.leagues.base import LeagueConfig, make_context

CSV_NAME = {
    'Anderlecht': 'Anderlecht',
    'Royal Antwerp': 'Antwerp',
    'Cercle Brugge': 'Cercle Brugge',
    'Charleroi': 'Charleroi',
    'Club Brugge': 'Club Brugge',
    'Dender': 'Dender',
    'Genk': 'Genk',
    'Gent': 'Gent',
    'Mechelen': 'Mechelen',
    'OH Leuven': 'Oud-Heverlee Leuven',
    'RAAL La Louvière': 'RAAL La Louviere',
    'Sint-Truiden': 'St Truiden',
    'Union Saint-Gilloise': 'St. Gilloise',
    'Standard Liège': 'Standard',
    'Zulte Waregem': 'Waregem',
    'Westerlo': 'Westerlo',
}

LAST_SEASON_POSITION = {
    'Union Saint-Gilloise': 1,
    'Club Brugge': 2,
    'Genk': 3,
    'Anderlecht': 4,
    'Royal Antwerp': 5,
    'Gent': 6,
    'Mechelen': 7,
    'Charleroi': 8,
    'Standard Liège': 9,
    'Westerlo': 10,
    'Sint-Truiden': 11,
    'OH Leuven': 12,
    'Cercle Brugge': 13,
    'Zulte Waregem': 14,
    'RAAL La Louvière': 15,
    'Dender': 16,
}

PROMOTED = frozenset([])

TEAM_CONTEXT = {
    'Anderlecht': make_context('Besnik Hasi', net_spend_m=28, squad_turnover=0.24, key_ins=['starting striker', 'centre-back'], key_outs=['young midfielder'], notes='A talented squad has been reinforced to return to title contention.'),
    'Royal Antwerp': make_context('Jonas De Roeck', net_spend_m=20, squad_turnover=0.23, key_ins=['creative winger', 'full-back'], key_outs=['senior striker'], notes='Strong resources and home form preserve a championship-round profile.'),
    'Cercle Brugge': make_context('Onur Cinel', net_spend_m=10, squad_turnover=0.28, key_ins=['pressing forward', 'centre-back'], key_outs=['leading midfielder'], notes='Youth and aggressive pressing offset another summer of turnover.'),
    'Charleroi': make_context('Rik De Mil', net_spend_m=12, squad_turnover=0.21, key_ins=['centre-forward'], key_outs=['starting defender'], notes='Tactical continuity supports a stable mid-table outlook.'),
    'Club Brugge': make_context('Nicky Hayen', pedigree='elite', net_spend_m=45, squad_turnover=0.21, key_ins=['elite winger', 'central midfielder'], key_outs=['star forward'], notes="The league's deepest squad remains a leading title favourite."),
    'Dender': make_context('Vincent Euvrard', net_spend_m=7, squad_turnover=0.3, key_ins=['goalkeeper', 'target striker'], key_outs=['starting centre-back'], notes='Limited resources and high churn leave a narrow survival margin.'),
    'Genk': make_context('Thorsten Fink', pedigree='elite', net_spend_m=32, squad_turnover=0.23, key_ins=['young striker', 'ball-playing defender'], key_outs=['leading winger'], notes='Elite development and reinvestment support another title challenge.'),
    'Gent': make_context('Ivan Leko', net_spend_m=22, squad_turnover=0.26, key_ins=['creative midfielder', 'centre-back'], key_outs=['senior forward'], notes='A broad refresh seeks to restore consistent European qualification.'),
    'Mechelen': make_context('Fred Vanderbiest', net_spend_m=11, squad_turnover=0.19, key_ins=['wide attacker'], key_outs=['rotation midfielder'], notes='Squad continuity and a productive attack provide a high mid-table floor.'),
    'OH Leuven': make_context('David Hubert', net_spend_m=13, squad_turnover=0.24, key_ins=['centre-forward', 'holding midfielder'], key_outs=['starting full-back'], notes='Targeted additions should keep Leuven clear of the bottom places.'),
    'RAAL La Louvière': make_context('Frédéric Taquin', net_spend_m=9, squad_turnover=0.29, key_ins=['experienced defender', 'winger'], key_outs=['promotion-era striker'], notes='Second-season consolidation depends on improved attacking depth.'),
    'Sint-Truiden': make_context('Wouter Vrancken', net_spend_m=12, squad_turnover=0.22, key_ins=['central midfielder'], key_outs=['starting winger'], notes='A coherent structure and strong home venue support mid-table safety.'),
    'Union Saint-Gilloise': make_context('Sébastien Pocognoli', pedigree='elite', net_spend_m=38, squad_turnover=0.25, key_ins=['starting striker', 'wing-back'], key_outs=['two title-winning starters'], notes='Excellent recruitment keeps the champions strong despite regular sales.'),
    'Standard Liège': make_context('Mircea Rednic', net_spend_m=15, squad_turnover=0.27, key_ins=['centre-back', 'creative midfielder'], key_outs=['leading attacker'], notes='Investment improves depth but a significant reset creates volatility.'),
    'Zulte Waregem': make_context('Sven Vandenbroeck', net_spend_m=10, squad_turnover=0.25, key_ins=['goalkeeper', 'striker'], key_outs=['starting midfielder'], notes='Pragmatic recruitment should support another survival campaign.'),
    'Westerlo': make_context('Timmy Simons', net_spend_m=14, squad_turnover=0.22, key_ins=['fast winger', 'full-back'], key_outs=['central defender'], notes='An athletic young squad has enough quality for the middle group.'),
}

NAME_ALIASES = {
    'RSC Anderlecht': 'Anderlecht',
    'Royal Antwerp FC': 'Antwerp',
    'Antwerp': 'Antwerp',
    'Cercle Brugge KSV': 'Cercle Brugge',
    'Sporting Charleroi': 'Charleroi',
    'Royal Charleroi': 'Charleroi',
    'Club Brugge KV': 'Club Brugge',
    'FCV Dender EH': 'Dender',
    'KRC Genk': 'Genk',
    'KAA Gent': 'Gent',
    'KV Mechelen': 'Mechelen',
    'Oud-Heverlee Leuven': 'Oud-Heverlee Leuven',
    'OH Leuven': 'Oud-Heverlee Leuven',
    'RAAL La Louvière': 'RAAL La Louviere',
    'RAAL La Louviere': 'RAAL La Louviere',
    'Sint-Truidense VV': 'St Truiden',
    'Sint-Truiden': 'St Truiden',
    'Union Saint-Gilloise': 'St. Gilloise',
    'Union St.-Gilloise': 'St. Gilloise',
    'Royale Union Saint-Gilloise': 'St. Gilloise',
    'Standard Liège': 'Standard',
    'Standard Liege': 'Standard',
    'SV Zulte Waregem': 'Waregem',
    'Zulte Waregem': 'Waregem',
    'KVC Westerlo': 'Westerlo',
}

CONFIG = LeagueConfig(
    id='belgium', name='Belgian Pro League', fd_code='B1',
    index_url='https://www.football-data.co.uk/belgiumm.php', currency='€',
    second_tier_label='Challenger Pro League', fixture_feed_slug=None,
    matchweek_count=30, csv_name=CSV_NAME,
    last_season_position=LAST_SEASON_POSITION, promoted=PROMOTED,
    team_context=TEAM_CONTEXT, name_aliases=NAME_ALIASES,
    season_start='2026-07-25', context_as_of='20 Aug 2026',
)
