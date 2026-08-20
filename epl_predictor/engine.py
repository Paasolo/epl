"""Historical EPL ratings and match-outcome predictions.

The model is trained only on `epl_final.csv` (2000/01–2025/26). Summer 2026
signings and coaching changes are applied afterwards as small, capped
adjustments so they cannot overwhelm 26 seasons of results.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .context import (
    CSV_NAME,
    DISPLAY_NAME,
    LAST_SEASON_POSITION,
    PREMIER_LEAGUE_2026_27,
    PROMOTED_TEAMS,
    TEAM_CONTEXT,
    context_adjustment,
)

DATA_PATH = Path(__file__).resolve().parent.parent / "epl_final.csv"

HOME_ADV_ELO = 55.0
ELO_K = 18.0
ELO_MEAN = 1500.0
MAX_GOALS = 8
FORM_WINDOW = 6
H2H_WINDOW = 8

# Typical newly promoted side vs established PL average.
PROMOTED_ATTACK_PRIOR = 0.82
PROMOTED_DEFENSE_PRIOR = 0.80  # <1 means easier to score against


def _season_sort_key(season: str) -> int:
    return int(str(season).split("/")[0])


def load_matches(path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(path or DATA_PATH)
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], dayfirst=True)
    df = df.sort_values(["MatchDate", "HomeTeam", "AwayTeam"]).reset_index(drop=True)
    for col in (
        "FullTimeHomeGoals",
        "FullTimeAwayGoals",
        "HomeShots",
        "AwayShots",
        "HomeShotsOnTarget",
        "AwayShotsOnTarget",
        "HomeCorners",
        "AwayCorners",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["FullTimeResult"] = df["FullTimeResult"].astype(str).str.upper().str.strip()
    return df


def _elo_expected(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def _result_score(hg: int, ag: int) -> tuple[float, float]:
    if hg > ag:
        return 1.0, 0.0
    if hg < ag:
        return 0.0, 1.0
    return 0.5, 0.5


def _num(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if number != number else number


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return float(math.exp(-lam) * lam**k / math.factorial(k))


def _dixon_coles_tau(hg: int, ag: int, lam_h: float, lam_a: float, rho: float = -0.08) -> float:
    """Low-score correction used in football Poisson models."""
    if hg == 0 and ag == 0:
        return 1.0 - lam_h * lam_a * rho
    if hg == 0 and ag == 1:
        return 1.0 + lam_h * rho
    if hg == 1 and ag == 0:
        return 1.0 + lam_a * rho
    if hg == 1 and ag == 1:
        return 1.0 - rho
    return 1.0


@dataclass
class TeamState:
    elo: float = ELO_MEAN
    attack: float = 0.0  # log rating
    defense: float = 0.0
    last_date: pd.Timestamp | None = None
    matches: int = 0
    recent: deque | None = None  # (date, gf, ga, shots, sot, is_home, result_pts)

    def __post_init__(self):
        if self.recent is None:
            self.recent = deque(maxlen=12)


class LeagueModel:
    def __init__(self, matches: pd.DataFrame):
        self.matches = matches
        self.states: dict[str, TeamState] = defaultdict(TeamState)
        self.league_home_goals = 1.45
        self.league_away_goals = 1.15
        self.h2h: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=H2H_WINDOW))
        self.backtest: list[dict] = []
        self._fitted = False

    def _idle_shrink(self, team: str, as_of: pd.Timestamp) -> float:
        """Share of stored ratings still valid after time out of the league."""
        st = self.states[team]
        if st.last_date is None:
            return 0.0
        years = max(0.0, (as_of - st.last_date).days / 365.25)
        if years < 0.45:
            return 1.0
        return float(0.70 ** years)

    def _decay_idle(self, team: str, as_of: pd.Timestamp) -> None:
        """Apply absence shrinkage once, when a club next plays."""
        st = self.states[team]
        shrink = self._idle_shrink(team, as_of)
        if shrink >= 0.999:
            return
        st.elo = ELO_MEAN + (st.elo - ELO_MEAN) * shrink
        st.attack *= shrink
        st.defense *= shrink
        st.last_date = as_of

    def fit(self) -> None:
        home_goals = []
        away_goals = []
        lr = 0.035

        for row in self.matches.itertuples(index=False):
            date = row.MatchDate
            home, away = row.HomeTeam, row.AwayTeam
            hg = int(row.FullTimeHomeGoals)
            ag = int(row.FullTimeAwayGoals)
            result = row.FullTimeResult

            self._decay_idle(home, date)
            self._decay_idle(away, date)
            hs, aws = self.states[home], self.states[away]

            # Predict before updating — used for 2025/26 backtest.
            season = row.Season
            if str(season) == "2025/26":
                pred = self._predict_from_states(home, away, date, apply_context=False)
                pred["actual"] = result
                pred["home"] = home
                pred["away"] = away
                self.backtest.append(pred)

            lam_h, lam_a = self._raw_lambdas(home, away, date)
            lam_h = min(max(lam_h, 0.25), 4.5)
            lam_a = min(max(lam_a, 0.20), 4.0)

            hs.attack += lr * (hg - lam_h)
            aws.defense += lr * (lam_h - hg)
            aws.attack += lr * (ag - lam_a)
            hs.defense += lr * (lam_a - ag)

            # Elo
            exp_home = _elo_expected(hs.elo + HOME_ADV_ELO, aws.elo)
            score_h, score_a = _result_score(hg, ag)
            mov = abs(hg - ag)
            k = ELO_K * (1.0 + 0.15 * mov)
            hs.elo += k * (score_h - exp_home)
            aws.elo += k * (score_a - (1.0 - exp_home))

            pts_h = 3 if hg > ag else 1 if hg == ag else 0
            pts_a = 3 if ag > hg else 1 if hg == ag else 0
            hs.recent.append((date, hg, ag, _num(row.HomeShots), _num(row.HomeShotsOnTarget), True, pts_h))
            aws.recent.append((date, ag, hg, _num(row.AwayShots), _num(row.AwayShotsOnTarget), False, pts_a))
            hs.last_date = date
            aws.last_date = date
            hs.matches += 1
            aws.matches += 1
            self.h2h[(home, away)].append((date, hg, ag))

            home_goals.append(hg)
            away_goals.append(ag)

        self.league_home_goals = float(np.mean(home_goals[-380:]))
        self.league_away_goals = float(np.mean(away_goals[-380:]))
        self._fitted = True

    def _form_multiplier(self, team: str, as_of: pd.Timestamp | None = None) -> float:
        st = self.states[team]
        if not st.recent:
            return 1.0
        as_of = as_of or pd.Timestamp("2026-08-21")
        if st.last_date is not None and (as_of - st.last_date).days > 400:
            return 1.0
        last = list(st.recent)[-FORM_WINDOW:]
        pts = sum(x[6] for x in last) / max(len(last), 1)
        return float(max(0.90, min(1.10, 1.0 + 0.06 * (pts - 1.4))))

    def _shot_quality(self, team: str, home: bool, as_of: pd.Timestamp | None = None) -> float:
        st = self.states[team]
        as_of = as_of or pd.Timestamp("2026-08-21")
        if st.last_date is not None and (as_of - st.last_date).days > 400:
            return 1.0
        rows = [x for x in st.recent if x[5] is home] or list(st.recent)
        if not rows:
            return 1.0
        sot = np.mean([x[4] for x in rows])
        baseline = 4.6 if home else 3.8
        return float(max(0.88, min(1.12, sot / baseline)))

    def _h2h_nudge(self, home: str, away: str) -> tuple[float, float]:
        meetings = list(self.h2h.get((home, away), [])) + [
            (d, ag, hg) for (d, hg, ag) in self.h2h.get((away, home), [])
        ]
        if len(meetings) < 2:
            return 0.0, 0.0
        meetings = sorted(meetings, key=lambda x: x[0])[-H2H_WINDOW:]
        hg = np.mean([m[1] for m in meetings])
        ag = np.mean([m[2] for m in meetings])
        return float(0.08 * (hg - self.league_home_goals)), float(0.08 * (ag - self.league_away_goals))

    def _raw_lambdas(self, home: str, away: str, as_of: pd.Timestamp | None = None) -> tuple[float, float]:
        hs, aws = self.states[home], self.states[away]
        as_of = as_of or pd.Timestamp("2026-08-21")
        sh = self._idle_shrink(home, as_of)
        sa = self._idle_shrink(away, as_of)
        lam_h = math.exp(0.28 + hs.attack * sh - aws.defense * sa)
        lam_a = math.exp(aws.attack * sa - hs.defense * sh)
        return lam_h, lam_a

    def _base_lambdas(self, home: str, away: str, as_of: pd.Timestamp | None = None) -> tuple[float, float]:
        lam_h, lam_a = self._raw_lambdas(home, away, as_of)
        form_h = self._form_multiplier(home, as_of)
        form_a = self._form_multiplier(away, as_of)
        shot_h = self._shot_quality(home, True, as_of)
        shot_a = self._shot_quality(away, False, as_of)
        h2h_h, h2h_a = self._h2h_nudge(home, away)
        lam_h = lam_h * form_h * shot_h + h2h_h
        lam_a = lam_a * form_a * shot_a + h2h_a
        return lam_h, lam_a

    def _promoted_prior(self, csv_name: str) -> tuple[float, float]:
        """If a club has little recent PL evidence, blend toward a promoted prior."""
        st = self.states[csv_name]
        display = DISPLAY_NAME.get(csv_name, csv_name)
        if display not in PROMOTED_TEAMS:
            return 1.0, 1.0
        if st.last_date is not None:
            gap_years = (pd.Timestamp("2026-08-20") - st.last_date).days / 365.25
        else:
            gap_years = 10.0
        if gap_years < 1.2:
            # Ipswich were in the PL in 2024/25.
            blend = 0.25
        elif gap_years < 4:
            blend = 0.45
        else:
            blend = 0.70
        return (
            (1 - blend) + blend * PROMOTED_ATTACK_PRIOR,
            (1 - blend) + blend * PROMOTED_DEFENSE_PRIOR,
        )

    def _predict_from_states(
        self,
        home_csv: str,
        away_csv: str,
        as_of: pd.Timestamp | None = None,
        apply_context: bool = True,
    ) -> dict:
        lam_h, lam_a = self._base_lambdas(home_csv, away_csv, as_of)

        ph_att, ph_def = self._promoted_prior(home_csv)
        pa_att, pa_def = self._promoted_prior(away_csv)
        lam_h *= ph_att / pa_def
        lam_a *= pa_att / ph_def

        reasons_h: list[str] = []
        reasons_a: list[str] = []
        if apply_context:
            home_disp = DISPLAY_NAME.get(home_csv, home_csv)
            away_disp = DISPLAY_NAME.get(away_csv, away_csv)
            if home_disp in TEAM_CONTEXT:
                adj = context_adjustment(home_disp)
                lam_h *= adj["attack_mult"]
                lam_a /= adj["defense_mult"]
                reasons_h = adj["reasons"]
            if away_disp in TEAM_CONTEXT:
                adj = context_adjustment(away_disp)
                lam_a *= adj["attack_mult"]
                lam_h /= adj["defense_mult"]
                reasons_a = adj["reasons"]

        lam_h = float(min(max(lam_h, 0.30), 4.2))
        lam_a = float(min(max(lam_a, 0.25), 3.8))

        grid = np.zeros((MAX_GOALS + 1, MAX_GOALS + 1))
        for i in range(MAX_GOALS + 1):
            pi = _poisson_pmf(i, lam_h)
            for j in range(MAX_GOALS + 1):
                grid[i, j] = pi * _poisson_pmf(j, lam_a) * _dixon_coles_tau(i, j, lam_h, lam_a)
        grid /= grid.sum()

        p_home = float(np.tril(grid, -1).sum())
        p_draw = float(np.trace(grid))
        p_away = float(np.triu(grid, 1).sum())
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

        # Football 1X2 is noisy. Mix toward the long-run Premier League prior
        # so even mismatches keep a realistic upset tail.
        prior_h, prior_d, prior_a = 0.455, 0.260, 0.285
        mix = 0.16
        p_home = (1 - mix) * p_home + mix * prior_h
        p_draw = (1 - mix) * p_draw + mix * prior_d
        p_away = (1 - mix) * p_away + mix * prior_a
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

        flat = [(i, j, float(grid[i, j])) for i in range(MAX_GOALS + 1) for j in range(MAX_GOALS + 1)]
        flat.sort(key=lambda x: x[2], reverse=True)
        top_scores = [{"score": f"{i}-{j}", "prob": p} for i, j, p in flat[:6]]

        p_btts = float(grid[1:, 1:].sum())
        p_over25 = float(sum(grid[i, j] for i in range(MAX_GOALS + 1) for j in range(MAX_GOALS + 1) if i + j >= 3))
        p_over15 = float(sum(grid[i, j] for i in range(MAX_GOALS + 1) for j in range(MAX_GOALS + 1) if i + j >= 2))

        outcomes = [
            ("Home win", p_home, "H"),
            ("Draw", p_draw, "D"),
            ("Away win", p_away, "A"),
        ]
        outcomes.sort(key=lambda x: x[1], reverse=True)
        best_label, best_p, best_code = outcomes[0]
        second_p = outcomes[1][1]
        gap = best_p - second_p

        if best_p >= 0.58 and gap >= 0.18:
            confidence = "High"
        elif best_p >= 0.48 and gap >= 0.10:
            confidence = "Medium"
        else:
            confidence = "Low"

        ease = best_p + 0.35 * gap  # ranking key for "easiest to call"

        elo_h = self.states[home_csv].elo
        elo_a = self.states[away_csv].elo

        extras = [
            {"market": "Both teams to score", "pick": "Yes" if p_btts >= 0.5 else "No", "prob": max(p_btts, 1 - p_btts)},
            {"market": "Over 2.5 goals", "pick": "Over" if p_over25 >= 0.5 else "Under", "prob": max(p_over25, 1 - p_over25)},
            {"market": "Over 1.5 goals", "pick": "Over" if p_over15 >= 0.5 else "Under", "prob": max(p_over15, 1 - p_over15)},
            {"market": "Most likely score", "pick": top_scores[0]["score"], "prob": top_scores[0]["prob"]},
        ]
        extras.sort(key=lambda x: x["prob"], reverse=True)

        return {
            "p_home": p_home,
            "p_draw": p_draw,
            "p_away": p_away,
            "lambda_home": lam_h,
            "lambda_away": lam_a,
            "best_label": best_label,
            "best_code": best_code,
            "best_prob": best_p,
            "confidence": confidence,
            "gap": gap,
            "ease": ease,
            "top_scores": top_scores,
            "extras": extras,
            "p_btts": p_btts,
            "p_over25": p_over25,
            "elo_home": elo_h,
            "elo_away": elo_a,
            "reasons_home": reasons_h,
            "reasons_away": reasons_a,
        }

    def predict_fixture(self, home_display: str, away_display: str) -> dict:
        if not self._fitted:
            self.fit()
        home_csv = CSV_NAME[home_display]
        away_csv = CSV_NAME[away_display]
        raw = self._predict_from_states(home_csv, away_csv, pd.Timestamp("2026-08-21"), apply_context=True)
        raw["home_display"] = home_display
        raw["away_display"] = away_display
        raw["home_csv"] = home_csv
        raw["away_csv"] = away_csv
        raw["home_context"] = TEAM_CONTEXT[home_display]
        raw["away_context"] = TEAM_CONTEXT[away_display]
        raw["home_position"] = LAST_SEASON_POSITION[home_display]
        raw["away_position"] = LAST_SEASON_POSITION[away_display]
        raw["h2h"] = self._h2h_table(home_csv, away_csv)
        raw["form_home"] = self._form_summary(home_csv)
        raw["form_away"] = self._form_summary(away_csv)
        return raw

    def _form_summary(self, csv_name: str) -> dict:
        st = self.states[csv_name]
        last = list(st.recent)[-FORM_WINDOW:]
        stale = st.last_date is None or (pd.Timestamp("2026-08-20") - st.last_date).days > 400
        if not last or stale:
            return {
                "played": 0,
                "points": 0,
                "gf": 0,
                "ga": 0,
                "sequence": "No recent Premier League matches",
            }
        seq = []
        for _, _gf, _ga, *_rest, pts in last:
            seq.append("W" if pts == 3 else "D" if pts == 1 else "L")
        return {
            "played": len(last),
            "points": int(sum(x[6] for x in last)),
            "gf": int(sum(x[1] for x in last)),
            "ga": int(sum(x[2] for x in last)),
            "sequence": "".join(seq),
        }

    def _h2h_table(self, home: str, away: str) -> list[dict]:
        rows = []
        for date, hg, ag in self.h2h.get((home, away), []):
            rows.append({"date": date.strftime("%d %b %Y"), "home": DISPLAY_NAME.get(home, home), "away": DISPLAY_NAME.get(away, away), "score": f"{hg}-{ag}"})
        for date, hg, ag in self.h2h.get((away, home), []):
            rows.append({"date": date.strftime("%d %b %Y"), "home": DISPLAY_NAME.get(away, away), "away": DISPLAY_NAME.get(home, home), "score": f"{hg}-{ag}"})
        rows.sort(key=lambda r: pd.to_datetime(r["date"]), reverse=True)
        return rows[:8]

    def backtest_summary(self) -> dict:
        if not self._fitted:
            self.fit()
        if not self.backtest:
            return {"n": 0, "accuracy": 0.0, "log_loss": 0.0, "high_conf_acc": 0.0, "high_conf_n": 0}
        n = len(self.backtest)
        correct = 0
        ll = 0.0
        high_n = 0
        high_ok = 0
        for row in self.backtest:
            actual = row["actual"]
            probs = {"H": row["p_home"], "D": row["p_draw"], "A": row["p_away"]}
            pred = max(probs, key=probs.get)
            p = max(min(probs[actual], 1 - 1e-9), 1e-9)
            ll -= math.log(p)
            if pred == actual:
                correct += 1
            if row["confidence"] == "High":
                high_n += 1
                if pred == actual:
                    high_ok += 1
        return {
            "n": n,
            "accuracy": correct / n,
            "log_loss": ll / n,
            "high_conf_acc": (high_ok / high_n) if high_n else 0.0,
            "high_conf_n": high_n,
            "baseline": 0.46,  # long-run home-win rate is the naive baseline
        }

    def snapshot(self, display_name: str) -> dict:
        csv_name = CSV_NAME[display_name]
        st = self.states[csv_name]
        ctx = TEAM_CONTEXT[display_name]
        return {
            "elo": st.elo,
            "attack": st.attack,
            "defense": st.defense,
            "matches": st.matches,
            "last_date": st.last_date.strftime("%d %b %Y") if st.last_date is not None else "No recent PL games",
            "form": self._form_summary(csv_name),
            "manager": ctx["manager"],
            "promoted": display_name in PROMOTED_TEAMS,
            "position": LAST_SEASON_POSITION[display_name],
        }


@lru_cache(maxsize=1)
def get_model() -> LeagueModel:
    model = LeagueModel(load_matches())
    model.fit()
    return model


def ranked_picks(predictions: list[dict]) -> list[dict]:
    """Highest-confidence / easiest calls first."""
    return sorted(predictions, key=lambda p: p["ease"], reverse=True)
