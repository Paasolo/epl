# Multi-league match predictor (2026/27)

Interactive Python model that predicts user-selected fixtures across nine European top flights — a custom slate or an official matchweek.

Supported leagues: **Premier League**, **La Liga**, **Bundesliga**, **Ligue 1**, **Serie A**, **Eredivisie**, **Primeira Liga**, **Süper Lig**, and **Belgian Pro League**.

Each league is fitted on football-data.co.uk results from **2000/01 through 2025/26**, plus any completed **2026/27** scores fetched live from the same provider. Summer 2026 signings and coaching changes are applied as a small overlay.

## Run

From this folder:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The app opens in your browser with a **League** switcher in the sidebar and three tabs:

- **Predict matches** — load any official matchweek (or add/remove fixtures by hand). Finished games are excluded automatically when you load a matchweek. Toggle the summer overlay on/off, then click **Predict**. Download the ranked slate as CSV or JSON.
- **Team strength** — Elo, attack/defence, recent form, manager, and promotion status for the current league.
- **Backtest explorer** — walk-forward 2025/26 accuracy by confidence band, month, and biggest misses.

Use **Refresh results** in the sidebar to re-fetch the latest scores and refit the **active** league. Primary source is football-data.co.uk; if that season’s CSV is not published yet, the app falls back to fixturedownload.com (where a feed exists). Belgian Pro League uses a custom slate only (no fixture feed).

First open of a non-EPL league downloads ~26 season CSVs into `data/` (one-time), then caches the fitted model under `epl_predictor/cache/`.

## What the model uses

- Historical results plus a shots-on-target **xG proxy** (falls back to goals when shots are missing)
- Live completed 2026/27 scores merged from football-data.co.uk (when reachable)
- Time-decayed attack/defence ratings with learned home advantage and season carry-over
- Elo strength blended with a Dixon–Coles Poisson score grid
- Walk-forward **temperature calibration** on 2023/24–2025/26 so probabilities are not over-confident
- Recent form, same-venue head-to-head, and a shrinkage prior for promoted clubs
- 2026 summer context: net spend, key ins/outs, manager changes (optional overlay)

**Every training and backtest prediction uses only earlier matches** — ratings are updated after each game is scored, never before.

The headline output is the most likely 1X2 result with a confidence band. Supporting markets (most likely score, over/under, BTTS) are shown when they are useful.

Football match outcomes are noisy. Lean on **High** confidence picks; treat Low as little more than a lean.
