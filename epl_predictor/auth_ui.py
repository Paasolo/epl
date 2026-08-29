"""Login / create-account gate UI (shown before the predictor loads)."""

from __future__ import annotations

import streamlit as st

from epl_predictor.auth import (
    auth_configured,
    is_authenticated,
    sign_in,
    sign_up,
)

MIN_PASSWORD_LEN = 6


def _validate_credentials(email: str, password: str, confirm: str | None = None) -> str | None:
    email = (email or "").strip()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return "Enter a valid email address."
    if len(password or "") < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if confirm is not None and password != confirm:
        return "Passwords do not match."
    return None


def render_auth_gate() -> bool:
    """Render the auth screen. Returns True if the user is authenticated."""
    if is_authenticated():
        return True

    st.markdown(
        """
        <div class="hero">
          <h1>Match predictor</h1>
          <p>Create an account or sign in to access multi-league predictions,
          team strength boards, and walk-forward backtests.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not auth_configured():
        st.error(
            "Authentication is not configured. Add Supabase credentials to "
            "`.streamlit/secrets.toml` (or Streamlit Cloud secrets):"
        )
        st.code(
            '[supabase]\nurl = "https://YOUR_PROJECT.supabase.co"\nkey = "YOUR_ANON_KEY"',
            language="toml",
        )
        st.caption(
            "Create a free project at supabase.com → Authentication → enable Email. "
            "Use the Project URL and anon public key."
        )
        return False

    tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
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

    with tab_signup:
        with st.form("signup_form", clear_on_submit=False):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
                help=f"At least {MIN_PASSWORD_LEN} characters.",
            )
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button(
                "Create account", type="primary", use_container_width=True
            )
        if submitted:
            err = _validate_credentials(email, password, confirm)
            if err:
                st.error(err)
            else:
                with st.spinner("Creating account…"):
                    result = sign_up(email, password)
                if result.ok:
                    if result.needs_confirmation:
                        st.success(result.message)
                        st.info("After you confirm your email, use the Sign in tab.")
                    else:
                        st.success(result.message)
                        st.rerun()
                else:
                    st.error(result.message)

    return False
