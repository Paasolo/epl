"""Paystack weekly unlock for Customer prediction results."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

from epl_predictor.auth import USER_KEY, _client, current_user
from epl_predictor.fixtures import next_unplayed_matchweek
from epl_predictor.results import LIVE_SEASON

PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{reference}"
PAYSTACK_LIST_URL = "https://api.paystack.co/transaction"

# GHS 50.00 in pesewas
WEEKLY_PRICE_PESEWAS = 5000
WEEKLY_PRICE_LABEL = "GHS 50"
CURRENCY = "GHS"

_LEDGER_PATH = Path(__file__).resolve().parent / "cache" / "payments_ledger.json"


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    message: str = ""
    authorization_url: str | None = None
    reference: str | None = None
    week: int | None = None


def get_paystack_config() -> tuple[str | None, str | None]:
    public_key: str | None = None
    secret_key: str | None = None
    try:
        secrets = st.secrets
        if "paystack" in secrets:
            block = secrets["paystack"]
            public_key = str(block.get("public_key") or "").strip() or None
            secret_key = str(block.get("secret_key") or "").strip() or None
        if not public_key:
            public_key = str(secrets.get("PAYSTACK_PUBLIC_KEY") or "").strip() or None
        if not secret_key:
            secret_key = str(secrets.get("PAYSTACK_SECRET_KEY") or "").strip() or None
    except Exception:  # noqa: BLE001
        pass
    public_key = public_key or (os.environ.get("PAYSTACK_PUBLIC_KEY") or "").strip() or None
    secret_key = secret_key or (os.environ.get("PAYSTACK_SECRET_KEY") or "").strip() or None
    # Guard against accidentally pasted keys (duplicate paste is a common mistake).
    if secret_key:
        for prefix in ("sk_test_", "sk_live_"):
            if secret_key.startswith(prefix):
                rest = secret_key[len(prefix) :]
                cut = rest.find(prefix)
                if cut >= 0:
                    secret_key = prefix + rest[:cut]
                break
        secret_key = secret_key.strip() or None
    return public_key, secret_key


def paystack_configured() -> bool:
    public_key, secret_key = get_paystack_config()
    if not public_key or not secret_key:
        return False
    if "REPLACE" in public_key.upper() or "REPLACE" in secret_key.upper():
        return False
    if public_key.endswith("...") or secret_key.endswith("..."):
        return False
    return True


def week_access_key(week: int, season: str = LIVE_SEASON) -> str:
    return f"{season}:{int(week)}"


def purchased_weeks(user: dict | None = None) -> list[str]:
    user = user if user is not None else current_user()
    if not user:
        return []
    weeks = user.get("purchased_weeks") or []
    if not isinstance(weeks, list):
        return []
    return [str(w) for w in weeks]


def purchased_week_numbers(user: dict | None = None, season: str = LIVE_SEASON) -> set[int]:
    nums: set[int] = set()
    prefix = f"{season}:"
    for key in purchased_weeks(user):
        if not str(key).startswith(prefix):
            continue
        try:
            nums.add(int(str(key).split(":", 1)[1]))
        except (TypeError, ValueError, IndexError):
            continue
    return nums


def has_week_access(user: dict | None, week: int | None, season: str = LIVE_SEASON) -> bool:
    if not user:
        return False
    if user.get("role") == "admin":
        return True
    if week is None:
        return False
    # Exact key or same week number anywhere this season (all leagues share week unlocks).
    if week_access_key(week, season) in purchased_weeks(user):
        return True
    return int(week) in purchased_week_numbers(user, season)


def current_unlock_week(league, model) -> int | None:
    """Official week the customer must unlock for prediction results."""
    if st.session_state.get("mw_locked") and st.session_state.get("mw_loaded") is not None:
        try:
            return int(st.session_state["mw_loaded"])
        except (TypeError, ValueError):
            pass
    return next_unplayed_matchweek(model.matches, league, season=LIVE_SEASON)


def all_leagues_current_weeks(season: str = LIVE_SEASON) -> set[int]:
    """Next unplayed matchweek number for every league that has a fixture slate.

    Uses the fixture/openfootball feed only (no model fit / history reload) so
    payment unlock stays fast on first expand.
    """
    from epl_predictor.fixtures import next_unplayed_matchweek_fast
    from epl_predictor.leagues import LEAGUES

    _ = season  # season is encoded in the live fixture feeds
    weeks: set[int] = set()
    for _league_id, league in LEAGUES.items():
        try:
            gw = next_unplayed_matchweek_fast(league)
            if gw is not None:
                weeks.add(int(gw))
        except Exception:  # noqa: BLE001 — skip leagues that fail to load
            continue
    return weeks


def _persist_purchased_weeks(weeks: list[str], role: str = "customer") -> None:
    """Write purchased_weeks to Supabase user metadata and local session."""
    tokens = st.session_state.get("auth_session") or {}
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    if not access or not refresh:
        raise RuntimeError("Sign in again, then complete payment.")

    user = current_user() or {}
    role = "admin" if (user.get("role") == "admin" or role == "admin") else "customer"
    unique = sorted(set(str(w) for w in weeks))

    client = _client()
    client.auth.set_session(access, refresh)
    response = client.auth.update_user(
        {
            "data": {
                "role": role,
                "purchased_weeks": unique,
                "cross_league_unlock": True,
            }
        }
    )
    updated = getattr(response, "user", None)
    email = (getattr(updated, "email", None) if updated is not None else None) or user.get("email")
    uid = (getattr(updated, "id", None) if updated is not None else None) or user.get("id")
    meta = getattr(updated, "user_metadata", None) if updated is not None else {}
    purchased = meta.get("purchased_weeks") if isinstance(meta, dict) else unique
    st.session_state[USER_KEY] = {
        "email": email,
        "id": str(uid) if uid else None,
        "role": role,
        "purchased_weeks": list(purchased) if isinstance(purchased, list) else unique,
        "cross_league_unlock": True,
    }
    session = getattr(response, "session", None)
    if session is not None:
        new_access = getattr(session, "access_token", None)
        new_refresh = getattr(session, "refresh_token", None)
        if new_access and new_refresh:
            st.session_state["auth_session"] = {
                "access_token": new_access,
                "refresh_token": new_refresh,
            }


def _grant_weeks_on_user(week_numbers: set[int], season: str = LIVE_SEASON) -> list[str]:
    """Append season week keys for every granted matchweek number."""
    user = current_user() or {}
    weeks = list(purchased_weeks(user))
    for num in week_numbers:
        key = week_access_key(int(num), season)
        if key not in weeks:
            weeks.append(key)
    _persist_purchased_weeks(weeks, role=str(user.get("role") or "customer"))
    return weeks


def expand_cross_league_unlock(season: str = LIVE_SEASON) -> bool:
    """One-time: if the customer paid this season, unlock every league's current week.

    Older payments only stored the EPL week while other leagues were on a different
    number. Runs once per account (metadata flag), not again when weeks advance.
    """
    user = current_user()
    if not user or user.get("role") == "admin":
        return False
    paid = purchased_week_numbers(user, season)
    if not paid:
        return False
    if st.session_state.get("cross_league_expanded"):
        return False
    # Already migrated / granted as a multi-league package.
    if user.get("cross_league_unlock"):
        st.session_state["cross_league_expanded"] = True
        return False

    current = all_leagues_current_weeks(season)
    if not current:
        st.session_state["cross_league_expanded"] = True
        return False
    try:
        _grant_weeks_on_user(paid | current, season=season)
        st.session_state[USER_KEY] = {
            **(current_user() or user),
            "cross_league_unlock": True,
        }
        st.session_state["cross_league_expanded"] = True
        return True
    except Exception:  # noqa: BLE001
        return False


def _app_callback_url() -> str:
    """Best-effort public URL for Paystack to redirect back to."""
    try:
        headers = getattr(st, "context", None)
        if headers is not None:
            hdrs = getattr(headers, "headers", None) or {}
            origin = hdrs.get("Origin") or hdrs.get("origin")
            if origin:
                return str(origin).rstrip("/")
            host = hdrs.get("Host") or hdrs.get("host")
            if host:
                proto = hdrs.get("X-Forwarded-Proto") or hdrs.get("x-forwarded-proto") or "https"
                return f"{proto}://{host}".rstrip("/")
    except Exception:  # noqa: BLE001
        pass
    try:
        base = st.secrets.get("APP_URL") or st.secrets.get("app_url")
        if base:
            return str(base).rstrip("/")
    except Exception:  # noqa: BLE001
        pass
    return (os.environ.get("APP_URL") or "http://localhost:8501").rstrip("/")


def _paystack_request(method: str, url: str, payload: dict | None = None) -> dict:
    """Call Paystack with browser-like headers (Cloudflare blocks bare urllib)."""
    import httpx

    _, secret_key = get_paystack_config()
    if not secret_key:
        raise RuntimeError("Paystack secret key is not configured.")

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36 LeaguePredict/1.0"
        ),
    }
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            if method.upper() == "GET":
                resp = client.get(url, headers=headers)
            else:
                resp = client.request(method.upper(), url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Cannot reach Paystack: {exc}") from exc

    if resp.status_code == 403 and ("1010" in resp.text or "cloudflare" in resp.text.lower()):
        raise RuntimeError(
            "Paystack blocked this server request (Cloudflare 1010). "
            "Check that your secret key is a single sk_test_/sk_live_ value "
            "(not pasted twice), then try again."
        )
    if resp.status_code >= 400:
        detail = (resp.text or "")[:200]
        raise RuntimeError(f"Paystack HTTP {resp.status_code}: {detail}")

    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Paystack returned a non-JSON response.") from exc
    if not data.get("status"):
        raise RuntimeError(str(data.get("message") or "Paystack request failed."))
    return data


def initialize_payment(email: str, week: int, season: str = LIVE_SEASON) -> PaymentResult:
    if not paystack_configured():
        return PaymentResult(
            ok=False,
            message=(
                "Paystack is not configured. Add [paystack] public_key and secret_key "
                "to .streamlit/secrets.toml."
            ),
        )
    email = email.strip().lower()
    if not email or week is None:
        return PaymentResult(ok=False, message="Missing email or matchweek for payment.")

    reference = f"mw{week}-{uuid.uuid4().hex[:16]}"
    callback = _app_callback_url()
    payload = {
        "email": email,
        "amount": WEEKLY_PRICE_PESEWAS,
        "currency": CURRENCY,
        "reference": reference,
        "callback_url": callback,
        "metadata": {
            "season": season,
            "matchweek": int(week),
            "email": email,
            "access_key": week_access_key(week, season),
            "custom_fields": [
                {"display_name": "Matchweek", "variable_name": "matchweek", "value": str(week)},
                {"display_name": "Season", "variable_name": "season", "value": season},
            ],
        },
    }
    try:
        data = _paystack_request("POST", PAYSTACK_INIT_URL, payload)
        info = data.get("data") or {}
        url = info.get("authorization_url")
        ref = info.get("reference") or reference
        if not url:
            return PaymentResult(ok=False, message="Paystack did not return a checkout URL.")
        return PaymentResult(
            ok=True,
            message="Checkout ready.",
            authorization_url=str(url),
            reference=str(ref),
            week=int(week),
        )
    except Exception as exc:  # noqa: BLE001
        return PaymentResult(ok=False, message=str(exc))


def _metadata_week(meta: Any) -> tuple[str | None, int | None]:
    if not isinstance(meta, dict):
        return None, None
    season = meta.get("season") or LIVE_SEASON
    week = meta.get("matchweek")
    try:
        week_i = int(week) if week is not None else None
    except (TypeError, ValueError):
        week_i = None
    return str(season) if season else None, week_i


def _grant_week_on_user(week: int, season: str = LIVE_SEASON) -> None:
    """Unlock the paid matchweek on every league's current slate."""
    weeks = {int(week)} | all_leagues_current_weeks(season)
    _grant_weeks_on_user(weeks, season=season)


def verify_and_grant(reference: str, expected_week: int | None = None) -> PaymentResult:
    if not reference:
        return PaymentResult(ok=False, message="Missing payment reference.")
    if not paystack_configured():
        return PaymentResult(ok=False, message="Paystack is not configured.")

    try:
        data = _paystack_request("GET", PAYSTACK_VERIFY_URL.format(reference=reference))
        info = data.get("data") or {}
    except Exception as exc:  # noqa: BLE001
        return PaymentResult(ok=False, message=str(exc))

    status = str(info.get("status") or "").lower()
    currency = str(info.get("currency") or "").upper()
    amount = info.get("amount")
    meta = info.get("metadata") or {}
    season, week = _metadata_week(meta)

    if status != "success":
        return PaymentResult(ok=False, message=f"Payment not successful (status: {status or 'unknown'}).")
    if currency != CURRENCY:
        return PaymentResult(ok=False, message=f"Unexpected currency {currency}; expected {CURRENCY}.")
    try:
        amount_i = int(amount)
    except (TypeError, ValueError):
        return PaymentResult(ok=False, message="Invalid payment amount from Paystack.")
    if amount_i < WEEKLY_PRICE_PESEWAS:
        return PaymentResult(ok=False, message="Paid amount is below the weekly unlock price.")
    if week is None:
        return PaymentResult(ok=False, message="Payment metadata is missing the matchweek.")
    if expected_week is not None and int(week) != int(expected_week):
        return PaymentResult(
            ok=False,
            message=f"Payment was for matchweek {week}, but you need matchweek {expected_week}.",
        )

    user = current_user()
    if not user:
        return PaymentResult(ok=False, message="Sign in again to unlock this week after payment.")

    paid_email = str(meta.get("email") or info.get("customer", {}).get("email") or "").strip().lower()
    if paid_email and user.get("email") and paid_email != str(user["email"]).strip().lower():
        return PaymentResult(ok=False, message="This payment belongs to a different account.")

    try:
        _grant_week_on_user(int(week), season or LIVE_SEASON)
    except Exception as exc:  # noqa: BLE001
        return PaymentResult(ok=False, message=f"Payment verified but unlock failed: {exc}")

    record_local_payment(
        {
            "reference": str(reference),
            "email": paid_email or (user.get("email") or ""),
            "amount_pesewas": amount_i,
            "amount_ghs": round(amount_i / 100, 2),
            "currency": currency,
            "status": status,
            "season": season or LIVE_SEASON,
            "matchweek": int(week),
            "paid_at": info.get("paid_at") or info.get("transaction_date") or datetime.now(timezone.utc).isoformat(),
            "channel": info.get("channel") or "",
            "gateway_response": info.get("gateway_response") or "",
            "source": "verify",
        }
    )

    return PaymentResult(
        ok=True,
        message=(
            f"Matchweek {week} unlocked across all leagues "
            f"(current slates included)."
        ),
        reference=reference,
        week=int(week),
    )


def _ledger_read() -> list[dict]:
    if not _LEDGER_PATH.exists():
        return []
    try:
        raw = json.loads(_LEDGER_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except Exception:  # noqa: BLE001
        return []


def _ledger_write(rows: list[dict]) -> None:
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def record_local_payment(row: dict) -> None:
    """Append/update a verified payment in the local admin ledger."""
    rows = _ledger_read()
    ref = str(row.get("reference") or "")
    if ref:
        rows = [r for r in rows if str(r.get("reference") or "") != ref]
    rows.append(row)
    rows.sort(key=lambda r: str(r.get("paid_at") or ""), reverse=True)
    try:
        _ledger_write(rows)
    except Exception:  # noqa: BLE001 — non-fatal on read-only hosts
        pass


def _normalize_paystack_row(item: dict) -> dict:
    meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    season, week = _metadata_week(meta)
    customer = item.get("customer") if isinstance(item.get("customer"), dict) else {}
    amount = item.get("amount")
    try:
        amount_i = int(amount)
    except (TypeError, ValueError):
        amount_i = 0
    email = (
        str(meta.get("email") or customer.get("email") or item.get("customer", {}).get("email") or "")
        .strip()
        .lower()
    )
    if not email and isinstance(item.get("customer"), dict):
        email = str(customer.get("email") or "").strip().lower()
    return {
        "reference": str(item.get("reference") or ""),
        "email": email,
        "amount_pesewas": amount_i,
        "amount_ghs": round(amount_i / 100, 2),
        "currency": str(item.get("currency") or "").upper(),
        "status": str(item.get("status") or "").lower(),
        "season": season or (meta.get("season") or ""),
        "matchweek": week,
        "paid_at": item.get("paid_at") or item.get("created_at") or item.get("transaction_date") or "",
        "channel": item.get("channel") or "",
        "gateway_response": item.get("gateway_response") or "",
        "source": "paystack",
    }


def fetch_paystack_transactions(pages: int = 3, per_page: int = 50) -> list[dict]:
    """Pull recent transactions from Paystack (newest first)."""
    if not paystack_configured():
        return []
    rows: list[dict] = []
    for page in range(1, max(1, pages) + 1):
        url = f"{PAYSTACK_LIST_URL}?perPage={per_page}&page={page}"
        data = _paystack_request("GET", url)
        batch = data.get("data") or []
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if isinstance(item, dict):
                rows.append(_normalize_paystack_row(item))
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        page_count = meta.get("pageCount") or meta.get("page_count")
        try:
            if page_count is not None and page >= int(page_count):
                break
        except (TypeError, ValueError):
            pass
        if len(batch) < per_page:
            break
    return rows


def load_payment_rows(*, prefer_paystack: bool = True, pages: int = 3) -> tuple[list[dict], str]:
    """Return payment rows for the admin screen and a short source note."""
    local = _ledger_read()
    remote: list[dict] = []
    note = "local ledger"
    if prefer_paystack and paystack_configured():
        try:
            remote = fetch_paystack_transactions(pages=pages)
            note = "Paystack + local ledger"
        except Exception as exc:  # noqa: BLE001
            note = f"local ledger (Paystack fetch failed: {exc})"
    # Prefer Paystack rows; fill gaps from local ledger by reference.
    by_ref: dict[str, dict] = {}
    for row in local + remote:
        ref = str(row.get("reference") or "")
        if not ref:
            continue
        # Remote overwrites local when both exist.
        if ref not in by_ref or row.get("source") == "paystack":
            by_ref[ref] = row
    rows = list(by_ref.values())
    rows.sort(key=lambda r: str(r.get("paid_at") or ""), reverse=True)
    return rows, note


def payment_summary(rows: list[dict]) -> dict[str, Any]:
    success = [r for r in rows if str(r.get("status") or "").lower() == "success"]
    # Focus on GHS weekly unlocks when currency present; still count success overall.
    ghs_success = [r for r in success if str(r.get("currency") or CURRENCY).upper() == CURRENCY]
    total_ghs = sum(float(r.get("amount_ghs") or 0) for r in ghs_success)
    emails = {str(r.get("email") or "").lower() for r in success if r.get("email")}
    by_week: dict[str, int] = {}
    for r in success:
        week = r.get("matchweek")
        season = r.get("season") or LIVE_SEASON
        label = f"{season} · MW{week}" if week is not None else f"{season} · unknown"
        by_week[label] = by_week.get(label, 0) + 1
    failed = [r for r in rows if str(r.get("status") or "").lower() not in {"success", ""}]
    pending = [r for r in rows if str(r.get("status") or "").lower() in {"abandoned", "failed", "ongoing", "pending", "reversed"}]
    return {
        "total_transactions": len(rows),
        "successful": len(success),
        "failed_or_other": len(failed) if failed else len(pending),
        "unique_customers": len(emails),
        "revenue_ghs": round(total_ghs, 2),
        "by_matchweek": dict(sorted(by_week.items(), key=lambda kv: kv[0])),
        "latest_paid_at": success[0].get("paid_at") if success else None,
    }


def handle_paystack_return() -> None:
    """If Paystack redirected with a reference, verify once and clear query params."""
    params = st.query_params
    reference = params.get("reference") or params.get("trxref")
    if not reference:
        return
    # Avoid re-processing the same reference in one browser session
    done_key = f"paystack_handled_{reference}"
    if st.session_state.get(done_key):
        try:
            del st.query_params["reference"]
        except Exception:  # noqa: BLE001
            pass
        try:
            del st.query_params["trxref"]
        except Exception:  # noqa: BLE001
            pass
        return

    result = verify_and_grant(str(reference))
    st.session_state[done_key] = True
    st.session_state["paystack_flash"] = {
        "ok": result.ok,
        "message": result.message,
        "week": result.week,
    }
    # Clear Paystack query params
    for key in ("reference", "trxref"):
        try:
            del st.query_params[key]
        except Exception:  # noqa: BLE001
            pass


def consume_paystack_flash() -> dict | None:
    flash = st.session_state.pop("paystack_flash", None)
    return flash if isinstance(flash, dict) else None


def render_paywall(week: int, email: str) -> None:
    """Show unlock card and start Paystack checkout."""
    st.markdown(
        f"""
        <div class="prediction-card" style="border-color:#C9A227;">
          <div class="match-title">Unlock Matchweek {week}</div>
          <div class="sub">
            Customers pay <b>{WEEKLY_PRICE_LABEL}</b> once to view prediction results for this
            official matchweek across <b>every league</b> (each league’s current slate is included).
            Admins do not need to pay.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not paystack_configured():
        st.error(
            "Paystack is not configured. Add keys to `.streamlit/secrets.toml`:\n\n"
            "```toml\n[paystack]\npublic_key = \"pk_test_...\"\nsecret_key = \"sk_test_...\"\n```"
        )
        return

    if st.button(
        f"Pay {WEEKLY_PRICE_LABEL} with Paystack — Matchweek {week}",
        type="primary",
        use_container_width=True,
        key=f"paystack_pay_mw_{week}",
    ):
        with st.spinner("Starting Paystack checkout…"):
            result = initialize_payment(email, week)
        if not result.ok or not result.authorization_url:
            st.error(result.message)
        else:
            st.session_state["pending_paystack_week"] = week
            st.session_state["pending_paystack_ref"] = result.reference
            st.link_button(
                "Continue to Paystack checkout",
                result.authorization_url,
                type="primary",
                use_container_width=True,
            )
            st.info("Complete payment on Paystack, then you will return here and Matchweek access unlocks.")
