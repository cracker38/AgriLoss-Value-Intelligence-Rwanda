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
            '<link rel="stylesheet" href="web/css/site.css?v=7">',
            ROOT / "web" / "css" / "site.css",
            "style",
        ),
        (
            '<script src="web/js/logic.js?v=7"></script>',
            ROOT / "web" / "js" / "logic.js",
            "script",
        ),
        (
            '<script src="web/js/site.js?v=8"></script>',
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
    html = html.replace(
        "<script>window.AGRILOSS_DATA = window.AGRILOSS_DATA || null;</script>",
        f"<script>window.AGRILOSS_DATA = {payload};</script>",
        1,
    )
    context_path = ROOT / "public_data" / "national_context.json"
    model_path = ROOT / "public_data" / "model_card.json"
    if context_path.is_file():
        html = html.replace(
            "<script>window.AGRILOSS_CONTEXT = window.AGRILOSS_CONTEXT || null;</script>",
            f"<script>window.AGRILOSS_CONTEXT = {context_path.read_text(encoding='utf-8')};</script>",
            1,
        )
    if model_path.is_file():
        html = html.replace(
            "<script>window.AGRILOSS_MODEL = window.AGRILOSS_MODEL || null;</script>",
            f"<script>window.AGRILOSS_MODEL = {model_path.read_text(encoding='utf-8')};</script>",
            1,
        )
    return html


if not PUBLIC_DASHBOARD_PATH.is_file() or not INDEX.is_file():
    st.error("The public website files are missing.")
    st.stop()

try:
    components.html(_website_html(), height=920, scrolling=True)
except (OSError, ValueError, json.JSONDecodeError) as error:
    st.error(f"Could not load the website: {error}")
