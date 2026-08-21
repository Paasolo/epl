"""Interactive 2026/27 Premier League match predictor."""

from __future__ import annotations

import json
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from epl_predictor.context import PREMIER_LEAGUE_2026_27, PROMOTED_TEAMS, TEAM_CONTEXT
from epl_predictor.engine import MODEL_API_VERSION, build_backtest_rows, clear_model_cache, get_model, ranked_picks
from epl_predictor.fixtures import fixtures_for, matchweek_options, validate_matchweeks

st.set_page_config(
    page_title="EPL Match Predictor 2026/27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#0B1220"
CARD = "#121A2B"
LINE = "#243049"
GOLD = "#C9A227"
TEAL = "#3DB2A0"
HOME_C = "#3D8BFF"
DRAW_C = "#C9A227"
AWAY_C = "#E45757"
TEXT = "#E8EEF7"
MUTED = "#93A0B5"

MAX_MATCHES = 10
DEFAULT_FIXTURES = [
    ("Arsenal", "Home", "Coventry City"),
    ("Manchester United", "Away", "Hull City"),
    ("Newcastle United", "Home", "Liverpool"),
    ("Manchester City", "Home", "AFC Bournemouth"),
    ("Fulham", "Home", "Chelsea"),
    ("Brentford", "Home", "Tottenham Hotspur"),
    ("Brighton & Hove Albion", "Home", "Aston Villa"),
    ("Ipswich Town", "Home", "Sunderland"),
    ("Nottingham Forest", "Home", "Leeds United"),
    ("Everton", "Home", "Crystal Palace"),
]

st.markdown(
    f"""
    <style>
      .stApp {{ background: {NAVY}; color: {TEXT}; }}
      [data-testid="stSidebar"] {{ background: #0E1626; border-right: 1px solid {LINE}; }}
      h1, h2, h3 {{ letter-spacing: -0.02em; }}
      .hero {{
        background: {CARD};
        border: 1px solid {LINE};
        border-radius: 16px;
        padding: 1.15rem 1.4rem 1.05rem;
        margin-bottom: 1rem;
      }}
      .hero h1 {{ margin: 0 0 0.35rem 0; font-size: 1.85rem; }}
      .hero p {{ margin: 0; color: {MUTED}; }}
      .result-card {{
        background: {CARD};
        border: 1px solid {LINE};
        border-radius: 16px;
        padding: 1.1rem 1.2rem 1.2rem;
        height: 100%;
      }}
      .match-title {{ font-size: 1.15rem; font-weight: 700; margin-bottom: 0.15rem; }}
      .sub {{ color: {MUTED}; font-size: 0.9rem; margin-bottom: 0.85rem; }}
      .pick {{
        font-size: 1.45rem;
        font-weight: 800;
        color: {GOLD};
        margin: 0.2rem 0 0.15rem;
      }}
      .conf-High {{ color: #5DDEA8; font-weight: 700; }}
      .conf-Medium {{ color: {GOLD}; font-weight: 700; }}
      .conf-Low {{ color: #E89B6A; font-weight: 700; }}
      .chip {{
        display: inline-block;
        border: 1px solid {LINE};
        background: #0E1626;
        border-radius: 999px;
        padding: 0.15rem 0.6rem;
        font-size: 0.78rem;
        color: {MUTED};
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
      }}
      .chip.hot {{ border-color: {GOLD}; color: {GOLD}; }}
      .easy-banner {{
        background: #10261F;
        border: 1px solid #1F6B55;
        color: #9BE7CF;
        border-radius: 12px;
        padding: 0.85rem 1.05rem;
        margin: 0.4rem 0 1rem;
        font-weight: 600;
      }}
      .stButton>button {{
        background: {TEAL};
        color: #06221D;
        border: 0;
        font-weight: 700;
        border-radius: 10px;
        height: 2.8rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading calibrated Premier League ratings…")
def load_fitted_model(api_version: int = MODEL_API_VERSION):
    # api_version is part of the cache key so Cloud rebuilds after model API bumps.
    _ = api_version
    return get_model()


def team_label(name: str) -> str:
    if name in PROMOTED_TEAMS:
        return f"{name}  · promoted"
    return name


def outcome_chart(pred: dict) -> go.Figure:
    labels = [
        f"{pred['home_display']} win",
        "Draw",
        f"{pred['away_display']} win",
    ]
    values = [pred["p_home"] * 100, pred["p_draw"] * 100, pred["p_away"] * 100]
    colors = [HOME_C, DRAW_C, AWAY_C]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.1f}%" for v in values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.update_layout(
        height=180,
        margin=dict(l=10, r=50, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 100], ticksuffix="%", showgrid=True, gridcolor=LINE, color=MUTED),
        yaxis=dict(color=TEXT, autorange="reversed"),
        font=dict(color=TEXT, size=13),
        showlegend=False,
    )
    return fig


def resolve_fixture(club: str, venue: str, opponent: str) -> tuple[str, str]:
    if venue == "Home":
        return club, opponent
    return opponent, club


def clear_match_widget_keys(match_ids: list[int]) -> None:
    for mid in match_ids:
        for prefix in ("club_", "venue_", "opp_"):
            st.session_state.pop(f"{prefix}{mid}", None)


def load_matchweek_into_state(gw: int) -> None:
    pairs = fixtures_for(gw)
    clear_match_widget_keys(list(st.session_state.get("match_ids", [])))
    new_ids = list(range(len(pairs)))
    st.session_state.match_ids = new_ids
    st.session_state.next_match_id = max(new_ids) + 1 if new_ids else 0
    for mid, (home, away) in enumerate(pairs):
        st.session_state[f"club_{mid}"] = home
        st.session_state[f"venue_{mid}"] = "Home"
        st.session_state[f"opp_{mid}"] = away
    st.session_state.pop("last_predictions", None)
    st.session_state.pop("last_ranked_table", None)
    st.session_state.pop("last_ranked", None)
    st.session_state.pop("last_apply_context", None)


def ranked_table_rows(ranked: list[dict]) -> list[dict]:
    rows = []
    for i, row in enumerate(ranked, start=1):
        alt = row.get("alt") or {}
        code = row["best_code"]
        key = {"H": "p_home", "D": "p_draw", "A": "p_away"}[code]
        overlay_p = row[key]
        history_p = alt.get(key, overlay_p)
        rows.append(
            {
                "Rank": i,
                "Match": f"{row['home_display']} vs {row['away_display']}",
                "Home": row["home_display"],
                "Away": row["away_display"],
                "Pick": row["best_label"],
                "Pick code": row["best_code"],
                "Probability": round(row["best_prob"] * 100, 1),
                "Home win %": round(row["p_home"] * 100, 1),
                "Draw %": round(row["p_draw"] * 100, 1),
                "Away win %": round(row["p_away"] * 100, 1),
                "Confidence": row["confidence"],
                "Expected home xG": round(row["lambda_home"], 2),
                "Expected away xG": round(row["lambda_away"], 2),
                "Most likely score": row["top_scores"][0]["score"],
                "BTTS %": round(row["p_btts"] * 100, 1),
                "Over 2.5 %": round(row["p_over25"] * 100, 1),
                "History-only pick": alt.get("best_label", "—"),
                "History-only %": round(alt.get("best_prob", 0) * 100, 1) if alt else None,
                "Overlay effect (pp)": round((overlay_p - history_p) * 100, 1) if alt else 0.0,
            }
        )
    return rows


def export_bytes(rows: list[dict]) -> tuple[str, str]:
    frame = pd.DataFrame(rows)
    csv_buf = StringIO()
    frame.to_csv(csv_buf, index=False)
    json_text = json.dumps(rows, indent=2)
    return csv_buf.getvalue(), json_text


def render_prediction(pred: dict, easiest: bool) -> None:
    ctx_h = pred["home_context"]
    ctx_a = pred["away_context"]
    chips = []
    if pred["home_display"] in PROMOTED_TEAMS:
        chips.append("Home promoted")
    if pred["away_display"] in PROMOTED_TEAMS:
        chips.append("Away promoted")
    if ctx_h["change_type"] != "none":
        chips.append(f"New coach: {ctx_h['manager']}")
    if ctx_a["change_type"] != "none":
        chips.append(f"New coach: {ctx_a['manager']}")

    easiest_html = '<span class="chip hot">Easiest call in this set</span>' if easiest else ""
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips) + easiest_html
    if pred.get("alt"):
        alt = pred["alt"]
        code = pred["best_code"]
        key = {"H": "p_home", "D": "p_draw", "A": "p_away"}[code]
        delta = (pred[key] - alt[key]) * 100
        sign = "+" if delta >= 0 else ""
        mode = "with summer overlay" if pred.get("apply_context", True) else "history only"
        chip_html += (
            f'<span class="chip">View: {mode}</span>'
            f'<span class="chip">Overlay vs history on pick: {sign}{delta:.1f}pp</span>'
        )

    pick_team = {
        "H": pred["home_display"],
        "D": "Draw",
        "A": pred["away_display"],
    }[pred["best_code"]]

    st.markdown(
        f"""
        <div class="result-card">
          <div class="match-title">{pred['home_display']} vs {pred['away_display']}</div>
          <div class="sub">Expected score {pred['lambda_home']:.2f} – {pred['lambda_away']:.2f}
            · Elo {pred['elo_home']:.0f} vs {pred['elo_away']:.0f}
            · Last season {pred['home_position']} vs {pred['away_position']}</div>
          {chip_html}
          <div class="pick">{pred['best_label']} &nbsp;·&nbsp; {pick_team}</div>
          <div>Probability <b>{pred['best_prob']*100:.1f}%</b>
            &nbsp;·&nbsp; Confidence
            <span class="conf-{pred['confidence']}">{pred['confidence']}</span>
            &nbsp;·&nbsp; Edge over next outcome {pred['gap']*100:.1f}pp</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        outcome_chart(pred),
        use_container_width=True,
        key=f"chart-{pred['home_display']}-{pred['away_display']}-{pred.get('slot_id', 0)}",
    )

    extras = pred["extras"]
    st.markdown("**Most likely supporting outcomes**")
    cols = st.columns(2)
    for i, extra in enumerate(extras[:4]):
        with cols[i % 2]:
            st.metric(extra["market"], extra["pick"], f"{extra['prob']*100:.1f}% model probability")

    st.markdown("**Most likely scorelines**")
    score_cols = st.columns(len(pred["top_scores"]))
    for col, item in zip(score_cols, pred["top_scores"]):
        col.metric(item["score"], f"{item['prob']*100:.1f}%")

    with st.expander("Why this lean — signings, coaching, form"):
        left, right = st.columns(2)
        with left:
            st.markdown(f"**{pred['home_display']}** (home)")
            st.caption(f"Manager: {ctx_h['manager']}  ·  in charge since {ctx_h['manager_since']}")
            form = pred["form_home"]
            st.write(
                f"Recent PL form: {form['sequence']}"
                + (f"  ({form['points']} pts from {form['played']})" if form["played"] else "")
            )
            st.write("Key arrivals:")
            st.write("\n".join(f"- {x}" for x in ctx_h["key_ins"][:5]) or "- None listed")
            st.write("Key departures:")
            st.write("\n".join(f"- {x}" for x in ctx_h["key_outs"][:5]) or "- None listed")
            for reason in pred["reasons_home"]:
                st.write(f"- {reason}")
        with right:
            st.markdown(f"**{pred['away_display']}** (away)")
            st.caption(f"Manager: {ctx_a['manager']}  ·  in charge since {ctx_a['manager_since']}")
            form = pred["form_away"]
            st.write(
                f"Recent PL form: {form['sequence']}"
                + (f"  ({form['points']} pts from {form['played']})" if form["played"] else "")
            )
            st.write("Key arrivals:")
            st.write("\n".join(f"- {x}" for x in ctx_a["key_ins"][:5]) or "- None listed")
            st.write("Key departures:")
            st.write("\n".join(f"- {x}" for x in ctx_a["key_outs"][:5]) or "- None listed")
            for reason in pred["reasons_away"]:
                st.write(f"- {reason}")
        if pred["h2h"]:
            st.markdown("**Head-to-head (most recent Premier League meetings)**")
            st.dataframe(pred["h2h"], hide_index=True, use_container_width=True)
        else:
            st.caption("No recent Premier League head-to-head in the dataset.")


def render_sidebar(model) -> None:
    bt = model.backtest_summary()
    st.header("Model card")
    st.write(
        "Walk-forward ensemble: shots-based xG ratings, Dixon–Coles Poisson, "
        "Elo 1X2, season mean-reversion, and temperature calibration on the last "
        "three Premier League seasons. Summer 2026 signings and coaching changes "
        "are a capped overlay. Promoted clubs are shrunk toward a Championship prior."
    )
    st.metric(
        "2025/26 walk-forward accuracy",
        f"{bt['accuracy']*100:.1f}%",
        help="Predicted 1X2 before each 2025/26 match, using only earlier data.",
    )
    st.metric("High-confidence hits", f"{bt['high_conf_acc']*100:.1f}%", f"n = {bt['high_conf_n']}")
    st.caption(
        f"Log loss {bt['log_loss']:.3f} · Brier {bt.get('brier', 0):.3f} on {bt['n']} matches. "
        f"Calibration T={bt.get('temperature', 1):.2f}, Poisson weight={bt.get('blend_w', 0.7):.2f}. "
        "A naive always-home-win rule is about 46%. Lean on High confidence calls."
    )
    st.divider()
    st.caption(
        "Context sources (as of 20 Aug 2026): Premier League manager list, "
        "ESPN summer transfer round-up, BBC, club announcements, Wikipedia 2026/27 season page. "
        "The transfer window remains open until 1 September."
    )


def render_team_board(model) -> None:
    st.subheader("Team strength board")
    st.caption(
        "Ratings after walking through every Premier League match in the dataset "
        "(2000/01–2025/26), before summer 2026 context is applied to individual fixtures."
    )

    rows = []
    for name in PREMIER_LEAGUE_2026_27:
        snap = model.snapshot(name)
        form = snap["form"]
        ctx = TEAM_CONTEXT[name]
        rows.append(
            {
                "Team": name,
                "Elo": round(snap["elo"], 0),
                "Attack": round(snap["attack"], 2),
                "Defence": round(snap["defense"], 2),
                "Last 6": form["sequence"],
                "Form pts": form["points"] if form["played"] else "—",
                "Last season": snap["position"],
                "Manager": snap["manager"],
                "Coach change": ctx["change_type"],
                "Promoted": "Yes" if snap["promoted"] else "",
                "Net spend £m": ctx["net_spend_m"],
                "Last PL game": snap["last_date"],
                "Career PL matches": snap["matches"],
            }
        )

    board = pd.DataFrame(rows).sort_values("Elo", ascending=False).reset_index(drop=True)
    board.insert(0, "Rank", board.index + 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strongest Elo", board.iloc[0]["Team"], f"{board.iloc[0]['Elo']:.0f}")
    c2.metric("Weakest Elo", board.iloc[-1]["Team"], f"{board.iloc[-1]['Elo']:.0f}")
    promoted = board[board["Promoted"] == "Yes"]["Team"].tolist()
    c3.metric("Promoted sides", str(len(promoted)), ", ".join(promoted) if promoted else "—")
    summer_changes = int((board["Coach change"] == "summer").sum())
    c4.metric("New summer coaches", summer_changes)

    st.dataframe(board, hide_index=True, use_container_width=True, height=720)

    csv_buf = StringIO()
    board.to_csv(csv_buf, index=False)
    st.download_button(
        "Download team board (CSV)",
        data=csv_buf.getvalue(),
        file_name="epl_team_strength_board.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_backtest_tab(model) -> None:
    st.subheader("Backtest explorer")
    st.caption(
        "Walk-forward 2025/26 predictions: each match is scored using only earlier history, "
        "then calibrated with the same blend and temperature used in the live app."
    )
    try:
        rows = build_backtest_rows(model, "2025/26")
    except Exception as exc:  # noqa: BLE001 — show a clean recovery path in the UI
        st.error(f"Could not build backtest rows ({type(exc).__name__}). Rebuilding model cache…")
        clear_model_cache()
        load_fitted_model.clear()
        model = load_fitted_model()
        rows = build_backtest_rows(model, "2025/26")
    if not rows:
        st.warning(
            "No enriched backtest rows yet. Click below to rebuild the model "
            "(needed once after upgrading the app)."
        )
        if st.button("Rebuild model cache", type="primary"):
            clear_model_cache()
            load_fitted_model.clear()
            st.rerun()
        return

    frame = pd.DataFrame(rows)
    bt = model.backtest_summary()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matches", bt["n"])
    m2.metric("Accuracy", f"{bt['accuracy']*100:.1f}%")
    m3.metric("Log loss", f"{bt['log_loss']:.3f}")
    m4.metric("High-conf hits", f"{bt['high_conf_acc']*100:.1f}%", f"n = {bt['high_conf_n']}")

    st.markdown("**By confidence band**")
    conf_rows = []
    for band in ("High", "Medium", "Low"):
        subset = frame[frame["confidence"] == band]
        if subset.empty:
            continue
        conf_rows.append(
            {
                "Confidence": band,
                "Matches": len(subset),
                "Accuracy": f"{subset['correct'].mean()*100:.1f}%",
                "Avg pick %": f"{subset['best_prob'].mean()*100:.1f}%",
            }
        )
    st.dataframe(pd.DataFrame(conf_rows), hide_index=True, use_container_width=True)

    st.markdown("**Home vs away correctness**")
    ha_rows = []
    for side, code in (("Home wins predicted", "H"), ("Draws predicted", "D"), ("Away wins predicted", "A")):
        subset = frame.loc[frame["predicted"] == code, "correct"]
        ha_rows.append(
            {
                "Side": side,
                "Matches": int(len(subset)),
                "Accuracy": f"{subset.mean()*100:.1f}%" if len(subset) else "—",
            }
        )
    st.dataframe(pd.DataFrame(ha_rows), hide_index=True, use_container_width=True)

    st.markdown("**Accuracy by month**")
    month = (
        frame.groupby("month", dropna=False)
        .agg(matches=("correct", "size"), accuracy=("correct", "mean"))
        .reset_index()
    )
    month["accuracy"] = (month["accuracy"] * 100).round(1)
    month = month.rename(columns={"month": "Month", "matches": "Matches", "accuracy": "Accuracy %"})
    st.dataframe(month, hide_index=True, use_container_width=True)

    chart = go.Figure(
        go.Bar(
            x=month["Month"],
            y=month["Accuracy %"],
            marker_color=TEAL,
            text=month["Accuracy %"].map(lambda v: f"{v:.1f}%"),
            textposition="outside",
        )
    )
    chart.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 100], ticksuffix="%", gridcolor=LINE, color=MUTED, title="Accuracy %"),
        xaxis=dict(color=MUTED, title="Month"),
        font=dict(color=TEXT),
    )
    st.plotly_chart(chart, use_container_width=True, key="backtest_month_chart")

    st.markdown("**Biggest misses** (wrong calls with the highest model probability)")
    misses = frame.loc[~frame["correct"]].sort_values("best_prob", ascending=False).head(15)
    if misses.empty:
        st.info("No misses in this sample — every calibrated pick matched the result.")
    else:
        miss_view = pd.DataFrame(
            {
                "Date": [
                    d.strftime("%d %b %Y") if pd.notna(d) else "—" for d in misses["date"]
                ],
                "Match": misses["match"].to_list(),
                "Score": misses["score"].to_list(),
                "Predicted": misses["predicted"].map({"H": "Home", "D": "Draw", "A": "Away"}).to_list(),
                "Actual": misses["actual"].map({"H": "Home", "D": "Draw", "A": "Away"}).to_list(),
                "Model %": (misses["best_prob"] * 100).round(1).to_list(),
                "Confidence": misses["confidence"].to_list(),
            }
        )
        st.dataframe(miss_view, hide_index=True, use_container_width=True)

    export = frame.copy()
    export["date"] = export["date"].map(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else "")
    csv_buf = StringIO()
    export.to_csv(csv_buf, index=False)
    st.download_button(
        "Download 2025/26 backtest rows (CSV)",
        data=csv_buf.getvalue(),
        file_name="epl_backtest_2025_26.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_backtest",
    )


def render_predict_tab(model) -> None:
    teams = PREMIER_LEAGUE_2026_27
    labels = {t: team_label(t) for t in teams}

    if "match_ids" not in st.session_state:
        st.session_state.match_ids = [0, 1]
        st.session_state.next_match_id = 2

    st.subheader("Select matches")
    st.caption(
        "Load an official matchweek, or build a custom slate. "
        "Choose a club, home or away, then the opponent."
    )

    apply_context = st.toggle(
        "Apply summer signings & coaching overlay",
        value=True,
        help="When on, 2026 transfer and manager adjustments are applied. "
        "Turn off for a history-only lean. The ranked table always shows the overlay effect.",
    )

    gw_labels = matchweek_options()
    load_c1, load_c2, load_c3 = st.columns([2.4, 1.2, 1.2])
    with load_c1:
        gw_label = st.selectbox("Official matchweek", list(gw_labels.keys()), key="gw_select")
    with load_c2:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        if st.button("Load matchweek", use_container_width=True, type="secondary"):
            load_matchweek_into_state(gw_labels[gw_label])
            st.rerun()
    with load_c3:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        if st.button(
            "Add match",
            disabled=len(st.session_state.match_ids) >= MAX_MATCHES,
            use_container_width=True,
        ):
            st.session_state.match_ids.append(st.session_state.next_match_id)
            st.session_state.next_match_id += 1
            st.rerun()

    fixtures: list[tuple[int, str, str]] = []
    ids = list(st.session_state.match_ids)
    for idx, match_id in enumerate(ids):
        club_default, venue_default, opp_default = DEFAULT_FIXTURES[match_id % len(DEFAULT_FIXTURES)]
        st.markdown(f"**Match {idx + 1}**")
        c1, c2, c3, c4 = st.columns([2.2, 1.2, 2.2, 0.7])
        with c1:
            club_key = f"club_{match_id}"
            if club_key not in st.session_state:
                st.session_state[club_key] = club_default
            club = st.selectbox(
                "Club",
                teams,
                format_func=lambda t: labels[t],
                key=club_key,
            )
        with c2:
            venue_key = f"venue_{match_id}"
            if venue_key not in st.session_state:
                st.session_state[venue_key] = venue_default
            venue = st.radio(
                "This club is playing",
                ["Home", "Away"],
                horizontal=True,
                key=venue_key,
            )
        with c3:
            opps = [t for t in teams if t != club]
            opp_key = f"opp_{match_id}"
            if opp_key not in st.session_state or st.session_state[opp_key] not in opps:
                st.session_state[opp_key] = opp_default if opp_default in opps else opps[0]
            opponent = st.selectbox(
                "Opponent",
                opps,
                format_func=lambda t: labels[t],
                key=opp_key,
            )
        with c4:
            st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
            if st.button("Remove", disabled=len(ids) <= 1, key=f"remove_{match_id}", use_container_width=True):
                clear_match_widget_keys([match_id])
                st.session_state.match_ids = [mid for mid in st.session_state.match_ids if mid != match_id]
                st.session_state.pop("last_predictions", None)
                st.session_state.pop("last_ranked_table", None)
                st.session_state.pop("last_ranked", None)
                st.session_state.pop("last_apply_context", None)
                st.rerun()
        home, away = resolve_fixture(club, venue, opponent)
        st.caption(f"Fixture: **{home}** vs **{away}**")
        fixtures.append((match_id, home, away))

    seen: dict[tuple[str, str], int] = {}
    duplicates = []
    for match_id, home, away in fixtures:
        key = (home, away)
        if key in seen:
            duplicates.append(f"{home} vs {away}")
        seen[key] = match_id
    if duplicates:
        st.warning(
            "Duplicate fixture in the list: "
            + ", ".join(sorted(set(duplicates)))
            + ". Remove one copy so the ranking stays clean."
        )

    n = len(fixtures)
    run = st.button(f"Predict {n} match{'es' if n != 1 else ''}", type="primary", use_container_width=True)

    if run:
        if any(home == away for _, home, away in fixtures):
            st.error("A team cannot play itself.")
            return
        preds = []
        for match_id, home, away in fixtures:
            primary = model.predict_fixture(home, away, apply_context=apply_context)
            alternate = model.predict_fixture(home, away, apply_context=not apply_context)
            primary["slot_id"] = match_id
            primary["alt"] = {
                "best_label": alternate["best_label"],
                "best_prob": alternate["best_prob"],
                "best_code": alternate["best_code"],
                "p_home": alternate["p_home"],
                "p_draw": alternate["p_draw"],
                "p_away": alternate["p_away"],
                "apply_context": alternate["apply_context"],
            }
            preds.append(primary)
        ranked = ranked_picks(preds)
        easiest_id = id(ranked[0])
        for pred in preds:
            pred["is_easiest"] = id(pred) == easiest_id
        table_rows = ranked_table_rows(ranked)
        st.session_state.last_predictions = preds
        st.session_state.last_ranked = ranked
        st.session_state.last_ranked_table = table_rows
        st.session_state.last_apply_context = apply_context

    preds = st.session_state.get("last_predictions")
    ranked = st.session_state.get("last_ranked")
    table_rows = st.session_state.get("last_ranked_table")
    if not preds or not ranked or not table_rows:
        return

    current_keys = {(h, a) for _, h, a in fixtures}
    predicted_keys = {(p["home_display"], p["away_display"]) for p in preds}
    if current_keys != predicted_keys or st.session_state.get("last_apply_context") != apply_context:
        st.info("Fixtures or overlay setting changed since the last prediction. Click Predict again to refresh.")
        return

    easiest = ranked[0]
    if len(ranked) == 1:
        banner_extra = ""
    else:
        runners = "; ".join(
            f"{row['home_display']} vs {row['away_display']} — {row['best_label']} ({row['best_prob']*100:.1f}%)"
            for row in ranked[1:3]
        )
        banner_extra = f" Next in the ranking: {runners}."

    mode_note = "summer overlay on" if apply_context else "history only"
    st.markdown(
        f"""
        <div class="easy-banner">
          Easiest, highest-confidence call of {len(preds)} ({mode_note}):
          {easiest['home_display']} vs {easiest['away_display']} —
          {easiest['best_label']} ({easiest['best_prob']*100:.1f}%, {easiest['confidence']} confidence).
          {banner_extra}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Ranked calls**")
    display_cols = [
        "Rank",
        "Match",
        "Pick",
        "Probability",
        "Confidence",
        "History-only pick",
        "History-only %",
        "Overlay effect (pp)",
        "Expected home xG",
        "Expected away xG",
        "Most likely score",
    ]
    st.dataframe(pd.DataFrame(table_rows)[display_cols], hide_index=True, use_container_width=True)
    st.caption(
        "Overlay effect is the change in probability for the current pick versus the history-only model "
        "(positive means summer context made that pick more likely)."
    )

    csv_text, json_text = export_bytes(table_rows)
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "Download ranked slate (CSV)",
            data=csv_text,
            file_name="epl_ranked_predictions.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv",
        )
    with dl2:
        st.download_button(
            "Download ranked slate (JSON)",
            data=json_text,
            file_name="epl_ranked_predictions.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json",
        )

    for start in range(0, len(preds), 2):
        cols = st.columns(2)
        chunk = preds[start : start + 2]
        for col, pred in zip(cols, chunk):
            with col:
                render_prediction(pred, pred["is_easiest"])


def main() -> None:
    model = load_fitted_model()
    mw_problems = validate_matchweeks()
    if mw_problems:
        st.warning("Fixture slate issue: " + "; ".join(mw_problems[:3]))

    st.markdown(
        """
        <div class="hero">
          <h1>Premier League match predictor</h1>
          <p>Load an official matchweek or build a custom slate. The model is fitted on every
          Premier League match in <code>epl_final.csv</code> (2000/01–2025/26), then adjusted for
          this summer’s signings and coaching changes. Compare history-only vs overlay leanings,
          inspect team strength, and review the 2025/26 walk-forward backtest.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        render_sidebar(model)

    tab_predict, tab_teams, tab_backtest = st.tabs(
        ["Predict matches", "Team strength", "Backtest explorer"]
    )
    with tab_predict:
        render_predict_tab(model)
    with tab_teams:
        render_team_board(model)
    with tab_backtest:
        render_backtest_tab(model)


if __name__ == "__main__":
    main()
