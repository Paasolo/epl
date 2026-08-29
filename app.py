"""Interactive multi-league football match predictor (2026/27)."""

from __future__ import annotations

import json
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from epl_predictor.ads import (
    inject_adsense_site_script,
    render_predict_bottom_ad,
    render_predict_top_ad,
)
from epl_predictor.auth import current_user, ensure_default_admin, sign_out
from epl_predictor.auth_ui import render_auth_gate
from epl_predictor.engine import (
    MODEL_API_VERSION,
    build_backtest_rows,
    clear_model_cache,
    current_results_fingerprint,
    get_model,
    ranked_picks,
)
from epl_predictor.fixtures import (
    clear_fixture_cache,
    fixture_load_error,
    fixtures_for_unplayed,
    matchweek_options,
    next_unplayed_matchweek,
    validate_matchweeks,
)
from epl_predictor.leagues import LEAGUE_ORDER, LEAGUES, get_league, league_options
from epl_predictor.payments import (
    WEEKLY_PRICE_LABEL,
    consume_paystack_flash,
    current_unlock_week,
    expand_cross_league_unlock,
    handle_paystack_return,
    has_week_access,
    load_payment_rows,
    payment_summary,
    paystack_configured,
    render_paywall,
)
from epl_predictor.results import LIVE_SEASON

st.set_page_config(
    page_title="Multi-League Match Predictor 2026/27",
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
      .prediction-card {{
        background: linear-gradient(180deg, #152036 0%, {CARD} 100%);
        border: 1px solid {LINE};
        border-radius: 18px;
        padding: 1.25rem 1.35rem 1.3rem;
        margin: 0 0 1.15rem 0;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28);
      }}
      .prediction-card.hot {{
        border-color: #3A6B58;
        box-shadow: 0 10px 28px rgba(16, 38, 31, 0.45);
      }}
      .prediction-card .match-title {{
        font-size: 1.28rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.02em;
      }}
      .prediction-card .sub {{
        color: {MUTED};
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
      }}
      .pick-block {{
        background: #0E1626;
        border: 1px solid {LINE};
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin: 0.65rem 0 0.9rem;
      }}
      .pick-block .pick {{
        font-size: 1.55rem;
        font-weight: 800;
        color: {GOLD};
        margin: 0 0 0.2rem 0;
        line-height: 1.2;
      }}
      .pick-block .pick-meta {{
        color: {TEXT};
        font-size: 0.98rem;
      }}
      .prob-row {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin: 0.35rem 0;
        font-size: 0.88rem;
      }}
      .prob-row .label {{
        width: 4.8rem;
        color: {MUTED};
        flex-shrink: 0;
      }}
      .prob-row .track {{
        flex: 1;
        height: 0.55rem;
        background: #0E1626;
        border: 1px solid {LINE};
        border-radius: 999px;
        overflow: hidden;
      }}
      .prob-row .fill {{
        height: 100%;
        border-radius: 999px;
      }}
      .prob-row .fill.home {{ background: {HOME_C}; }}
      .prob-row .fill.draw {{ background: {DRAW_C}; }}
      .prob-row .fill.away {{ background: {AWAY_C}; }}
      .prob-row .pct {{
        width: 3.2rem;
        text-align: right;
        font-weight: 700;
        color: {TEXT};
      }}
      .score-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.75rem;
      }}
      .score-pill {{
        background: #0E1626;
        border: 1px solid {LINE};
        border-radius: 10px;
        padding: 0.35rem 0.55rem;
        font-size: 0.82rem;
        color: {MUTED};
      }}
      .score-pill strong {{
        color: {TEXT};
        margin-right: 0.35rem;
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


def active_league():
    lid = st.session_state.get("league_id", "epl")
    return get_league(lid)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_results_fingerprint(league_id: str) -> str:
    try:
        return current_results_fingerprint(league_id, include_live=True)
    except Exception as exc:  # noqa: BLE001 — show a Cloud-safe message
        # Fall back to a history-only fingerprint so the UI can still boot.
        try:
            return current_results_fingerprint(league_id, include_live=False)
        except Exception:
            raise RuntimeError(
                f"Failed to load {league_id} training data ({type(exc).__name__}). "
                "Try Refresh results, or check that historical CSVs are available."
            ) from None


@st.cache_resource(show_spinner="Loading calibrated league ratings…")
def load_fitted_model(league_id: str, api_version: int = MODEL_API_VERSION, fingerprint: str = ""):
    return get_model(league_id, fingerprint or cached_results_fingerprint(league_id))


def refresh_training_data(league_id: str | None = None) -> None:
    """Drop disk/process caches and force a live re-fetch on next load."""
    lid = league_id or st.session_state.get("league_id", "epl")
    clear_model_cache(lid)
    cached_results_fingerprint.clear()
    load_fitted_model.clear()
    st.session_state.pop("gw_default_for_league", None)


def reset_slate_state(*, empty: bool = False) -> None:
    ids = list(st.session_state.get("match_ids", []))
    clear_match_widget_keys(ids)
    if empty:
        st.session_state.match_ids = []
        st.session_state.next_match_id = 0
    else:
        st.session_state.match_ids = [0, 1]
        st.session_state.next_match_id = 2
    for key in (
        "last_predictions",
        "last_ranked_table",
        "last_ranked",
        "last_apply_context",
        "mw_excluded",
        "mw_loaded",
        "mw_complete",
        "mw_locked",
    ):
        st.session_state.pop(key, None)


def customer_league_options() -> dict[str, str]:
    """League picker for customers — Belgian Pro League is admin-only."""
    return {label: lid for label, lid in league_options().items() if lid != "belgium"}


def is_customer_user() -> bool:
    user = current_user()
    return bool(user and user.get("role") != "admin")


def is_admin_user() -> bool:
    user = current_user()
    return bool(user and user.get("role") == "admin")


def render_admin_payments_tab() -> None:
    st.subheader("Payments")
    st.caption(
        f"Weekly unlocks are {WEEKLY_PRICE_LABEL} via Paystack. "
        "This view combines Paystack transactions with the local verification ledger."
    )
    if not paystack_configured():
        st.warning(
            "Paystack is not configured. Add `[paystack]` keys to `.streamlit/secrets.toml` "
            "to load live transaction history."
        )

    c1, c2 = st.columns([1, 3])
    with c1:
        refresh = st.button("Refresh payments", use_container_width=True, type="primary")
    with c2:
        pages = st.selectbox("Paystack pages to fetch", [1, 2, 3, 5], index=2, help="50 transactions per page")

    if refresh:
        st.session_state.pop("admin_payments_cache", None)

    cache = st.session_state.get("admin_payments_cache")
    if cache is None or refresh:
        with st.spinner("Loading payment data…"):
            rows, note = load_payment_rows(prefer_paystack=True, pages=int(pages))
        st.session_state["admin_payments_cache"] = {"rows": rows, "note": note}
    else:
        rows = cache.get("rows") or []
        note = cache.get("note") or ""

    summary = payment_summary(rows)
    st.caption(f"Source: {note}")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Successful payments", summary["successful"])
    m2.metric("Revenue (GHS)", f"{summary['revenue_ghs']:.2f}")
    m3.metric("Unique customers", summary["unique_customers"])
    m4.metric("All transactions", summary["total_transactions"])
    m5.metric("Failed / other", summary["failed_or_other"])

    by_week = summary.get("by_matchweek") or {}
    if by_week:
        st.markdown("**Successful payments by matchweek**")
        week_df = pd.DataFrame(
            [{"Matchweek": k, "Successful payments": v} for k, v in by_week.items()]
        )
        st.dataframe(week_df, hide_index=True, use_container_width=True)

    st.markdown("**All payment records**")
    if not rows:
        st.info("No payments found yet.")
        return

    status_filter = st.multiselect(
        "Filter by status",
        sorted({str(r.get("status") or "unknown") for r in rows}),
        default=["success"] if any(str(r.get("status")) == "success" for r in rows) else None,
    )
    filtered = rows
    if status_filter:
        filtered = [r for r in rows if str(r.get("status") or "unknown") in status_filter]

    table = pd.DataFrame(filtered)
    display_cols = [
        c
        for c in (
            "paid_at",
            "email",
            "status",
            "amount_ghs",
            "currency",
            "matchweek",
            "season",
            "reference",
            "channel",
            "gateway_response",
            "source",
        )
        if c in table.columns
    ]
    st.dataframe(table[display_cols] if display_cols else table, hide_index=True, use_container_width=True)

    csv_buf = StringIO()
    (table[display_cols] if display_cols else table).to_csv(csv_buf, index=False)
    st.download_button(
        "Download payments (CSV)",
        data=csv_buf.getvalue(),
        file_name="payments_export.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_admin_payments_csv",
    )


def team_label(name: str, league) -> str:
    if name in league.promoted:
        return f"{name}  · promoted"
    return name


def default_fixtures(league) -> list[tuple[str, str, str]]:
    clubs = league.clubs
    if len(clubs) < 4:
        return [("—", "Home", "—")]
    pairs = []
    for i in range(0, min(10, len(clubs) - 1), 2):
        pairs.append((clubs[i], "Home", clubs[i + 1]))
    while len(pairs) < 2:
        pairs.append((clubs[0], "Home", clubs[1]))
    return pairs


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


def load_matchweek_into_state(gw: int, model, league) -> None:
    remaining, excluded = fixtures_for_unplayed(gw, model.matches, league, season=LIVE_SEASON)
    clear_match_widget_keys(list(st.session_state.get("match_ids", [])))
    new_ids = list(range(len(remaining)))
    st.session_state.match_ids = new_ids
    st.session_state.next_match_id = max(new_ids) + 1 if new_ids else 0
    for mid, (home, away) in enumerate(remaining):
        st.session_state[f"club_{mid}"] = home
        st.session_state[f"venue_{mid}"] = "Home"
        st.session_state[f"opp_{mid}"] = away
    st.session_state.pop("last_predictions", None)
    st.session_state.pop("last_ranked_table", None)
    st.session_state.pop("last_ranked", None)
    st.session_state.pop("last_apply_context", None)
    st.session_state["mw_excluded"] = excluded
    st.session_state["mw_loaded"] = gw
    st.session_state["mw_locked"] = True
    if not remaining and excluded:
        st.session_state["mw_complete"] = True
    else:
        st.session_state.pop("mw_complete", None)


def unlock_matchweek_slate() -> None:
    """Allow editing the current fixtures as a custom slate."""
    st.session_state.pop("mw_locked", None)
    st.session_state.pop("mw_loaded", None)
    st.session_state.pop("mw_excluded", None)
    st.session_state.pop("mw_complete", None)
    st.session_state.pop("gw_default_for_league", None)


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


def render_prediction(pred: dict, easiest: bool, league, rank: int | None = None) -> None:
    ctx_h = pred["home_context"]
    ctx_a = pred["away_context"]
    chips = []
    if rank is not None:
        chips.append(f"Rank #{rank}")
    if pred["home_display"] in league.promoted:
        chips.append("Home promoted")
    if pred["away_display"] in league.promoted:
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
    top_score = pred["top_scores"][0]["score"] if pred.get("top_scores") else "—"
    score_pills = "".join(
        f'<span class="score-pill"><strong>{item["score"]}</strong>{item["prob"]*100:.1f}%</span>'
        for item in pred.get("top_scores", [])[:4]
    )
    extras = pred.get("extras") or []
    extra_pills = "".join(
        f'<span class="score-pill"><strong>{extra["market"]}:</strong>{extra["pick"]} · {extra["prob"]*100:.0f}%</span>'
        for extra in extras[:3]
    )
    card_class = "prediction-card hot" if easiest else "prediction-card"
    conf = pred["confidence"]

    st.markdown(
        f"""
        <div class="{card_class}">
          <div class="match-title">{pred['home_display']} vs {pred['away_display']}</div>
          <div class="sub">Expected xG {pred['lambda_home']:.2f} – {pred['lambda_away']:.2f}
            · Elo {pred['elo_home']:.0f} vs {pred['elo_away']:.0f}
            · Last season {pred['home_position']} vs {pred['away_position']}
            · Most likely score <b style="color:{TEXT}">{top_score}</b></div>
          {chip_html}
          <div class="pick-block">
            <div class="pick">{pred['best_label']} · {pick_team}</div>
            <div class="pick-meta">
              Probability <b>{pred['best_prob']*100:.1f}%</b>
              &nbsp;·&nbsp; Confidence
              <span class="conf-{conf}">{conf}</span>
              &nbsp;·&nbsp; Edge {pred['gap']*100:.1f}pp
            </div>
          </div>
          <div class="prob-row">
            <div class="label">Home</div>
            <div class="track"><div class="fill home" style="width:{pred['p_home']*100:.1f}%"></div></div>
            <div class="pct">{pred['p_home']*100:.1f}%</div>
          </div>
          <div class="prob-row">
            <div class="label">Draw</div>
            <div class="track"><div class="fill draw" style="width:{pred['p_draw']*100:.1f}%"></div></div>
            <div class="pct">{pred['p_draw']*100:.1f}%</div>
          </div>
          <div class="prob-row">
            <div class="label">Away</div>
            <div class="track"><div class="fill away" style="width:{pred['p_away']*100:.1f}%"></div></div>
            <div class="pct">{pred['p_away']*100:.1f}%</div>
          </div>
          <div class="score-grid">{score_pills}{extra_pills}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Chart, markets & why this lean", expanded=False):
        st.plotly_chart(
            outcome_chart(pred),
            use_container_width=True,
            key=f"chart-{league.id}-{pred['home_display']}-{pred['away_display']}-{pred.get('slot_id', 0)}",
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

        left, right = st.columns(2)
        with left:
            st.markdown(f"**{pred['home_display']}** (home)")
            st.caption(f"Manager: {ctx_h['manager']}  ·  in charge since {ctx_h['manager_since']}")
            form = pred["form_home"]
            st.write(
                f"Recent form: {form['sequence']}"
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
                f"Recent form: {form['sequence']}"
                + (f"  ({form['points']} pts from {form['played']})" if form["played"] else "")
            )
            st.write("Key arrivals:")
            st.write("\n".join(f"- {x}" for x in ctx_a["key_ins"][:5]) or "- None listed")
            st.write("Key departures:")
            st.write("\n".join(f"- {x}" for x in ctx_a["key_outs"][:5]) or "- None listed")
            for reason in pred["reasons_away"]:
                st.write(f"- {reason}")
        if pred["h2h"]:
            st.markdown(f"**Head-to-head (most recent {league.name} meetings)**")
            st.dataframe(pred["h2h"], hide_index=True, use_container_width=True)
        else:
            st.caption(f"No recent {league.name} head-to-head in the dataset.")


def render_sidebar(model, league) -> None:
    user = current_user()
    if user and user.get("email"):
        role_label = "Admin" if user.get("role") == "admin" else "Customer"
        st.caption(f"Signed in as **{user['email']}** · {role_label}")
        unlock_week = current_unlock_week(league, model)
        if user.get("role") == "admin":
            st.caption("Admin — prediction results unlocked")
        elif unlock_week is not None and has_week_access(user, unlock_week):
            st.caption(f"Matchweek {unlock_week} unlocked")
        elif unlock_week is not None:
            st.caption(f"Matchweek {unlock_week} locked · {WEEKLY_PRICE_LABEL}")
        if st.button("Log out", use_container_width=True):
            sign_out()
            st.rerun()
        st.divider()

    options = customer_league_options() if is_customer_user() else league_options()
    labels = list(options.keys())
    # Customers cannot stay on Belgian Pro League if it was selected earlier.
    if is_customer_user() and st.session_state.get("league_id") == "belgium":
        st.session_state.league_id = "epl"
        reset_slate_state(empty=True)
        st.session_state.pop("gw_default_for_league", None)
        st.rerun()
    current_label = next((k for k, v in options.items() if v == league.id), labels[0])
    chosen = st.selectbox("League", labels, index=labels.index(current_label), key="league_select")
    new_id = options[chosen]
    if new_id != st.session_state.get("league_id", "epl"):
        st.session_state.league_id = new_id
        reset_slate_state(empty=is_customer_user())
        st.session_state.pop("gw_default_for_league", None)
        st.rerun()

    bt = model.backtest_summary()
    st.header("Model card")
    meta = getattr(model, "training_meta", {}) or {}
    through = meta.get("through")
    through_txt = through.strftime("%d %b %Y") if through is not None else "—"
    n_matches = meta.get("n_matches", len(getattr(model, "matches", [])))
    n_live = meta.get("n_live_season", 0)
    live_status = meta.get("live_status") or {}
    st.caption(
        f"Training through **{through_txt}** · {n_matches:,} matches"
        + (f" · {n_live} from {LIVE_SEASON}" if n_live else "")
    )
    if live_status and not live_status.get("ok", True) and live_status.get("message"):
        if live_status.get("soft"):
            st.info(live_status["message"])
        else:
            st.warning(live_status["message"])
    elif live_status.get("ok") and live_status.get("message"):
        st.caption(live_status["message"])
    elif live_status.get("message") and n_live == 0:
        st.caption(live_status["message"])
    if st.button("Refresh results", use_container_width=True, help="Re-fetch football-data.co.uk and refit"):
        refresh_training_data(league.id)
        st.rerun()
    st.write(
        f"Walk-forward ensemble for **{league.name}**: shots-based xG ratings, Dixon–Coles Poisson, "
        "Elo 1X2, season mean-reversion, and temperature calibration on the last "
        "three seasons. Completed 2026/27 scores are merged from football-data.co.uk. "
        "Summer 2026 signings and coaching changes are a capped overlay. "
        f"Promoted clubs are shrunk toward a {league.second_tier_label} prior."
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
        "Lean on High confidence calls."
    )
    st.divider()
    st.caption(
        f"Context sources (as of {league.context_as_of}): club announcements, transfer round-ups, "
        f"and {league.name} season pages. Transfer windows may still be open."
    )


def render_team_board(model, league) -> None:
    st.subheader("Team strength board")
    st.caption(
        f"Ratings after walking through every {league.name} match in the dataset "
        "(historical CSV plus any completed 2026/27 results), before summer 2026 "
        "context is applied to individual fixtures."
    )

    rows = []
    for name in league.clubs:
        snap = model.snapshot(name)
        form = snap["form"]
        ctx = league.team_context[name]
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
                f"Net spend {league.currency}m": ctx["net_spend_m"],
                "Last league game": snap["last_date"],
                "Career league matches": snap["matches"],
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
        file_name=f"{league.id}_team_strength_board.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_backtest_tab(model, league) -> None:
    st.subheader("Backtest explorer")
    st.caption(
        f"Walk-forward 2025/26 {league.name} predictions: each match is scored using only earlier history, "
        "then calibrated with the same blend and temperature used in the live app."
    )
    try:
        rows = build_backtest_rows(model, "2025/26")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not build backtest rows ({type(exc).__name__}). Rebuilding model cache…")
        refresh_training_data(league.id)
        model = load_fitted_model(
            league.id,
            api_version=MODEL_API_VERSION,
            fingerprint=cached_results_fingerprint(league.id),
        )
        rows = build_backtest_rows(model, "2025/26")
    if not rows:
        st.warning(
            "No enriched backtest rows yet. Click below to rebuild the model "
            "(needed once after upgrading the app)."
        )
        if st.button("Rebuild model cache", type="primary"):
            refresh_training_data(league.id)
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
    st.plotly_chart(chart, use_container_width=True, key=f"backtest_month_chart_{league.id}")

    st.markdown("**Biggest misses** (wrong calls with the highest model probability)")
    misses = frame.loc[~frame["correct"]].sort_values("best_prob", ascending=False).head(15)
    if misses.empty:
        st.caption("No misses in this sample.")
    else:
        miss_view = pd.DataFrame(
            {
                "Date": [d.strftime("%d %b %Y") if pd.notna(d) else "—" for d in misses["date"]],
                "Match": misses["match"].to_list(),
                "Score": misses["score"].to_list(),
                "Predicted": misses["predicted"].map({"H": "Home", "D": "Draw", "A": "Away"}).to_list(),
                "Actual": misses["actual"].map({"H": "Home", "D": "Draw", "A": "Away"}).to_list(),
                "Model %": (misses["best_prob"] * 100).round(1).to_list(),
                "Confidence": misses["confidence"].to_list(),
            }
        )
        st.dataframe(miss_view, hide_index=True, use_container_width=True)

    csv_buf = StringIO()
    frame.to_csv(csv_buf, index=False)
    st.download_button(
        "Download backtest rows (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"{league.id}_backtest_2025_26.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"dl_backtest_{league.id}",
    )


def render_predict_tab(model, league) -> None:
    teams = league.clubs
    labels = {t: team_label(t, league) for t in teams}
    defaults = default_fixtures(league)
    mw_locked = bool(st.session_state.get("mw_locked"))
    is_customer = is_customer_user()

    if "match_ids" not in st.session_state:
        # Customers start with an empty slate until they click Load matchweek.
        if is_customer:
            st.session_state.match_ids = []
            st.session_state.next_match_id = 0
        else:
            st.session_state.match_ids = [0, 1]
            st.session_state.next_match_id = 2
    elif is_customer and not mw_locked and not st.session_state.get("mw_loaded"):
        # Never keep placeholder pairs for customers before Load matchweek.
        if st.session_state.match_ids:
            clear_match_widget_keys(list(st.session_state.match_ids))
            st.session_state.match_ids = []
            st.session_state.next_match_id = 0

    st.subheader("Select matches")
    if mw_locked:
        gw = st.session_state.get("mw_loaded")
        st.caption(
            f"Official matchweek {gw} is loaded and locked. "
            + (
                "Switch leagues, then click Load matchweek to load that league’s fixtures."
                if is_customer
                else "Selections cannot be changed until you unlock to a custom slate."
            )
        )
    elif is_customer:
        st.caption(
            "Choose a league, then click **Load matchweek** to load the current "
            "official fixtures. Matches are not pre-loaded when you switch leagues."
        )
    else:
        st.caption(
            "Load an official matchweek, or build a custom slate. "
            "Finished games are dropped automatically when you load a matchweek. "
            "Choose a club, home or away, then the opponent."
        )

    apply_context = st.toggle(
        "Apply summer signings & coaching overlay",
        value=True,
        help="When on, 2026 transfer and manager adjustments are applied. "
        "Turn off for a history-only lean. The ranked table always shows the overlay effect.",
    )

    gw_labels = matchweek_options(league)
    gw_label_list = list(gw_labels.keys())
    default_gw = next_unplayed_matchweek(model.matches, league, season=LIVE_SEASON)
    default_gw_label = None
    if default_gw is not None:
        default_gw_label = next(
            (label for label, num in gw_labels.items() if num == default_gw),
            None,
        )
    user = current_user()
    # is_customer already set at top of render_predict_tab
    # Customers may only use the current (next unplayed) matchweek — no future weeks.
    if is_customer and default_gw_label:
        gw_label_list = [default_gw_label]
        gw_labels = {default_gw_label: default_gw} if default_gw is not None else gw_labels

    gw_select_key = f"gw_select_{league.id}"
    # Point the dropdown at the next unplayed week when unlocked / on league switch.
    if (
        gw_labels
        and default_gw_label
        and not mw_locked
        and (
            st.session_state.get("gw_default_for_league") != league.id
            or (is_customer and st.session_state.get(gw_select_key) != default_gw_label)
        )
    ):
        st.session_state[gw_select_key] = default_gw_label
        st.session_state["gw_default_for_league"] = league.id

    load_c1, load_c2, load_c3 = st.columns([2.4, 1.2, 1.2])
    with load_c1:
        if gw_labels and gw_label_list:
            default_index = (
                gw_label_list.index(default_gw_label)
                if default_gw_label in gw_label_list
                else 0
            )
            help_txt = (
                f"Customers can only load the current matchweek"
                + (f" ({default_gw_label})." if default_gw_label else ".")
                if is_customer
                else (
                    "Defaults to the next matchweek with unplayed fixtures"
                    + (f" (currently {default_gw_label})." if default_gw_label else ".")
                )
            )
            gw_label = st.selectbox(
                "Official matchweek",
                gw_label_list,
                index=default_index,
                key=gw_select_key,
                disabled=is_customer and len(gw_label_list) <= 1,
                help=help_txt,
            )
        else:
            gw_label = None
            feed_err = fixture_load_error(league)
            empty_label = (
                "Fixture feed temporarily unavailable — Retry"
                if (feed_err or league.fixture_feed_slug)
                else "No fixture feed — use custom slate"
            )
            st.selectbox(
                "Official matchweek",
                [empty_label],
                disabled=True,
                key=f"gw_select_{league.id}_empty",
            )
            if feed_err:
                st.caption(f"Could not load fixtures: {feed_err}")
    with load_c2:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        if gw_labels and gw_label:
            if st.button(
                "Load matchweek",
                use_container_width=True,
                type="secondary",
            ):
                selected_gw = gw_labels[gw_label]
                if is_customer and default_gw is not None and selected_gw != default_gw:
                    st.error("Customers can only load the current matchweek.")
                else:
                    load_matchweek_into_state(selected_gw, model, league)
                    st.rerun()
        else:
            if st.button(
                "Retry fixtures",
                use_container_width=True,
                type="secondary",
                help="Clear the fixture cache and fetch the official matchweek list again.",
            ):
                clear_fixture_cache(league.id)
                st.rerun()
    with load_c3:
        st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
        if mw_locked:
            if st.button(
                "Unlock custom slate",
                use_container_width=True,
                disabled=is_customer,
                help="Customers stay on the official current matchweek." if is_customer else None,
            ):
                unlock_matchweek_slate()
                st.rerun()
        else:
            if st.button(
                "Add match",
                disabled=is_customer or len(st.session_state.match_ids) >= MAX_MATCHES,
                use_container_width=True,
                help="Customers use the official current matchweek only." if is_customer else None,
            ):
                st.session_state.match_ids.append(st.session_state.next_match_id)
                st.session_state.next_match_id += 1
                st.rerun()

    excluded = st.session_state.get("mw_excluded") or []
    if st.session_state.get("mw_complete"):
        st.success(
            "This matchweek is fully played — nothing left to predict. "
            + "; ".join(row["label"] for row in excluded[:10])
        )
    elif excluded:
        st.info(
            f"Excluded {len(excluded)} finished match(es): "
            + "; ".join(row["label"] for row in excluded)
        )

    fixtures: list[tuple[int, str, str]] = []
    ids = list(st.session_state.match_ids)
    if not ids:
        st.caption("No fixtures on the slate. Load a matchweek with remaining games, or add a match.")
    for idx, match_id in enumerate(ids):
        club_default, venue_default, opp_default = defaults[match_id % len(defaults)]
        st.markdown(f"**Match {idx + 1}**")
        c1, c2, c3, c4 = st.columns([2.2, 1.2, 2.2, 0.7])
        with c1:
            club_key = f"club_{match_id}"
            if club_key not in st.session_state or st.session_state[club_key] not in teams:
                st.session_state[club_key] = club_default if club_default in teams else teams[0]
            club = st.selectbox(
                "Club",
                teams,
                format_func=lambda t: labels[t],
                key=club_key,
                disabled=mw_locked,
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
                disabled=mw_locked,
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
                disabled=mw_locked,
            )
        with c4:
            st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
            if st.button(
                "Remove",
                disabled=mw_locked or len(ids) <= 1,
                key=f"remove_{match_id}",
                use_container_width=True,
            ):
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
    run = st.button(
        f"Predict {n} match{'es' if n != 1 else ''}",
        type="primary",
        use_container_width=True,
        disabled=n == 0,
    )

    if run:
        if not fixtures:
            st.error("Add at least one match to predict.")
            return
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
        st.session_state.last_league_id = league.id

    preds = st.session_state.get("last_predictions")
    ranked = st.session_state.get("last_ranked")
    table_rows = st.session_state.get("last_ranked_table")
    if not preds or not ranked or not table_rows:
        return
    if st.session_state.get("last_league_id") != league.id:
        st.info("League changed since the last prediction. Click Predict again to refresh.")
        return

    current_keys = {(h, a) for _, h, a in fixtures}
    predicted_keys = {(p["home_display"], p["away_display"]) for p in preds}
    if current_keys != predicted_keys or st.session_state.get("last_apply_context") != apply_context:
        st.info("Fixtures or overlay setting changed since the last prediction. Click Predict again to refresh.")
        return

    user = current_user()
    if is_customer:
        render_predict_top_ad()

    unlock_week = current_unlock_week(league, model)
    if not has_week_access(user, unlock_week):
        st.subheader("Prediction results locked")
        if unlock_week is None:
            st.warning(
                "Load an official matchweek (or wait until fixtures are available) "
                "so we know which week to unlock."
            )
            if is_customer:
                render_predict_bottom_ad()
            return
        email = (user or {}).get("email") or ""
        render_paywall(unlock_week, email)
        if is_customer:
            render_predict_bottom_ad()
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
            file_name=f"{league.id}_ranked_predictions.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"dl_csv_{league.id}",
        )
    with dl2:
        st.download_button(
            "Download ranked slate (JSON)",
            data=json_text,
            file_name=f"{league.id}_ranked_predictions.json",
            mime="application/json",
            use_container_width=True,
            key=f"dl_json_{league.id}",
        )

    st.markdown("**Match prediction cards**")
    st.caption("Each card shows the headline pick, confidence, and 1X2 probabilities. Open a card’s expander for charts and context.")
    # Show in ranked order so the strongest calls appear first.
    rank_by_id = {id(p): i for i, p in enumerate(ranked, start=1)}
    for pred in ranked:
        render_prediction(
            pred,
            pred["is_easiest"],
            league,
            rank=rank_by_id.get(id(pred)),
        )

    if is_customer:
        render_predict_bottom_ad()


def main() -> None:
    ensure_default_admin()
    inject_adsense_site_script()
    if not render_auth_gate():
        st.stop()

    handle_paystack_return()
    flash = consume_paystack_flash()
    if flash:
        if flash.get("ok"):
            st.success(flash.get("message") or "Payment successful.")
        else:
            st.error(flash.get("message") or "Payment could not be verified.")
    expand_cross_league_unlock()

    if "league_id" not in st.session_state:
        st.session_state.league_id = "epl"

    league = active_league()
    fingerprint = cached_results_fingerprint(league.id)
    model = load_fitted_model(
        league.id,
        api_version=MODEL_API_VERSION,
        fingerprint=fingerprint,
    )
    mw_problems = validate_matchweeks(league)
    # Skip the expected "no feed" notice for leagues without a configured source (e.g. Belgium).
    actionable = [p for p in mw_problems if not p.startswith("No fixture feed configured")]
    if actionable:
        st.warning("Fixture slate issue: " + "; ".join(actionable[:3]))

    st.markdown(
        f"""
        <div class="hero">
          <h1>{league.name} match predictor</h1>
          <p>Load an official matchweek or build a custom slate. The model is fitted on
          {league.name} history (2000/01 onward from football-data.co.uk) plus completed 2026/27 scores,
          then adjusted for this summer’s signings and coaching.
          Finished fixtures are skipped when you load a matchweek. Switch leagues in the sidebar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        render_sidebar(model, league)

    # Re-read after sidebar may have switched league
    league = active_league()
    if league.id != getattr(model, "league", league).id:
        fingerprint = cached_results_fingerprint(league.id)
        model = load_fitted_model(
            league.id,
            api_version=MODEL_API_VERSION,
            fingerprint=fingerprint,
        )

    if is_admin_user():
        tab_predict, tab_teams, tab_backtest, tab_admin = st.tabs(
            ["Predict matches", "Team strength", "Backtest explorer", "Admin · Payments"]
        )
    else:
        tab_predict, tab_teams, tab_backtest = st.tabs(
            ["Predict matches", "Team strength", "Backtest explorer"]
        )
        tab_admin = None

    with tab_predict:
        render_predict_tab(model, league)
    with tab_teams:
        render_team_board(model, league)
    with tab_backtest:
        render_backtest_tab(model, league)
    if tab_admin is not None:
        with tab_admin:
            render_admin_payments_tab()


if __name__ == "__main__":
    main()
