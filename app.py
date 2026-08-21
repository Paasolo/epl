"""Interactive 2026/27 Premier League match predictor."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from epl_predictor.context import PREMIER_LEAGUE_2026_27, PROMOTED_TEAMS
from epl_predictor.engine import get_model, ranked_picks

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
def load_fitted_model():
    return get_model()


def team_label(name: str) -> str:
    if name in PROMOTED_TEAMS:
        return f"{name}  · promoted"
    return name


def outcome_chart(pred: dict, key: str) -> go.Figure:
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

    easiest_html = '<span class="chip hot">Easiest call of the pair</span>' if easiest else ""
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips) + easiest_html

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
    st.plotly_chart(outcome_chart(pred, pred["home_display"]), use_container_width=True)

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
            st.write(f"Recent PL form: {form['sequence']}" + (f"  ({form['points']} pts from {form['played']})" if form["played"] else ""))
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
            st.write(f"Recent PL form: {form['sequence']}" + (f"  ({form['points']} pts from {form['played']})" if form["played"] else ""))
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


def main() -> None:
    model = load_fitted_model()
    bt = model.backtest_summary()

    st.markdown(
        """
        <div class="hero">
          <h1>Premier League match predictor</h1>
          <p>Pick two 2026/27 fixtures. The model is fitted on every Premier League match in
          <code>epl_final.csv</code> (2000/01–2025/26), then adjusted for this summer’s signings
          and coaching changes. It ranks the most likely 1X2 result and flags which game is
          the easier, higher-confidence call.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Model card")
        st.write(
            "Walk-forward ensemble: shots-based xG ratings, Dixon–Coles Poisson, "
            "Elo 1X2, season mean-reversion, and temperature calibration on the last "
            "three Premier League seasons. Summer 2026 signings and coaching changes "
            "are a capped overlay. Promoted clubs are shrunk toward a Championship prior."
        )
        st.metric("2025/26 walk-forward accuracy", f"{bt['accuracy']*100:.1f}%", help="Predicted 1X2 before each 2025/26 match, using only earlier data.")
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

    teams = PREMIER_LEAGUE_2026_27
    labels = {t: team_label(t) for t in teams}

    st.subheader("Select two matches")
    st.caption("Choose a club, whether they are at home or away, then the opponent. Both fixtures are predicted together.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Match 1**")
        club1 = st.selectbox("Club", teams, index=teams.index("Arsenal"), format_func=lambda t: labels[t], key="club1")
        venue1 = st.radio("This club is playing", ["Home", "Away"], horizontal=True, key="venue1")
        opps1 = [t for t in teams if t != club1]
        opp1 = st.selectbox("Opponent", opps1, index=opps1.index("Coventry City") if "Coventry City" in opps1 else 0, format_func=lambda t: labels[t], key="opp1")
        h1, a1 = resolve_fixture(club1, venue1, opp1)
        st.caption(f"Fixture: **{h1}** vs **{a1}**")

    with c2:
        st.markdown("**Match 2**")
        club2 = st.selectbox("Club", teams, index=teams.index("Manchester United"), format_func=lambda t: labels[t], key="club2")
        venue2 = st.radio("This club is playing", ["Home", "Away"], horizontal=True, key="venue2", index=1)
        opps2 = [t for t in teams if t != club2]
        default_opp2 = "Hull City" if "Hull City" in opps2 else opps2[0]
        opp2 = st.selectbox("Opponent", opps2, index=opps2.index(default_opp2), format_func=lambda t: labels[t], key="opp2")
        h2, a2 = resolve_fixture(club2, venue2, opp2)
        st.caption(f"Fixture: **{h2}** vs **{a2}**")

    if {h1, a1} == {h2, a2} and h1 == h2:
        st.warning("Both cards are the same fixture. Change one so the model can compare two matches.")

    run = st.button("Predict both matches", type="primary", use_container_width=True)

    if run:
        if h1 == a1 or h2 == a2:
            st.error("A team cannot play itself.")
            return
        preds = [model.predict_fixture(h1, a1), model.predict_fixture(h2, a2)]
        ranked = ranked_picks(preds)
        easiest = ranked[0]
        other = ranked[1]
        preds[0]["is_easiest"] = easiest is preds[0]
        preds[1]["is_easiest"] = easiest is preds[1]

        st.markdown(
            f"""
            <div class="easy-banner">
              Easiest, highest-confidence call:
              {easiest['home_display']} vs {easiest['away_display']} —
              {easiest['best_label']} ({easiest['best_prob']*100:.1f}%, {easiest['confidence']} confidence).
              The other fixture is closer: {other['best_label']} at {other['best_prob']*100:.1f}%.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            render_prediction(preds[0], preds[0]["is_easiest"])
        with col_b:
            render_prediction(preds[1], preds[1]["is_easiest"])


if __name__ == "__main__":
    main()
