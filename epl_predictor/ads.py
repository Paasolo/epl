"""Google AdSense display units for Customer Predict-tab placements."""

from __future__ import annotations

import os

import streamlit as st
import streamlit.components.v1 as components

MUTED = "#93A0B5"
LINE = "#243049"
CARD = "#121A2B"


def get_adsense_config() -> dict[str, str | None]:
    client_id: str | None = None
    slot_top: str | None = None
    slot_bottom: str | None = None
    try:
        secrets = st.secrets
        if "adsense" in secrets:
            block = secrets["adsense"]
            client_id = str(block.get("client_id") or "").strip() or None
            slot_top = str(block.get("slot_top") or "").strip() or None
            slot_bottom = str(block.get("slot_bottom") or "").strip() or None
        if not client_id:
            client_id = str(secrets.get("ADSENSE_CLIENT_ID") or "").strip() or None
        if not slot_top:
            slot_top = str(secrets.get("ADSENSE_SLOT_TOP") or "").strip() or None
        if not slot_bottom:
            slot_bottom = str(secrets.get("ADSENSE_SLOT_BOTTOM") or "").strip() or None
    except Exception:  # noqa: BLE001
        pass
    client_id = client_id or (os.environ.get("ADSENSE_CLIENT_ID") or "").strip() or None
    slot_top = slot_top or (os.environ.get("ADSENSE_SLOT_TOP") or "").strip() or None
    slot_bottom = slot_bottom or (os.environ.get("ADSENSE_SLOT_BOTTOM") or "").strip() or None
    return {
        "client_id": client_id,
        "slot_top": slot_top,
        "slot_bottom": slot_bottom,
    }


def adsense_client_configured() -> bool:
    """True when a real ca-pub- publisher ID is set (enough for site script)."""
    client = get_adsense_config().get("client_id") or ""
    return bool(client.startswith("ca-pub-") and "xxxx" not in client.lower())


def adsense_configured() -> bool:
    """True when publisher ID and at least one ad slot are set."""
    if not adsense_client_configured():
        return False
    cfg = get_adsense_config()
    top = (cfg.get("slot_top") or "").strip()
    bottom = (cfg.get("slot_bottom") or "").strip()
    return bool(
        (top and not top.startswith("#"))
        or (bottom and not bottom.startswith("#"))
    )


def inject_adsense_site_script() -> None:
    """Inject the AdSense site script Google asks for (into document head).

    Streamlit has no editable <head>, so we append the official script there via JS.
    Call this on the public sign-in page so Google can crawl it for site approval.
    """
    if not adsense_client_configured():
        return
    if st.session_state.get("_adsense_site_script_injected"):
        return
    client_id = get_adsense_config()["client_id"]
    st.markdown(
        f"""
        <script>
        (function () {{
          if (document.querySelector('script[data-adsense-site="1"]')) return;
          var s = document.createElement('script');
          s.async = true;
          s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}';
          s.crossOrigin = 'anonymous';
          s.setAttribute('data-adsense-site', '1');
          document.head.appendChild(s);
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_adsense_site_script_injected"] = True


def render_adsense_unit(slot_id: str | None, *, key: str, height: int = 120) -> None:
    """Render one AdSense display unit. No-op if client/slot missing."""
    cfg = get_adsense_config()
    client_id = cfg.get("client_id")
    slot = (slot_id or "").strip()
    if not client_id or not slot or "xxxx" in client_id.lower() or slot.startswith("#"):
        return

    st.caption("Advertisement")
    html = f"""
    <div style="
      width:100%;
      min-height:{height}px;
      background:{CARD};
      border:1px solid {LINE};
      border-radius:12px;
      overflow:hidden;
      display:flex;
      align-items:center;
      justify-content:center;
    ">
      <script async
        src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}"
        crossorigin="anonymous"></script>
      <ins class="adsbygoogle"
           style="display:block;width:100%;min-height:{height}px;"
           data-ad-client="{client_id}"
           data-ad-slot="{slot}"
           data-ad-format="horizontal"
           data-full-width-responsive="true"></ins>
      <script>
        try {{ (adsbygoogle = window.adsbygoogle || []).push({{}}); }}
        catch (e) {{}}
      </script>
    </div>
    <div style="color:{MUTED};font-size:0.75rem;margin-top:0.25rem;text-align:center;">
      Ads may take a moment to load and may not fill on localhost or unapproved domains.
    </div>
    """
    components.html(html, height=height + 36, scrolling=False)


def render_predict_top_ad() -> None:
    cfg = get_adsense_config()
    if not adsense_configured():
        return
    render_adsense_unit(cfg.get("slot_top"), key="adsense_predict_top", height=100)


def render_predict_bottom_ad() -> None:
    cfg = get_adsense_config()
    if not adsense_configured():
        return
    slot = cfg.get("slot_bottom") or cfg.get("slot_top")
    render_adsense_unit(slot, key="adsense_predict_bottom", height=100)
