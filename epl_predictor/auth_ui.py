"""Modern sign-in / create-account gate (shown before the predictor loads)."""

from __future__ import annotations

import streamlit as st

from epl_predictor.auth import (
    auth_configured,
    default_admin_bootstrap_message,
    is_authenticated,
    sign_in,
    sign_up,
    validate_phone,
)
from epl_predictor.ads import inject_adsense_site_script

MIN_PASSWORD_LEN = 6

NAVY = "#0B1220"
CARD = "#121A2B"
LINE = "#243049"
GOLD = "#C9A227"
TEAL = "#3DB2A0"
TEXT = "#E8EEF7"
MUTED = "#93A0B5"


def _inject_auth_styles() -> None:
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,700&display=swap" rel="stylesheet">
        <style>
          /* Focus the viewport on auth — hide chrome noise */
          [data-testid="stSidebar"],
          [data-testid="stSidebarCollapsedControl"],
          header[data-testid="stHeader"] {{
            display: none !important;
          }}
          .stApp {{
            background:
              radial-gradient(1200px 600px at 12% -10%, rgba(61, 178, 160, 0.18), transparent 55%),
              radial-gradient(900px 500px at 95% 10%, rgba(201, 162, 39, 0.12), transparent 50%),
              linear-gradient(165deg, #071018 0%, {NAVY} 42%, #0E1A2E 100%);
            color: {TEXT};
            font-family: "Outfit", sans-serif;
          }}
          .stApp > div:first-child {{
            padding-top: 0.5rem;
          }}
          .block-container {{
            max-width: 1100px;
            padding-top: 2.5rem !important;
            padding-bottom: 3rem !important;
          }}
          .auth-brand {{
            min-height: 28rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 1.5rem 0.5rem 1.5rem 0.25rem;
            animation: authRise 0.7s ease-out both;
          }}
          .auth-kicker {{
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {TEAL};
            margin-bottom: 1rem;
          }}
          .auth-brand h1 {{
            font-family: "Fraunces", Georgia, serif;
            font-weight: 700;
            font-size: clamp(2.4rem, 4.5vw, 3.6rem);
            line-height: 1.05;
            letter-spacing: -0.03em;
            margin: 0 0 1rem 0;
            color: {TEXT};
          }}
          .auth-brand h1 span {{
            color: {GOLD};
          }}
          .auth-brand p {{
            margin: 0;
            max-width: 28rem;
            color: {MUTED};
            font-size: 1.05rem;
            line-height: 1.55;
          }}
          .auth-points {{
            margin-top: 1.75rem;
            display: grid;
            gap: 0.65rem;
          }}
          .auth-point {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            color: {TEXT};
            font-size: 0.95rem;
          }}
          .auth-point i {{
            width: 0.45rem;
            height: 0.45rem;
            border-radius: 50%;
            background: {TEAL};
            flex-shrink: 0;
            display: inline-block;
          }}
          .auth-panel-shell {{
            background: linear-gradient(180deg, rgba(21, 32, 54, 0.95) 0%, {CARD} 100%);
            border: 1px solid {LINE};
            border-radius: 22px;
            padding: 1.35rem 1.25rem 0.35rem;
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
            animation: authRise 0.7s ease-out 0.08s both;
            margin-bottom: 0.75rem;
          }}
          div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(180deg, rgba(21, 32, 54, 0.97) 0%, {CARD} 100%) !important;
            border: 1px solid {LINE} !important;
            border-radius: 22px !important;
            padding: 1.15rem 1rem 0.85rem !important;
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
            animation: authRise 0.7s ease-out 0.08s both;
          }}
          .auth-panel-title {{
            font-family: "Fraunces", Georgia, serif;
            font-size: 1.65rem;
            font-weight: 700;
            margin: 0 0 0.35rem 0;
            letter-spacing: -0.02em;
          }}
          .auth-panel-sub {{
            color: {MUTED};
            font-size: 0.92rem;
            margin: 0 0 0.35rem 0;
            line-height: 1.45;
          }}
          .auth-switch {{
            margin-top: 0.35rem;
            margin-bottom: 0.5rem;
            text-align: center;
            color: {MUTED};
            font-size: 0.9rem;
          }}
          /* Form controls on the auth page only (styles injected solely here) */
          [data-testid="stTextInput"] label,
          [data-testid="stForm"] label {{
            font-weight: 600 !important;
            color: {TEXT} !important;
            font-size: 0.88rem !important;
          }}
          [data-testid="stTextInput"] input {{
            background: #0E1626 !important;
            border: 1px solid {LINE} !important;
            border-radius: 12px !important;
            color: {TEXT} !important;
            padding: 0.7rem 0.85rem !important;
          }}
          [data-testid="stTextInput"] input:focus {{
            border-color: {TEAL} !important;
            box-shadow: 0 0 0 1px rgba(61, 178, 160, 0.35) !important;
          }}
          [data-testid="stFormSubmitButton"] button {{
            background: linear-gradient(135deg, {TEAL} 0%, #2A9B8A 100%) !important;
            color: #041018 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 0.01em !important;
            padding-top: 0.65rem !important;
            padding-bottom: 0.65rem !important;
            transition: transform 0.15s ease, filter 0.15s ease !important;
          }}
          [data-testid="stFormSubmitButton"] button:hover {{
            filter: brightness(1.06);
            transform: translateY(-1px);
          }}
          .auth-mode-row + div button,
          div[data-testid="stHorizontalBlock"] button {{
            border-radius: 11px !important;
            font-weight: 600 !important;
          }}
          .auth-setup {{
            background: {CARD};
            border: 1px solid {LINE};
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            margin-top: 1rem;
          }}
          @keyframes authRise {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to {{ opacity: 1; transform: translateY(0); }}
          }}
          @media (max-width: 768px) {{
            .auth-brand {{
              min-height: auto;
              padding: 0.5rem 0 1rem;
            }}
            .auth-brand h1 {{
              font-size: 2.15rem;
            }}
            .block-container {{
              padding-top: 1.25rem !important;
            }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _validate_credentials(
    email: str,
    password: str,
    confirm: str | None = None,
    *,
    phone: str | None = None,
    require_phone: bool = False,
) -> str | None:
    email = (email or "").strip()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return "Enter a valid email address."
    if require_phone:
        phone_err = validate_phone(phone)
        if phone_err:
            return phone_err
    if len(password or "") < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if confirm is not None and password != confirm:
        return "Passwords do not match."
    return None


def _render_brand_column() -> None:
    st.markdown(
        """
        <div class="auth-brand">
          <div class="auth-kicker">League Predict</div>
          <h1>Match calls<br/>with <span>clarity</span></h1>
          <p>
            Sign in for ranked 1X2 predictions across Europe’s top flights —
            calibrated models, summer overlays, and weekly unlocks.
          </p>
          <div class="auth-points">
            <div class="auth-point"><i></i> Nine leagues, one walk-forward engine</div>
            <div class="auth-point"><i></i> Confidence bands you can lean on</div>
            <div class="auth-point"><i></i> Pay once per matchweek for full results</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_mode_switch(mode: str) -> str:
    st.markdown('<div class="auth-mode-row">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            "Sign in",
            use_container_width=True,
            type="primary" if mode == "signin" else "secondary",
            key="auth_mode_signin",
        ):
            st.session_state["auth_mode"] = "signin"
            st.rerun()
    with c2:
        if st.button(
            "Create account",
            use_container_width=True,
            type="primary" if mode == "signup" else "secondary",
            key="auth_mode_signup",
        ):
            st.session_state["auth_mode"] = "signup"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    return st.session_state.get("auth_mode", mode)


def _render_signin_form() -> None:
    st.markdown(
        """
        <div class="auth-panel-title">Welcome back</div>
        <p class="auth-panel-sub">Sign in to open your matchweek slate and ranked calls.</p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email", placeholder="you@email.com")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            placeholder="Your password",
        )
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        err = _validate_credentials(email, password)
        if err:
            st.error(err)
        else:
            with st.spinner("Signing in…"):
                result = sign_in(email, password)
            if result.ok:
                st.success(result.message)
                st.rerun()
            else:
                st.error(result.message)
    st.markdown(
        """
        <div class="auth-switch">New here? Switch to <b>Create account</b> above.</div>
        """,
        unsafe_allow_html=True,
    )


def _render_signup_form() -> None:
    st.markdown(
        """
        <div class="auth-panel-title">Create your account</div>
        <p class="auth-panel-sub">
          Join as a customer to unlock weekly predictions after a short checkout.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("signup_form", clear_on_submit=False):
        email = st.text_input("Email", key="signup_email", placeholder="you@email.com")
        st.caption("We’ll use your phone to send a payment confirmation SMS.")
        phone = st.text_input(
            "Phone number *",
            key="signup_phone",
            placeholder="024 XXX XXXX or +233…",
            help="Required. Used for Nalo SMS after you unlock a matchweek.",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
            placeholder=f"At least {MIN_PASSWORD_LEN} characters",
            help=f"At least {MIN_PASSWORD_LEN} characters.",
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm",
            placeholder="Repeat password",
        )
        submitted = st.form_submit_button(
            "Create account", type="primary", use_container_width=True
        )
    if submitted:
        err = _validate_credentials(
            email, password, confirm, phone=phone, require_phone=True
        )
        if err:
            st.error(err)
        else:
            with st.spinner("Creating account…"):
                result = sign_up(email, password, phone=phone)
            if result.ok:
                if result.needs_confirmation:
                    st.success(result.message)
                    st.info("After you confirm your email, switch to Sign in.")
                else:
                    st.success(result.message)
                    st.rerun()
            else:
                st.error(result.message)
    st.markdown(
        """
        <div class="auth-switch">Already have an account? Switch to <b>Sign in</b> above.</div>
        """,
        unsafe_allow_html=True,
    )


def render_auth_gate() -> bool:
    """Render the auth screen. Returns True if the user is authenticated."""
    if is_authenticated():
        return True

    # Public page: AdSense site script must be crawlable for Google approval.
    inject_adsense_site_script()
    _inject_auth_styles()

    if not auth_configured():
        st.markdown(
            """
            <div class="auth-brand">
              <div class="auth-kicker">League Predict</div>
              <h1>Almost ready</h1>
              <p>Authentication is not configured on this deployment yet.</p>
            </div>
            <div class="auth-setup">
            """,
            unsafe_allow_html=True,
        )
        st.error(
            "Add Supabase credentials to `.streamlit/secrets.toml` "
            "(or Streamlit Cloud secrets):"
        )
        st.code(
            '[supabase]\nurl = "https://YOUR_PROJECT.supabase.co"\nkey = "YOUR_ANON_KEY"',
            language="toml",
        )
        st.caption(
            "Create a free project at supabase.com → Authentication → enable Email. "
            "Use the Project URL and anon public key."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return False

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "signin"

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        _render_brand_column()
    with right:
        with st.container(border=True):
            mode = _render_mode_switch(st.session_state["auth_mode"])
            st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)
            boot_msg = default_admin_bootstrap_message()
            if boot_msg:
                st.warning(boot_msg)
            if mode == "signup":
                _render_signup_form()
            else:
                _render_signin_form()

    return False
