"""2026/27 Premier League squad context: managers, signings, and disruption.

Figures are compiled from club announcements, Premier League, ESPN, BBC and
Wikipedia as of 20 August 2026 (window still open until 1 September).
They are used as small rating adjustments on top of historical match data —
not as a replacement for it.
"""

from __future__ import annotations

# Display name -> football-data.co.uk / epl_final.csv name
CSV_NAME = {
    "AFC Bournemouth": "Bournemouth",
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Brentford": "Brentford",
    "Brighton & Hove Albion": "Brighton",
    "Chelsea": "Chelsea",
    "Coventry City": "Coventry",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland": "Sunderland",
    "Tottenham Hotspur": "Tottenham",
}

DISPLAY_NAME = {csv: display for display, csv in CSV_NAME.items()}

PREMIER_LEAGUE_2026_27 = list(CSV_NAME.keys())

PROMOTED_TEAMS = {"Coventry City", "Hull City", "Ipswich Town"}

# Last completed PL season (2025/26) finishing position. Promoted sides use
# Championship rank as a proxy (21/22/23) so the model knows they are new.
LAST_SEASON_POSITION = {
    "Arsenal": 1,
    "Manchester City": 2,
    "Manchester United": 3,
    "Aston Villa": 4,
    "Liverpool": 5,
    "AFC Bournemouth": 6,
    "Sunderland": 7,
    "Brighton & Hove Albion": 8,
    "Brentford": 9,
    "Chelsea": 10,
    "Fulham": 11,
    "Newcastle United": 12,
    "Everton": 13,
    "Leeds United": 14,
    "Crystal Palace": 15,
    "Nottingham Forest": 16,
    "Tottenham Hotspur": 17,
    "Coventry City": 21,  # Championship champions
    "Ipswich Town": 22,  # Championship automatic promotion
    "Hull City": 23,  # Championship play-off winners
}

# Manager change this summer (before 2026/27 kickoff).
# change_type: none | mid_season | summer
# pedigree: elite | established | unproven_pl
TEAM_CONTEXT = {
    "AFC Bournemouth": {
        "manager": "Marco Rose",
        "previous_manager": "Andoni Iraola",
        "manager_since": "1 June 2026",
        "change_type": "summer",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 20,
        "squad_turnover": 0.22,
        "key_ins": [
            "António Silva (Benfica, ~£26m)",
            "Juanlu Sánchez (Sevilla)",
            "Álvaro Rodríguez (Elche)",
        ],
        "key_outs": [
            "Marcos Senesi (Tottenham, free)",
            "Hamed Traoré (Marseille)",
            "Luis Sinisterra (Cruzeiro)",
        ],
        "notes": "Iraola left for Liverpool; Rose inherits a side that finished 6th.",
    },
    "Arsenal": {
        "manager": "Mikel Arteta",
        "previous_manager": "Mikel Arteta",
        "manager_since": "22 December 2019",
        "change_type": "none",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": 90,
        "squad_turnover": 0.18,
        "key_ins": [
            "Bruno Guimarães (Newcastle, £75m)",
            "Christos Tzolis (Club Brugge, £34m)",
            "Piero Hincapié (Leverkusen, permanent)",
            "Illan Meslier (Leeds, free)",
        ],
        "key_outs": [
            "Leandro Trossard (Beşiktaş, £17m)",
            "Christian Nørgaard (Everton)",
            "Jakub Kiwior (Porto)",
        ],
        "notes": "Defending champions. Saliba started the season with a back injury.",
    },
    "Aston Villa": {
        "manager": "Unai Emery",
        "previous_manager": "Unai Emery",
        "manager_since": "1 November 2022",
        "change_type": "none",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": -70,
        "squad_turnover": 0.28,
        "key_ins": [
            "Johan Manzambi (Freiburg, ~£60m)",
            "João Gomes (Wolves, £34m)",
            "Alejandro Garnacho (Chelsea, loan)",
            "Zion Suzuki (Parma)",
        ],
        "key_outs": [
            "Morgan Rogers (Chelsea, £117m)",
            "Youri Tielemans (Manchester United, £35m)",
            "Lucas Digne (PSG)",
        ],
        "notes": "Sold British-record outgoing Rogers; Emery continuity is the main asset.",
    },
    "Brentford": {
        "manager": "Keith Andrews",
        "previous_manager": "Keith Andrews",
        "manager_since": "27 June 2025",
        "change_type": "none",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 15,
        "squad_turnover": 0.16,
        "key_ins": [
            "Callum Wilson (West Ham, free)",
            "Jaidon Anthony (Burnley)",
            "Mamadou Sangaré (Lens)",
            "Jannik Schuster (RB Salzburg)",
        ],
        "key_outs": [
            "Jordan Henderson (Chelsea, free)",
        ],
        "notes": "Andrews kept Brentford mid-table in his first season.",
    },
    "Brighton & Hove Albion": {
        "manager": "Fabian Hürzeler",
        "previous_manager": "Fabian Hürzeler",
        "manager_since": "15 June 2024",
        "change_type": "none",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 5,
        "squad_turnover": 0.24,
        "key_ins": [
            "Luka Vušković (Tottenham, £50m)",
            "Pascal Struijk (Leeds)",
            "Promise David (Union SG, loan)",
        ],
        "key_outs": [
            "Jan Paul van Hecke (Tottenham, £52m)",
            "Danny Welbeck (Chelsea)",
            "Carl Rushworth (Coventry)",
        ],
        "notes": "Typical Brighton churn; Hürzeler remains in charge.",
    },
    "Chelsea": {
        "manager": "Xabi Alonso",
        "previous_manager": "Liam Rosenior / Calum McFarlane (interim)",
        "manager_since": "1 July 2026",
        "change_type": "summer",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": 160,
        "squad_turnover": 0.32,
        "key_ins": [
            "Morgan Rogers (Aston Villa, £117m British record)",
            "Marco Palestra (Atalanta, £47m)",
            "Maxence Lacroix (Crystal Palace)",
            "Emmanuel Emegha (Strasbourg)",
            "Danny Welbeck (Brighton)",
        ],
        "key_outs": [
            "Marc Cucurella (Real Madrid, £52m)",
            "Andrey Santos (Manchester United, £48m)",
            "Trevoh Chalobah (Como, £25m)",
        ],
        "notes": "Heavy summer spend under a new elite coach after a 10th-place season.",
    },
    "Coventry City": {
        "manager": "Frank Lampard",
        "previous_manager": "Frank Lampard",
        "manager_since": "28 November 2024",
        "change_type": "none",
        "pedigree": "established",
        "promoted": True,
        "net_spend_m": 130,
        "squad_turnover": 0.40,
        "key_ins": [
            "Caleb Yirenkyi (Nordsjælland, ~£23m club record)",
            "Carl Rushworth (Brighton, ~£23m)",
            "Loum Tchaouna (Burnley, £20m)",
            "Aurèle Amenda (Eintracht Frankfurt, £15m)",
            "Taiwo Awoniyi (Nottingham Forest, £9m)",
            "Sidiki Cherif (Fenerbahçe)",
            "Gustavo Hamer (Sheffield United)",
        ],
        "key_outs": [],
        "notes": "Championship champions, first PL season since 2000/01. Big spend, same manager.",
    },
    "Crystal Palace": {
        "manager": "Pierre Sage",
        "previous_manager": "Oliver Glasner",
        "manager_since": "15 June 2026",
        "change_type": "summer",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": -15,
        "squad_turnover": 0.26,
        "key_ins": [
            "Takehiro Tomiyasu (Ajax, free)",
            "Óscar Mingueza (Celta, free)",
            "Dwight McNeil (Everton)",
            "Evann Guessand (Aston Villa, loan)",
        ],
        "key_outs": [
            "Maxence Lacroix (Chelsea)",
            "Brennan Johnson (Everton)",
        ],
        "notes": "Glasner left for Forest; Sage is a new voice after a 15th-place finish.",
    },
    "Everton": {
        "manager": "David Moyes",
        "previous_manager": "David Moyes",
        "manager_since": "11 January 2025",
        "change_type": "none",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 40,
        "squad_turnover": 0.20,
        "key_ins": [
            "Brennan Johnson (Crystal Palace)",
            "Hayden Hackney (Middlesbrough, £25m)",
            "Christian Nørgaard (Arsenal)",
            "Merlin Röhl (Freiburg)",
        ],
        "key_outs": [
            "Dwight McNeil (Crystal Palace)",
        ],
        "notes": "Moyes rebuilt Everton into a 13th-place side; Johnson is the headline arrival.",
    },
    "Fulham": {
        "manager": "Álvaro Arbeloa",
        "previous_manager": "Marco Silva",
        "manager_since": "7 July 2026",
        "change_type": "summer",
        "pedigree": "unproven_pl",
        "promoted": False,
        "net_spend_m": 25,
        "squad_turnover": 0.24,
        "key_ins": [
            "Gonzalo García (Real Madrid)",
            "Jonah Kusi-Asare (Bayern)",
            "César Palacios (Real Madrid)",
            "Shea Charles (Southampton)",
        ],
        "key_outs": [
            "Issa Diop (Ipswich)",
            "Saša Lukić (Ipswich)",
            "Raúl Jiménez (Wolves, free)",
            "Harry Wilson (Leeds, free)",
        ],
        "notes": "Silva departed; Arbeloa is untested in the Premier League.",
    },
    "Hull City": {
        "manager": "Sergej Jakirović",
        "previous_manager": "Sergej Jakirović",
        "manager_since": "11 June 2025",
        "change_type": "none",
        "pedigree": "unproven_pl",
        "promoted": True,
        "net_spend_m": 75,
        "squad_turnover": 0.45,
        "key_ins": [
            "Nobel Mendy (Rayo Vallecano, club record)",
            "Konstantinos Tzolakis (Olympiacos)",
            "Jack Butland (Rangers)",
            "Matt Targett (Newcastle, free)",
            "Hidemasa Morita (Sporting, free)",
            "Joe Gelhardt (Leeds)",
            "Lucas Gourna-Douath (RB Salzburg)",
        ],
        "key_outs": [
            "Ivor Pandur (Rangers)",
        ],
        "notes": "Play-off winners, first PL season since 2016/17. Manager has no PL experience.",
    },
    "Ipswich Town": {
        "manager": "Gary O'Neil",
        "previous_manager": "Kieran McKenna",
        "manager_since": "23 June 2026",
        "change_type": "summer",
        "pedigree": "established",
        "promoted": True,
        "net_spend_m": 150,
        "squad_turnover": 0.42,
        "key_ins": [
            "Julio Enciso (Strasbourg, ~£23m)",
            "Abdoul Ouattara (Strasbourg, ~£17m)",
            "Abdul Fatawu (Leicester)",
            "Daizen Maeda (Celtic)",
            "Issa Diop (Fulham)",
            "Saša Lukić (Fulham)",
            "Emersonn (Toulouse)",
        ],
        "key_outs": [
            "Arijanet Murić (Sassuolo)",
        ],
        "notes": "Immediate return after one year out. McKenna left; O'Neil has PL know-how and ~£150m spend.",
    },
    "Leeds United": {
        "manager": "Daniel Farke",
        "previous_manager": "Daniel Farke",
        "manager_since": "4 July 2023",
        "change_type": "none",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 30,
        "squad_turnover": 0.22,
        "key_ins": [
            "James Trafford (Manchester City, £40m)",
            "Nico Elvedi (Mönchengladbach)",
            "Harry Wilson (Fulham, free)",
            "Tarik Muharemović (Sassuolo)",
        ],
        "key_outs": [
            "Pascal Struijk (Brighton)",
            "Illan Meslier (Arsenal, free)",
            "Joe Gelhardt (Hull)",
        ],
        "notes": "Survived in 14th; Farke retained. Trafford is a statement keeper signing.",
    },
    "Liverpool": {
        "manager": "Andoni Iraola",
        "previous_manager": "Arne Slot",
        "manager_since": "4 June 2026",
        "change_type": "summer",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": 40,
        "squad_turnover": 0.20,
        "key_ins": [
            "Jérémy Jacquet (Rennes, £55m)",
            "Ronald Araújo (Barcelona, loan)",
            "Víctor Muñoz (Osasuna, £35m)",
        ],
        "key_outs": [
            "Mohamed Salah (Trabzonspor, free)",
            "Andrew Robertson (Tottenham, free)",
            "Ibrahima Konaté (Real Madrid, free)",
        ],
        "notes": "Slot sacked after 5th. Iraola arrives as Salah, Robertson and Konaté leave.",
    },
    "Manchester City": {
        "manager": "Enzo Maresca",
        "previous_manager": "Pep Guardiola",
        "manager_since": "29 June 2026",
        "change_type": "summer",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": 20,
        "squad_turnover": 0.30,
        "key_ins": [
            "Elliot Anderson (Nottingham Forest, £116m)",
            "Jeremy Monga (Leicester)",
            "Gerónimo Rulli (Marseille)",
        ],
        "key_outs": [
            "Rodri (Barcelona, £51m)",
            "Bernardo Silva (Real Madrid, free)",
            "Tijjani Reijnders (Al-Qadsiah, £47m)",
            "John Stones (Inter, free)",
            "Nathan Aké (Fenerbahçe)",
            "James Trafford (Leeds, £40m)",
        ],
        "notes": "Post-Guardiola reset. Haaland remains; midfield spine (Rodri, Bernardo) has been gutted.",
    },
    "Manchester United": {
        "manager": "Michael Carrick",
        "previous_manager": "Michael Carrick",
        "manager_since": "13 January 2026",
        "change_type": "mid_season",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 40,
        "squad_turnover": 0.18,
        "key_ins": [
            "Andrey Santos (Chelsea, £48m)",
            "Youri Tielemans (Aston Villa, £35m)",
        ],
        "key_outs": [
            "Rasmus Højlund (Napoli, £43m)",
            "Casemiro (Inter Miami, free)",
            "André Onana (Trabzonspor, loan)",
        ],
        "notes": "Finished 3rd after Carrick took over in January; first full season in charge.",
    },
    "Newcastle United": {
        "manager": "Matthias Jaissle",
        "previous_manager": "Eddie Howe",
        "manager_since": "5 August 2026",
        "change_type": "summer",
        "pedigree": "unproven_pl",
        "promoted": False,
        "net_spend_m": -170,
        "squad_turnover": 0.35,
        "key_ins": [
            "Bazoumana Touré (Hoffenheim, £42m)",
            "Sean Steur (Ajax, £23m)",
            "Amar Dedić (Benfica)",
        ],
        "key_outs": [
            "Sandro Tonali (Tottenham, £100m)",
            "Bruno Guimarães (Arsenal, £75m)",
            "Anthony Gordon (Barcelona, £61m)",
            "Kieran Trippier (Wolves, free)",
        ],
        "notes": "Howe resigned late July. Core midfield sold; Jaissle appointed 16 days before kick-off.",
    },
    "Nottingham Forest": {
        "manager": "Oliver Glasner",
        "previous_manager": "Vítor Pereira",
        "manager_since": "6 July 2026",
        "change_type": "summer",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": -90,
        "squad_turnover": 0.18,
        "key_ins": [
            "Ousmane Diomande (Sporting)",
            "Xaver Schlager (RB Leipzig, free)",
        ],
        "key_outs": [
            "Elliot Anderson (Manchester City, £116m)",
            "Taiwo Awoniyi (Coventry)",
        ],
        "notes": "Pereira sacked; Glasner is a proven PL upgrade but the attack lost Anderson.",
    },
    "Sunderland": {
        "manager": "Régis Le Bris",
        "previous_manager": "Régis Le Bris",
        "manager_since": "1 July 2024",
        "change_type": "none",
        "pedigree": "established",
        "promoted": False,
        "net_spend_m": 5,
        "squad_turnover": 0.10,
        "key_ins": [
            "Thomas Meunier (Lille, free)",
        ],
        "key_outs": [
            "Dan Neil (released)",
        ],
        "notes": "Quiet window after a remarkable 7th-place season. Continuity is the plan.",
    },
    "Tottenham Hotspur": {
        "manager": "Roberto De Zerbi",
        "previous_manager": "Roberto De Zerbi",
        "manager_since": "31 March 2026",
        "change_type": "mid_season",
        "pedigree": "elite",
        "promoted": False,
        "net_spend_m": 180,
        "squad_turnover": 0.34,
        "key_ins": [
            "Sandro Tonali (Newcastle, £100m)",
            "Mateus Fernandes (West Ham, £85m)",
            "Jan Paul van Hecke (Brighton, £52m)",
            "Andrew Robertson (Liverpool, free)",
            "Marcos Senesi (Bournemouth, free)",
        ],
        "key_outs": [
            "Cristian Romero (Atlético Madrid)",
            "Guglielmo Vicario (Juventus, loan)",
            "Djed Spence (Inter)",
            "Luka Vušković (Brighton, £50m)",
        ],
        "notes": "Finished 17th, then spent heavily. De Zerbi's first full season after a March appointment.",
    },
}


def context_adjustment(display_name: str) -> dict:
    """Translate qualitative summer context into a small multiplicative rating tweak.

    Returns attack_mult, defense_mult (higher defense_mult = harder to score against)
    and a short explanation list. Tweaks are capped so history still dominates.
    """
    ctx = TEAM_CONTEXT[display_name]
    attack = 1.0
    defense = 1.0
    reasons: list[str] = []

    spend = ctx["net_spend_m"]
    spend_effect = max(-0.08, min(0.10, spend / 1200.0))
    attack += spend_effect
    defense += spend_effect * 0.5
    if abs(spend) >= 40:
        direction = "strengthened" if spend > 0 else "weakened"
        reasons.append(f"Net spend ~£{spend}m ({direction} the squad on paper).")

    turnover = ctx["squad_turnover"]
    if turnover >= 0.30:
        attack -= 0.03
        defense -= 0.03
        reasons.append("High squad turnover — chemistry risk in the opening weeks.")

    if ctx["change_type"] == "summer":
        if ctx["pedigree"] == "elite":
            attack += 0.02
            defense += 0.02
            reasons.append(f"New coach {ctx['manager']} (elite pedigree) — small upgrade, bedding-in risk.")
        elif ctx["pedigree"] == "unproven_pl":
            attack -= 0.04
            defense -= 0.05
            reasons.append(f"New coach {ctx['manager']} has not managed in the Premier League before.")
        else:
            attack -= 0.015
            defense -= 0.02
            reasons.append(f"New coach {ctx['manager']} this summer — typical early-season dip.")
    elif ctx["change_type"] == "mid_season":
        attack += 0.015
        defense += 0.015
        reasons.append(f"{ctx['manager']} already in place from last season — continuity into 2026/27.")
    else:
        reasons.append(f"Manager continuity: {ctx['manager']}.")

    if ctx["promoted"]:
        # History already underweights them (no recent PL games). Extra conservative
        # haircut because Championship form does not fully transfer.
        attack -= 0.06
        defense -= 0.07
        reasons.append("Newly promoted — Premier League step-up applied.")
        if spend >= 100:
            attack += 0.04
            defense += 0.03
            reasons.append("Promotion spend is large enough to offset some of that step-up.")

    # Club-specific shocks that net spend does not fully capture.
    if display_name == "Liverpool":
        attack -= 0.05
        reasons.append("Mohamed Salah departure is a direct hit to chance conversion.")
        defense -= 0.02
        reasons.append("Konaté and Robertson left the back line.")
    elif display_name == "Manchester City":
        defense -= 0.03
        attack -= 0.015
        reasons.append("Rodri and Bernardo Silva exits hit control more than Haaland's goals.")
    elif display_name == "Newcastle United":
        attack -= 0.05
        defense -= 0.02
        reasons.append("Guimarães, Tonali and Gordon sold — midfield creation is gutted.")
    elif display_name == "Arsenal":
        attack += 0.03
        defense += 0.02
        reasons.append("Guimarães arrival plus title-winning spine; Saliba fitness is the caveat.")
    elif display_name == "Chelsea":
        attack += 0.04
        reasons.append("Rogers at a British-record fee plus Alonso is an attacking upgrade on 10th.")
    elif display_name == "Tottenham Hotspur":
        attack += 0.03
        defense += 0.02
        reasons.append("Tonali and Fernandes are a midfield reset after a 17th-place season.")
    elif display_name == "Nottingham Forest":
        attack -= 0.04
        reasons.append("Elliot Anderson sale removes the side's main creator.")
        defense += 0.02
        reasons.append("Glasner is a defensive upgrade on last season's coaching.")

    attack = float(max(0.82, min(1.16, attack)))
    defense = float(max(0.82, min(1.16, defense)))
    return {
        "attack_mult": attack,
        "defense_mult": defense,
        "reasons": reasons,
        "raw": ctx,
    }
