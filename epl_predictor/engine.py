"""Premier League match-outcome model (2000/01–2025/26).

Pipeline
--------
1. Clean results and build a shots-on-target xG proxy (less noisy than raw goals).
2. Walk ratings through history:
     - time-decayed attack / defence (Dixon–Coles intercepts = rolling league xG)
     - Elo with margin-of-victory, season carry-over, and absence shrinkage
3. Convert ratings to a score grid (vectorized Poisson + Dixon–Coles).
4. Blend with an Elo 1X2 (draws rise when sides are close).
5. Temperature-scale on a 3-season walk-forward hold-out so probabilities
   are calibrated, not over-confident.
6. Apply 2026/27 signings / coaching as a small capped overlay.

History always dominates the summer overlay. Promoted clubs are shrunk
toward a Championship-to-Premier-League prior.
"""

from __future__ import annotations

import math
import pickle
from collections import defaultdict, deque
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .context import (
    CSV_NAME,
    DISPLAY_NAME,
    LAST_SEASON_POSITION,
    PROMOTED_TEAMS,
    TEAM_CONTEXT,
    context_adjustment,
)

DATA_PATH = Path(__file__).resolve().parent.parent / "epl_final.csv"
CACHE_PATH = Path(__file__).resolve().parent / "model_cache.pkl"

ELO_MEAN = 1500.0
ELO_HFA = 62.0
ELO_K = 18.0
MAX_GOALS = 8
FORM_WINDOW = 6
H2H_WINDOW = 6
CARRYOVER = 0.74
Xg_SOT = 0.31
Xg_SHOT = 0.025
ATTACK_LR = 0.042
LEAGUE_EMA = 0.008
DC_RHO = -0.11
PROMOTED_ATTACK_PRIOR = 0.84
PROMOTED_DEFENSE_PRIOR = 0.82
HOLDOUT_SEASONS = ("2023/24", "2024/25", "2025/26")
AS_OF_KICKOFF = pd.Timestamp("2026-08-21")

_K = np.arange(MAX_GOALS + 1)
_LOG_FACT = np.array([math.lgamma(k + 1.0) for k in _K])
_OVER25 = np.add.outer(_K, _K) >= 3
_OVER15 = np.add.outer(_K, _K) >= 2


def _new_h2h() -> deque:
    return deque(maxlen=H2H_WINDOW)


def _new_recent() -> deque:
    return deque(maxlen=12)


def load_matches(path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(path or DATA_PATH)
    df["MatchDate"] = pd.to_datetime(df["MatchDate"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["MatchDate", "HomeTeam", "AwayTeam"])
    for col in (
        "FullTimeHomeGoals",
        "FullTimeAwayGoals",
        "HomeShots",
        "AwayShots",
        "HomeShotsOnTarget",
        "AwayShotsOnTarget",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["FullTimeHomeGoals", "FullTimeAwayGoals"])
    df["FullTimeHomeGoals"] = df["FullTimeHomeGoals"].clip(0, 10).astype(int)
    df["FullTimeAwayGoals"] = df["FullTimeAwayGoals"].clip(0, 10).astype(int)
    # Goals are ground truth; repair inconsistent result labels.
    hg, ag = df["FullTimeHomeGoals"], df["FullTimeAwayGoals"]
    df["FullTimeResult"] = np.select([hg > ag, hg < ag], ["H", "A"], default="D")
    df["HomeXG"] = _xg_proxy(hg, df["HomeShotsOnTarget"], df["HomeShots"])
    df["AwayXG"] = _xg_proxy(ag, df["AwayShotsOnTarget"], df["AwayShots"])
    return df.sort_values(["MatchDate", "HomeTeam", "AwayTeam"]).reset_index(drop=True)


def _xg_proxy(goals: pd.Series, sot: pd.Series, shots: pd.Series) -> np.ndarray:
    """Blend observed goals with a shots-on-target xG so blowout scores do not dominate."""
    g = goals.to_numpy(dtype=float)
    s = sot.to_numpy(dtype=float)
    sh = shots.to_numpy(dtype=float)
    s = np.where(np.isnan(s), np.nan, np.clip(s, 0, 20))
    sh = np.where(np.isnan(sh), np.nan, np.clip(sh, 0, 40))
    off_target = np.clip(np.nan_to_num(sh - s, nan=0.0), 0, 25)
    shot_xg = Xg_SOT * np.nan_to_num(s, nan=0.0) + Xg_SHOT * off_target
    shot_xg = np.clip(shot_xg, 0.0, 5.5)
    has_shots = np.isfinite(s)
    blended = np.where(has_shots, 0.50 * np.clip(g, 0, 5) + 0.50 * shot_xg, np.clip(g, 0, 5))
    return blended.astype(float)


def _elo_expected(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def _poisson_pmf(lam: float) -> np.ndarray:
    lam = float(np.clip(lam, 1e-8, 8.0))
    return np.exp(-lam + _K * math.log(lam) - _LOG_FACT)


def score_grid(lam_h: float, lam_a: float, rho: float = DC_RHO) -> np.ndarray:
    """Independent Poisson score matrix with Dixon–Coles low-score correction."""
    grid = np.outer(_poisson_pmf(lam_h), _poisson_pmf(lam_a))
    grid[0, 0] *= 1.0 - lam_h * lam_a * rho
    grid[0, 1] *= 1.0 + lam_h * rho
    grid[1, 0] *= 1.0 + lam_a * rho
    grid[1, 1] *= 1.0 - rho
    grid = np.maximum(grid, 0.0)
    total = grid.sum()
    if total <= 0:
        grid[:] = 1.0 / grid.size
    else:
        grid /= total
    return grid


def _one_x_two(grid: np.ndarray) -> tuple[float, float, float]:
    p_home = float(np.tril(grid, -1).sum())
    p_draw = float(np.trace(grid))
    p_away = float(np.triu(grid, 1).sum())
    total = p_home + p_draw + p_away
    return p_home / total, p_draw / total, p_away / total


def elo_1x2(elo_home: float, elo_away: float, hfa: float = ELO_HFA) -> tuple[float, float, float]:
    """Map two-way Elo into 1X2. Draws peak when the sides are evenly matched."""
    p_home_2 = _elo_expected(elo_home + hfa, elo_away)
    gap = abs(p_home_2 - 0.5)
    p_draw = float(np.clip(0.275 * (1.0 - 1.45 * gap), 0.145, 0.325))
    p_home = (1.0 - p_draw) * p_home_2
    p_away = (1.0 - p_draw) * (1.0 - p_home_2)
    return p_home, p_draw, p_away


def _blend(a: tuple[float, float, float], b: tuple[float, float, float], w: float) -> tuple[float, float, float]:
    mixed = tuple(w * x + (1.0 - w) * y for x, y in zip(a, b))
    total = sum(mixed)
    return tuple(x / total for x in mixed)  # type: ignore[return-value]


def _temperature(probs: tuple[float, float, float], temp: float) -> tuple[float, float, float]:
    logits = np.log(np.clip(probs, 1e-12, 1.0)) / max(temp, 0.4)
    logits -= logits.max()
    exp = np.exp(logits)
    exp /= exp.sum()
    return float(exp[0]), float(exp[1]), float(exp[2])


@dataclass
class TeamState:
    elo: float = ELO_MEAN
    attack: float = 0.0
    defense: float = 0.0
    last_date: pd.Timestamp | None = None
    matches: int = 0
    recent: deque = field(default_factory=_new_recent)


class LeagueModel:
    def __init__(self, matches: pd.DataFrame):
        self.matches = matches
        self.states: dict[str, TeamState] = defaultdict(TeamState)
        self.league_home = 1.48
        self.league_away = 1.16
        self.h2h: dict[tuple[str, str], deque] = defaultdict(_new_h2h)
        self.backtest: list[dict] = []
        self.blend_w = 0.72
        self.temperature = 1.0
        self._fitted = False

    def _idle_shrink(self, team: str, as_of: pd.Timestamp) -> float:
        st = self.states[team]
        if st.last_date is None:
            return 0.0
        years = max(0.0, (as_of - st.last_date).days / 365.25)
        if years < 0.45:
            return 1.0
        return float(0.68 ** years)

    def _decay_idle(self, team: str, as_of: pd.Timestamp) -> None:
        st = self.states[team]
        shrink = self._idle_shrink(team, as_of)
        if shrink >= 0.999:
            return
        st.elo = ELO_MEAN + (st.elo - ELO_MEAN) * shrink
        st.attack *= shrink
        st.defense *= shrink
        st.last_date = as_of

    def _center_ratings(self, teams: set[str]) -> None:
        if not teams:
            return
        atts = [self.states[t].attack for t in teams]
        defs = [self.states[t].defense for t in teams]
        mean_a = float(np.mean(atts))
        mean_d = float(np.mean(defs))
        for t in teams:
            self.states[t].attack -= mean_a
            self.states[t].defense -= mean_d

    def _season_carryover(self, teams: set[str]) -> None:
        for t in teams:
            st = self.states[t]
            st.elo = ELO_MEAN + CARRYOVER * (st.elo - ELO_MEAN)
            st.attack *= CARRYOVER
            st.defense *= CARRYOVER
        self._center_ratings(teams)

    def _lr(self, team: str) -> float:
        n = self.states[team].matches
        return ATTACK_LR / math.sqrt(1.0 + n / 36.0)

    def fit(self) -> None:
        prev_season: str | None = None
        season_teams: set[str] = set()
        holdout: list[dict] = []

        homes = self.matches["HomeTeam"].to_numpy()
        aways = self.matches["AwayTeam"].to_numpy()
        dates = self.matches["MatchDate"].to_numpy()
        seasons = self.matches["Season"].astype(str).to_numpy()
        hg_all = self.matches["FullTimeHomeGoals"].to_numpy()
        ag_all = self.matches["FullTimeAwayGoals"].to_numpy()
        xg_h_all = self.matches["HomeXG"].to_numpy()
        xg_a_all = self.matches["AwayXG"].to_numpy()
        sot_h_all = self.matches["HomeShotsOnTarget"].to_numpy()
        sot_a_all = self.matches["AwayShotsOnTarget"].to_numpy()
        res_all = self.matches["FullTimeResult"].to_numpy()

        for i in range(len(self.matches)):
            season = seasons[i]
            if prev_season is not None and season != prev_season:
                self._season_carryover(season_teams)
                season_teams = set()
            prev_season = season

            home, away = str(homes[i]), str(aways[i])
            date = pd.Timestamp(dates[i])
            hg, ag = int(hg_all[i]), int(ag_all[i])
            xg_h, xg_a = float(xg_h_all[i]), float(xg_a_all[i])
            result = str(res_all[i])
            season_teams.add(home)
            season_teams.add(away)

            self._decay_idle(home, date)
            self._decay_idle(away, date)
            hs, aws = self.states[home], self.states[away]

            if season in HOLDOUT_SEASONS:
                lam_h, lam_a = self._rating_lambdas(home, away, date)
                poisson = _one_x_two(
                    score_grid(float(np.clip(lam_h, 0.32, 3.6)), float(np.clip(lam_a, 0.26, 3.2)))
                )
                elo = elo_1x2(hs.elo, aws.elo)
                holdout.append(
                    {
                        "poisson": poisson,
                        "elo": elo,
                        "actual": result,
                        "season": season,
                        "home": home,
                        "away": away,
                        "date": date,
                        "hg": hg,
                        "ag": ag,
                    }
                )

            lam_h, lam_a = self._rating_lambdas(home, away, date)
            lam_h = float(np.clip(lam_h, 0.25, 4.2))
            lam_a = float(np.clip(lam_a, 0.20, 3.6))

            lr_h, lr_a = self._lr(home), self._lr(away)
            hs.attack += lr_h * (xg_h - lam_h)
            aws.defense += lr_a * (lam_h - xg_h)
            aws.attack += lr_a * (xg_a - lam_a)
            hs.defense += lr_h * (lam_a - xg_a)
            hs.attack = float(np.clip(hs.attack, -1.35, 1.35))
            hs.defense = float(np.clip(hs.defense, -1.35, 1.35))
            aws.attack = float(np.clip(aws.attack, -1.35, 1.35))
            aws.defense = float(np.clip(aws.defense, -1.35, 1.35))

            self.league_home = (1.0 - LEAGUE_EMA) * self.league_home + LEAGUE_EMA * xg_h
            self.league_away = (1.0 - LEAGUE_EMA) * self.league_away + LEAGUE_EMA * xg_a

            exp_home = _elo_expected(hs.elo + ELO_HFA, aws.elo)
            if hg > ag:
                score_h = 1.0
            elif hg < ag:
                score_h = 0.0
            else:
                score_h = 0.5
            mov = math.log1p(abs(xg_h - xg_a))
            k = ELO_K * (1.0 + 0.35 * mov) / math.sqrt(1.0 + min(hs.matches, aws.matches) / 50.0)
            hs.elo += k * (score_h - exp_home)
            aws.elo += k * ((1.0 - score_h) - (1.0 - exp_home))
            hs.elo = float(np.clip(hs.elo, 1100, 1950))
            aws.elo = float(np.clip(aws.elo, 1100, 1950))

            pts_h = 3 if hg > ag else 1 if hg == ag else 0
            pts_a = 3 if ag > hg else 1 if hg == ag else 0
            sot_h = 0.0 if np.isnan(sot_h_all[i]) else float(sot_h_all[i])
            sot_a = 0.0 if np.isnan(sot_a_all[i]) else float(sot_a_all[i])
            hs.recent.append((date, hg, ag, xg_h, sot_h, True, pts_h))
            aws.recent.append((date, ag, hg, xg_a, sot_a, False, pts_a))
            hs.last_date = date
            aws.last_date = date
            hs.matches += 1
            aws.matches += 1
            self.h2h[(home, away)].append((date, xg_h, xg_a, hg, ag))

        if season_teams:
            self._season_carryover(season_teams)

        self._calibrate(holdout)
        self.backtest = [
            row for row in holdout if row["season"] == "2025/26"
        ]
        self._fitted = True

    def _calibrate(self, holdout: list[dict]) -> None:
        if len(holdout) < 80:
            self.blend_w, self.temperature = 0.72, 1.05
            return
        poisson = np.array([row["poisson"] for row in holdout], dtype=float)
        elo = np.array([row["elo"] for row in holdout], dtype=float)
        y = np.array([{"H": 0, "D": 1, "A": 2}[row["actual"]] for row in holdout], dtype=int)
        idx = np.arange(len(y))
        best_ll = 1e9
        best = (0.72, 1.05)
        for w in np.linspace(0.58, 0.88, 7):
            mixed = w * poisson + (1.0 - w) * elo
            mixed = mixed / mixed.sum(axis=1, keepdims=True)
            log_mixed = np.log(np.clip(mixed, 1e-12, 1.0))
            for temp in np.linspace(0.80, 1.35, 12):
                logits = log_mixed / temp
                logits = logits - logits.max(axis=1, keepdims=True)
                q = np.exp(logits)
                q = q / q.sum(axis=1, keepdims=True)
                ll = float(-np.log(np.clip(q[idx, y], 1e-9, 1.0)).mean())
                if ll < best_ll:
                    best_ll = ll
                    best = (float(w), float(temp))
        self.blend_w, self.temperature = best

    def _rating_lambdas(self, home: str, away: str, as_of: pd.Timestamp | None) -> tuple[float, float]:
        hs, aws = self.states[home], self.states[away]
        as_of = as_of or AS_OF_KICKOFF
        sh = self._idle_shrink(home, as_of)
        sa = self._idle_shrink(away, as_of)
        lam_h = self.league_home * math.exp(hs.attack * sh - aws.defense * sa)
        lam_a = self.league_away * math.exp(aws.attack * sa - hs.defense * sh)
        return lam_h, lam_a

    def _form_multiplier(self, team: str, as_of: pd.Timestamp) -> float:
        st = self.states[team]
        if not st.recent or (st.last_date is not None and (as_of - st.last_date).days > 400):
            return 1.0
        last = list(st.recent)[-FORM_WINDOW:]
        n = len(last)
        weights = np.array([0.82 ** (n - 1 - i) for i in range(n)], dtype=float)
        weights /= weights.sum()
        pts = float(np.dot(weights, [x[6] for x in last]))
        xg_gd = float(np.dot(weights, [x[3] - x[2] for x in last]))
        return float(np.clip(1.0 + 0.045 * (pts - 1.4) + 0.035 * np.clip(xg_gd, -1.6, 1.6), 0.90, 1.10))

    def _shot_quality(self, team: str, home: bool, as_of: pd.Timestamp) -> float:
        st = self.states[team]
        if not st.recent or (st.last_date is not None and (as_of - st.last_date).days > 400):
            return 1.0
        rows = [x for x in st.recent if x[5] is home] or list(st.recent)
        sot = float(np.mean([x[4] for x in rows]))
        baseline = 4.6 if home else 3.8
        return float(np.clip(sot / max(baseline, 0.5), 0.90, 1.10))

    def _h2h_nudge(self, home: str, away: str) -> tuple[float, float]:
        meetings = list(self.h2h.get((home, away), []))
        if len(meetings) < 2:
            return 0.0, 0.0
        recent = meetings[-H2H_WINDOW:]
        n = len(recent)
        w = np.array([0.80 ** (n - 1 - i) for i in range(n)], dtype=float)
        w /= w.sum()
        xg_h = float(np.dot(w, [m[1] for m in recent]))
        xg_a = float(np.dot(w, [m[2] for m in recent]))
        return 0.06 * (xg_h - self.league_home), 0.06 * (xg_a - self.league_away)

    def _base_lambdas(self, home: str, away: str, as_of: pd.Timestamp | None) -> tuple[float, float]:
        as_of = as_of or AS_OF_KICKOFF
        lam_h, lam_a = self._rating_lambdas(home, away, as_of)
        lam_h = lam_h * self._form_multiplier(home, as_of) * self._shot_quality(home, True, as_of)
        lam_a = lam_a * self._form_multiplier(away, as_of) * self._shot_quality(away, False, as_of)
        h2h_h, h2h_a = self._h2h_nudge(home, away)
        return lam_h + h2h_h, lam_a + h2h_a

    def _promoted_prior(self, csv_name: str, as_of: pd.Timestamp | None) -> tuple[float, float]:
        as_of = as_of or AS_OF_KICKOFF
        if as_of < pd.Timestamp("2026-06-01"):
            return 1.0, 1.0
        display = DISPLAY_NAME.get(csv_name, csv_name)
        if display not in PROMOTED_TEAMS:
            return 1.0, 1.0
        st = self.states[csv_name]
        if st.last_date is None:
            gap_years = 10.0
        else:
            gap_years = (AS_OF_KICKOFF - st.last_date).days / 365.25
        if gap_years < 1.2:
            blend = 0.22
        elif gap_years < 4:
            blend = 0.40
        else:
            blend = 0.62
        return (
            (1 - blend) + blend * PROMOTED_ATTACK_PRIOR,
            (1 - blend) + blend * PROMOTED_DEFENSE_PRIOR,
        )

    def _lambdas_for_match(
        self,
        home_csv: str,
        away_csv: str,
        as_of: pd.Timestamp | None,
        apply_context: bool,
    ) -> tuple[float, float]:
        lam_h, lam_a = self._base_lambdas(home_csv, away_csv, as_of)
        ph_att, ph_def = self._promoted_prior(home_csv, as_of)
        pa_att, pa_def = self._promoted_prior(away_csv, as_of)
        lam_h *= ph_att / max(pa_def, 0.6)
        lam_a *= pa_att / max(ph_def, 0.6)
        if apply_context:
            home_disp = DISPLAY_NAME.get(home_csv, home_csv)
            away_disp = DISPLAY_NAME.get(away_csv, away_csv)
            if home_disp in TEAM_CONTEXT:
                adj = context_adjustment(home_disp)
                lam_h *= adj["attack_mult"]
                lam_a /= adj["defense_mult"]
            if away_disp in TEAM_CONTEXT:
                adj = context_adjustment(away_disp)
                lam_a *= adj["attack_mult"]
                lam_h /= adj["defense_mult"]
        return float(np.clip(lam_h, 0.32, 3.6)), float(np.clip(lam_a, 0.26, 3.2))

    def _predict_from_states(
        self,
        home_csv: str,
        away_csv: str,
        as_of: pd.Timestamp | None = None,
        apply_context: bool = True,
    ) -> dict:
        as_of = as_of or AS_OF_KICKOFF
        lam_h, lam_a = self._lambdas_for_match(home_csv, away_csv, as_of, apply_context)
        grid = score_grid(lam_h, lam_a)
        poisson = _one_x_two(grid)
        elo = elo_1x2(self.states[home_csv].elo, self.states[away_csv].elo)
        p_home, p_draw, p_away = _temperature(_blend(poisson, elo, self.blend_w), self.temperature)

        reasons_h: list[str] = []
        reasons_a: list[str] = []
        if apply_context:
            home_disp = DISPLAY_NAME.get(home_csv, home_csv)
            away_disp = DISPLAY_NAME.get(away_csv, away_csv)
            if home_disp in TEAM_CONTEXT:
                reasons_h = context_adjustment(home_disp)["reasons"]
            if away_disp in TEAM_CONTEXT:
                reasons_a = context_adjustment(away_disp)["reasons"]

        order = np.argsort(grid, axis=None)[::-1][:6]
        top_scores = []
        for idx in order:
            i, j = divmod(int(idx), MAX_GOALS + 1)
            top_scores.append({"score": f"{i}-{j}", "prob": float(grid[i, j])})

        p_btts = float(grid[1:, 1:].sum())
        p_over25 = float(grid[_OVER25].sum())
        p_over15 = float(grid[_OVER15].sum())

        outcomes = [
            ("Home win", p_home, "H"),
            ("Draw", p_draw, "D"),
            ("Away win", p_away, "A"),
        ]
        outcomes.sort(key=lambda x: x[1], reverse=True)
        best_label, best_p, best_code = outcomes[0]
        gap = best_p - outcomes[1][1]
        if best_p >= 0.58 and gap >= 0.16:
            confidence = "High"
        elif best_p >= 0.47 and gap >= 0.08:
            confidence = "Medium"
        else:
            confidence = "Low"

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
            "ease": best_p + 0.35 * gap,
            "top_scores": top_scores,
            "extras": extras,
            "p_btts": p_btts,
            "p_over25": p_over25,
            "elo_home": self.states[home_csv].elo,
            "elo_away": self.states[away_csv].elo,
            "reasons_home": reasons_h,
            "reasons_away": reasons_a,
        }

    def predict_fixture(
        self,
        home_display: str,
        away_display: str,
        apply_context: bool = True,
    ) -> dict:
        if not self._fitted:
            self.fit()
        if home_display not in CSV_NAME or away_display not in CSV_NAME:
            raise KeyError("Unknown club — pick two 2026/27 Premier League sides.")
        if home_display == away_display:
            raise ValueError("Home and away clubs must differ.")
        home_csv = CSV_NAME[home_display]
        away_csv = CSV_NAME[away_display]
        raw = self._predict_from_states(home_csv, away_csv, AS_OF_KICKOFF, apply_context=apply_context)
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
        raw["apply_context"] = apply_context
        return raw

    def _form_summary(self, csv_name: str) -> dict:
        st = self.states[csv_name]
        last = list(st.recent)[-FORM_WINDOW:]
        stale = st.last_date is None or (AS_OF_KICKOFF - st.last_date).days > 400
        if not last or stale:
            return {
                "played": 0,
                "points": 0,
                "gf": 0,
                "ga": 0,
                "sequence": "No recent Premier League matches",
            }
        seq = [("W" if x[6] == 3 else "D" if x[6] == 1 else "L") for x in last]
        return {
            "played": len(last),
            "points": int(sum(x[6] for x in last)),
            "gf": int(sum(x[1] for x in last)),
            "ga": int(sum(x[2] for x in last)),
            "sequence": "".join(seq),
        }

    def _h2h_table(self, home: str, away: str) -> list[dict]:
        rows = []
        for date, _xg_h, _xg_a, hg, ag in self.h2h.get((home, away), []):
            rows.append(
                {
                    "date": pd.Timestamp(date).strftime("%d %b %Y"),
                    "home": DISPLAY_NAME.get(home, home),
                    "away": DISPLAY_NAME.get(away, away),
                    "score": f"{hg}-{ag}",
                }
            )
        for date, _xg_h, _xg_a, hg, ag in self.h2h.get((away, home), []):
            rows.append(
                {
                    "date": pd.Timestamp(date).strftime("%d %b %Y"),
                    "home": DISPLAY_NAME.get(away, away),
                    "away": DISPLAY_NAME.get(home, home),
                    "score": f"{hg}-{ag}",
                }
            )
        rows.sort(key=lambda r: pd.to_datetime(r["date"]), reverse=True)
        return rows[:8]

    def backtest_summary(self) -> dict:
        if not self._fitted:
            self.fit()
        if not self.backtest:
            return {
                "n": 0,
                "accuracy": 0.0,
                "log_loss": 0.0,
                "brier": 0.0,
                "high_conf_acc": 0.0,
                "high_conf_n": 0,
                "baseline": 0.46,
                "temperature": self.temperature,
                "blend_w": self.blend_w,
            }
        correct = 0
        ll = 0.0
        brier = 0.0
        high_n = 0
        high_ok = 0
        for row in self.backtest:
            ph, pd_, pa = _temperature(_blend(row["poisson"], row["elo"], self.blend_w), self.temperature)
            probs = {"H": ph, "D": pd_, "A": pa}
            pred = max(probs, key=probs.get)
            actual = row["actual"]
            p = min(max(probs[actual], 1e-9), 1.0)
            ll -= math.log(p)
            brier += (ph - (actual == "H")) ** 2 + (pd_ - (actual == "D")) ** 2 + (pa - (actual == "A")) ** 2
            if pred == actual:
                correct += 1
            outcomes = sorted(probs.values(), reverse=True)
            gap = outcomes[0] - outcomes[1]
            if outcomes[0] >= 0.58 and gap >= 0.16:
                high_n += 1
                if pred == actual:
                    high_ok += 1
        n = len(self.backtest)
        return {
            "n": n,
            "accuracy": correct / n,
            "log_loss": ll / n,
            "brier": brier / n,
            "high_conf_acc": (high_ok / high_n) if high_n else 0.0,
            "high_conf_n": high_n,
            "baseline": 0.46,
            "temperature": self.temperature,
            "blend_w": self.blend_w,
        }

    def backtest_rows(self, season: str = "2025/26") -> list[dict]:
        """Calibrated walk-forward rows for the explorer UI."""
        if not self._fitted:
            self.fit()
        rows = []
        for row in self.backtest:
            if season and row.get("season") != season:
                continue
            ph, pd_, pa = _temperature(_blend(row["poisson"], row["elo"], self.blend_w), self.temperature)
            probs = {"H": ph, "D": pd_, "A": pa}
            pred = max(probs, key=probs.get)
            outcomes = sorted(probs.values(), reverse=True)
            gap = outcomes[0] - outcomes[1]
            if outcomes[0] >= 0.58 and gap >= 0.16:
                confidence = "High"
            elif outcomes[0] >= 0.47 and gap >= 0.08:
                confidence = "Medium"
            else:
                confidence = "Low"
            home = row.get("home", "")
            away = row.get("away", "")
            date = row.get("date")
            rows.append(
                {
                    "date": pd.Timestamp(date) if date is not None else None,
                    "month": pd.Timestamp(date).strftime("%Y-%m") if date is not None else "—",
                    "home": DISPLAY_NAME.get(home, home),
                    "away": DISPLAY_NAME.get(away, away),
                    "match": f"{DISPLAY_NAME.get(home, home)} vs {DISPLAY_NAME.get(away, away)}",
                    "actual": row["actual"],
                    "predicted": pred,
                    "correct": pred == row["actual"],
                    "confidence": confidence,
                    "p_home": ph,
                    "p_draw": pd_,
                    "p_away": pa,
                    "best_prob": outcomes[0],
                    "gap": gap,
                    "hg": row.get("hg"),
                    "ag": row.get("ag"),
                    "score": (
                        f"{row['hg']}-{row['ag']}"
                        if row.get("hg") is not None and row.get("ag") is not None
                        else "—"
                    ),
                }
            )
        return rows

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


def _write_cache(model: LeagueModel) -> None:
    try:
        CACHE_PATH.write_bytes(pickle.dumps(model, protocol=pickle.HIGHEST_PROTOCOL))
    except OSError:
        pass


@lru_cache(maxsize=1)
def get_model() -> LeagueModel:
    if CACHE_PATH.exists():
        try:
            model = pickle.loads(CACHE_PATH.read_bytes())
            if getattr(model, "_fitted", False) and model.backtest and "home" in model.backtest[0]:
                return model
        except (OSError, pickle.UnpicklingError, AttributeError, TypeError, IndexError, KeyError):
            pass
    model = LeagueModel(load_matches())
    model.fit()
    _write_cache(model)
    return model


def ranked_picks(predictions: list[dict]) -> list[dict]:
    return sorted(predictions, key=lambda p: p["ease"], reverse=True)
