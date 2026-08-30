"""Supabase email/password auth for the Streamlit app gate."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

SESSION_KEY = "auth_session"
USER_KEY = "auth_user"

DEFAULT_ADMIN_EMAIL = "paasolo3041@yahoo.com"
DEFAULT_ADMIN_PASSWORD = "Melvin@2019"
DEFAULT_ADMIN_PHONE = "0244445813"


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    message: str = ""
    needs_confirmation: bool = False


def get_supabase_config() -> tuple[str | None, str | None]:
    """Return (url, anon_key) from st.secrets or environment."""
    url: str | None = None
    key: str | None = None

    try:
        secrets = st.secrets
        if "supabase" in secrets:
            block = secrets["supabase"]
            url = str(block.get("url") or "").strip() or None
            key = str(block.get("key") or block.get("anon_key") or "").strip() or None
        if not url:
            url = str(secrets.get("SUPABASE_URL") or "").strip() or None
        if not key:
            key = (
                str(secrets.get("SUPABASE_ANON_KEY") or secrets.get("SUPABASE_KEY") or "").strip()
                or None
            )
    except Exception:  # noqa: BLE001 — no secrets.toml
        pass

    url = url or (os.environ.get("SUPABASE_URL") or "").strip() or None
    key = (
        key
        or (os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
        or None
    )
    return url, key


def auth_configured() -> bool:
    url, key = get_supabase_config()
    return bool(url and key)


def _client():
    from supabase import create_client

    url, key = get_supabase_config()
    if not url or not key:
        raise RuntimeError(
            "Supabase is not configured. Add [supabase] url and key to "
            ".streamlit/secrets.toml (or set SUPABASE_URL / SUPABASE_ANON_KEY)."
        )
    return create_client(url, key)


def _phone_from_user(user: Any) -> str | None:
    meta = getattr(user, "user_metadata", None) or {}
    if not isinstance(meta, dict):
        return None
    phone = str(meta.get("phone") or "").strip()
    return phone or None


def normalize_phone(raw: str | None) -> str:
    """Strip common separators; keep a leading + for international format."""
    text = str(raw or "").strip()
    if not text:
        return ""
    keep_plus = text.startswith("+")
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return ""
    return f"+{digits}" if keep_plus else digits


def validate_phone(raw: str | None) -> str | None:
    """Return an error message, or None if the phone looks usable."""
    phone = normalize_phone(raw)
    if not phone:
        return "Enter your phone number."
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return "Enter a valid phone number (7–15 digits)."
    return None


def _purchased_weeks_from_user(user: Any) -> list[str]:
    meta = getattr(user, "user_metadata", None) or {}
    if not isinstance(meta, dict):
        return []
    weeks = meta.get("purchased_weeks") or []
    if not isinstance(weeks, list):
        return []
    return [str(w) for w in weeks]


def _store_session(session: Any, user: Any) -> None:
    access = getattr(session, "access_token", None) if session is not None else None
    refresh = getattr(session, "refresh_token", None) if session is not None else None
    if access and refresh:
        st.session_state[SESSION_KEY] = {
            "access_token": access,
            "refresh_token": refresh,
        }
    email = getattr(user, "email", None) if user is not None else None
    uid = getattr(user, "id", None) if user is not None else None
    if email or uid:
        meta = getattr(user, "user_metadata", None) or {}
        cross = False
        if isinstance(meta, dict):
            cross = bool(meta.get("cross_league_unlock"))
        st.session_state[USER_KEY] = {
            "email": email,
            "id": str(uid) if uid else None,
            "role": _user_role(user, email),
            "purchased_weeks": _purchased_weeks_from_user(user),
            "cross_league_unlock": cross,
            "phone": _phone_from_user(user),
        }


def _user_role(user: Any, email: str | None = None) -> str:
    meta = getattr(user, "user_metadata", None) or {}
    raw = ""
    if isinstance(meta, dict):
        raw = str(meta.get("role") or "").strip().lower()
    if raw == "admin" or (email and email.strip().lower() == DEFAULT_ADMIN_EMAIL):
        return "admin"
    return "customer"


def default_admin_credentials() -> tuple[str, str]:
    email = DEFAULT_ADMIN_EMAIL
    password = DEFAULT_ADMIN_PASSWORD
    try:
        block = st.secrets.get("supabase") or {}
        email = str(block.get("default_admin_email") or email).strip() or email
        password = str(block.get("default_admin_password") or password).strip() or password
    except Exception:  # noqa: BLE001
        pass
    email = os.environ.get("DEFAULT_ADMIN_EMAIL", email).strip() or email
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD", password).strip() or password
    return email.lower(), password


def ensure_default_admin() -> str:
    """Create the default admin once if missing — avoid burning email rate limits."""
    status = _bootstrap_default_admin()
    st.session_state["default_admin_status"] = status
    return status


def _admin_marker_path() -> Path:
    return Path(__file__).resolve().parent / "cache" / "default_admin_ready.flag"


def _admin_phone_marker_path() -> Path:
    return Path(__file__).resolve().parent / "cache" / "default_admin_phone.flag"


def _admin_phone_value() -> str:
    phone = DEFAULT_ADMIN_PHONE
    try:
        block = st.secrets.get("supabase") or {}
        phone = str(block.get("default_admin_phone") or phone).strip() or phone
    except Exception:  # noqa: BLE001
        pass
    phone = os.environ.get("DEFAULT_ADMIN_PHONE", phone).strip() or phone
    return normalize_phone(phone) or DEFAULT_ADMIN_PHONE


def _set_admin_phone_on_session(client) -> None:
    """Attach phone (+ role) to the signed-in default admin user."""
    phone = _admin_phone_value()
    client.auth.update_user(
        {
            "data": {
                "role": "admin",
                "phone": phone,
            }
        }
    )


def _clear_admin_markers() -> None:
    for path in (_admin_marker_path(), _admin_phone_marker_path()):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def _write_admin_markers(email: str) -> None:
    marker = _admin_marker_path()
    phone_marker = _admin_phone_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(email, encoding="utf-8")
    phone_marker.write_text(_admin_phone_value(), encoding="utf-8")


def _try_admin_sign_in(client, email: str, password: str) -> tuple[bool, str]:
    """Return (ok, reason). ok means credentials work."""
    try:
        client.auth.sign_in_with_password({"email": email, "password": password})
        try:
            _set_admin_phone_on_session(client)
        except Exception:  # noqa: BLE001
            pass
        try:
            client.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        text = str(exc).lower()
        if "rate limit" in text or "too many" in text:
            return False, "rate_limited"
        if "email not confirmed" in text:
            return False, "unconfirmed"
        if "invalid" in text or "credentials" in text:
            return False, "invalid_credentials"
        return False, "error"


def _bootstrap_default_admin() -> str:
    """Ensure the default admin can sign in; create it when missing.

    The on-disk marker is only written after a successful credential check, so a
    stale flag cannot block recreation forever.
    """
    if not auth_configured():
        return "skipped"

    email, password = default_admin_credentials()
    marker = _admin_marker_path()

    try:
        client = _client()
    except Exception:  # noqa: BLE001
        return "error"

    # Fast path: marker present AND credentials still work.
    if marker.exists():
        ok, reason = _try_admin_sign_in(client, email, password)
        if ok:
            _write_admin_markers(email)
            return "exists"
        if reason == "rate_limited":
            return "rate_limited"
        if reason == "unconfirmed":
            # Account exists; user must confirm email — do not recreate.
            _write_admin_markers(email)
            return "unconfirmed"
        # Stale marker / wrong password / deleted user → recreate attempt.
        _clear_admin_markers()

    # Sign-in first (no confirmation email) before creating.
    ok, reason = _try_admin_sign_in(client, email, password)
    if ok:
        _write_admin_markers(email)
        return "exists"
    if reason == "rate_limited":
        return "rate_limited"
    if reason == "unconfirmed":
        _write_admin_markers(email)
        return "unconfirmed"
    if reason == "error":
        return "error"

    # Invalid credentials → account missing (or password mismatch). Try sign-up.
    try:
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "role": "admin",
                        "phone": _admin_phone_value(),
                    }
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        text = str(exc).lower()
        if "already" in text:
            # Email taken but our password failed — cannot fix without service role.
            return "exists_mismatch"
        if "rate limit" in text or "too many" in text:
            return "rate_limited"
        return "error"

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    identities = getattr(user, "identities", None) if user is not None else None

    # Fake "success" with empty identities usually means email already registered.
    if user is None or identities == []:
        ok, reason = _try_admin_sign_in(client, email, password)
        if ok:
            _write_admin_markers(email)
            return "exists"
        if reason == "unconfirmed":
            _write_admin_markers(email)
            return "unconfirmed"
        return "exists_mismatch"

    if session is None:
        # Created but email confirmation required before sign-in works.
        _write_admin_markers(email)
        try:
            client.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass
        return "created_unconfirmed"

    try:
        _set_admin_phone_on_session(client)
    except Exception:  # noqa: BLE001
        pass
    try:
        client.auth.sign_out()
    except Exception:  # noqa: BLE001
        pass

    # Verify credentials before declaring success.
    ok, reason = _try_admin_sign_in(client, email, password)
    if ok:
        _write_admin_markers(email)
        return "created"
    if reason == "unconfirmed":
        _write_admin_markers(email)
        return "created_unconfirmed"
    return "error"


def default_admin_bootstrap_message(status: str | None = None) -> str | None:
    """Human-readable bootstrap note for the auth screen (or None if quiet)."""
    status = status or st.session_state.get("default_admin_status")
    if not status or status in {"exists", "created", "skipped"}:
        return None
    if status == "created_unconfirmed" or status == "unconfirmed":
        return (
            "Default admin was created but must confirm email in Supabase "
            "(or disable Confirm email) before signing in."
        )
    if status == "rate_limited":
        return (
            "Could not bootstrap the default admin — Supabase email rate limit. "
            "Wait and retry, or create the admin manually in Supabase."
        )
    if status == "exists_mismatch":
        return (
            "Default admin email already exists in Supabase with a different password. "
            "Reset it in Supabase Auth, or update default_admin_password in secrets."
        )
    if status == "error":
        return "Could not create the default admin account. Check Supabase Auth settings."
    return None


def _clear_session() -> None:
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop(USER_KEY, None)


def _friendly_error(exc: BaseException) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    lower = text.lower()
    if "invalid login" in lower or "invalid credentials" in lower:
        return "Invalid email or password."
    if "already registered" in lower or "already been registered" in lower:
        return "An account with this email already exists. Sign in instead."
    if "email not confirmed" in lower:
        return "Confirm your email before signing in (check your inbox)."
    if "password" in lower and ("weak" in lower or "least" in lower or "characters" in lower):
        return "Password is too weak. Use at least 6 characters."
    if "rate limit" in lower or "too many" in lower or "over_email_send_rate_limit" in lower:
        return (
            "Supabase email rate limit hit (built-in mail allows only about 2 auth emails per hour). "
            "Wait up to an hour, or in Supabase go to Authentication → Providers → Email and turn off "
            "“Confirm email” for local testing (or add custom SMTP)."
        )
    if "getaddrinfo" in lower or "name or service not known" in lower or "11001" in lower:
        return (
            "Cannot reach Supabase. Check that [supabase] url in "
            ".streamlit/secrets.toml is https://YOUR_PROJECT_REF.supabase.co "
            "(the project ref from Settings → API, not the project display name)."
        )
    if len(text) > 180:
        return "Authentication failed. Check your details and try again."
    return text


def sign_up(email: str, password: str, phone: str | None = None) -> AuthResult:
    email = email.strip().lower()
    phone_err = validate_phone(phone)
    if phone_err:
        return AuthResult(ok=False, message=phone_err)
    phone_norm = normalize_phone(phone)
    try:
        client = _client()
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "role": "customer",
                        "phone": phone_norm,
                    }
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return AuthResult(ok=False, message=_friendly_error(exc))

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if user is None:
        return AuthResult(ok=False, message="Sign-up failed. Try a different email.")

    # Email confirmation enabled: session may be None until confirmed
    if session is None:
        return AuthResult(
            ok=True,
            message="Account created. Check your email to confirm, then sign in.",
            needs_confirmation=True,
        )

    _store_session(session, user)
    return AuthResult(ok=True, message="Account created. You are signed in.")


def sign_in(email: str, password: str) -> AuthResult:
    email = email.strip().lower()
    try:
        client = _client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:  # noqa: BLE001
        return AuthResult(ok=False, message=_friendly_error(exc))

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if user is None or session is None:
        return AuthResult(ok=False, message="Sign-in failed. Check your email and password.")

    _store_session(session, user)
    return AuthResult(ok=True, message="Signed in.")


def sign_out() -> None:
    try:
        if auth_configured() and st.session_state.get(SESSION_KEY):
            _client().auth.sign_out()
    except Exception:  # noqa: BLE001 — still clear local session
        pass
    _clear_session()


def restore_session() -> bool:
    """Restore Supabase session from Streamlit state after a rerun."""
    if st.session_state.get(USER_KEY) and st.session_state.get(SESSION_KEY):
        return True
    tokens = st.session_state.get(SESSION_KEY)
    if not tokens or not auth_configured():
        return False
    try:
        client = _client()
        response = client.auth.set_session(tokens["access_token"], tokens["refresh_token"])
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)
        if user is None:
            _clear_session()
            return False
        _store_session(session if session is not None else tokens, user)
        return True
    except Exception:  # noqa: BLE001
        _clear_session()
        return False


def current_user() -> dict | None:
    restore_session()
    user = st.session_state.get(USER_KEY)
    if not user or not user.get("email"):
        return None
    return user


def is_authenticated() -> bool:
    return current_user() is not None
