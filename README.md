# Premier League match predictor (2026/27)

Interactive Python model that predicts two user-selected Premier League fixtures.

It is fitted on `epl_final.csv` (Premier League matches from 2000/01 through 2025/26, originally from football-data.co.uk) and then adjusted for summer 2026 signings and coaching changes.

## Run

From this folder:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The app opens in your browser. Pick a club, whether that club is **home or away**, then the opponent — twice — and click **Predict both matches**.

## What the model uses

- Historical results, goals, shots and shots on target
- Elo strength and attack/defence Poisson ratings with home advantage
- Recent form and Premier League head-to-head
- A shrinkage prior for promoted clubs (Coventry City, Ipswich Town, Hull City)
- 2026 summer context only: net spend, key ins/outs, manager changes, and a few club-specific shocks (for example Salah leaving Liverpool, or Guardiola leaving Manchester City)

The headline output is the most likely 1X2 result with a confidence band. Supporting markets (most likely score, over/under, BTTS) are shown only when they are useful. When two fixtures are selected, the app ranks which one is the easier, higher-confidence call.

Football match outcomes are noisy. Lean on **High** confidence picks; treat Low as little more than a lean.
