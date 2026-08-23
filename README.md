# Premier League match predictor (2026/27)

Interactive Python model that predicts user-selected Premier League fixtures — a custom slate or an official matchweek.

It is fitted on `epl_final.csv` (Premier League matches from 2000/01 through 2025/26, originally from football-data.co.uk), plus any completed **2026/27** results fetched live from the same provider. Summer 2026 signings and coaching changes are applied as a small overlay.

## Run

From this folder:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The app opens in your browser with three tabs:

- **Predict matches** — load any official Matchweek 1–38 (or add/remove fixtures by hand). Finished games are excluded automatically when you load a matchweek. Toggle the summer overlay on/off, then click **Predict**. Download the ranked slate as CSV or JSON.
- **Team strength** — Elo, attack/defence, recent form, manager, and promotion status for all 20 clubs.
- **Backtest explorer** — walk-forward 2025/26 accuracy by confidence band, month, and biggest misses.

Use **Refresh results** in the sidebar to re-fetch the latest scores and refit. Primary source is football-data.co.uk; if that season’s Premier League CSV is not published yet, the app falls back to fixturedownload.com. If both fail, it uses `epl_final.csv` only.

## What the model uses

- Historical results plus a shots-on-target **xG proxy** (less noisy than raw goals)
- Live completed 2026/27 scores merged from football-data.co.uk (when reachable)
- Time-decayed attack/defence ratings with learned home advantage and season carry-over
- Elo strength blended with a Dixon–Coles Poisson score grid
- Walk-forward **temperature calibration** on 2023/24–2025/26 so probabilities are not over-confident
- Recent form, same-venue head-to-head, and a shrinkage prior for promoted clubs
- 2026 summer context only: net spend, key ins/outs, manager changes, and a few club-specific shocks (optional overlay)

The headline output is the most likely 1X2 result with a confidence band. Supporting markets (most likely score, over/under, BTTS) are shown when they are useful.

Football match outcomes are noisy. Lean on **High** confidence picks; treat Low as little more than a lean.
