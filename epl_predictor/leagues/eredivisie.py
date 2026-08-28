"""Eredivisie 2026/27 configuration."""

from epl_predictor.leagues.base import LeagueConfig, make_context

CSV_NAME = {
    'AZ Alkmaar': 'AZ Alkmaar',
    'Ajax': 'Ajax',
    'Excelsior': 'Excelsior',
    'Feyenoord': 'Feyenoord',
    'Fortuna Sittard': 'For Sittard',
    'Go Ahead Eagles': 'Go Ahead Eagles',
    'FC Groningen': 'Groningen',
    'Heerenveen': 'Heerenveen',
    'NEC Nijmegen': 'Nijmegen',
    'PSV Eindhoven': 'PSV Eindhoven',
    'Sparta Rotterdam': 'Sparta Rotterdam',
    'Telstar': 'Telstar',
    'FC Twente': 'Twente',
    'FC Utrecht': 'Utrecht',
    'PEC Zwolle': 'Zwolle',
    'ADO Den Haag': 'ADO Den Haag',
    'SC Cambuur': 'Cambuur',
    'Willem II': 'Willem II',
}

LAST_SEASON_POSITION = {
    'PSV Eindhoven': 1,
    'Feyenoord': 2,
    'NEC Nijmegen': 3,
    'FC Twente': 4,
    'Ajax': 5,
    'FC Utrecht': 6,
    'AZ Alkmaar': 7,
    'Heerenveen': 8,
    'FC Groningen': 9,
    'Sparta Rotterdam': 10,
    'Fortuna Sittard': 11,
    'Go Ahead Eagles': 12,
    'Excelsior': 13,
    'Telstar': 14,
    'PEC Zwolle': 15,
    'ADO Den Haag': 21,
    'SC Cambuur': 22,
    'Willem II': 23,
}

PROMOTED = frozenset(['ADO Den Haag', 'SC Cambuur', 'Willem II'])

TEAM_CONTEXT = {
    'AZ Alkmaar': make_context('Lee-Roy Echteld', net_spend_m=18, squad_turnover=0.22, key_ins=['young striker', 'centre-back'], key_outs=['starting midfielder'], notes='A strong academy and European-level talent preserve a high ceiling.'),
    'Ajax': make_context('Míchel', previous_manager='Fred Grim', change_type='summer', pedigree='elite', net_spend_m=48, squad_turnover=0.3, key_ins=['elite winger', 'holding midfielder'], key_outs=['senior striker', 'centre-back'], notes='Major investment accompanies another attempt to restore title standards.'),
    'Excelsior': make_context('Ruben den Uil', net_spend_m=7, squad_turnover=0.25, key_ins=['centre-forward'], key_outs=['loan midfielder'], notes="Coaching continuity helps one of the league's smallest squads."),
    'Feyenoord': make_context('Giovanni van Bronckhorst', previous_manager='Robin van Persie', change_type='summer', pedigree='elite', net_spend_m=36, squad_turnover=0.23, key_ins=['starting winger', 'central defender'], key_outs=['leading scorer'], notes='An experienced returning coach keeps Feyenoord in the title race.'),
    'Fortuna Sittard': make_context('Danny Buijs', net_spend_m=8, squad_turnover=0.24, key_ins=['target striker'], key_outs=['first-choice full-back'], notes='A physical and direct identity supports mid-table stability.'),
    'Go Ahead Eagles': make_context('Joseph Oosting', previous_manager='Melvin Boel', change_type='summer', net_spend_m=12, squad_turnover=0.24, key_ins=['creative midfielder', 'full-back'], key_outs=['starting winger'], notes='A clear recruitment model should absorb the coaching change.'),
    'FC Groningen': make_context('Dick Lukkien', net_spend_m=11, squad_turnover=0.18, key_ins=['wide forward'], key_outs=['rotation defender'], notes='Young-player development and continuity point toward incremental improvement.'),
    'Heerenveen': make_context('Robin Veldman', net_spend_m=10, squad_turnover=0.21, key_ins=['striker', 'central midfielder'], key_outs=['starting winger'], notes='A balanced squad remains a credible top-half contender.'),
    'NEC Nijmegen': make_context('Dick Schreuder', net_spend_m=20, squad_turnover=0.24, key_ins=['goal-scoring winger', 'centre-back'], key_outs=['key midfielder'], notes='Smart reinvestment aims to consolidate a surprise top-three finish.'),
    'PSV Eindhoven': make_context('Peter Bosz', pedigree='elite', net_spend_m=55, squad_turnover=0.17, key_ins=['elite forward', 'right-back'], key_outs=['rotation winger'], notes='The champions combine elite attack, depth and tactical continuity.'),
    'Sparta Rotterdam': make_context('Rogier Meijer', previous_manager='Maurice Steijn', change_type='summer', net_spend_m=10, squad_turnover=0.25, key_ins=['centre-back', 'winger'], key_outs=['leading forward'], notes='A coaching transition slightly lowers a reliable mid-table baseline.'),
    'Telstar': make_context('Henk Brugge', previous_manager='Anthony Correia', change_type='summer', net_spend_m=6, squad_turnover=0.29, key_ins=['goalkeeper', 'target forward'], key_outs=['promotion-era midfielder'], notes='Limited resources make second-season survival the clear objective.'),
    'FC Twente': make_context('John van den Brom', net_spend_m=17, squad_turnover=0.2, key_ins=['creative winger'], key_outs=['starting full-back'], notes='Strong home form and technical quality sustain European ambitions.'),
    'FC Utrecht': make_context('Anthony Correia', previous_manager='Ron Jans', change_type='summer', net_spend_m=19, squad_turnover=0.23, key_ins=['centre-forward', 'holding midfielder'], key_outs=['veteran defender'], notes='Good depth should ease the handover to a new coach.'),
    'PEC Zwolle': make_context('Henry van der Vegt', net_spend_m=8, squad_turnover=0.22, key_ins=['centre-back'], key_outs=['starting striker'], notes='A stable structure offsets modest spending and attacking turnover.'),
    'ADO Den Haag': make_context('Robin Peter', change_type='summer', pedigree='unproven', promoted=True, net_spend_m=16, squad_turnover=0.31, key_ins=['Eredivisie midfielder', 'centre-back'], key_outs=['loan winger'], notes='Strong promotion form meets a substantial defensive step up.'),
    'SC Cambuur': make_context('Johan Plat', change_type='summer', pedigree='unproven', promoted=True, net_spend_m=13, squad_turnover=0.3, key_ins=['goalkeeper', 'mobile striker'], key_outs=['promotion captain'], notes='An attacking identity gives Cambuur upside despite a shallow squad.'),
    'Willem II': make_context('John Stegeman', change_type='summer', pedigree='unproven', promoted=True, net_spend_m=15, squad_turnover=0.32, key_ins=['experienced centre-back', 'winger'], key_outs=['leading scorer'], notes='Top-flight familiarity and targeted additions improve survival prospects.'),
}

NAME_ALIASES = {
    'AZ': 'AZ Alkmaar',
    'NEC': 'Nijmegen',
    'N.E.C.': 'Nijmegen',
    'N.E.C. Nijmegen': 'Nijmegen',
    'NEC Nijmegen': 'Nijmegen',
    'sc Heerenveen': 'Heerenveen',
    'Fortuna Sittard': 'For Sittard',
    'PEC Zwolle': 'Zwolle',
    'PSV': 'PSV Eindhoven',
    'FC Groningen': 'Groningen',
    'FC Twente': 'Twente',
    'FC Utrecht': 'Utrecht',
    'Excelsior Rotterdam': 'Excelsior',
    'SC Cambuur': 'Cambuur',
    'ADO Den Haag': 'ADO Den Haag',
    'Go Ahead Eagles': 'Go Ahead Eagles',
    'Sparta Rotterdam': 'Sparta Rotterdam',
    'SC Heerenveen': 'Heerenveen',
    'Willem II Tilburg': 'Willem II',
}

CONFIG = LeagueConfig(
    id='eredivisie', name='Eredivisie', fd_code='N1',
    index_url='https://www.football-data.co.uk/netherlandsm.php', currency='€',
    second_tier_label='Eerste Divisie', fixture_feed_slug='eredivisie-2026',
    matchweek_count=34, csv_name=CSV_NAME,
    last_season_position=LAST_SEASON_POSITION, promoted=PROMOTED,
    team_context=TEAM_CONTEXT, name_aliases=NAME_ALIASES,
    season_start='2026-08-07', context_as_of='20 Aug 2026',
)
