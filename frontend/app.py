import os
import re
from html import escape

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from pathlib import Path
import base64

# ==========================================================
# CONFIGURATION
# ==========================================================

BACKEND_URL = "http://127.0.0.1:8000"

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(FRONTEND_DIR, "assets")


def find_existing_file(*relative_paths):
    """Return the first existing file from the supplied paths."""
    for relative_path in relative_paths:
        path = os.path.join(FRONTEND_DIR, relative_path)
        if os.path.exists(path):
            return path
    return None


# Robust logo lookup.
LOGO_PATH = find_existing_file(
    "assets/razorpulse_logo.png",
    "razorpulse_logo.png",
    "assets/logo.png",
    "logo.png",
)

LOGO_MARK_PATH = find_existing_file(
    "assets/razorpulse_logo_mark.png",
    "razorpulse_logo_mark.png",
    "assets/logo_mark.png",
    "logo_mark.png",
)

def image_to_data_uri(path):
    if not path:
        return None

    path = Path(path)

    if not path.exists():
        return None

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }

    mime = mime_types.get(path.suffix.lower(), "image/png")

    data = base64.b64encode(path.read_bytes()).decode("utf-8")

    return f"data:{mime};base64,{data}"

PAGE_ICON = LOGO_MARK_PATH if LOGO_MARK_PATH else "⚡"


st.set_page_config(
    page_title="RazorPulse",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# SESSION STATE
# ==========================================================

if "page" not in st.session_state:
    st.session_state.page = "Overview"

if "last_recovery_result" not in st.session_state:
    st.session_state.last_recovery_result = None

if "last_recovery_mode" not in st.session_state:
    st.session_state.last_recovery_mode = None

if "last_ai_result" not in st.session_state:
    st.session_state.last_ai_result = None

if "last_ai_payment_id" not in st.session_state:
    st.session_state.last_ai_payment_id = None


# ==========================================================
# HTML RENDER HELPER
# ==========================================================

def render_html(content):
    html = content.strip()

    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


# ==========================================================
# GLOBAL CSS
# ==========================================================

render_html(
    """
<style>

:root {
    --rp-radius: 18px;
    --rp-shadow: 0 10px 30px rgba(15,23,42,0.08);
}

/* ======================================================
   GLOBAL
   ====================================================== */

html,
body,
[class*="css"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    font-weight: 550;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Make normal Streamlit text readable and slightly bolder */
.stMarkdown,
.stText,
.stCaption,
p,
label,
div {
    line-height: 1.5;
    font-weight: 550;
}

/* ======================================================
   PAGE HEADER
   ====================================================== */

.page-header {
    margin-bottom: 30px;
}

.page-kicker {
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em;
    color: #6366f1 !important;
    margin-bottom: 7px;
    text-transform: uppercase;
}

.page-title {
    font-size: 38px !important;
    line-height: 1.12 !important;
    font-weight: 600 !important;
    letter-spacing: -0.035em;
    color: var(--text-color) !important;
}

.page-subtitle {
    font-size: 16px !important;
    line-height: 1.6 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    margin-top: 8px;
    max-width: 850px;
}


/* ======================================================
   SIDEBAR
   ====================================================== */

section[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] > div {
    background: #111827 !important;
}

section[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}

.sidebar-brand {
     padding: 4px 0 20px 0;
    text-align: center;
}

.sidebar-logo {
    width: 190px;
    max-width: 100%;
    height: auto;
    margin: 4px auto 12px auto;
    display: block;
}

.sidebar-fallback-logo {
    width: 68px;
    height: 68px;
    margin: 4px auto 15px auto;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(
        135deg,
        #6366f1,
        #8b5cf6
    );
    color: white !important;
    font-size: 30px;
    font-weight: 600;
    box-shadow: 0 8px 20px rgba(99,102,241,0.3);
}

.sidebar-title {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.7px;
    line-height: 1.15;
    margin-top: 2px;

    background: linear-gradient(
        90deg,
        #7c3aed 0%,
        #6366f1 50%,
        #2563eb 100%
    );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.sidebar-subtitle {
    margin-top: 7px;
    font-size: 11px !important;
    color: #94a3b8 !important;
    line-height: 1.45 !important;
    font-weight: 400 !important;
}

.sidebar-divider {
    height: 1px;
     background: rgba(148, 163, 184, 0.16);
    margin-top: 19px;
}

.sidebar-status {
    margin-top: 22px;
    padding: 15px 16px;
    border-radius: 14px;
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.sidebar-status-title {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #f8fafc !important;
}

.sidebar-status-text {
    margin-top: 5px;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
}

.sidebar-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 7px;
    background: #22c55e;
}

.sidebar-dot.offline {
    background: #ef4444;
}

/* Sidebar radio */
section[data-testid="stSidebar"]
div[role="radiogroup"] {
    gap: 6px !important;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label {
    border-radius: 11px !important;
    padding: 11px 12px !important;
    min-height: 44px !important;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label p {
    font-size: 15px !important;
    font-weight: 650 !important;
    color: #cbd5e1 !important;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label:has(input:checked) {
    background: rgba(99,102,241,0.22) !important;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label:has(input:checked) p {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Hide image controls completely */
[data-testid="stImage"] button,
[data-testid="stImage"] [role="button"],
[data-testid="stImageToolbar"] {
    display: none !important;
}

/* ======================================================
   SECTION TITLES
   ====================================================== */

.section-title {
    font-size: 22px !important;
    line-height: 1.25 !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
    margin-top: 28px;
    margin-bottom: 5px;
}

.section-subtitle {
    font-size: 14px !important;
    line-height: 1.55 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    margin-bottom: 16px;
}


/* ======================================================
   GENERAL CARDS
   ====================================================== */

.rp-card {
    padding: 21px 22px;
    min-height: 125px;
    border-radius: var(--rp-radius);
    border: 1px solid rgba(100,116,139,0.17);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
}

.rp-label {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    text-transform: uppercase;
    letter-spacing: 0.055em;
}

.rp-value {
    margin-top: 8px;
    font-size: 31px !important;
    line-height: 1.15 !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.rp-sub {
    margin-top: 7px;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}


/* ======================================================
   KPI CARDS
   ====================================================== */

.rp-kpi {
    padding: 22px 22px;
    min-height: 145px;
    border-radius: 18px;
    border: 1px solid rgba(100,116,139,0.17);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
    position: relative;
    overflow: hidden;
}

.rp-kpi-label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

.rp-kpi-value {
    margin-top: 9px;
    font-size: 32px !important;
    line-height: 1.1 !important;
    font-weight: 900 !important;
    color: var(--text-color) !important;
}

.rp-kpi-sub {
    margin-top: 8px;
    font-size: 13px !important;
    line-height: 1.4 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}


/* ======================================================
   HERO
   ====================================================== */

.rp-hero {
    padding: 28px 30px;
    margin: 8px 0 25px 0;
    border-radius: 20px;
    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,0.13),
            rgba(139,92,246,0.06)
        );
    border: 1px solid rgba(99,102,241,0.18);
    box-shadow: var(--rp-shadow);
}

.rp-hero-kicker {
    font-size: 12px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6366f1 !important;
}

.rp-hero-title {
    margin-top: 6px;
    font-size: 27px !important;
    font-weight: 700 !important;
    color: var(--text-color) !important;
}

.rp-hero-sub {
    margin-top: 8px;
    font-size: 15px !important;
    line-height: 1.6 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    max-width: 850px;
}


/* ======================================================
   INFO BOXES
   ====================================================== */

.info-box {
    padding: 18px 20px;
    margin: 16px 0;
    border-radius: 15px;
    border: 1px solid rgba(100,116,139,0.17);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
}

.info-title {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.info-text {
    margin-top: 6px;
    font-size: 14px !important;
    line-height: 1.65 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.info-text strong {
    font-weight: 600 !important;
    color: var(--text-color) !important;
}


/* ======================================================
   FAILED PAYMENT CARDS
   ====================================================== */

.payment-card {
    padding: 20px 22px;
    margin-bottom: 13px;
    border-radius: 17px;
    border: 1px solid rgba(100,116,139,0.16);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
}

.payment-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 15px;
}

.payment-customer {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.payment-id {
    margin-top: 4px;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.payment-amount {
    font-size: 22px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
    white-space: nowrap;
}

.payment-reason {
    margin-top: 12px;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.payment-reason strong {
    font-weight: 800 !important;
}

.payment-meta {
    margin-top: 8px;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}


/* ======================================================
   BADGES / PILLS
   ====================================================== */

.risk-pill,
.badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.risk-high {
    color: #b91c1c !important;
    background: rgba(239,68,68,0.13);
}

.risk-medium {
    color: #a16207 !important;
    background: rgba(234,179,8,0.15);
}

.risk-low {
    color: #047857 !important;
    background: rgba(16,185,129,0.13);
}

.badge-ai {
    background: rgba(139,92,246,0.15);
    color: #7c3aed !important;
}

.badge-success {
    background: rgba(16,185,129,0.14);
    color: #047857 !important;
}

.badge-recovery {
    background: rgba(59,130,246,0.14);
    color: #2563eb !important;
}

.badge-system {
    background: rgba(100,116,139,0.14);
    color: #475569 !important;
}


/* ======================================================
   RECOVERY
   ====================================================== */

.recovery-workflow {
    padding: 25px;
    margin-top: 15px;
    border-radius: 20px;
    border: 1px solid rgba(99,102,241,0.18);
    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,0.08),
            rgba(59,130,246,0.04)
        );
    box-shadow: var(--rp-shadow);
}

.recovery-workflow-title {
    font-size: 23px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.recovery-workflow-sub {
    margin-top: 6px;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.selected-payment-name {
    margin-top: 20px;
    font-size: 19px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.selected-payment-id {
    margin-top: 4px;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.selected-payment-amount {
    margin-top: 13px;
    font-size: 31px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.decision-card {
    padding: 22px;
    margin-top: 18px;
    border-radius: 17px;
    border: 1px solid rgba(100,116,139,0.16);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
}

.decision-title {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.decision-copy {
    margin-top: 8px;
    font-size: 15px !important;
    line-height: 1.65 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.decision-copy strong {
    font-weight: 600 !important;
}

.confidence {
    margin-top: 8px;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #6366f1 !important;
}

.success-recovery {
    padding: 20px;
    margin-top: 18px;
    border-radius: 17px;
    border: 1px solid rgba(16,185,129,0.25);
    background: rgba(16,185,129,0.09);
    box-shadow: var(--rp-shadow);
}

.success-title {
    font-size: 19px !important;
    font-weight: 600 !important;
    color: #047857 !important;
}


/* ======================================================
   AI PAGE
   ====================================================== */

.ai-page-hero {
    padding: 30px;
    border-radius: 21px;
    margin: 8px 0 28px 0;
    border: 1px solid rgba(139,92,246,0.2);
    background:
        linear-gradient(
            135deg,
            rgba(99,102,241,0.14),
            rgba(139,92,246,0.08),
            rgba(59,130,246,0.05)
        );
    box-shadow: var(--rp-shadow);
}

.ai-kicker {
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #7c3aed !important;
}

.ai-title {
    margin-top: 7px;
    font-size: 29px !important;
    line-height: 1.2 !important;
    font-weight: 900 !important;
    color: var(--text-color) !important;
}

.ai-subtitle {
    margin-top: 9px;
    font-size: 15px !important;
    line-height: 1.65 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
    max-width: 920px;
}

/* ==========================================================
   AI INSIGHTS
   ========================================================== */

.ai-insight-stack {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-top: 18px;
}

.ai-insight-card {
    padding: 22px 26px;
    border-radius: 16px;
    border: 1px solid rgba(99, 102, 241, 0.20);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
    transition: border-color 0.2s ease;
}

.ai-insight-card:hover {
    border-color: rgba(99, 102, 241, 0.38);
}

.ai-insight-top {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 10px;
}

.ai-insight-number {
    width: 30px;
    height: 30px;
    min-width: 30px;
    border-radius: 9px;

    display: flex;
    align-items: center;
    justify-content: center;

    background: rgba(99, 102, 241, 0.14);
    color: #818cf8;

    font-size: 11px !important;
    font-weight: 600 !important;
}

.ai-insight-label {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #818cf8 !important;
}

.ai-insight-heading {
    margin-top: 4px;
    font-size: 19px !important;
    line-height: 1.35 !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.ai-insight-copy {
    margin-top: 8px;
    font-size: 14px !important;
    line-height: 1.7 !important;

    /* Reduced from 600 */
    font-weight: 400 !important;

    color: var(
        --secondary-text-color,
        #64748b
    ) !important;
}

.ai-insight-copy strong {
    font-weight: 600 !important;
    color: var(--text-color) !important;
}


/* AI recommendation */
.ai-recommendation-card {
    padding: 28px;
    margin-top: 15px;
    border-radius: 21px;
    border: 1px solid rgba(124,58,237,0.25);
    background:
        linear-gradient(
            135deg,
            rgba(124,58,237,0.13),
            rgba(99,102,241,0.07)
        );
    box-shadow: var(--rp-shadow);
}

.ai-recommendation-kicker {
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #7c3aed !important;
}

.ai-recommendation-action {
    margin-top: 8px;
    font-size: 28px !important;
    line-height: 1.2 !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.ai-recommendation-why {
    margin-top: 13px;
    font-size: 15px !important;
    line-height: 1.7 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.ai-recommendation-why strong {
    font-weight: 800 !important;
    color: var(--text-color) !important;
}

.ai-meta-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 22px;
}

.ai-meta {
    padding: 14px;
    border-radius: 13px;
    background: rgba(255,255,255,0.35);
    border: 1px solid rgba(100,116,139,0.13);
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.ai-meta-label {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #d6d7e0 !important;
    text-transform: uppercase;
}

.ai-meta-value {
    margin-top: 5px;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}


/* ======================================================
   AUDIT
   ====================================================== */

.audit-card {
    padding: 20px 22px;
    margin-bottom: 12px;
    border-radius: 17px;
    border: 1px solid rgba(100,116,139,0.15);
    background: var(--secondary-background-color);
    box-shadow: var(--rp-shadow);
}

.audit-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
}

.audit-event {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.audit-time {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}

.audit-message {
    margin-top: 12px;
    font-size: 15px !important;
    line-height: 1.6 !important;
    font-weight: 600 !important;
    color: var(--text-color) !important;
}

.audit-detail {
    margin-top: 7px;
    font-size: 13px !important;
    line-height: 1.5 !important;
    font-weight: 600 !important;
    color: var(--secondary-text-color, #64748b) !important;
}


/* ======================================================
   STREAMLIT CONTROLS
   ====================================================== */

div[data-baseweb="select"] *,
div[data-baseweb="input"] *,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    font-size: 15px !important;
    font-weight: 600 !important;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stRadio"] label,
div[data-testid="stNumberInput"] label {
    font-size: 14px !important;
    font-weight: 600 !important;
}

div[role="radiogroup"] {
    gap: 10px !important;
}

div[role="radiogroup"] label p {
    font-size: 15px !important;
    font-weight: 600 !important;
}

button[kind="primary"],
button[kind="secondary"] {
    min-height: 46px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
}

button[kind="primary"] p,
button[kind="secondary"] p {
    font-size: 15px !important;
    font-weight: 600 !important;
}


/* ======================================================
   METRICS
   ====================================================== */

div[data-testid="stMetricLabel"] {
    font-size: 13px !important;
    font-weight: 700 !important;
}

div[data-testid="stMetricValue"] {
    font-size: 29px !important;
    font-weight: 700 !important;
}

div[data-testid="stMetricDelta"] {
    font-size: 13px !important;
    font-weight: 700 !important;
}


/* ======================================================
   DATAFRAMES
   ====================================================== */

div[data-testid="stDataFrame"] {
    font-size: 14px !important;
    box-shadow: var(--rp-shadow);
    border-radius: var(--rp-radius);
    overflow: hidden;
}

div[data-testid="stDataFrame"] [role="gridcell"],
div[data-testid="stDataFrame"] [role="columnheader"] {
    font-size: 14px !important;
    font-weight: 600 !important;
}

div[data-testid="stDataFrame"] [role="columnheader"] {
    font-weight: 700 !important;
}


/* ======================================================
   RESPONSIVE
   ====================================================== */

@media (max-width: 900px) {

    .page-title {
        font-size: 31px !important;
    }

    .ai-title {
        font-size: 24px !important;
    }

    .ai-meta-grid {
        grid-template-columns: repeat(2, 1fr);
    }

}

@media (max-width: 600px) {

    .page-title {
        font-size: 28px !important;
    }

    .page-subtitle {
        font-size: 14px !important;
    }

    .ai-meta-grid {
        grid-template-columns: 1fr;
    }

}

</style>
"""
)


# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def safe_number(value, default=0):
    try:
        if value is None:
            return default

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, str):
            value = (
                value.replace("₹", "")
                .replace(",", "")
                .strip()
            )

        return float(value)
    except (TypeError, ValueError):
        return default


def money(value):
    amount = safe_number(value)
    return f"₹{amount:,.2f}"


def compact_money(value):
    amount = safe_number(value)

    if abs(amount) >= 1_000_000:
        return f"₹{amount / 1_000_000:.1f}M"

    if abs(amount) >= 1000:
        return f"₹{amount / 1000:.1f}K"

    return f"₹{amount:,.0f}"


def first_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


def normalize_list(data):
    if data is None:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in (
            "data",
            "items",
            "results",
            "payments",
            "recoveries",
            "risks",
            "logs",
            "audit_logs",
        ):
            if isinstance(data.get(key), list):
                return data[key]

        return [data]

    return []


def display_text(value, default="-"):
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def humanize(value):
    text = display_text(value, "")

    if not text:
        return "-"

    text = text.replace("_", " ")
    text = text.replace("-", " ")

    return " ".join(word.capitalize() for word in text.split())


def risk_class(level):
    level = str(level).upper()

    if level == "HIGH":
        return "risk-high"

    if level == "MEDIUM":
        return "risk-medium"

    return "risk-low"


def risk_pill(level):
    clean_level = str(level).upper()

    return (
        f'<span class="risk-pill {risk_class(clean_level)}">'
        f'{escape(clean_level)}'
        f'</span>'
    )


# ==========================================================
# API HELPERS
# ==========================================================

def api_get(endpoint):
    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        return None

    except requests.exceptions.Timeout:
        return None

    except requests.exceptions.RequestException:
        return None

    except ValueError:
        return None


def api_post(endpoint, payload):
    try:
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json=payload,
            timeout=20,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            "Unable to connect to the FastAPI backend."
        )
        return None

    except requests.exceptions.Timeout:
        st.error(
            "The backend request timed out."
        )
        return None

    except requests.exceptions.HTTPError as exc:
        try:
            detail = response.json()
        except Exception:
            detail = str(exc)

        st.error(
            f"Backend request failed: {detail}"
        )
        return None

    except requests.exceptions.RequestException as exc:
        st.error(
            f"Request failed: {exc}"
        )
        return None

    except ValueError:
        st.error(
            "The backend returned an invalid JSON response."
        )
        return None


# ==========================================================
# DATA LOADERS
# ==========================================================

def load_failed_payments():
    return normalize_list(
        api_get("/api/failed-payments")
    )


def load_recovery_attempts():
    return normalize_list(
        api_get("/api/recovery-attempts")
    )


def load_risk_analysis():
    return normalize_list(
        api_get("/api/risk-analysis")
    )


def load_audit_logs():
    return normalize_list(
        api_get("/api/audit-logs")
    )


# ==========================================================
# BACKEND HEALTH
# ==========================================================

def backend_is_healthy():
    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=3,
        )

        return response.ok

    except Exception:
        return False


# ==========================================================
# PAGE HEADER
# ==========================================================

def page_header(
    title,
    subtitle,
    kicker="RAZORPULSE",
):
    render_html(
        f"""
        <div class="page-header">

            <div class="page-kicker">
                {escape(kicker)}
            </div>

            <div class="page-title">
                {escape(title)}
            </div>

            <div class="page-subtitle">
                {escape(subtitle)}
            </div>

        </div>
        """
    )


def image_to_data_uri(path):
    if not path:
        return None

    path = Path(path)

    if not path.exists():
        return None

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }

    mime = mime_types.get(path.suffix.lower(), "image/png")

    data = base64.b64encode(path.read_bytes()).decode("utf-8")

    return f"data:{mime};base64,{data}"


# ==========================================================
# SIDEBAR
# ==========================================================

def render_sidebar():

    with st.sidebar:

        # --------------------------------------------------
        # LOGO - CENTERED
        # --------------------------------------------------

        if LOGO_PATH:

            logo_left, logo_center, logo_right = st.columns(
                [1, 2, 1]
            )

            with logo_center:

                logo_uri = image_to_data_uri(LOGO_PATH)

                if logo_uri:
                    st.markdown(
                        f"""
                        <div class="sidebar-logo-wrap">
                            <img
                                src="{logo_uri}"
                                class="sidebar-logo"
                            >
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        elif LOGO_MARK_PATH:

            logo_left, logo_center, logo_right = st.columns(
                [1, 2, 1]
            )

            with logo_center:

                logo_uri = image_to_data_uri(LOGO_MARK_PATH)

                if logo_uri:
                    st.markdown(
                        f"""
                        <div class="sidebar-logo-wrap">
                            <img
                                src="{logo_uri}"
                                class="sidebar-logo sidebar-logo-mark"
                            >
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        else:

            render_html(
                """
                <div class="sidebar-fallback-logo">
                    R
                </div>
                """
            )

        # --------------------------------------------------
        # BRAND NAME
        # --------------------------------------------------

        render_html(
            """
            <div class="sidebar-brand">

                <div class="sidebar-title">
                    RazorPulse
                </div>

                <div class="sidebar-subtitle">
                    AI-powered payment<br>
                    intelligence
                </div>

                <div class="sidebar-divider"></div>

            </div>
            """
        )

        # --------------------------------------------------
        # UNIFIED NAVIGATION
        # --------------------------------------------------

        pages = [
            "Overview",
            "Failed Payments",
            "Recovery",
            "Risk Analysis",
            "AI Insights",
            "Audit Logs",
            "Settings",
        ]

        selected_page = st.radio(
            "Navigation",
            pages,
            index=pages.index(
                st.session_state.page
            )
            if st.session_state.page in pages
            else 0,
            label_visibility="collapsed",
        )

        st.session_state.page = selected_page

        # --------------------------------------------------
        # BACKEND STATUS
        # --------------------------------------------------

        healthy = backend_is_healthy()

        if healthy:

            render_html(
                """
                <div class="sidebar-status">

                    <div class="sidebar-status-title">
                        <span class="sidebar-dot"></span>
                        Backend connected
                    </div>

                    <div class="sidebar-status-text">
                        FastAPI is responding normally.
                    </div>

                </div>
                """
            )

        else:

            render_html(
                """
                <div class="sidebar-status">

                    <div class="sidebar-status-title">
                        <span class="sidebar-dot offline"></span>
                        Backend offline
                    </div>

                    <div class="sidebar-status-text">
                        Start FastAPI to use live features.
                    </div>

                </div>
                """
            )


render_sidebar()

# ==========================================================
# OVERVIEW
# ==========================================================

def overview_page():

    page_header(
        "Executive Dashboard",
        "A real-time view of payment failures, recovery performance and revenue exposure.",
        "EXECUTIVE OVERVIEW",
    )

    payments = load_failed_payments()
    recoveries = load_recovery_attempts()
    risks = load_risk_analysis()

    if not payments:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    No payment data available
                </div>

                <div class="info-text">
                    The dashboard is connected, but no failed
                    payment records have been returned by the backend yet.
                </div>

            </div>
            """
        )

        return

    # ------------------------------------------------------
    # CALCULATIONS
    # ------------------------------------------------------

    failed_revenue = sum(
        safe_number(
            first_value(
                payment,
                "amount",
                "invoice_amount",
                default=0,
            )
        )
        for payment in payments
    )

    recovered_revenue = sum(
        safe_number(
            first_value(
                recovery,
                "amount_recovered",
                "recovered_amount",
                default=0,
            )
        )
        for recovery in recoveries
    )

    outstanding = max(
        failed_revenue - recovered_revenue,
        0,
    )

    recovery_rate = (
        (recovered_revenue / failed_revenue) * 100
        if failed_revenue > 0
        else 0
    )

    # ------------------------------------------------------
    # KPI CARDS
    # ------------------------------------------------------

    cols = st.columns(4)

    with cols[0]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    Revenue at Risk
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(failed_revenue))}
                </div>

                <div class="rp-kpi-sub">
                    Failed payment exposure
                </div>

            </div>
            """
        )

    with cols[1]:

        render_html(
            f"""
            <div class="rp-kpi green">

                <div class="rp-kpi-label">
                    Money Recovered
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(recovered_revenue))}
                </div>

                <div class="rp-kpi-sub">
                    Successfully recovered
                </div>

            </div>
            """
        )

    with cols[2]:

        render_html(
            f"""
            <div class="rp-kpi blue">

                <div class="rp-kpi-label">
                    Outstanding Exposure
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(outstanding))}
                </div>

                <div class="rp-kpi-sub">
                    Remaining revenue exposure
                </div>

            </div>
            """
        )

    with cols[3]:

        render_html(
            f"""
            <div class="rp-kpi purple">

                <div class="rp-kpi-label">
                    Recovery Rate
                </div>

                <div class="rp-kpi-value">
                    {recovery_rate:.1f}%
                </div>

                <div class="rp-kpi-sub">
                    Across recorded recovery attempts
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # HERO
    # ------------------------------------------------------

    render_html(
        """
        <div class="rp-hero">

            <div class="rp-hero-kicker">
                Revenue protection
            </div>

            <div class="rp-hero-title">
                Turn failed payments into recoverable revenue
            </div>

            <div class="rp-hero-sub">
                RazorPulse combines payment failure signals,
                risk intelligence and recovery strategies to
                help operators prioritize the revenue that needs attention.
            </div>

        </div>
        """
    )

    # ------------------------------------------------------
    # CHARTS
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Revenue Recovery Performance
        </div>

        <div class="section-subtitle">
            Compare exposure against the money successfully recovered.
        </div>
        """
    )

    chart_col1, chart_col2 = st.columns(2)

    # Risk distribution
    with chart_col1:

        risk_counts = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

        for risk in risks:

            level = str(
                first_value(
                    risk,
                    "risk_level",
                    default="UNKNOWN",
                )
            ).upper()

            if level in risk_counts:
                risk_counts[level] += 1

        risk_df = pd.DataFrame(
            {
                "Risk Level": list(
                    risk_counts.keys()
                ),
                "Payments": list(
                    risk_counts.values()
                ),
            }
        )

        fig = px.pie(
            risk_df,
            names="Risk Level",
            values="Payments",
            hole=0.58,
        )

        fig.update_layout(
            title="Risk Distribution",
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # Recovery performance
    with chart_col2:

        recovery_chart_df = pd.DataFrame(
            {
                "Metric": [
                    "Failed Revenue",
                    "Recovered",
                    "Outstanding",
                ],
                "Amount": [
                    failed_revenue,
                    recovered_revenue,
                    outstanding,
                ],
            }
        )

        fig = px.bar(
            recovery_chart_df,
            x="Metric",
            y="Amount",
            text="Amount",
        )

        fig.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
        )

        fig.update_layout(
            title="Recovery Performance",
            height=350,
            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # ------------------------------------------------------
    # RECENT PAYMENTS
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Recent Failed Payments
        </div>

        <div class="section-subtitle">
            Payments currently contributing to revenue exposure.
        </div>
        """
    )

    rows = []

    for payment in payments[:10]:

        payment_id = first_value(
            payment,
            "payment_id",
            default="-",
        )

        risk_record = next(
            (
                r
                for r in risks
                if first_value(
                    r,
                    "payment_id",
                    default=None,
                )
                == payment_id
            ),
            {},
        )

        risk_level = str(
            first_value(
                risk_record,
                "risk_level",
                default="UNKNOWN",
            )
        ).upper()

        rows.append(
            {
                "Payment ID": payment_id,
                "Invoice": first_value(
                    payment,
                    "invoice_id",
                    default="-",
                ),
                "Customer": first_value(
                    payment,
                    "customer",
                    "customer_name",
                    default="-",
                ),
                "Amount": money(
                    first_value(
                        payment,
                        "amount",
                        "invoice_amount",
                        default=0,
                    )
                ),
                "Failure Reason": humanize(
                    first_value(
                        payment,
                        "failure_reason",
                        default="-",
                    )
                ),
                "Risk": risk_level,
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


# ==========================================================
# FAILED PAYMENTS
# ==========================================================

def failed_payments_page():

    page_header(
        "Failed Payments",
        "Review failed transactions and prioritize the revenue that needs intervention.",
        "PAYMENT OPERATIONS",
    )

    payments = load_failed_payments()
    risks = load_risk_analysis()

    if not payments:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    No failed payments found
                </div>

                <div class="info-text">
                    The backend has not returned any failed payment records.
                </div>

            </div>
            """
        )

        return

    # ------------------------------------------------------
    # KPI
    # ------------------------------------------------------

    total_exposure = sum(
        safe_number(
            first_value(
                payment,
                "amount",
                "invoice_amount",
                default=0,
            )
        )
        for payment in payments
    )

    high_risk = 0

    for risk in risks:

        if (
            str(
                first_value(
                    risk,
                    "risk_level",
                    default="",
                )
            ).upper()
            == "HIGH"
        ):
            high_risk += 1

    cols = st.columns(3)

    with cols[0]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    Failed Payments
                </div>

                <div class="rp-kpi-value">
                    {len(payments)}
                </div>

                <div class="rp-kpi-sub">
                    Transactions requiring attention
                </div>

            </div>
            """
        )

    with cols[1]:

        render_html(
            f"""
            <div class="rp-kpi blue">

                <div class="rp-kpi-label">
                    Revenue Exposure
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(total_exposure))}
                </div>

                <div class="rp-kpi-sub">
                    Combined failed payment amount
                </div>

            </div>
            """
        )

    with cols[2]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    High Risk
                </div>

                <div class="rp-kpi-value">
                    {high_risk}
                </div>

                <div class="rp-kpi-sub">
                    Highest-priority payment exposures
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # HERO
    # ------------------------------------------------------

    render_html(
        """
        <div class="rp-hero">

            <div class="rp-hero-kicker">
                Revenue protection queue
            </div>

            <div class="rp-hero-title">
                Payments that need attention
            </div>

            <div class="rp-hero-sub">
                Identify failure patterns, understand risk and
                move high-value failed payments into the recovery workflow.
            </div>

        </div>
        """
    )

    # ------------------------------------------------------
    # FAILURE PROFILE
    # ------------------------------------------------------

    reason_counts = {}

    for payment in payments:

        reason = humanize(
            first_value(
                payment,
                "failure_reason",
                default="Unknown",
            )
        )

        reason_counts[reason] = (
            reason_counts.get(reason, 0) + 1
        )

    render_html(
        """
        <div class="section-title">
            Failure Profile
        </div>

        <div class="section-subtitle">
            Most common reasons behind failed transactions.
        </div>
        """
    )

    if reason_counts:

        profile_cols = st.columns(
            min(4, len(reason_counts))
        )

        for index, (reason, count) in enumerate(
            list(reason_counts.items())[:4]
        ):

            with profile_cols[index]:

                render_html(
                    f"""
                    <div class="rp-card">

                        <div class="rp-label">
                            Failure reason
                        </div>

                        <div class="rp-value"
                             style="font-size:25px !important;">
                            {count}
                        </div>

                        <div class="rp-sub">
                            {escape(reason)}
                        </div>

                    </div>
                    """
                )

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

    search = st.text_input(
        "Search payments",
        placeholder=(
            "Search by customer, payment ID, invoice or failure reason..."
        ),
    )

    filtered_payments = payments

    if search.strip():

        query = search.lower().strip()

        filtered_payments = [
            payment
            for payment in payments
            if query in str(
                first_value(
                    payment,
                    "customer",
                    "customer_name",
                    default="",
                )
            ).lower()
            or query in str(
                first_value(
                    payment,
                    "payment_id",
                    default="",
                )
            ).lower()
            or query in str(
                first_value(
                    payment,
                    "invoice_id",
                    default="",
                )
            ).lower()
            or query in str(
                first_value(
                    payment,
                    "failure_reason",
                    default="",
                )
            ).lower()
        ]

    # ------------------------------------------------------
    # PAYMENT CARDS
    # ------------------------------------------------------

    render_html(
        f"""
        <div class="section-title">
            Payment Queue
        </div>

        <div class="section-subtitle">
            Showing {len(filtered_payments)} payment(s).
        </div>
        """
    )

    for payment in filtered_payments:

        payment_id = first_value(
            payment,
            "payment_id",
            default="-",
        )

        customer = first_value(
            payment,
            "customer",
            "customer_name",
            default="-",
        )

        invoice = first_value(
            payment,
            "invoice_id",
            default="-",
        )

        amount = safe_number(
            first_value(
                payment,
                "amount",
                "invoice_amount",
                default=0,
            )
        )

        reason = humanize(
            first_value(
                payment,
                "failure_reason",
                default="Unknown",
            )
        )

        risk_record = next(
            (
                r
                for r in risks
                if first_value(
                    r,
                    "payment_id",
                    default=None,
                )
                == payment_id
            ),
            {},
        )

        risk_level = str(
            first_value(
                risk_record,
                "risk_level",
                default="UNKNOWN",
            )
        ).upper()

        render_html(
            f"""
            <div class="payment-card">

                <div class="payment-top">

                    <div>

                        <div class="payment-customer">
                            {escape(str(customer))}
                        </div>

                        <div class="payment-id">
                            Payment ID: {escape(str(payment_id))}
                            &nbsp; • &nbsp;
                            Invoice: {escape(str(invoice))}
                        </div>

                    </div>

                    <div style="text-align:right;">

                        <div class="payment-amount">
                            {money(amount)}
                        </div>

                        <div style="margin-top:7px;">
                            {risk_pill(risk_level)}
                        </div>

                    </div>

                </div>

                <div class="payment-reason">
                    Failure reason:
                    <strong>{escape(reason)}</strong>
                </div>

                <div class="payment-meta">
                    This payment is available for risk analysis
                    and recovery action.
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------

    if filtered_payments:

        export_rows = []

        for payment in filtered_payments:

            export_rows.append(
                {
                    "Payment ID": first_value(
                        payment,
                        "payment_id",
                        default="-",
                    ),
                    "Invoice": first_value(
                        payment,
                        "invoice_id",
                        default="-",
                    ),
                    "Customer": first_value(
                        payment,
                        "customer",
                        "customer_name",
                        default="-",
                    ),
                    "Amount": safe_number(
                        first_value(
                            payment,
                            "amount",
                            "invoice_amount",
                            default=0,
                        )
                    ),
                    "Failure Reason": humanize(
                        first_value(
                            payment,
                            "failure_reason",
                            default="-",
                        )
                    ),
                }
            )

        csv_data = pd.DataFrame(
            export_rows
        ).to_csv(index=False)

        st.download_button(
            "Export Failed Payments CSV",
            data=csv_data,
            file_name="razorpulse_failed_payments.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ==========================================================
# RECOVERY
# ==========================================================

def recovery_page():

    page_header(
        "Recovery Center",
        "Choose a failed payment, select the recovery mode and execute a recovery decision.",
        "REVENUE RECOVERY",
    )

    payments = load_failed_payments()
    risks = load_risk_analysis()
    recoveries = load_recovery_attempts()

    if not payments:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    Recovery queue is empty
                </div>

                <div class="info-text">
                    No failed payments are currently available
                    for recovery.
                </div>

            </div>
            """
        )

        return

    # ------------------------------------------------------
    # KPI
    # ------------------------------------------------------

    revenue_at_risk = sum(
        safe_number(
            first_value(
                payment,
                "amount",
                "invoice_amount",
                default=0,
            )
        )
        for payment in payments
    )

    recovered = sum(
        safe_number(
            first_value(
                recovery,
                "amount_recovered",
                "recovered_amount",
                default=0,
            )
        )
        for recovery in recoveries
    )

    recovery_rate = (
        (recovered / revenue_at_risk) * 100
        if revenue_at_risk
        else 0
    )

    cols = st.columns(4)

    with cols[0]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    Payments in Queue
                </div>

                <div class="rp-kpi-value">
                    {len(payments)}
                </div>

                <div class="rp-kpi-sub">
                    Failed transactions
                </div>

            </div>
            """
        )

    with cols[1]:

        render_html(
            f"""
            <div class="rp-kpi blue">

                <div class="rp-kpi-label">
                    Revenue at Risk
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(revenue_at_risk))}
                </div>

                <div class="rp-kpi-sub">
                    Recovery opportunity
                </div>

            </div>
            """
        )

    with cols[2]:

        render_html(
            f"""
            <div class="rp-kpi green">

                <div class="rp-kpi-label">
                    Recovered
                </div>

                <div class="rp-kpi-value">
                    {escape(compact_money(recovered))}
                </div>

                <div class="rp-kpi-sub">
                    Successfully recovered
                </div>

            </div>
            """
        )

    with cols[3]:

        render_html(
            f"""
            <div class="rp-kpi purple">

                <div class="rp-kpi-label">
                    Recovery Rate
                </div>

                <div class="rp-kpi-value">
                    {recovery_rate:.1f}%
                </div>

                <div class="rp-kpi-sub">
                    Overall recovery performance
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # MODE
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Recovery Decision
        </div>

        <div class="section-subtitle">
            Select how RazorPulse should determine the recovery action.
        </div>
        """
    )

    mode = st.radio(
        "Recovery mode",
        [
            "Deterministic",
            "AI",
        ],
        horizontal=True,
    )

    # ------------------------------------------------------
    # PAYMENT SELECTION
    # ------------------------------------------------------

    payment_options = {}

    for payment in payments:

        payment_id = first_value(
            payment,
            "payment_id",
            default="-",
        )

        customer = first_value(
            payment,
            "customer",
            "customer_name",
            default="-",
        )

        payment_options[
            f"{customer} • {payment_id}"
        ] = payment

    selected_label = st.selectbox(
        "Select failed payment",
        list(payment_options.keys()),
    )

    selected_payment = payment_options[
        selected_label
    ]

    selected_payment_id = first_value(
        selected_payment,
        "payment_id",
        default="-",
    )

    customer = first_value(
        selected_payment,
        "customer",
        "customer_name",
        default="-",
    )

    invoice = first_value(
        selected_payment,
        "invoice_id",
        default="-",
    )

    amount = safe_number(
        first_value(
            selected_payment,
            "amount",
            "invoice_amount",
            default=0,
        )
    )

    reason = humanize(
        first_value(
            selected_payment,
            "failure_reason",
            default="Unknown",
        )
    )

    risk_record = next(
        (
            r
            for r in risks
            if first_value(
                r,
                "payment_id",
                default=None,
            )
            == selected_payment_id
        ),
        {},
    )

    risk_level = str(
        first_value(
            risk_record,
            "risk_level",
            default="UNKNOWN",
        )
    ).upper()

    # ------------------------------------------------------
    # WORKFLOW
    # ------------------------------------------------------

    render_html(
        f"""
        <div class="recovery-workflow">

            <div class="recovery-workflow-title">
                Recovery workflow
            </div>

            <div class="recovery-workflow-sub">
                Review the payment context before executing
                a recovery decision.
            </div>

            <div class="selected-payment-name">
                {escape(str(customer))}
            </div>

            <div class="selected-payment-id">
                Payment: {escape(str(selected_payment_id))}
                &nbsp; • &nbsp;
                Invoice: {escape(str(invoice))}
            </div>

            <div class="selected-payment-amount">
                {money(amount)}
            </div>

            <div style="margin-top:9px;">
                {risk_pill(risk_level)}
            </div>

        </div>
        """
    )

    # ------------------------------------------------------
    # DIAGNOSIS
    # ------------------------------------------------------

    diagnosis_cols = st.columns(3)

    with diagnosis_cols[0]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Failure Diagnosis
                </div>

                <div class="rp-value"
                     style="font-size:20px !important;">
                    {escape(reason)}
                </div>

                <div class="rp-sub">
                    Recorded payment failure signal
                </div>

            </div>
            """
        )

    with diagnosis_cols[1]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Risk Classification
                </div>

                <div class="rp-value"
                     style="font-size:22px !important;">
                    {escape(risk_level)}
                </div>

                <div class="rp-sub">
                    Payment-level risk assessment
                </div>

            </div>
            """
        )

    with diagnosis_cols[2]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Recovery Mode
                </div>

                <div class="rp-value"
                     style="font-size:22px !important;">
                    {escape(mode)}
                </div>

                <div class="rp-sub">
                    Decision engine selected
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # EXECUTE
    # ------------------------------------------------------

    if st.button(
        "Run Recovery Decision",
        type="primary",
        use_container_width=True,
    ):

        result = api_post(
            f"/api/recovery/{selected_payment_id}",
            {
                "mode": (
                    "ai"
                    if mode == "AI"
                    else "deterministic"
                )
            },
        )

        if result is not None:

            st.session_state.last_recovery_result = result

            st.session_state.last_recovery_mode = mode

            st.success(
                "Recovery decision generated successfully."
            )

    # ------------------------------------------------------
    # RESULT
    # ------------------------------------------------------

    if st.session_state.last_recovery_result:

        result = st.session_state.last_recovery_result

        recovery_id = first_value(
            result,
            "recovery_id",
            "id",
            default=None,
        )
        strategy = first_value(
            result,
            "strategy",
            "recovery_strategy",
            default="manual_review",
        )

        status = first_value(
            result,
            "status",
            default="pending",
        )

        confidence = safe_number(
            first_value(
                result,
                "confidence",
                default=0,
            )
        )

        if confidence <= 1:
            confidence_percent = confidence * 100
        else:
            confidence_percent = confidence

        amount_recovered = safe_number(
            first_value(
                result,
                "amount_recovered",
                "recovered_amount",
                default=0,
            )
        )

        notes = first_value(
            result,
            "notes",
            "reason",
            "explanation",
            default="No additional decision details available.",
        )

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        if amount_recovered > 0:

            render_html(
                f"""
                <div class="success-recovery">

                    <div class="success-title">
                        Recovery outcome recorded
                    </div>

                    <div class="payment-meta">
                        {money(amount_recovered)}
                        successfully recovered from this attempt.
                    </div>

                </div>
                """
            )

        # --------------------------------------------------
        # DECISION
        # --------------------------------------------------

        render_html(
            f"""
            <div class="decision-card">

                <div class="decision-title">
                    Latest Recovery Decision
                </div>

                <div class="decision-copy">

                    <strong>
                        Strategy:
                    </strong>
                    {escape(humanize(strategy))}

                    <br>

                    <strong>
                        Status:
                    </strong>
                    {escape(str(status).upper())}

                    <br>

                    <strong>
                        Notes:
                    </strong>
                    {escape(str(notes))}

                </div>

                <div class="confidence">
                    Confidence: {confidence_percent:.0f}%
                </div>

            </div>
            """
        )

        # --------------------------------------------------
        # RESULT METRICS
        # --------------------------------------------------

        result_cols = st.columns(3)

        with result_cols[0]:
            st.metric(
                "Status",
                str(status).upper(),
            )

        with result_cols[1]:
            st.metric(
                "Mode",
                st.session_state.last_recovery_mode
                or mode,
            )
        with result_cols[2]:
            st.metric(
                "Recovered",
                money(amount_recovered),
            )

            if str(status).lower() == "planned" and recovery_id is not None:
              if st.button(
                "Execute Recovery",
                type="primary",
                use_container_width=True,
                key="execute_recovery",
            ):
                outcome = api_post(
                    f"/api/recovery/{recovery_id}/outcome"
                    f"?status=completed"
                    f"&amount_recovered={amount}"
                    f"&notes=Controlled test-mode recovery completed.",
                    {},
                )

                if outcome is not None:
                    st.session_state.last_recovery_result = {
                        **result,
                        **outcome,
                    }
                    st.success("Recovery executed successfully.")
                    st.rerun()
        

    # ------------------------------------------------------
    # ACTIVITY
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Recovery Activity
        </div>

        <div class="section-subtitle">
            Previously recorded recovery attempts.
        </div>
        """
    )

    activity_rows = []

    for recovery in recoveries:

        activity_rows.append(
            {
                "Recovery ID": first_value(
                    recovery,
                    "recovery_id",
                    "id",
                    default="-",
                ),
                "Invoice": first_value(
                    recovery,
                    "invoice_id",
                    default="-",
                ),
                "Amount": money(
                    first_value(
                        recovery,
                        "amount",
                        default=0,
                    )
                ),
                "Strategy": humanize(
                    first_value(
                        recovery,
                        "strategy",
                        default="-",
                    )
                ),
                "Status": str(
                    first_value(
                        recovery,
                        "status",
                        default="-",
                    )
                ).upper(),
                "Recovered": money(
                    first_value(
                        recovery,
                        "amount_recovered",
                        "recovered_amount",
                        default=0,
                    )
                ),
            }
        )

    activity_df = pd.DataFrame(
        activity_rows
    )

    if not activity_df.empty:

        st.dataframe(
            activity_df,
            use_container_width=True,
            hide_index=True,
        )

        recovery_labels = [
            (
                f"Recovery #{row['Recovery ID']} "
                f"• {row['Invoice']} "
                f"• {row['Strategy']}"
            )
            for _, row in activity_df.iterrows()
        ]

        selected_recovery_label = st.selectbox(
            "View recovery details",
            recovery_labels,
        )

        selected_index = recovery_labels.index(
            selected_recovery_label
        )

        selected_recovery = recoveries[
            selected_index
        ]

        notes = first_value(
            selected_recovery,
            "notes",
            "reason",
            "explanation",
            default="No additional details available.",
        )

        render_html(
            f"""
            <div class="info-box">

                <div class="info-title">
                    Recovery #
                    {escape(
                        str(
                            first_value(
                                selected_recovery,
                                "recovery_id",
                                "id",
                                default="-",
                            )
                        )
                    )}
                </div>

                <div class="info-text">

                    <strong>
                        Invoice:
                    </strong>
                    {escape(
                        str(
                            first_value(
                                selected_recovery,
                                "invoice_id",
                                default="-",
                            )
                        )
                    )}

                    <br>

                    <strong>
                        Strategy:
                    </strong>
                    {escape(
                        humanize(
                            first_value(
                                selected_recovery,
                                "strategy",
                                default="-",
                            )
                        )
                    )}

                    <br>

                    <strong>
                        Status:
                    </strong>
                    {escape(
                        str(
                            first_value(
                                selected_recovery,
                                "status",
                                default="-",
                            )
                        ).upper()
                    )}

                    <br>

                    <strong>
                        Amount:
                    </strong>
                    {money(
                        first_value(
                            selected_recovery,
                            "amount",
                            default=0,
                        )
                    )}

                    <br>

                    <strong>
                        Amount Recovered:
                    </strong>
                    {money(
                        first_value(
                            selected_recovery,
                            "amount_recovered",
                            "recovered_amount",
                            default=0,
                        )
                    )}

                    <br><br>

                    <strong>
                        Decision Details:
                    </strong>

                    {escape(str(notes))}

                </div>

            </div>
            """
        )


# ==========================================================
# RISK ANALYSIS
# ==========================================================

def risk_analysis_page():

    page_header(
        "Risk Analysis",
        "Prioritize revenue exposure using payment-level risk signals.",
        "RISK INTELLIGENCE",
    )

    risks = load_risk_analysis()

    if not risks:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    No risk analysis available
                </div>

                <div class="info-text">
                    Risk analysis records have not been returned
                    by the backend yet.
                </div>

            </div>
            """
        )

        return

    high_count = 0
    medium_count = 0
    low_count = 0

    high_revenue = 0
    medium_revenue = 0
    low_revenue = 0

    for risk in risks:

        level = str(
            first_value(
                risk,
                "risk_level",
                default="UNKNOWN",
            )
        ).upper()

        revenue = safe_number(
            first_value(
                risk,
                "revenue_at_risk",
                "amount",
                default=0,
            )
        )

        if level == "HIGH":

            high_count += 1
            high_revenue += revenue

        elif level == "MEDIUM":

            medium_count += 1
            medium_revenue += revenue

        elif level == "LOW":

            low_count += 1
            low_revenue += revenue

    total_revenue_risk = (
        high_revenue
        + medium_revenue
        + low_revenue
    )

    # ------------------------------------------------------
    # KPI
    # ------------------------------------------------------

    cols = st.columns(4)

    with cols[0]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    High Risk
                </div>

                <div class="rp-kpi-value">
                    {high_count}
                </div>

                <div class="rp-kpi-sub">
                    Highest-priority exposures
                </div>

            </div>
            """
        )

    with cols[1]:

        render_html(
            f"""
            <div class="rp-kpi">

                <div class="rp-kpi-label">
                    Medium Risk
                </div>

                <div class="rp-kpi-value">
                    {medium_count}
                </div>

                <div class="rp-kpi-sub">
                    Requires monitoring
                </div>

            </div>
            """
        )

    with cols[2]:

        render_html(
            f"""
            <div class="rp-kpi green">

                <div class="rp-kpi-label">
                    Low Risk
                </div>

                <div class="rp-kpi-value">
                    {low_count}
                </div>

                <div class="rp-kpi-sub">
                    Lower-risk payment exposure
                </div>

            </div>
            """
        )

    with cols[3]:

        render_html(
            f"""
            <div class="rp-kpi blue">

                <div class="rp-kpi-label">
                    Revenue at Risk
                </div>

                <div class="rp-kpi-value">
                    {escape(
                        compact_money(
                            total_revenue_risk
                        )
                    )}
                </div>

                <div class="rp-kpi-sub">
                    Combined risk exposure
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # CHARTS
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Risk Exposure Overview
        </div>

        <div class="section-subtitle">
            Compare payment volume and revenue exposure across risk levels.
        </div>
        """
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        risk_df = pd.DataFrame(
            {
                "Risk Level": [
                    "HIGH",
                    "MEDIUM",
                    "LOW",
                ],
                "Payments": [
                    high_count,
                    medium_count,
                    low_count,
                ],
            }
        )

        fig = px.pie(
            risk_df,
            names="Risk Level",
            values="Payments",
            hole=0.58,
        )

        fig.update_layout(
            title="Risk Distribution",
            height=360,
            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with chart_col2:

        revenue_df = pd.DataFrame(
            {
                "Risk Level": [
                    "HIGH",
                    "MEDIUM",
                    "LOW",
                ],
                "Revenue at Risk": [
                    high_revenue,
                    medium_revenue,
                    low_revenue,
                ],
            }
        )

        fig = px.bar(
            revenue_df,
            x="Risk Level",
            y="Revenue at Risk",
            text="Revenue at Risk",
        )

        fig.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
        )

        fig.update_layout(
            title="Revenue Exposure by Risk",
            height=360,
            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    # ------------------------------------------------------
    # DETAILS
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Risk Details
        </div>

        <div class="section-subtitle">
            Payment-level risk signals returned by the backend.
        </div>
        """
    )

    rows = []

    for risk in risks:

        rows.append(
            {
                "Payment ID": first_value(
                    risk,
                    "payment_id",
                    default="-",
                ),
                "Invoice": first_value(
                    risk,
                    "invoice_id",
                    default="-",
                ),
                "Risk Score": round(
                    safe_number(
                        first_value(
                            risk,
                            "risk_score",
                            default=0,
                        )
                    ),
                    2,
                ),
                "Risk Level": str(
                    first_value(
                        risk,
                        "risk_level",
                        default="-",
                    )
                ).upper(),
                "Revenue at Risk": money(
                    first_value(
                        risk,
                        "revenue_at_risk",
                        default=0,
                    )
                ),
                "Reason": first_value(
                    risk,
                    "reason",
                    default="-",
                ),
            }
        )

    risk_details_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        risk_details_df,
        use_container_width=True,
        hide_index=True,
    )


# ==========================================================
# AI INSIGHTS
# ==========================================================

def ai_insights_page():

    page_header(
        "AI Insights",
        "Separate what Gemini observes from what Gemini recommends you do.",
        "AI PAYMENT INTELLIGENCE",
    )

    payments = load_failed_payments()
    risks = load_risk_analysis()

    if not payments:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    AI analysis is waiting for payment data
                </div>

                <div class="info-text">
                    No failed payment records are currently available
                    for AI analysis.
                </div>

            </div>
            """
        )

        return

    # ------------------------------------------------------
    # HERO
    # ------------------------------------------------------

    render_html(
        """
        <div class="ai-page-hero">

            <div class="ai-kicker">
                Gemini payment intelligence
            </div>

            <div class="ai-title">
                From payment evidence to an actionable decision
            </div>

            <div class="ai-subtitle">
                RazorPulse first identifies what the payment data
                indicates, then presents the AI-generated action
                separately so the operator can understand the
                reasoning before acting.
            </div>

        </div>
        """
    )

    # ------------------------------------------------------
    # LOOKUPS
    # ------------------------------------------------------

    risk_lookup = {}

    for risk in risks:

        payment_id = first_value(
            risk,
            "payment_id",
            default=None,
        )

        if payment_id:
            risk_lookup[payment_id] = risk

    payment_options = {}

    for payment in payments:

        payment_id = first_value(
            payment,
            "payment_id",
            default="-",
        )

        customer = first_value(
            payment,
            "customer",
            "customer_name",
            default="-",
        )

        payment_options[
            f"{customer} • {payment_id}"
        ] = payment

    selected_label = st.selectbox(
        "Select payment for AI analysis",
        list(payment_options.keys()),
    )

    payment = payment_options[
        selected_label
    ]

    payment_id = first_value(
        payment,
        "payment_id",
        default="-",
    )

    customer = first_value(
        payment,
        "customer",
        "customer_name",
        default="-",
    )

    amount = safe_number(
        first_value(
            payment,
            "amount",
            "invoice_amount",
            default=0,
        )
    )

    raw_reason = first_value(
        payment,
        "failure_reason",
        default="unknown",
    )

    reason = humanize(
        raw_reason
    )

    risk = risk_lookup.get(
        payment_id,
        {},
    )

    risk_level = str(
        first_value(
            risk,
            "risk_level",
            default="UNKNOWN",
        )
    ).upper()

    # ------------------------------------------------------
    # PAYMENT CONTEXT
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Payment Context
        </div>

        <div class="section-subtitle">
            The evidence supplied to the AI decision layer.
        </div>
        """
    )

    context_cols = st.columns(4)

    with context_cols[0]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Customer
                </div>

                <div class="rp-value"
                     style="font-size:21px !important;">
                    {escape(str(customer))}
                </div>

            </div>
            """
        )

    with context_cols[1]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Payment
                </div>

                <div class="rp-value"
                     style="font-size:18px !important;">
                    {escape(str(payment_id))}
                </div>

            </div>
            """
        )

    with context_cols[2]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Amount
                </div>

                <div class="rp-value">
                    {escape(money(amount))}
                </div>

            </div>
            """
        )

    with context_cols[3]:

        render_html(
            f"""
            <div class="rp-card">

                <div class="rp-label">
                    Risk Level
                </div>

                <div class="rp-value"
                     style="font-size:22px !important;">
                    {escape(risk_level)}
                </div>

            </div>
            """
        )

    render_html(
        f"""
        <div class="info-box">

            <div class="info-title">
                Payment failure signal
            </div>

            <div class="info-text">
                The payment failed because of
                <strong>
                    {escape(reason)}
                </strong>.

                This failure context, payment amount,
                customer information and risk level are used
                to generate the AI analysis.
            </div>

        </div>
        """
    )

    # ======================================================
    # AI INSIGHTS
    # ======================================================

    render_html(
        """
        <div class="section-title">
            AI INSIGHTS
        </div>

        <div class="section-subtitle">
            What the AI observes from the payment and risk evidence.
            This section describes the situation — not the action.
        </div>
        """
    )

        # ------------------------------------------------------
    # STRUCTURED AI INSIGHTS
    # ------------------------------------------------------

    render_html(
        f"""
        <div class="ai-insight-stack">

            <!-- 01 - KEY FINDING -->
            <div class="ai-insight-card">

                <div class="ai-insight-top">

                    <div class="ai-insight-number">
                        01
                    </div>

                    <div class="ai-insight-label">
                        Key Finding
                    </div>

                </div>

                <div class="ai-insight-heading">
                    Payment failure detected
                </div>

                <div class="ai-insight-copy">

                    Payment
                    <strong>
                        {escape(str(payment_id))}
                    </strong>

                    for

                    <strong>
                        {escape(str(customer))}
                    </strong>

                    has failed with the reason

                    <strong>
                        {escape(reason)}
                    </strong>.

                    The transaction represents

                    <strong>
                        {escape(money(amount))}
                    </strong>

                    of potentially exposed revenue.

                </div>

            </div>


            <!-- 02 - RISK INTERPRETATION -->
            <div class="ai-insight-card">

                <div class="ai-insight-top">

                    <div class="ai-insight-number">
                        02
                    </div>

                    <div class="ai-insight-label">
                        Risk Interpretation
                    </div>

                </div>

                <div class="ai-insight-heading">
                    {escape(risk_level)} risk exposure
                </div>

                <div class="ai-insight-copy">

                    The current payment-level risk signal is

                    <strong>
                        {escape(risk_level)}
                    </strong>.

                    This gives the recovery layer context
                    about how aggressively the payment should
                    be treated.

                </div>

            </div>


            <!-- 03 - FAILURE PATTERN -->
            <div class="ai-insight-card">

                <div class="ai-insight-top">

                    <div class="ai-insight-number">
                        03
                    </div>

                    <div class="ai-insight-label">
                        Failure Pattern
                    </div>

                </div>

                <div class="ai-insight-heading">
                    {escape(reason)}
                </div>

                <div class="ai-insight-copy">

                    The observed payment failure is classified
                    as

                    <strong>
                        {escape(reason)}
                    </strong>.

                    This failure reason becomes part of the
                    evidence used by the AI analysis layer.

                </div>

            </div>


            <!-- 04 - REVENUE IMPACT -->
            <div class="ai-insight-card">

                <div class="ai-insight-top">

                    <div class="ai-insight-number">
                        04
                    </div>

                    <div class="ai-insight-label">
                        Revenue Impact
                    </div>

                </div>

                <div class="ai-insight-heading">
                    {escape(money(amount))} exposed revenue
                </div>

                <div class="ai-insight-copy">

                    The transaction exposes

                    <strong>
                        {escape(money(amount))}
                    </strong>

                    until a successful recovery outcome
                    is recorded.

                    This represents the immediate revenue
                    opportunity associated with the failed
                    payment.

                </div>

            </div>


            <!-- 05 - RISK SIGNAL -->
            <div class="ai-insight-card">

                <div class="ai-insight-top">

                    <div class="ai-insight-number">
                        05
                    </div>

                    <div class="ai-insight-label">
                        Risk Signal
                    </div>

                </div>

                <div class="ai-insight-heading">
                    {escape(risk_level)}
                </div>

                <div class="ai-insight-copy">

                    Current payment risk classification:

                    <strong>
                        {escape(risk_level)}
                    </strong>.

                    This signal is passed to the recovery and
                    recommendation layers as decision context.

                </div>

            </div>

        </div>
        """
    )
    # ======================================================
    # AI RECOMMENDATIONS
    # ======================================================

    render_html(
        """
        <div class="section-title">
            AI RECOMMENDATIONS
        </div>

        <div class="section-subtitle">
            What Gemini recommends doing next based on the observed
            payment evidence. This is intentionally separated from
            the insight layer.
        </div>
        """
    )

    # ------------------------------------------------------
    # GENERATE
    # ------------------------------------------------------

    if st.button(
        "Generate AI Recommendation",
        type="primary",
        use_container_width=True,
    ):

        result = api_post(
            "/api/ai-insights",
            {
                "customer_name": str(
                    customer
                ),
                "invoice_amount": amount,
                "failure_reason": str(
                    raw_reason
                ),
                "risk_level": risk_level,
            },
        )

        if result is not None:

            st.session_state.last_ai_result = result

            st.session_state.last_ai_payment_id = (
                payment_id
            )

            st.success(
                "AI recommendation generated successfully."
            )

    # ------------------------------------------------------
    # RESULT
    # ------------------------------------------------------

    if st.session_state.last_ai_result:

        result = st.session_state.last_ai_result

        recommendation = first_value(
            result,
            "recommendation",
            default="manual_review",
        )

        explanation = first_value(
            result,
            "explanation",
            "reason",
            "notes",
            default="No explanation provided.",
        )

        confidence = safe_number(
            first_value(
                result,
                "confidence",
                default=0,
            )
        )

        if confidence <= 1:
            confidence_percent = confidence * 100
        else:
            confidence_percent = confidence

        priority = first_value(
            result,
            "priority",
            "risk_level",
            default=risk_level,
        )

        manual_review = first_value(
            result,
            "manual_review_required",
            "requires_manual_review",
            "manual_review",
            default=None,
        )

        next_step = first_value(
            result,
            "next_step",
            "suggested_next_step",
            default=recommendation,
        )

        # --------------------------------------------------
        # RECOMMENDATION CARD
        # --------------------------------------------------

        render_html(
            f"""
            <div class="ai-recommendation-card">

                <div class="ai-recommendation-kicker">
                    Recommended Action
                </div>

                <div class="ai-recommendation-action">
                    {escape(
                        humanize(
                            recommendation
                        )
                    )}
                </div>

                <div class="ai-recommendation-why">

                    <strong>
                        Why this action?
                    </strong>

                    <br>

                    {escape(
                        str(explanation)
                    )}

                </div>

                <div class="ai-meta-grid">

                    <div class="ai-meta">

                        <div class="ai-meta-label">
                            Priority
                        </div>

                        <div class="ai-meta-value">
                            {escape(
                                str(priority).upper()
                            )}
                        </div>

                    </div>

                    <div class="ai-meta">

                        <div class="ai-meta-label">
                            Confidence
                        </div>

                        <div class="ai-meta-value">
                            {confidence_percent:.0f}%
                        </div>

                    </div>

                    <div class="ai-meta">

                        <div class="ai-meta-label">
                            Manual Review
                        </div>

                        <div class="ai-meta-value">
                            {
                                "Required"
                                if manual_review is True
                                else
                                "Not required"
                                if manual_review is False
                                else
                                "Not specified"
                            }
                        </div>

                    </div>

                    <div class="ai-meta">

                        <div class="ai-meta-label">
                            Suggested Next Step
                        </div>

                        <div class="ai-meta-value">
                            {escape(
                                humanize(
                                    next_step
                                )
                            )}
                        </div>

                    </div>

                </div>

            </div>
            """
        )

        # --------------------------------------------------
        # VISUAL DISTINCTION
        # --------------------------------------------------

        render_html(
            """
            <div style="
                height:1px;
                margin:25px 0 18px;
                background:rgba(128,128,128,.18);
            "></div>

            <div class="info-box">

                <div class="info-title">
                    Decision interpretation
                </div>

                <div class="info-text">

                    <strong>
                        AI Insights
                    </strong>
                    explain what the payment data indicates.

                    <br><br>

                    <strong>
                        AI Recommendations
                    </strong>
                    explain what the system recommends doing
                    about that situation.

                </div>

            </div>
            """
        )

    else:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    Recommendation not generated yet
                </div>

                <div class="info-text">

                    Select a failed payment and use
                    <strong>
                        Generate AI Recommendation
                    </strong>
                    to ask the backend AI service for an
                    actionable recommendation.

                </div>

            </div>
            """
        )


# ==========================================================
# AUDIT LOGS
# ==========================================================

def audit_logs_page():

    page_header(
        "Audit Logs",
        "Trace recovery decisions, AI recommendations and recorded outcomes.",
        "AUDIT TRAIL",
    )

    logs = load_audit_logs()

    if not logs:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    No audit events recorded
                </div>

                <div class="info-text">
                    Recovery and AI events will appear here once
                    activity is recorded by the backend.
                </div>

            </div>
            """
        )

        return

    recovery_events = 0
    ai_events = 0

    for log in logs:

        event_type = str(
            first_value(
                log,
                "event_type",
                default="",
            )
        ).upper()

        if "RECOVERY" in event_type:
            recovery_events += 1

        if "AI" in event_type:
            ai_events += 1

    # ------------------------------------------------------
    # KPI
    # ------------------------------------------------------

    cols = st.columns(3)

    with cols[0]:

        render_html(
            f"""
            <div class="rp-kpi neutral">

                <div class="rp-kpi-label">
                    Total Events
                </div>

                <div class="rp-kpi-value">
                    {len(logs)}
                </div>

                <div class="rp-kpi-sub">
                    Recorded system activity
                </div>

            </div>
            """
        )

    with cols[1]:

        render_html(
            f"""
            <div class="rp-kpi blue">

                <div class="rp-kpi-label">
                    Recovery Events
                </div>

                <div class="rp-kpi-value">
                    {recovery_events}
                </div>

                <div class="rp-kpi-sub">
                    Recovery-related activity
                </div>

            </div>
            """
        )

    with cols[2]:

        render_html(
            f"""
            <div class="rp-kpi purple">

                <div class="rp-kpi-label">
                    AI Decisions
                </div>

                <div class="rp-kpi-value">
                    {ai_events}
                </div>

                <div class="rp-kpi-sub">
                    AI-related events
                </div>

            </div>
            """
        )

    # ------------------------------------------------------
    # TIMELINE
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            Activity Timeline
        </div>

        <div class="section-subtitle">
            Newest audit events are shown first.
        </div>
        """
    )

    sorted_logs = sorted(
        logs,
        key=lambda x: str(
            first_value(
                x,
                "created_at",
                default="",
            )
        ),
        reverse=True,
    )

    for log in sorted_logs[:50]:

        event_type = str(
            first_value(
                log,
                "event_type",
                default="SYSTEM",
            )
        ).upper()

        entity_type = str(
            first_value(
                log,
                "entity_type",
                default="",
            )
        )

        entity_id = str(
            first_value(
                log,
                "entity_id",
                default="",
            )
        )

        message = str(
            first_value(
                log,
                "message",
                default="",
            )
        )

        created_at = str(
            first_value(
                log,
                "created_at",
                default="-",
            )
        )

        clean_message = (
            message
            .replace("â¹", "INR ")
            .replace("₹", "INR ")
        )

        detail_parts = re.split(
            r"\.\s+(?=(?:Strategy|Reason|Extension days|"
            r"Discount|AI recommendation|Confidence|"
            r"Final strategy|Risk level|Amount recovered|"
            r"Status):)",
            clean_message,
        )

        detail_parts = [
            part.strip(" .")
            for part in detail_parts
            if part.strip(" .")
        ]

        if "AI" in event_type:

            badge_class = "badge-ai"
            badge_text = "AI"

        elif (
            "OUTCOME" in event_type
            or "SUCCESS" in event_type
        ):

            badge_class = "badge-success"
            badge_text = "SUCCESS"

        elif "RECOVERY" in event_type:

            badge_class = "badge-recovery"
            badge_text = "RECOVERY"

        else:

            badge_class = "badge-system"
            badge_text = "SYSTEM"

        main_message = (
            detail_parts[0]
            if detail_parts
            else clean_message
        )

        extra_details = detail_parts[1:]

        detail_html = ""

        for detail in extra_details:

            detail_html += (
                '<div class="audit-detail">'
                f"{escape(detail)}"
                "</div>"
            )

        render_html(
            f"""
            <div class="audit-card">

                <div class="audit-top">

                    <div>

                        <span class="badge {badge_class}">
                            {escape(badge_text)}
                        </span>

                        <span class="audit-event">
                            &nbsp;
                            {escape(event_type)}
                        </span>

                    </div>

                    <div class="audit-time">
                        {escape(created_at)}
                    </div>

                </div>

                <div class="audit-message">
                    {escape(main_message)}
                </div>

                <div class="audit-detail">

                    Entity:
                    {escape(entity_type)}

                    {
                        escape(" #" + entity_id)
                        if entity_id
                        else ""
                    }

                </div>

                {detail_html}

            </div>
            """
        )

    # ------------------------------------------------------
    # RAW RECORDS
    # ------------------------------------------------------

    with st.expander(
        "View raw audit records"
    ):

        raw_df = pd.DataFrame(
            logs
        )

        st.dataframe(
            raw_df,
            use_container_width=True,
            hide_index=True,
        )


# ==========================================================
# SETTINGS
# ==========================================================

def settings_page():

    page_header(
        "Settings",
        "Review RazorPulse runtime configuration and system connectivity.",
        "SYSTEM SETTINGS",
    )

    # ------------------------------------------------------
    # ENVIRONMENT
    # ------------------------------------------------------

    render_html(
        """
        <div class="rp-hero">

            <div class="rp-hero-kicker">
                System configuration
            </div>

            <div class="rp-hero-title">
                RazorPulse environment
            </div>

            <div class="rp-hero-sub">
                These settings describe the active frontend
                configuration. Sensitive API credentials are not
                displayed in the dashboard.
            </div>

        </div>
        """
    )

    c1, c2 = st.columns(2)

    with c1:

        st.text_input(
            "Backend URL",
            value=BACKEND_URL,
            disabled=True,
        )

        st.text_input(
            "Database",
            value="SQLite + SQLAlchemy",
            disabled=True,
        )

    with c2:

        st.text_input(
            "AI Provider",
            value="Google Gemini",
            disabled=True,
        )

        st.text_input(
            "Recovery Engine",
            value="Deterministic + AI",
            disabled=True,
        )

    # ------------------------------------------------------
    # SYSTEM STATUS
    # ------------------------------------------------------

    render_html(
        """
        <div class="section-title">
            System Status
        </div>

        <div class="section-subtitle">
            Current connectivity between the Streamlit frontend
            and FastAPI backend.
        </div>
        """
    )

    if backend_is_healthy():

        render_html(
            """
            <div class="success-recovery">

                <div class="success-title">
                    Backend connection is healthy
                </div>

                <div class="payment-meta">
                    FastAPI is responding at the configured
                    backend endpoint.
                </div>

            </div>
            """
        )

    else:

        render_html(
            """
            <div class="info-box">

                <div class="info-title">
                    Backend is currently offline
                </div>

                <div class="info-text">
                    Start the FastAPI backend before using
                    live payment, risk, recovery or AI features.
                </div>

            </div>
            """
        )




# ==========================================================
# MAIN ROUTER
# ==========================================================

if st.session_state.page == "Overview":

    overview_page()

elif st.session_state.page == "Failed Payments":

    failed_payments_page()

elif st.session_state.page == "Recovery":

    recovery_page()

elif st.session_state.page == "Risk Analysis":

    risk_analysis_page()

elif st.session_state.page == "AI Insights":

    ai_insights_page()

elif st.session_state.page == "Audit Logs":

    audit_logs_page()

elif st.session_state.page == "Settings":

    settings_page()

else:

    st.session_state.page = "Overview"

    overview_page()
