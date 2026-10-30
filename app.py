from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from scripts.dashboard_data import PUBLIC_DASHBOARD_PATH, load_public_dashboard_data


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"


st.set_page_config(
    page_title="AgriLoss Rwanda | After harvest",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], #MainMenu { visibility: hidden; height: 0; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    iframe { position: fixed; inset: 0; width: 100%; height: 100%; border: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _website_html() -> str:
    html = INDEX.read_text(encoding="utf-8")
    assets = (
        (
            '<link rel="stylesheet" href="web/css/site.css?v=6">',
            ROOT / "web" / "css" / "site.css",
            "style",
        ),
        (
            '<script src="web/js/logic.js?v=6"></script>',
            ROOT / "web" / "js" / "logic.js",
            "script",
        ),
        (
            '<script src="web/js/site.js?v=6"></script>',
            ROOT / "web" / "js" / "site.js",
            "script",
        ),
    )
    for reference, asset_path, tag in assets:
        if reference not in html:
            raise ValueError(f"Could not find website asset reference: {reference}")
        asset = asset_path.read_text(encoding="utf-8")
        html = html.replace(reference, f"<{tag}>\n{asset}\n</{tag}>", 1)

    payload = json.dumps(load_public_dashboard_data(), ensure_ascii=False)
    injection = f"<script>window.AGRILOSS_DATA = {payload};</script>"
    data_placeholder = "<script>window.AGRILOSS_DATA = window.AGRILOSS_DATA || null;</script>"
    if data_placeholder not in html:
        raise ValueError("Could not find the public dashboard data placeholder")
    return html.replace(data_placeholder, injection, 1)


if not PUBLIC_DASHBOARD_PATH.is_file() or not INDEX.is_file():
    st.error("The public website files are missing.")
    st.stop()

try:
    components.html(_website_html(), height=920, scrolling=True)
except (OSError, ValueError, json.JSONDecodeError) as error:
    st.error(f"Could not load the website: {error}")
