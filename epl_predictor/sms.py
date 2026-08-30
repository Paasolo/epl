"""Nalo Solutions SMS — payment confirmations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import streamlit as st

DEFAULT_API_URL = (
    "https://sms.nalosolutions.com/smsbackend/clientapi/Resl_Nalo/send-message/"
)
DEFAULT_SENDER = "SpareLink"


@dataclass(frozen=True)
class SmsResult:
    ok: bool
    message: str = ""
    skipped: bool = False


def _truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _secret_block(*names: str) -> Any | None:
    try:
        secrets = st.secrets
    except Exception:  # noqa: BLE001
        return None
    for name in names:
        try:
            if name in secrets:
                return secrets[name]
        except Exception:  # noqa: BLE001
            continue
        # Case-insensitive fallback for Streamlit secrets keys
        try:
            for key in secrets.keys():  # type: ignore[attr-defined]
                if str(key).lower() == name.lower():
                    return secrets[key]
        except Exception:  # noqa: BLE001
            continue
    return None


def _block_get(block: Any, *keys: str) -> Any:
    if block is None:
        return None
    for key in keys:
        try:
            if key in block:
                val = block[key]
                if val is not None and str(val).strip() != "":
                    return val
        except Exception:  # noqa: BLE001
            pass
        try:
            for existing in block.keys():  # type: ignore[attr-defined]
                if str(existing).lower() == key.lower():
                    val = block[existing]
                    if val is not None and str(val).strip() != "":
                        return val
        except Exception:  # noqa: BLE001
            continue
    return None


def _load_secrets_file() -> dict[str, Any]:
    """Direct TOML fallback when st.secrets is unavailable or redacts values."""
    import tomllib
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return {}


def get_nalo_config() -> dict[str, Any]:
    """Load NaloSms-style config from secrets or environment.

    Preferred secrets shape (matches appsettings-style JSON)::

        [NaloSms]
        Enabled = true
        NaloApiUrl = "https://sms.nalosolutions.com/smsbackend/clientapi/Resl_Nalo/send-message/"
        NaloApiKey = "..."
        NaloSenderId = "SpareLink"
        RequestDeliveryReport = true
    """
    enabled = True
    api_url = DEFAULT_API_URL
    api_key = None
    sender = DEFAULT_SENDER
    dlr = True
    username = password = None

    block = _secret_block("NaloSms", "nalo", "nalo_sms")
    file_block = None
    file_secrets = _load_secrets_file()
    for name in ("NaloSms", "nalo", "nalo_sms"):
        cand = file_secrets.get(name)
        if isinstance(cand, dict):
            file_block = cand
            break
    # Prefer file block when st.secrets is missing keys (common outside `streamlit run`).
    if block is None:
        block = file_block

    def _apply(block_obj: Any) -> None:
        nonlocal enabled, api_url, api_key, sender, dlr, username, password
        if block_obj is None:
            return
        enabled = _truthy(_block_get(block_obj, "Enabled", "enabled"), enabled)
        api_url = str(_block_get(block_obj, "NaloApiUrl", "api_url", "url") or api_url).strip() or api_url
        raw_key = _block_get(block_obj, "NaloApiKey", "auth_key", "api_key")
        if raw_key is not None and str(raw_key).strip():
            api_key = str(raw_key).strip()
        sender = (
            str(_block_get(block_obj, "NaloSenderId", "sender", "source") or sender).strip() or sender
        )
        dlr = _truthy(_block_get(block_obj, "RequestDeliveryReport", "dlr"), dlr)
        username = str(_block_get(block_obj, "username") or "").strip() or username
        password = str(_block_get(block_obj, "password") or "").strip() or password

    _apply(block)
    # Fill any gaps from the on-disk secrets file
    if not api_key:
        _apply(file_block)

    # Flat env / top-level secret fallbacks
    try:
        secrets = st.secrets
        api_key = api_key or str(secrets.get("NALO_API_KEY") or secrets.get("NALO_AUTH_KEY") or "").strip() or None
        sender = (
            str(secrets.get("NALO_SENDER_ID") or secrets.get("NALO_SENDER") or sender).strip()
            or sender
        )
        api_url = str(secrets.get("NALO_API_URL") or api_url).strip() or api_url
        if "NALO_ENABLED" in secrets:
            enabled = _truthy(secrets.get("NALO_ENABLED"), enabled)
    except Exception:  # noqa: BLE001
        pass

    if os.environ.get("NALO_ENABLED") is not None:
        enabled = _truthy(os.environ.get("NALO_ENABLED"), enabled)
    api_url = (os.environ.get("NALO_API_URL") or api_url).strip() or api_url
    api_key = (os.environ.get("NALO_API_KEY") or os.environ.get("NALO_AUTH_KEY") or api_key or "").strip() or None
    sender = (os.environ.get("NALO_SENDER_ID") or os.environ.get("NALO_SENDER") or sender).strip() or DEFAULT_SENDER
    username = username or (os.environ.get("NALO_USERNAME") or "").strip() or None
    password = password or (os.environ.get("NALO_PASSWORD") or "").strip() or None
    if os.environ.get("NALO_REQUEST_DLR") is not None:
        dlr = _truthy(os.environ.get("NALO_REQUEST_DLR"), dlr)

    return {
        "enabled": enabled,
        "api_url": api_url.rstrip("?") or DEFAULT_API_URL,
        "api_key": api_key,
        "sender": sender[:11],
        "dlr": dlr,
        "username": username,
        "password": password,
    }


def nalo_configured() -> bool:
    cfg = get_nalo_config()
    if not cfg.get("enabled"):
        return False
    if cfg.get("api_key"):
        return True
    return bool(cfg.get("username") and cfg.get("password"))


def to_nalo_destination(phone: str | None) -> str | None:
    """Normalize to Ghana-friendly MSISDN (233XXXXXXXXX) when possible."""
    if not phone:
        return None
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("233") and len(digits) >= 12:
        return digits
    if digits.startswith("0") and len(digits) >= 10:
        return "233" + digits[1:]
    if len(digits) == 9:
        return "233" + digits
    return digits


def _http_get(url: str, timeout: float = 20.0) -> tuple[int, str]:
    try:
        import httpx

        resp = httpx.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; league-predict/1.0)",
                "Accept": "*/*",
            },
            follow_redirects=True,
        )
        return resp.status_code, (resp.text or "").strip()
    except ImportError:
        from urllib.request import Request, urlopen

        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; league-predict/1.0)"})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
            return getattr(resp, "status", 200) or 200, body


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 20.0) -> tuple[int, str]:
    import json

    try:
        import httpx

        resp = httpx.post(
            url,
            json=payload,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; league-predict/1.0)",
                "Accept": "application/json,text/plain,*/*",
                "Content-Type": "application/json",
            },
            follow_redirects=True,
        )
        return resp.status_code, (resp.text or "").strip()
    except ImportError:
        from urllib.request import Request, urlopen

        raw = json.dumps(payload).encode("utf-8")
        req = Request(
            url,
            data=raw,
            method="POST",
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; league-predict/1.0)",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
            return getattr(resp, "status", 200) or 200, body


def _looks_successful(body: str, status_code: int) -> bool:
    if status_code >= 400:
        return False
    lower = (body or "").lower()
    if not body:
        return status_code < 300
    if any(code in body for code in ("1701", '"status":"success"', "'status':'success'")):
        return True
    if body.strip().isdigit() and body.strip() in {"1701", "0"}:
        return True
    if any(tok in lower for tok in ("error", "fail", "invalid", "denied", "insufficient", "unauthor")):
        if "success" not in lower and "submitted" not in lower:
            return False
    if "success" in lower or "submitted" in lower:
        return True
    return status_code < 300


def send_sms(destination: str, message: str) -> SmsResult:
    """Send one SMS via Nalo. Returns ok=False on API/config errors."""
    cfg = get_nalo_config()
    if not cfg.get("enabled"):
        return SmsResult(ok=False, skipped=True, message="Nalo SMS is disabled.")
    if not nalo_configured():
        return SmsResult(ok=False, skipped=True, message="Nalo SMS is not configured.")

    msisdn = to_nalo_destination(destination)
    if not msisdn:
        return SmsResult(ok=False, skipped=True, message="No valid phone number for SMS.")

    text = (message or "").strip()
    if not text:
        return SmsResult(ok=False, message="SMS message is empty.")

    api_url = str(cfg.get("api_url") or DEFAULT_API_URL)
    if not api_url.endswith("/"):
        # Keep trailing slash consistent with Nalo docs; query string still works either way
        pass
    sender = str(cfg.get("sender") or DEFAULT_SENDER)[:11]
    dlr_flag = "1" if cfg.get("dlr") else "0"

    payload: dict[str, Any] = {
        "destination": msisdn,
        "msisdn": msisdn,
        "message": text,
        "source": sender,
        "sender_id": sender,
        "type": 0,
        "dlr": int(dlr_flag),
    }
    if cfg.get("api_key"):
        payload["auth_key"] = cfg["api_key"]
        payload["api_key"] = cfg["api_key"]
    else:
        payload["username"] = cfg.get("username")
        payload["password"] = cfg.get("password")

    try:
        status_code, body = _http_post_json(api_url, payload)
        if _looks_successful(body, status_code):
            return SmsResult(ok=True, message="SMS sent.")
    except Exception:  # noqa: BLE001
        status_code, body = 0, ""

    params: dict[str, str] = {
        "type": "0",
        "destination": msisdn,
        "source": sender,
        "message": text,
        "dlr": dlr_flag,
    }
    if cfg.get("api_key"):
        params["auth_key"] = str(cfg["api_key"])
    else:
        params["username"] = str(cfg.get("username") or "")
        params["password"] = str(cfg.get("password") or "")

    sep = "&" if "?" in api_url else "?"
    url = api_url + sep + urlencode(params)
    try:
        status_code, body = _http_get(url)
    except Exception as exc:  # noqa: BLE001
        return SmsResult(ok=False, message=f"Nalo SMS request failed: {exc}")

    if _looks_successful(body, status_code):
        return SmsResult(ok=True, message="SMS sent.")
    snippet = (body or f"HTTP {status_code}")[:160]
    return SmsResult(ok=False, message=f"Nalo SMS rejected: {snippet}")


def payment_confirmation_message(*, week: int, season: str, amount_label: str = "GHS 50") -> str:
    return (
        f"League Predict: Payment of {amount_label} received. "
        f"Matchweek {week} ({season}) is unlocked across all leagues. Thank you!"
    )


def notify_payment_success(
    phone: str | None,
    *,
    week: int,
    season: str,
    amount_label: str = "GHS 50",
) -> SmsResult:
    """Send the post-payment SMS if Nalo + phone are available."""
    if not phone:
        return SmsResult(ok=False, skipped=True, message="Customer has no phone number on file.")
    if not nalo_configured():
        return SmsResult(ok=False, skipped=True, message="Nalo SMS is not configured.")
    return send_sms(
        phone,
        payment_confirmation_message(week=week, season=season, amount_label=amount_label),
    )
