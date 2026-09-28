import streamlit as st
from streamlit_folium import st_folium
from streamlit_plotly_events import plotly_events
import folium
from folium.plugins import HeatMap,AntPath
import pandas as pd
import sqlalchemy
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import subprocess
import tempfile
import zipfile
import shutil
import os
import json
import base64
import html
import shlex
import re
import math
import platform
import xml.etree.ElementTree as ET

# LOOM SVG post-processing re-serializes the document with ElementTree.
# Without this registration ET writes tags as <ns0:svg>, <ns0:text>, ...
# (an unbound, arbitrary prefix), which (a) breaks rendering in browsers
# and (b) makes tag searches like rfind("</svg>") fail -- silently dropping
# landmark injection and any other string-level SVG surgery.
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

st.set_page_config(layout="wide")

pio.templates.default = "plotly_dark"

# -------------------------------------------------------------------
# LOOM bundled native libraries
# -------------------------------------------------------------------
LOOM_LIB_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "loom-libs",
)

if os.path.isdir(LOOM_LIB_DIR):
    os.environ["LD_LIBRARY_PATH"] = (
        LOOM_LIB_DIR
        + os.pathsep
        + os.environ.get("LD_LIBRARY_PATH", "")
    )

# ================= STYLE FIX =================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
/* =========================================================
   TOKENS
========================================================= */
:root {
    --bg:         #080b12;
    --bg-1:       #0d1017;
    --bg-2:       #111520;
    --bg-3:       #161b2c;
    --border:     rgba(255,255,255,0.06);
    --border-md:  rgba(255,255,255,0.10);
    --border-hi:  rgba(255,255,255,0.16);
    --text-1:     #eef0f8;
    --text-2:     #8892aa;
    --text-3:     #4a5268;
    --mono:       'JetBrains Mono', monospace;
    --sans:       'Outfit', sans-serif;
    --radius-sm:  6px;
    --radius-md:  10px;
    --radius-lg:  14px;
    --radius-xl:  18px;
    --blue:       #4f87ff;
    --teal:       #2dd4bf;
    --red:        #f05454;
    --amber:      #f5a623;
    --purple:     #9f7aea;
    --green:      #38d975;
}

/* =========================================================
   GLOBAL
========================================================= */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #000000 !important;
    color: white !important;
}

/* MAIN APP */
.stApp {
    background-color: #000000 !important;
}

/* REMOVE DEFAULT STREAMLIT WIDTH */
.block-container {
    max-width: 100% !important;
    padding-top: 0.7rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
    padding-bottom: 1rem !important;
}

/* =========================================================
   SIDEBAR
========================================================= */
section[data-testid="stSidebar"] {
    background-color: #050505 !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* =========================================================
   CHECKBOX
========================================================= */
div[data-testid="stCheckbox"] label {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #e5e5e5 !important;
}

/* =========================================================
   KPI CARDS
========================================================= */
div[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        rgba(255,255,255,0.04),
        rgba(255,255,255,0.02)
    ) !important;

    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 18px 18px 14px 18px;

    backdrop-filter: blur(6px);

    transition: 0.3s ease;
}

/* HOVER EFFECT */
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border: 1px solid rgba(255,255,255,0.12);
}

/* =========================================================
   KPI CARDS (CUSTOM)
========================================================= */
.kpi-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.07);
    border-top: 3px solid var(--kpi-color);
    border-radius: 14px;
    padding: 16px 18px 14px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
    height: 100%;
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255,255,255,0.13);
}

.kpi-card::after {
    content: '';
    position: absolute;
    top: -30px; right: -30px;
    width: 80px; height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--kpi-color) 0%, transparent 70%);
    opacity: 0.07;
    pointer-events: none;
}

/* icon + pill row */
.kpi-icon-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

/* pills */
.kpi-pill {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #9ca3af;
}

.kpi-pill-red    { color:#ef4444; background:rgba(239,68,68,0.1);   border-color:rgba(239,68,68,0.2); }
.kpi-pill-amber  { color:#f59e0b; background:rgba(245,158,11,0.1);  border-color:rgba(245,158,11,0.2); }
.kpi-pill-purple { color:#a78bfa; background:rgba(167,139,250,0.1); border-color:rgba(167,139,250,0.2); }
.kpi-pill-green  { color:#22c55e; background:rgba(34,197,94,0.1);   border-color:rgba(34,197,94,0.2); }

/* label */
.kpi-label {
    font-size: 9.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    color: #6b7280 !important;
    margin-bottom: 6px !important;
}

/* main value */
.kpi-val {
    font-size: 30px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    line-height: 1 !important;
    letter-spacing: -0.5px;
    margin-bottom: 0 !important;
}

.kpi-val-sm {
    font-size: 16px !important;
    letter-spacing: 0 !important;
    line-height: 1.2 !important;
}

/* divider */
.kpi-divider {
    height: 1px;
    background: rgba(255,255,255,0.06);
    margin: 10px 0 8px;
}

/* sub labels */
.kpi-sub {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #9ca3af !important;
}

.kpi-sub.up     { color: #22c55e !important; }
.kpi-sub.warn   { color: #f59e0b !important; }
.kpi-sub.info   { color: #60a5fa !important; }
.kpi-sub.purple { color: #a78bfa !important; }

/* =========================================================
   EXPANDERS
========================================================= */
div[data-testid="stExpander"] {
    background-color: #0d0d0d !important;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px !important;
    overflow: hidden;
}

/* DEFAULT SMALL EXPANDERS */
div[data-testid="stExpander"] details summary p {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: white !important;
    margin: 0 !important;
}

/* HEADER PADDING */
div[data-testid="stExpander"] details summary {
    padding: 0.6rem 0.8rem !important;
}

/* MAIN BIG HEADERS ONLY */
.main-header details summary p {
    font-size: 18px !important;
    font-weight: 700 !important;
}

/* CONTENT TEXT */
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li {
    font-size: 14px !important;
    font-weight: 500 !important;
    line-height: 1.7 !important;
    color: #d0d0d0 !important;
}

/* =========================================================
   PLOTLY
========================================================= */
.js-plotly-plot,
.plotly,
.plot-container {
    font-family: 'Inter', sans-serif !important;
    background-color: transparent !important;
}

/* =========================================================
   PLOTLY OVERFLOW FIX
========================================================= */
.js-plotly-plot,
.plot-container,
.svg-container {
    overflow: visible !important;
    max-width: 100% !important;
}

div[data-testid="stPlotlyChart"] {
    overflow: visible !important;
}

/* =========================================================
   LEAFLET MAP
========================================================= */
.leaflet-container {
    background-color: #000000 !important;
    border-radius: 14px !important;
}

/* POPUPS */
.leaflet-popup-content {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* LAYER CONTROL */
.leaflet-control {
    font-family: 'Inter', sans-serif !important;
}

/* =========================================================
   BUTTONS
========================================================= */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;

    background-color: #111111 !important;
    color: white !important;

    transition: 0.25s ease;
}

.stButton > button:hover {
    background-color: #1c1c1c !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* =========================================================
   DATAFRAME
========================================================= */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)
# ================= DB =================
def get_engine():
    db_url = st.secrets["DB_URL"]
    return sqlalchemy.create_engine(db_url)


# ================= DATA =================
@st.cache_data
def fetch_kpi():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            (SELECT COUNT(*) FROM routes) AS routes,
            (SELECT COUNT(*) FROM trips) AS trips,
            (SELECT COUNT(*) FROM stops) AS stops,
            (SELECT COUNT(*) FROM agency) AS agency
    """, engine).iloc[0].to_dict()

# ================= CONGESTION =================
@st.cache_data
def fetch_congestion():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            EXTRACT(HOUR FROM TO_TIMESTAMP("Date", 'MM/DD/YYYY HH24:MI')) AS hour,
            COUNT(*) AS gps_points,
            COUNT(DISTINCT "Location") AS active_vehicles,

            AVG(
                CAST(REPLACE("Speed", 'km/h', '') AS FLOAT)
            ) AS avg_speed,

            COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT "Location"), 0) AS congestion_index,

            CASE
                WHEN EXTRACT(HOUR FROM TO_TIMESTAMP("Date", 'MM/DD/YYYY HH24:MI')) BETWEEN 5 AND 9
                    THEN 'Morning Peak (5–9)'
                WHEN EXTRACT(HOUR FROM TO_TIMESTAMP("Date", 'MM/DD/YYYY HH24:MI')) BETWEEN 10 AND 15
                    THEN 'Midday Flow (10–15)'
                WHEN EXTRACT(HOUR FROM TO_TIMESTAMP("Date", 'MM/DD/YYYY HH24:MI')) BETWEEN 16 AND 19
                    THEN 'Evening Peak (16–19)'
                ELSE 'Night Low (20–4)'
            END AS time_block

        FROM clustered_gps_points
        GROUP BY hour
        ORDER BY hour
    """, engine)

# ================= MARKET SHARE =================
@st.cache_data
def routes_per_agency():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            COALESCE(a.agency_name, 'Unknown') AS agency_name,
            COUNT(r.route_id) AS route_count,
            ROUND(
                COUNT(r.route_id) * 100.0 / SUM(COUNT(r.route_id)) OVER (),
                2
            ) AS percentage
        FROM routes r
        LEFT JOIN agency a ON r.agency_id = a.agency_id
        GROUP BY a.agency_name
        ORDER BY route_count DESC
    """, engine)


@st.cache_data
def fetch_routes():
    engine = get_engine()
    return pd.read_sql(
        "SELECT route_id, route_short_name, agency_id FROM routes",
        engine
    )

@st.cache_data
def fetch_agencies():
    engine = get_engine()
    return pd.read_sql(
        "SELECT agency_id, agency_name FROM agency",
        engine
    )

@st.cache_data
def get_route_agency_map():
    """route_id -> agency_name, used to append the operating agency onto
    route labels wherever a legend is rendered (Transit Map, LOOM map)."""
    routes_df = fetch_routes()
    agencies_df = fetch_agencies()
    merged = routes_df.merge(agencies_df, on="agency_id", how="left")
    merged["agency_name"] = merged["agency_name"].fillna("Unknown Agency")
    return dict(zip(merged["route_id"], merged["agency_name"]))

# ================= SHARED ROUTE COLORS (SINGLE SOURCE OF TRUTH) =================
ROUTE_COLOR_NAMES = [
    "blue", "red", "green", "purple", "orange", "black", "brown", "grey"
]

ROUTE_COLOR_HEX = {
    "blue":   "#1d4ed8",
    "red":    "#dc2626",
    "green":  "#16a34a",
    "purple": "#7c3aed",
    "orange": "#ea580c",
    "black":  "#111111",
    "brown":  "#92400e",
    "grey":   "#4b5563",
}

COLOR_EMOJI_MAP = {
    "blue": "🟦",
    "red": "🟥",
    "green": "🟩",
    "purple": "🟪",
    "orange": "🟧",
    "black": "⬛",
    "brown": "🟫",
    "grey": "◼️",
}

MAJOR_TRANSIT_STOPS = {
    "kalanki",
    "chabahil",
    "koteshwor",
    "balkhu",
}


def is_major_transit_stop(stop_name):
    """Match numbered or extended GTFS names to a major exchange."""
    normalized = re.sub(r"[\s_-]*\d+\s*$", "", str(stop_name).strip().casefold())
    return any(
        normalized == major or normalized.startswith(major + " ")
        for major in MAJOR_TRANSIT_STOPS
    )



# =========================================================
# VECTOR LANDMARKS
# =========================================================
LANDMARKS = {
    "Pashupati Temple": {"lat":27.710637, "lon": 85.349527, "svg": "icon/pashupati.svg"},
    "Dharahara": {"lat": 27.700846100092736, "lon":  85.31200513924873, "svg": "icon/darahara.svg"},
    "Boudhanath Stupa": {"lat": 27.7215, "lon": 85.3620, "svg": "icon/boudhastupa.svg"},
    "Swayambhunath": {"lat": 27.7149, "lon": 85.2906, "svg": "icon/swayambhustupa1.svg"},
    "Tribhuvan International Airport": {"lat": 27.698428, "lon":85.362892, "svg": "icon/vector.svg"},
    "UN Park": {"lat":27.6854334117676, "lon":85.3257565314652, "svg": "icon/ic_baseline-park.svg"},
    "Kathmandu Fun Park": {"lat": 27.701374732249555, "lon": 85.32040843415382,"svg": "icon/park.svg"},
    "ZOO": {"lat": 27.672943662412717, "lon":  85.31179605885961,"svg": "icon/zoo.svg"},
    "Bir Hospital": {"lat": 27.705641517753943, "lon": 85.31286308128226, "svg": "icon/hospital.svg"},
    "Basantapur  Durbar Square": {"lat": 27.70429180598546, "lon": 85.30745144002829, "svg": "icon/Group 347.svg"},
    "Patan Durbar Square": {"lat": 27.672660069722838, "lon":  85.32555712962338, "svg": "icon/PDS.svg"},
}
DEFAULT_LANDMARKS = tuple(LANDMARKS.keys())


def get_landmark_records(selected_landmarks):
    records = []
    for name in selected_landmarks or ():
        if name not in LANDMARKS:
            continue
        record = dict(LANDMARKS[name])
        record["name"] = name
        try:
            record["lat"] = float(record["lat"])
            record["lon"] = float(record["lon"])
        except (TypeError, ValueError):
            continue
        records.append(record)
    return records


# ------------------------------------------------------------
# CUSTOM SVG ICONS FOR LANDMARKS
# ------------------------------------------------------------

def get_landmark_custom_svg_status(record):
    """Resolve a landmark's custom SVG and report exactly what happened.

    Returns a dict:
        {"ok": bool, "reason": str, "path": str|None, "svg": str|None}

    "reason" is a short human-readable explanation, always filled in, even
    on success -- this is what get_landmark_custom_svg() used to swallow,
    making silent fallback-to-generic-icon impossible to debug.
    """
    svg_value = record.get("svg")
    name = record.get("name", "?")

    if not svg_value:
        return {"ok": False, "reason": "No \"svg\" key set for this landmark.",
                "path": None, "svg": None}

    svg_text = str(svg_value).strip()
    resolved_path = None

    if "<svg" not in svg_text.lower():
        # Treat as a file path relative to this script's own folder.
        resolved_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), svg_value
        )
        if not os.path.isfile(resolved_path):
            return {
                "ok": False,
                "reason": (
                    f'File not found: "{resolved_path}". The "svg" value '
                    f'"{svg_value}" is resolved relative to app.py\'s own '
                    f"folder -- check the icons/ folder actually ships "
                    f"next to app.py in this environment."
                ),
                "path": resolved_path, "svg": None,
            }
        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                svg_text = f.read()
        except OSError as exc:
            return {"ok": False, "reason": f"Could not read file: {exc}",
                     "path": resolved_path, "svg": None}

    if "<svg" not in svg_text.lower():
        return {
            "ok": False,
            "reason": (
                "Resolved content has no <svg> tag -- the file/string isn't "
                "actually SVG markup (empty file, HTML error page, wrong "
                "path pointing at something else, etc.)."
            ),
            "path": resolved_path, "svg": None,
        }

    cleaned = sanitize_uploaded_svg(svg_text)
    return {"ok": True, "reason": f"Loaded OK ({len(cleaned)} chars).",
            "path": resolved_path, "svg": cleaned}


def get_landmark_custom_svg(record):
    return get_landmark_custom_svg_status(record)["svg"]


def landmark_svg_data_uri(svg_text):
    encoded = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def sanitize_uploaded_svg(svg_text):
    text = str(svg_text)
    text = re.sub(r"<script\b[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\son\w+\s*=\s*\"[^\"]*\"", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\son\w+\s*=\s*'[^']*'", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(href|xlink:href)\s*=\s*\"(?!#)[^\"]*\"", "", text, flags=re.IGNORECASE)
    return text


def uploaded_svg_viewbox(svg_text):
    match = re.search(
        r'\bviewBox\s*=\s*["\']\s*([\d.eE+-]+)\s+([\d.eE+-]+)\s+'
        r'([\d.eE+-]+)\s+([\d.eE+-]+)\s*["\']',
        svg_text,
    )
    if match:
        return tuple(float(v) for v in match.groups())
    # Fall back to width/height if the icon has no viewBox.
    wm = re.search(r'\bwidth\s*=\s*["\']([\d.]+)', svg_text)
    hm = re.search(r'\bheight\s*=\s*["\']([\d.]+)', svg_text)
    if wm and hm:
        return 0.0, 0.0, float(wm.group(1)), float(hm.group(1))
    return None


def _svg_landmark_group(record, x, y, size=28):
    name = html.escape(str(record["name"]))
    s = float(size)
    hx = s * 0.5
    hy = s * 0.5

    custom_svg = get_landmark_custom_svg(record)
    if custom_svg:
        vb = uploaded_svg_viewbox(custom_svg)
        vb_attr = (
            f'viewBox="{vb[0]:.3f} {vb[1]:.3f} {vb[2]:.3f} {vb[3]:.3f}"'
            if vb else 'viewBox="0 0 100 100"'
        )
    
        inner_match = re.search(r"<svg\b[^>]*>([\s\S]*)</\s*svg\s*>", custom_svg, re.IGNORECASE)
        inner = inner_match.group(1) if inner_match else custom_svg
        shapes = (
            f'<svg x="{x-hx:.3f}" y="{y-hy:.3f}" width="{s:.3f}" height="{s:.3f}" '
            f'{vb_attr} preserveAspectRatio="xMidYMid meet">{inner}</svg>'
        )
    else:
        kind = record.get("kind", "monument")
        shapes = _builtin_landmark_shapes(record, x, y, size)

    return f"""
      <g class="loom-landmark" data-landmark="{name}" data-landmark-name="{name}" tabindex="0" style="cursor:pointer">
        {shapes}
        <text class="landmark-label" x="{x+hx*0.95:.3f}" y="{y-hy*0.95:.3f}"
              visibility="hidden"
              font-family="Arial, sans-serif" font-size="{max(7,s*0.42):.2f}"
              font-weight="600" fill="#111111"
              stroke="white" stroke-width="{max(1,s*0.09):.2f}"
              paint-order="stroke" stroke-linejoin="round">{name}</text>
      </g>
    """


def _builtin_landmark_shapes(record, x, y, size=28):
    """Built-in vector landmark icons (used when no custom SVG is uploaded)."""
    kind = record.get("kind", "monument")
    s = float(size)
    hx = s * 0.5
    hy = s * 0.5

    if kind == "temple":
        shapes = f"""
            <polygon points="{x},{y-hy*0.95} {x-hx*0.72},{y-hy*0.05}
                     {x+hx*0.72},{y-hy*0.05}"
                     fill="white" stroke="#7c3aed" stroke-width="{s*0.07:.2f}"/>
            <rect x="{x-hx*0.42}" y="{y-hy*0.02}"
                  width="{hx*0.84}" height="{hy*0.78}"
                  fill="white" stroke="#7c3aed" stroke-width="{s*0.07:.2f}"/>
            <rect x="{x-hx*0.12}" y="{y+hy*0.18}"
                  width="{hx*0.24}" height="{hy*0.58}"
                  fill="white" stroke="#7c3aed" stroke-width="{s*0.06:.2f}"/>
        """
    elif kind == "tower":
        shapes = f"""
            <polygon points="{x-hx*0.32},{y+hy*0.9}
                     {x+hx*0.32},{y+hy*0.9}
                     {x+hx*0.22},{y-hy*0.25}
                     {x-hx*0.22},{y-hy*0.25}"
                     fill="white" stroke="#dc2626" stroke-width="{s*0.07:.2f}"/>
            <rect x="{x-hx*0.36}" y="{y-hy*0.40}"
                  width="{hx*0.72}" height="{hy*0.18}"
                  fill="white" stroke="#dc2626" stroke-width="{s*0.06:.2f}"/>
            <polygon points="{x},{y-hy*0.95}
                     {x-hx*0.35},{y-hy*0.42}
                     {x+hx*0.35},{y-hy*0.42}"
                     fill="white" stroke="#dc2626" stroke-width="{s*0.07:.2f}"/>
        """
    elif kind == "stupa":
        shapes = f"""
            <circle cx="{x}" cy="{y-hy*0.18}" r="{hx*0.50}"
                    fill="white" stroke="#ea580c" stroke-width="{s*0.07:.2f}"/>
            <path d="M {x-hx*0.72},{y+hy*0.55}
                     Q {x},{y+hy*0.02} {x+hx*0.72},{y+hy*0.55}
                     L {x+hx*0.55},{y+hy*0.78}
                     L {x-hx*0.55},{y+hy*0.78} Z"
                  fill="white" stroke="#ea580c" stroke-width="{s*0.07:.2f}"/>
            <line x1="{x}" y1="{y-hy*0.70}" x2="{x}" y2="{y-hy*0.98}"
                  stroke="#ea580c" stroke-width="{s*0.07:.2f}"/>
        """
    elif kind == "park":
        shapes = f"""
            <circle cx="{x}" cy="{y}" r="{hx*0.78}"
                    fill="white" stroke="#16a34a" stroke-width="{s*0.07:.2f}"/>
            <path d="M {x},{y+hy*0.52} L {x},{y-hy*0.28}
                     M {x},{y-hy*0.10} L {x-hx*0.35},{y-hy*0.38}
                     M {x},{y+hy*0.08} L {x+hx*0.34},{y-hy*0.18}"
                  fill="none" stroke="#16a34a" stroke-width="{s*0.07:.2f}"
                  stroke-linecap="round"/>
        """
    else:
        shapes = f"""
            <rect x="{x-hx*0.65}" y="{y-hy*0.65}"
                  width="{s*0.65}" height="{s*0.65}" rx="{s*0.10:.2f}"
                  transform="rotate(45 {x} {y})"
                  fill="white" stroke="#1d4ed8" stroke-width="{s*0.07:.2f}"/>
            <circle cx="{x}" cy="{y}" r="{hx*0.20}" fill="#1d4ed8"/>
        """
    return shapes


def _svg_viewbox(svg):
    match = re.search(
        r'\bviewBox\s*=\s*["\']\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+'
        r'([-\d.eE+]+)\s+([-\d.eE+]+)\s*["\']',
        svg,
    )
    return tuple(float(v) for v in match.groups()) if match else None


def _normalize_stop_name_for_match(name):
    """Normalize a stop name so a real GTFS stop can be matched against its
    rendered LOOM station-label text, which may carry a trailing sequence
    number LOOM/the GTFS feed appends to disambiguate repeated stop names
    (e.g. the label "Kalanki Bus Stop1" for the GTFS stop "Kalanki Bus
    Stop"). Mirrors the normalization is_major_transit_stop() already uses
    elsewhere in the app for the same reason."""
    return re.sub(r"[\s_-]*\d+\s*$", "", str(name or "").strip().casefold())


def _extract_svg_polyline_segments(svg):
    """Pull every visibly-stroked <path>'s polyline segments out of a LOOM
    SVG, in the SVG's own coordinate space. Used to keep landmark icons
    clear of the actual rendered transit lines -- which, in schematic
    (octilinear) mode, follow a distorted grid layout rather than a simple
    function of real-world lon/lat, so this has to read the real drawn
    geometry rather than recompute it."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return []

    def tag_local(el):
        return el.tag.split('}')[-1] if '}' in el.tag else el.tag

    segments = []
    for el in root.iter():
        if tag_local(el) != 'path':
            continue
        # A path counts as a drawn line if it has a visible stroke via
        # attribute OR inline style. LOOM sometimes carries stroke only in
        # style="...stroke:#xxxxxx..." or via a CSS class (e.g. on the
        # <g> wrapper), so checking only the attribute silently missed real
        # route lines -- which is why landmark icons could still land on
        # them. Paths with no stroke indication at all are still skipped so
        # invisible hit-areas / label paths don't create fake obstacles.
        stroke = (el.get('stroke') or '').strip().lower()
        style = (el.get('style') or '').lower()
        style_stroke = re.search(r'stroke\s*:\s*([^;]+)', style)
        if style_stroke:
            stroke = style_stroke.group(1).strip().lower()
        cls = (el.get('class') or '').lower()
        has_stroke_attr = stroke not in ('', 'none')
        styled_line = has_stroke_attr or 'transitline' in cls or 'line' in cls
        if not styled_line:
            continue
        stroke_width = el.get('stroke-width')
        if not stroke_width:
            m_w = re.search(r'stroke-width\s*:\s*([\d.]+)', style)
            stroke_width = m_w.group(1) if m_w else None
        try:
            if stroke_width is not None and float(stroke_width) <= 0:
                continue
        except ValueError:
            pass
        d = el.get('d') or ''
        coords = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
        pts = [(float(a), float(b)) for _, a, b in coords]
        # Guard against degenerate one-point paths (M-only label paths etc.).
        if len(pts) < 2:
            continue
        for i in range(len(pts) - 1):
            segments.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))
    return segments


def _collect_route_stops_with_names(selected_routes):
    """All (name, lon, lat) stops across the selected routes -- used to
    find, for a given landmark, the nearest real transit stop, so its
    rendered LOOM position can be looked up by name."""
    stops = []
    for route_id in selected_routes:
        try:
            ordered = route_stops_ordered(route_id)
        except Exception:
            continue
        if ordered is None or ordered.empty:
            continue
        for _, row in ordered.iterrows():
            try:
                lon = float(row["stop_lon"])
                lat = float(row["stop_lat"])
            except (TypeError, ValueError):
                continue
            name = "" if pd.isna(row.get("stop_name")) else str(row["stop_name"]).strip()
            if not name:
                continue
            stops.append({"name": name, "lon": lon, "lat": lat})
    return stops


def _find_svg_station_anchor(landmark_record, route_stops, svg_labels):
    """Find where the landmark's nearest real transit stop actually ended
    up in the rendered LOOM SVG, by matching stop names to station-label
    text. Returns (x, y) or None if no confident match is found (nothing
    forces a landmark to a wrong spot when its nearest stop's label can't
    be located)."""
    if not route_stops or not svg_labels:
        return None

    lon, lat = float(landmark_record["lon"]), float(landmark_record["lat"])
    nearest = min(
        route_stops,
        key=lambda s: (s["lon"] - lon) ** 2 + (s["lat"] - lat) ** 2,
    )
    target = _normalize_stop_name_for_match(nearest["name"])
    if not target:
        return None

    for label in svg_labels:
        if _normalize_stop_name_for_match(label["text"]) == target:
            try:
                return float(label["cx"]), float(label["cy"])
            except (TypeError, ValueError):
                return None
    return None


def _find_svg_landmark_anchor(landmark_record, route_stops, svg_labels, k=5):
    """Estimate an octilinear landmark position from several nearby stops."""
    if not route_stops or not svg_labels:
        return None
    label_by_name = {}
    for label in svg_labels:
        key = _normalize_stop_name_for_match(label.get("text", ""))
        if key and key not in label_by_name:
            try:
                label_by_name[key] = (float(label["cx"]), float(label["cy"]))
            except (TypeError, ValueError):
                pass
    lon, lat = float(landmark_record["lon"]), float(landmark_record["lat"])
    coslat = math.cos(math.radians(lat))
    candidates = []
    for stop in route_stops:
        pos = label_by_name.get(_normalize_stop_name_for_match(stop.get("name", "")))
        if pos is None:
            continue
        try:
            slon, slat = float(stop["lon"]), float(stop["lat"])
        except (TypeError, ValueError):
            continue
        dx, dy = (slon-lon)*coslat, slat-lat
        candidates.append((dx*dx + dy*dy, pos[0], pos[1]))
    if not candidates:
        return None
    candidates.sort(key=lambda v: v[0])
    if candidates[0][0] < 1e-10:
        return candidates[0][1], candidates[0][2]
    nearby = candidates[:min(k, len(candidates))]
    weights = [1.0/max(v[0],1e-10) for v in nearby]
    total = sum(weights)
    return (sum(w*v[1] for w,v in zip(weights,nearby))/total,
            sum(w*v[2] for w,v in zip(weights,nearby))/total)


def add_landmarks_to_loom_svg(svg, selected_routes, selected_landmarks,
                               icon_size=28, schematic=False):
    """Embed geographic vector landmarks into the LOOM SVG.

    Each landmark is placed either:
      - anchored to its nearest real transit stop's actual rendered
        position (found by matching stop names to the SVG's own
        station-label text) -- this is the only reliable option in
        schematic/octilinear mode, since octi's layout distorts real-world
        coordinates; or
      - if no matching station label is found, a plain linear scaling of
        its real lon/lat into the map's bounding box (only meaningful in
        the non-schematic, geographically-accurate layout).

    Either way, the icon is then nudged off any transit line it would
    otherwise sit on top of (using the map's actual drawn line geometry,
    not an assumption about where lines "should" be), with a thin dotted
    leader line back to its anchor point when it had to move.
    """
    records = get_landmark_records(selected_landmarks)
    vb = _svg_viewbox(svg)
    if not records or not selected_routes or vb is None:
        return svg

    vx, vy, vw, vh = vb
    route_stops = _collect_route_stops_with_names(selected_routes)
    if not route_stops:
        return svg

    svg_labels = get_svg_label_texts(svg)
    segments = _extract_svg_polyline_segments(svg)

    # Keep the icon comfortably smaller than the whole map canvas. With the
    # 3x UI scale (icon_size 84) on a compact/dense LOOM map, a fixed size
    # can dwarf the lines, so cap it relative to the viewbox and shrink it
    # further when many landmarks share the same canvas.
    eff_size = icon_size
    if segments or svg_labels:
        max_side = max(vw, vh)
        canvas_cap = max_side * (
            0.07 if len(records) > 6 else 0.09 if len(records) > 3 else 0.12
        )
        eff_size = min(eff_size, canvas_cap)
        # Also shrink the whole batch proportionally when landmarks crowd
        # the smaller map dimension.
        min_side_cap = min(vw, vh) * 0.12
        if eff_size > min_side_cap:
            eff_size = max(eff_size * 0.75, min(eff_size, min_side_cap))
    eff_size = max(eff_size, 16.0)

    lon_min = min(s["lon"] for s in route_stops)
    lon_max = max(s["lon"] for s in route_stops)
    lat_min = min(s["lat"] for s in route_stops)
    lat_max = max(s["lat"] for s in route_stops)
    lon_span = max(lon_max-lon_min, 1e-9)
    lat_span = max(lat_max-lat_min, 1e-9)

    def geo_to_svg(lon, lat):
        return (vx + ((lon-lon_min)/lon_span)*vw, vy + ((lat_max-lat)/lat_span)*vh)

    placements = []
    for record in records:
        if schematic:
            anchor = _find_svg_landmark_anchor(record, route_stops, svg_labels, k=5)
            if anchor is None:
                continue
            base_x, base_y = anchor
        else:
            base_x, base_y = geo_to_svg(record["lon"], record["lat"])
        x, y, moved = _clear_landmark_of_lines(
            base_x, base_y, segments, eff_size * 1.6
        )
        placements.append((record, x, y, base_x, base_y, moved))

    # After clearing transit lines, spread icons apart so two landmarks
    # never render on top of each other.
    canvas_limit = max(vx + vw, vy + vh) * 2.0
    _separate_landmark_icons(placements, eff_size, segments, canvas_limit)

    if not placements:
        return svg

    pad = max(icon_size * 2.0, min(vw, vh) * 0.035)
    all_x = [vx, vx + vw] + [p[1] for p in placements]
    all_y = [vy, vy + vh] + [p[2] for p in placements]
    new_min_x, new_max_x = min(all_x) - pad, max(all_x) + pad
    new_min_y, new_max_y = min(all_y) - pad, max(all_y) + pad

    parts = []
    for record, x, y, base_x, base_y, moved in placements:
        if moved:
            parts.append(
                f'<line x1="{base_x:.3f}" y1="{base_y:.3f}" '
                f'x2="{x:.3f}" y2="{y:.3f}" '
                f'stroke="#9ca3af" stroke-width="1" stroke-dasharray="3,3"/>'
            )
        parts.append(_svg_landmark_group(record, x, y, eff_size))

    markup = "\n<!-- Geographic vector landmarks -->\n"
    markup += "".join(parts)
    markup += "\n<!-- End geographic vector landmarks -->\n"

    closing = svg.lower().rfind("</svg>")
    if closing == -1:
        # ET may have serialized tags with a namespace prefix (e.g.
        # "</ns0:svg>") if namespace registration was missed -- fall back
        # to the last element-closing tag rather than silently dropping
        # the landmarks.
        closing = svg.lower().rfind("</")
        if closing == -1:
            return svg
    updated = svg[:closing] + markup + svg[closing:]
    updated = re.sub(
        r'(\bviewBox\s*=\s*["\'])[-\d.eE+]+\s+[-\d.eE+]+\s+[-\d.eE+]+\s+[-\d.eE+]+(["\'])',
        lambda m: m.group(1) + f"{new_min_x:.3f} {new_min_y:.3f} "
                             f"{new_max_x-new_min_x:.3f} {new_max_y-new_min_y:.3f}" + m.group(2),
        updated, count=1, flags=re.IGNORECASE
    )
    return updated


def _separate_landmark_icons(placements, icon_size, segments, max_push):
    """Push landmark icons apart so no two icons overlap each other.

    Two landmarks whose nearest stops anchor them to the same region
    (common in schematic mode, where several landmarks can resolve to the
    same weighted cluster of stop labels) would otherwise be drawn stacked
    on top of one another. This nudges each icon away from its nearest
    already-placed neighbour, one pass at a time, while keeping the result
    clear of the transit lines.
    """
    # Icons are drawn at roughly `icon_size` px and each carries a hover
    # label, so centers need well over one icon-width of separation or the
    # glyphs still visually overlap. 1.7x keeps even the widest custom SVG
    # icons apart (hospital / fun park / durbar square anchor within ~1 km
    # of each other in the real data, so the old 1.15x gap left them
    # stacked on top of one another).
    min_gap = icon_size * 1.7
    moved_any = False
    for i in range(len(placements)):
        record_i, x_i, y_i, bx_i, by_i, moved_i = placements[i]
        for _ in range(48):  # bounded relaxation passes
            best = None
            for j in range(len(placements)):
                if i == j:
                    continue
                _, x_j, y_j = placements[j][0], placements[j][1], placements[j][2]
                dx, dy = x_i - x_j, y_i - y_j
                dist = math.hypot(dx, dy) or 1e-6
                if dist < min_gap and (best is None or dist < best[0]):
                    best = (dist, dx / dist, dy / dist)
            if best is None:
                break
            dist, ux, uy = best
            step = min_gap - dist + icon_size * 0.25
            nx = x_i + ux * step
            ny = y_i + uy * step
            nx, ny, moved = _clear_landmark_of_lines(nx, ny, segments, icon_size)
            nx = max(-max_push, min(max_push, nx))
            ny = max(-max_push, min(max_push, ny))
            x_i, y_i = nx, ny
            moved_i = moved_i or moved
            moved_any = True
        placements[i] = (record_i, x_i, y_i, bx_i, by_i, moved_i)

    # Second phase: if a whole CLUSTER is still tighter than the gap around
    # its shared centroid (several landmarks anchored to nearly the same
    # spot), fan the members out in a ring around that centroid so they
    # don't just slide as one clump.
    n = len(placements)
    if n >= 2:
        cx = sum(p[1] for p in placements) / n
        cy = sum(p[2] for p in placements) / n
        cluster = [p for p in placements if math.hypot(p[1] - cx, p[2] - cy) < min_gap]
        if len(cluster) >= 2:
            ring_r = min_gap * max(1.0, 0.55 * len(cluster))
            by_index = {id(p): idx for idx, p in enumerate(placements)}
            for k, p in enumerate(cluster):
                angle = 2 * math.pi * k / len(cluster)
                tx = cx + math.cos(angle) * ring_r
                ty = cy + math.sin(angle) * ring_r
                tx, ty, moved = _clear_landmark_of_lines(tx, ty, segments, icon_size)
                tx = max(-max_push, min(max_push, tx))
                ty = max(-max_push, min(max_push, ty))
                idx = by_index[id(p)]
                rec, _, _, bx, by, mvd = placements[idx]
                placements[idx] = (rec, tx, ty, bx, by, mvd or moved)
                moved_any = True
    return moved_any


def _plotly_landmark_path(record, size_deg=0.0019):
    lat, lon = float(record["lat"]), float(record["lon"])
    sx = size_deg / max(math.cos(math.radians(lat)), 0.2)
    sy = size_deg
    hx, hy = sx*0.5, sy*0.5
    x, y = lon, lat
    kind = record.get("kind", "monument")

    if kind == "tower":
        return (
            f"M {x-hx*.32},{y+hy*.95} L {x+hx*.32},{y+hy*.95} "
            f"L {x+hx*.22},{y-hy*.25} L {x-hx*.22},{y-hy*.25} Z "
            f"M {x-hx*.38},{y-hy*.45} L {x+hx*.38},{y-hy*.45} "
            f"L {x+hx*.38},{y-hy*.25} L {x-hx*.38},{y-hy*.25} Z "
            f"M {x},{y-hy*.95} L {x-hx*.35},{y-hy*.42} L {x+hx*.35},{y-hy*.42} Z"
        )
    if kind == "stupa":
        return (
            f"M {x-hx*.72},{y+hy*.58} Q {x},{y+.02*hy} {x+hx*.72},{y+hy*.58} "
            f"L {x+hx*.55},{y+hy*.80} L {x-hx*.55},{y+hy*.80} Z "
            f"M {x-hx*.50},{y-hy*.18} A {hx*.50},{hy*.50} 0 1 0 "
            f"{x+hx*.50},{y-hy*.18} A {hx*.50},{hy*.50} 0 1 0 {x-hx*.50},{y-hy*.18} Z"
        )
    if kind == "park":
        return (
            f"M {x},{y-hy*.75} A {hx*.75},{hy*.75} 0 1 0 {x},{y+hy*.75} "
            f"A {hx*.75},{hy*.75} 0 1 0 {x},{y-hy*.75} Z "
            f"M {x},{y+hy*.50} L {x},{y-hy*.25} "
            f"M {x},{y-hy*.05} L {x-hx*.35},{y-hy*.38} "
            f"M {x},{y+hy*.10} L {x+hx*.34},{y-hy*.18}"
        )
    if kind == "temple":
        return (
            f"M {x},{y-hy*.95} L {x-hx*.72},{y-hy*.05} L {x+hx*.72},{y-hy*.05} Z "
            f"M {x-hx*.42},{y-hy*.02} L {x+hx*.42},{y-hy*.02} "
            f"L {x+hx*.42},{y+hy*.76} L {x-hx*.42},{y+hy*.76} Z"
        )
    return f"M {x},{y-hy*.72} L {x+hx*.72},{y} L {x},{y+hy*.72} L {x-hx*.72},{y} Z"


def _point_segment_dist_and_normal(px, py, ax, ay, bx, by):
    """Shortest distance from point (px,py) to segment (a->b), plus a unit
    vector pointing from the segment out towards the point (used to push a
    landmark icon clear of the line it's closest to)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        ddx, ddy = px - ax, py - ay
        dist = math.hypot(ddx, ddy)
        return (dist, (1.0, 0.0)) if dist == 0 else (dist, (ddx / dist, ddy / dist))
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    cx, cy = ax + t * dx, ay + t * dy
    ddx, ddy = px - cx, py - cy
    dist = math.hypot(ddx, ddy)
    if dist == 0:
        # Point sits exactly on the line -- push perpendicular to it.
        seg_len = math.hypot(dx, dy) or 1.0
        return dist, (-dy / seg_len, dx / seg_len)
    return dist, (ddx / dist, ddy / dist)


def _collect_route_line_segments(fig):
    """Pull every route-line segment (in lon/lat data space) already drawn
    on the figure, so landmark icons can be checked against them."""
    segments = []
    for trace in fig.data:
        mode = getattr(trace, "mode", "") or ""
        if "lines" not in mode:
            continue
        xs, ys = trace.x, trace.y
        if xs is None or ys is None:
            continue
        xs, ys = list(xs), list(ys)
        for i in range(len(xs) - 1):
            x0, y0, x1, y1 = xs[i], ys[i], xs[i + 1], ys[i + 1]
            if None in (x0, y0, x1, y1):
                continue
            segments.append((float(x0), float(y0), float(x1), float(y1)))
    return segments


def _clear_landmark_of_lines(lon, lat, segments, icon_size_deg):
    """Nudge (x, y) away from the nearest route-line segment so the
    landmark icon never sits on top of / touches a transit line. Returns
    (new_x, new_y, moved).

    One push can land the icon on a *different* nearby segment (lines run
    close together), so iterate until the icon is clear of every segment,
    bounded so dense/overlapping geometry can't loop forever.
    """
    radius = (icon_size_deg / 2.0) * 1.15  # icon half-size + a small margin
    x, y = lon, lat
    for _ in range(12):  # bounded passes
        best_dist, best_dir = None, (0.0, 1.0)
        for (x0, y0, x1, y1) in segments:
            dist, direction = _point_segment_dist_and_normal(x, y, x0, y0, x1, y1)
            if best_dist is None or dist < best_dist:
                best_dist, best_dir = dist, direction

        if best_dist is None or best_dist >= radius:
            break

        push = min(radius - best_dist + radius * 0.35, radius * 2.5)
        nx, ny = best_dir
        norm = math.hypot(nx, ny) or 1.0
        nx, ny = nx / norm, ny / norm
        x, y = x + nx * push, y + ny * push
    return x, y, (x, y) != (lon, lat)


def add_landmarks_to_transit_figure(fig, selected_landmarks, icon_size_deg=0.0026):
    """Add landmark icons in Plotly longitude/latitude data coordinates.

    Each landmark is anchored to its real (lon, lat) by default, so it
    stays in the correct relative place as the user zooms/pans, and is
    drawn at a fixed size in data-space (icon_size_deg), so every landmark
    reads at the same visual size regardless of how spread out the
    selected routes are.

    Before drawing, each landmark is checked against every route line
    already on the map; if the icon would touch or overlap a line, it is
    nudged sideways just far enough to clear it, and a thin dotted leader
    line is drawn back to the landmark's real position so its true
    location is still visible.

    If the landmark has a custom uploaded SVG (record["svg"]), that exact
    SVG is embedded as a Plotly layout image -- matching what the LOOM map
    already does with _svg_landmark_group(). Landmarks without a custom SVG
    keep using the built-in vector shape as before.
    """
    segments = _collect_route_line_segments(fig)

    for record in get_landmark_records(selected_landmarks):
        kind = record.get("kind", "monument")
        stroke = {
            "temple": "#7c3aed", "tower": "#dc2626", "stupa": "#ea580c",
            "park": "#16a34a", "monument": "#1d4ed8",
        }.get(kind, "#1d4ed8")

        true_lon, true_lat = float(record["lon"]), float(record["lat"])
        # Nudge the icon off any route line it would otherwise touch --
        # same collision handling the LOOM map uses (_clear_landmark_of_lines
        # works in plain x/y numbers, so pass lon as x and lat as y).
        icon_lon, icon_lat, moved = _clear_landmark_of_lines(
            true_lon, true_lat, segments, icon_size_deg
        )

        if moved:
            fig.add_shape(
                type="line",
                xref="x", yref="y",
                x0=true_lon, y0=true_lat, x1=icon_lon, y1=icon_lat,
                line=dict(color="#9ca3af", width=1, dash="dot"),
                layer="above",
            )

        placed_record = dict(record, lon=icon_lon, lat=icon_lat)

        custom_svg = get_landmark_custom_svg(record)
        if custom_svg:
            # Longitude degrees are narrower than latitude degrees away
            # from the equator, so widen sizex to keep the icon visually
            # square -- same correction _plotly_landmark_path() uses.
            sizex = icon_size_deg / max(math.cos(math.radians(icon_lat)), 0.2)
            sizey = icon_size_deg
            fig.add_layout_image(
                dict(
                    source=landmark_svg_data_uri(custom_svg),
                    xref="x", yref="y",
                    x=icon_lon, y=icon_lat,
                    xanchor="center", yanchor="middle",
                    sizex=sizex, sizey=sizey,
                    sizing="contain",
                    layer="above",
                )
            )
        else:
            fig.add_shape(
                type="path",
                path=_plotly_landmark_path(placed_record),
                xref="x", yref="y",
                line=dict(color=stroke, width=2.5),
                fillcolor="white",
                layer="above",
            )
        # Name label: hidden by default, revealed only when the icon is
        # touched/tapped (mobile) or hovered (desktop) -- a real click-to-
        # toggle needs custom JS wired into the embedded plot HTML, but an
        # invisible marker with Plotly's own built-in hover tooltip gets the
        # same "touch it to see the name, otherwise nothing shows" behavior
        # for free: on touch devices, tapping a point fires the same hover
        # event a mouse-over would, and the tooltip disappears again once
        # you tap/move elsewhere.
        touch_px = 30 * max(icon_size_deg / 0.0026, 1.0)
        fig.add_trace(
            go.Scatter(
                x=[icon_lon], y=[icon_lat],
                xaxis="x", yaxis="y",
                mode="markers",
                marker=dict(size=touch_px, color="rgba(0,0,0,0)"),
                                customdata=[[record["name"]]],
                hovertemplate=f"<b>{html.escape(record['name'])}</b><extra></extra>",
                showlegend=False,
            )
        )


@st.cache_data
def get_route_color_maps():
    df = fetch_routes()
    name_map = {
        rid: ROUTE_COLOR_NAMES[i % len(ROUTE_COLOR_NAMES)]
        for i, rid in enumerate(df["route_id"])
    }
    hex_map = {rid: ROUTE_COLOR_HEX[name] for rid, name in name_map.items()}
    return name_map, hex_map


# ================= STARTING STOPS (NEW FEATURE) =================
@st.cache_data
def fetch_starting_stops():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
    s.stop_name,
    COUNT(DISTINCT st.trip_id) AS trips_starting_at_stop
FROM stop_times st
JOIN stops s
    ON st.stop_id = s.stop_id
WHERE st.stop_sequence = 1
GROUP BY s.stop_name
ORDER BY trips_starting_at_stop DESC
LIMIT 5;
    """, engine)

@st.cache_data
def route_geom(route_id):
    engine = get_engine()
    df = pd.read_sql(f"""
        SELECT s.shape_id, s.shape_pt_lat, s.shape_pt_lon, s.shape_pt_sequence
        FROM shapes s
        WHERE s.shape_id IN (
            SELECT DISTINCT shape_id
            FROM trips
            WHERE route_id = '{route_id}'
            AND shape_id IS NOT NULL
        )
    """, engine)

    if df.empty:
        return pd.DataFrame(columns=["shape_id", "path"])

    # Ensure shape_pt_sequence is sorted numerically
    df["shape_pt_sequence"] = pd.to_numeric(df["shape_pt_sequence"], errors="coerce")
    df = df.dropna(subset=["shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"])
    df = df.sort_values(["shape_id", "shape_pt_sequence"])

    records = []
    for shape_id, group in df.groupby("shape_id"):
        coords = [
            [lon, lat]
            for lon, lat in zip(group["shape_pt_lon"], group["shape_pt_lat"])
        ]
        if coords:
            records.append({"shape_id": shape_id, "path": coords})

    return pd.DataFrame(records)

@st.cache_data
def stops(route_id):
    engine = get_engine()
    return pd.read_sql(f"""
        SELECT DISTINCT
            s.stop_name,
            s.stop_lat,
            s.stop_lon
        FROM stops s
        JOIN stop_times st ON s.stop_id = st.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        WHERE t.route_id = '{route_id}'
    """, engine)

# ================= ORDERED STOPS FOR TRANSIT MAP (NEW FEATURE) =================
@st.cache_data
def route_stops_ordered(route_id):
    engine = get_engine()

    trip_row = pd.read_sql(f"""
        SELECT t.trip_id, COUNT(*) AS stop_count
        FROM trips t
        JOIN stop_times st ON t.trip_id = st.trip_id
        WHERE t.route_id = '{route_id}'
        GROUP BY t.trip_id
        ORDER BY stop_count DESC
        LIMIT 1
    """, engine)

    if trip_row.empty:
        return pd.DataFrame(columns=["stop_name", "stop_lat", "stop_lon", "stop_sequence"])

    trip_id = trip_row["trip_id"].iloc[0]

    return pd.read_sql(f"""
        SELECT s.stop_name, s.stop_lat, s.stop_lon, st.stop_sequence
        FROM stop_times st
        JOIN stops s ON st.stop_id = s.stop_id
        WHERE st.trip_id = '{trip_id}'
        ORDER BY st.stop_sequence
    """, engine)


def _offset_polyline(lons, lats, offset_deg):
    """Shift a polyline sideways by offset_deg (in lon/lat degrees), using
    the local perpendicular ('normal') direction at each vertex so the
    offset copy stays roughly parallel to the original. Used to fan out
    routes that share the same corridor instead of drawing exactly on top
    of one another."""
    n = len(lons)
    if n < 2 or not offset_deg:
        return list(lons), list(lats)

    new_lons, new_lats = [0.0] * n, [0.0] * n
    for i in range(n):
        if i == 0:
            dx, dy = lons[1] - lons[0], lats[1] - lats[0]
        elif i == n - 1:
            dx, dy = lons[-1] - lons[-2], lats[-1] - lats[-2]
        else:
            dx, dy = lons[i + 1] - lons[i - 1], lats[i + 1] - lats[i - 1]
        length = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / length, dx / length  # unit normal
        new_lons[i] = lons[i] + nx * offset_deg
        new_lats[i] = lats[i] + ny * offset_deg
    return new_lons, new_lats


def build_transit_map(selected_routes, route_color_map, route_name_map,
                      route_agency_map=None,
                      title_text="Transit Map of Kathmandu Valley",
                      separate_overlapping_routes=True,
                      route_spacing=1.0,
                      label_density="Every other stop",
                      show_stop_markers=True,
                      hidden_label_names=(),
                      selected_landmarks=(),
                      landmark_icon_size_deg=0.0026):
    """Build the Plotly transit map with automatic label decluttering.

    The important change here is that labels are treated as screen-space
    objects rather than being separated only by geographic distance.
    Interchanges/terminals are placed first, then ordinary stop labels are
    placed around them using many possible positions.  If a label cannot be
    placed cleanly, the route and stop marker remain visible and the name is
    still available in hover.
    """
    fig = go.Figure()

    route_data = {}
    map_lons, map_lats = [], []
    stop_routes = {}

    # ------------------------------------------------------------
    # LOAD ROUTE STOP SEQUENCES ONCE
    # ------------------------------------------------------------
    for route_id in selected_routes:
        ordered = route_stops_ordered(route_id)
        if ordered.empty:
            continue

        ordered = ordered.copy()
        ordered["stop_lat"] = pd.to_numeric(ordered["stop_lat"], errors="coerce")
        ordered["stop_lon"] = pd.to_numeric(ordered["stop_lon"], errors="coerce")
        ordered = ordered.dropna(subset=["stop_lat", "stop_lon"])
        if ordered.empty:
            continue

        route_data[route_id] = ordered
        map_lons.extend(ordered["stop_lon"].tolist())
        map_lats.extend(ordered["stop_lat"].tolist())

        for _, row in ordered.iterrows():
            name = "" if pd.isna(row["stop_name"]) else str(row["stop_name"]).strip()
            key = (
                name.casefold(),
                round(float(row["stop_lat"]), 6),
                round(float(row["stop_lon"]), 6),
            )
            stop_routes.setdefault(key, []).append(route_id)

    landmark_records = get_landmark_records(selected_landmarks)
    map_lons.extend([r["lon"] for r in landmark_records])
    map_lats.extend([r["lat"] for r in landmark_records])

    if not route_data:
        fig.add_annotation(
            text="No stop-sequence data found for the selected route(s).",
            showarrow=False,
            font=dict(size=16, color="#666666"),
            xref="paper", yref="paper", x=0.5, y=0.5,
        )
        return fig

    for key in stop_routes:
        stop_routes[key] = list(dict.fromkeys(stop_routes[key]))

    shared_stops = {k for k, routes in stop_routes.items() if len(routes) > 1}

    bbox_diag = math.hypot(
        max(map_lons) - min(map_lons),
        max(map_lats) - min(map_lats),
    )
    bbox_diag = max(bbox_diag, 0.01)

    # Keep parallel routes visually separated without moving them too far.
    route_offset_unit = bbox_diag * 0.010 * route_spacing

    def format_stop_name(stop_name, max_chars=18):
        """Wrap long stop names so they do not create very wide labels."""
        if pd.isna(stop_name):
            return ""
        text = str(stop_name).strip()
        if not text:
            return ""

        words = text.split()
        lines = []
        current = ""
        for word in words:
            # Break extremely long single words as a last resort.
            if len(word) > max_chars:
                if current:
                    lines.append(current)
                    current = ""
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                if word:
                    current = word
            elif not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current += " " + word
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)
        return "<br>".join(lines)

    def stop_label_name(stop_name):
        """Group numbered variants such as 'Gaushala 1' and 'Gaushala 2'."""
        text = "" if pd.isna(stop_name) else str(stop_name).strip()
        return re.sub(r"\s+\d+\s*$", "", text).strip() or text

    hidden_label_keys = {
        str(name).strip().casefold()
        for name in hidden_label_names
        if str(name).strip()
    }

    # ------------------------------------------------------------
    # SCREEN-SPACE LABEL COLLISION ENGINE
    # ------------------------------------------------------------
    plot_width_px = 980
    plot_height_px = 680
    label_lon_min, label_lon_max = min(map_lons), max(map_lons)
    label_lat_min, label_lat_max = min(map_lats), max(map_lats)

    def label_width_chars(label):
        return max((len(line) for line in label.split("<br>")), default=0)

    def label_box(label, x, y, xshift, yshift, xanchor, yanchor, font_size=10):
        x_range = max(label_lon_max - label_lon_min, 1e-9)
        y_range = max(label_lat_max - label_lat_min, 1e-9)

        anchor_x = (x - label_lon_min) / x_range * plot_width_px + xshift
        anchor_y = (label_lat_max - y) / y_range * plot_height_px - yshift

        # Arial/Plotly text is approximately 6.5 px per character at 10 px.
        width = max(label_width_chars(label) * (font_size * 0.62), 28) + 10
        height = max(len(label.split("<br>")) * (font_size + 4), font_size + 4) + 8

        if xanchor == "right":
            left = anchor_x - width
        elif xanchor == "center":
            left = anchor_x - width / 2
        else:
            left = anchor_x

        if yanchor == "top":
            top = anchor_y
        elif yanchor == "middle":
            top = anchor_y - height / 2
        else:
            top = anchor_y - height

        return left, top, left + width, top + height

    label_positions = [
        (24, 0, "left", "middle"),
        (-24, 0, "right", "middle"),
        (38, 0, "left", "middle"),
        (-38, 0, "right", "middle"),
    ]

    occupied_label_boxes = []
    placed_leader_lines = []  # ((x1,y1),(x2,y2)) of already-placed leaders
    label_counter = 0

    def _segments_cross(seg_a, seg_b):
        """True if two line segments properly intersect."""
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        def is_point_on_seg(p, q, r):
            return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
                    and min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))

        p1, p2 = seg_a
        q1, q2 = seg_b
        d1 = cross(q1, q2, p1)
        d2 = cross(q1, q2, p2)
        d3 = cross(p1, p2, q1)
        d4 = cross(p1, p2, q2)
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            return True
        return False

    def leader_crosses_existing(anchor_x, anchor_y, end_x, end_y, min_angle_diff=20):
        """True if this leader line crosses any placed leader, or approaches
        one at nearly the same angle near the anchor (which makes two labels
        look ambiguous about which stop they belong to)."""
        for (q1, q2) in placed_leader_lines:
            if _segments_cross(((anchor_x, anchor_y), (end_x, end_y)), (q1, q2)):
                return True


            a1 = math.atan2(end_y - anchor_y, end_x - anchor_x)
            a2 = math.atan2(q2[1] - q1[1], q2[0] - q1[0])
            diff = abs(math.degrees(a1 - a2)) % 180.0
            diff = min(diff, 180.0 - diff)
            if diff < min_angle_diff:

                if math.hypot(anchor_x - q1[0], anchor_y - q1[1]) < 90:
                    return True
        return False

    def choose_label_position(label, x, y, font_size=10, extra_gap=7):
        """Return a collision-free annotation position, or None."""
        nonlocal label_counter
        for attempt in range(len(label_positions)):
            position_index = (label_counter + attempt) % len(label_positions)
            xshift, yshift, xanchor, yanchor = label_positions[position_index]

            candidate = label_box(
                label, x, y,
                xshift, -yshift,
                xanchor, yanchor,
                font_size=font_size,
            )

            padded = (
                candidate[0] - extra_gap,
                candidate[1] - extra_gap,
                candidate[2] + extra_gap,
                candidate[3] + extra_gap,
            )

            collision = any(
                padded[0] < box[2]
                and box[0] < padded[2]
                and padded[1] < box[3]
                and box[1] < padded[3]
                for box in occupied_label_boxes
            )

            if not collision:
                label_counter = position_index + 1
                occupied_label_boxes.append(padded)
                return xshift, yshift, xanchor, yanchor

        return None

    def add_stop_label(label, x, y, font_size=10, arrow_color="#777777"):
        """Add one collision-free label and return whether it was placed."""
        if not label:
            return False

        position = choose_label_position(
            label, x, y, font_size=font_size, extra_gap=8
        )
        if position is None:
            return False

        xshift, yshift, xanchor, yanchor = position
        fig.add_annotation(
            x=x,
            y=y,
            xref="x",
            yref="y",
            text=label,
            showarrow=False,
            xshift=xshift,
            yshift=yshift,
            xanchor=xanchor,
            yanchor=yanchor,
            align=(
                "left" if xanchor == "left"
                else "right" if xanchor == "right"
                else "center"
            ),
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            borderpad=0,
            font=dict(
                size=font_size,
                color="#111111",
                family="Arial, sans-serif",
            ),
        )
        return True

    # ------------------------------------------------------------
    # DRAW ROUTES + STOP MARKERS
    # ------------------------------------------------------------
    n_routes = max(len(route_data), 1)
    draw_cache = {}

    for route_index, (route_id, ordered) in enumerate(route_data.items()):
        base_color = route_color_map.get(route_id, "blue")
        color = ROUTE_COLOR_HEX.get(base_color, base_color)
        route_label = route_name_map.get(route_id, route_id)
        agency_label = (route_agency_map or {}).get(route_id, "Unknown Agency")
        agency_group = f"agency-{agency_label}"

        # Agency heading: its own legend row (bold, no visible glyph) so
        # EVERY route keeps its own color swatch underneath it.
        first_agency_route = not any(
            getattr(trace, "legendgroup", None) == agency_group
            for trace in fig.data
        )
        if first_agency_route:
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=1, color="rgba(0,0,0,0)", opacity=0),
                name=f"<b>{html.escape(str(agency_label))}</b>",
                legendgroup=agency_group,
                showlegend=True,
                hoverinfo="skip",
                uid=f"agency-{route_id}",
            ))

        legend_name = html.escape(str(route_label))

        lons = ordered["stop_lon"].tolist()
        lats = ordered["stop_lat"].tolist()

        if separate_overlapping_routes and n_routes > 1:
            offset_deg = route_offset_unit * (
                route_index - (n_routes - 1) / 2.0
            )
            draw_lons, draw_lats = _offset_polyline(lons, lats, offset_deg)
        else:
            draw_lons, draw_lats = lons, lats

        draw_cache[route_id] = (draw_lons, draw_lats)

        line_lons, line_lats = draw_lons, draw_lats

        fig.add_trace(go.Scatter(
            x=line_lons,
            y=line_lats,
            mode="lines",
            line=dict(color=color, width=5.0),
            name=legend_name,
            hoverinfo="skip",
            legendgroup=agency_group,
            uid=f"line-{route_id}",
            cliponaxis=False,
        ))

        marker_size = 8 if show_stop_markers else 9
        marker_color = "white" if show_stop_markers else "rgba(0,0,0,0)"
        marker_line_width = 2.5 if show_stop_markers else 0

        hover_names = [
            "" if pd.isna(v) else str(v).strip()
            for v in ordered["stop_name"]
        ]
        hover_sequences = ordered["stop_sequence"].tolist()

        fig.add_trace(go.Scatter(
            x=draw_lons,
            y=draw_lats,
            mode="markers",
            marker=dict(
                size=marker_size,
                color=marker_color,
                line=dict(color=color, width=marker_line_width),
            ),
            text=hover_names,
            customdata=hover_sequences,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Route: " + html.escape(str(route_label)) +
                "<br>Stop sequence: %{customdata}<extra></extra>"
            ),
            showlegend=False,
            legendgroup=agency_group,
            cliponaxis=False,
            uid=f"stops-{route_id}",
        ))

    # ------------------------------------------------------------
    # DRAW SHARED / INTERCHANGE CONNECTORS AND MARKERS
    # ------------------------------------------------------------
    shared_records = []

    for shared_key in shared_stops:
        name_key, lat, lon = shared_key
        routes_here = stop_routes[shared_key]
        if not routes_here:
            continue

        shared_name = name_key
        for rid in routes_here:
            ordered = route_data[rid]
            for _, row in ordered.iterrows():
                candidate = (
                    "" if pd.isna(row["stop_name"])
                    else str(row["stop_name"]).strip()
                )
                if candidate.casefold() == name_key:
                    shared_name = candidate
                    break
            if shared_name != name_key:
                break

        label_name = stop_label_name(shared_name)
        if label_name.casefold() in hidden_label_keys:
            continue

        # NEW: tie the interchange circle to the legend group of whichever
        # route "owns" it first, so toggling that route's legend entry also
        # hides the shared/interchange marker instead of leaving it stuck
        # on the map forever. (A circle shared by routes from different
        # agencies can only follow ONE of those legend groups -- see the
        # caveat below build_transit_map.)
        anchor_route = routes_here[0]
        anchor_agency = (route_agency_map or {}).get(anchor_route, "Unknown Agency")
        shared_legendgroup = f"agency-{anchor_agency}"

        shared_points = []
        shared_colors = []
        shared_hovertext = []
        for rid in routes_here:
            ordered = route_data[rid]
            draw_lons, draw_lats = draw_cache[rid]
            for index, (_, row) in enumerate(ordered.iterrows()):
                candidate_name = (
                    "" if pd.isna(row["stop_name"])
                    else str(row["stop_name"]).strip()
                )
                candidate_key = (
                    candidate_name.casefold(),
                    round(float(row["stop_lat"]), 6),
                    round(float(row["stop_lon"]), 6),
                )
                if candidate_key == shared_key:
                    shared_points.append((draw_lons[index], draw_lats[index]))
                    shared_colors.append(
                        ROUTE_COLOR_HEX.get(
                            route_color_map.get(rid, "blue"),
                            "#234FC9",
                        )
                    )
                    shared_hovertext.append(shared_name)
                    break

        if shared_points:
            fig.add_trace(go.Scatter(
                x=[point[0] for point in shared_points],
                y=[point[1] for point in shared_points],
                mode="markers",
                marker=dict(
                    size=14,
                    symbol="circle",
                    color="white",
                    line=dict(color=shared_colors, width=2.5),
                ),
                hovertext=shared_hovertext,
                hovertemplate=(
                    "<b>%{hovertext}</b><br>Shared by "
                    + str(len(routes_here))
                    + " routes<extra></extra>"
                ),
                showlegend=False,
                legendgroup=shared_legendgroup,
                cliponaxis=False,
                uid=f"shared-center-{name_key}",
            ))

        if label_density != "Major exchanges only" or is_major_transit_stop(label_name):
            shared_records.append({
                "name": label_name,
                "lat": lat,
                "lon": lon,
                "routes": routes_here,
            })

    # ------------------------------------------------------------
    # BUILD LABEL CANDIDATES
    # ------------------------------------------------------------
    label_candidates = []
    seen_candidate_keys = set()

    # Interchanges have the highest priority.
    for record in shared_records:
        key = (
            "shared",
            record["name"].casefold(),
            round(record["lat"], 6),
            round(record["lon"], 6),
        )
        if key in seen_candidate_keys:
            continue
        seen_candidate_keys.add(key)
        label_candidates.append({
            "priority": 0,
            "name": record["name"],
            "lat": record["lat"],
            "lon": record["lon"],
            "font_size": 11,
        })

    # Collect terminal and ordinary stops.
    for route_id, ordered in route_data.items():
        draw_lons, draw_lats = draw_cache[route_id]
        last_index = len(ordered) - 1

        for index, (_, stop_row) in enumerate(ordered.iterrows()):
            stop_name = (
                "" if pd.isna(stop_row["stop_name"])
                else str(stop_row["stop_name"]).strip()
            )
            stop_lat = float(stop_row["stop_lat"])
            stop_lon = float(stop_row["stop_lon"])
            stop_key = (
                stop_name.casefold(),
                round(stop_lat, 6),
                round(stop_lon, 6),
            )

            if stop_key in shared_stops:
                continue

            label_name = stop_label_name(stop_name)
            if not label_name or label_name.casefold() in hidden_label_keys:
                continue

            is_terminal = index == 0 or index == last_index

            if label_density == "Major exchanges only":
                if not is_major_transit_stop(label_name):
                    continue

            if label_density == "Terminals & interchanges only" and not is_terminal:
                continue

            if label_density == "Every other stop" and not is_terminal and index % 2 == 1:
                continue

            label_candidates.append({
                "priority": 1 if is_terminal else 2,
                "name": label_name,
                "lat": stop_lat,
                "lon": stop_lon,
                "font_size": 11 if is_terminal else 10,
                "base_lat": stop_lat,
                "base_lon": stop_lon,
            })

    deduped_candidates = []
    seen_base_names = set()
    for candidate in label_candidates:
        name_key = candidate["name"].casefold()
        if name_key in seen_base_names:
            continue
        seen_base_names.add(name_key)
        deduped_candidates.append(candidate)

    # Highest priority first; among ordinary stops, preserve route order.
    deduped_candidates.sort(key=lambda item: item["priority"])

    # ------------------------------------------------------------
    # PLACE LABELS
    # ------------------------------------------------------------
    for candidate in deduped_candidates:
        label = format_stop_name(candidate["name"])
        if not label:
            continue

        font_size = candidate.get("font_size", 10)
        if label_width_chars(label) > 20 and font_size > 10:
            font_size = 10

        add_stop_label(
            label,
            candidate["lon"],
            candidate["lat"],
            font_size=font_size,
            arrow_color="#666666" if candidate["priority"] < 2 else "#999999",
        )


    # ------------------------------------------------------------
    # LEGEND SYMBOLS
    # ------------------------------------------------------------
    symbol_stop_color = ROUTE_COLOR_HEX.get(
        route_color_map.get(next(iter(route_data), ""), "blue"), "#1d4ed8"
    )

    first_shared_colors = []
    for shared_key in shared_stops:
        for rid in stop_routes[shared_key]:
            first_shared_colors.append(
                ROUTE_COLOR_HEX.get(route_color_map.get(rid, "blue"), "#1d4ed8")
            )
            break
        break
    symbol_interchange_color = (
        first_shared_colors[0] if first_shared_colors else symbol_stop_color
    )

    # Symbols section in the same format as the LOOM legend:
    #   Symbols
    #   -- Route line (color = route)
    #   o  Bus stop / station
    #   O  Interchange (shared stop)
    #   -- Station name (text beside a stop)
    # 'Symbols' gets its own heading row so every symbol entry keeps
    # its own glyph.
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=1, color="rgba(0,0,0,0)", opacity=0),
        name="<b>Symbols</b>",
        legendgroup="symbols",
        legend="legend2",
        showlegend=True,
        hoverinfo="skip",
        uid="legend-symbol-header",
    ))

    fig.add_trace(go.Scatter(
        x=[None, None],
        y=[None, None],
        mode="lines",
        line=dict(color=symbol_stop_color, width=5),
        name="Route line (color = route)",
        legendgroup="symbols",
        legend="legend2",
        showlegend=True,
        hoverinfo="skip",
        uid="legend-symbol-line",
    ))

    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            size=8,
            symbol="circle",
            color="white",
            line=dict(color=symbol_stop_color, width=2.5),
        ),
        name="Bus stop / station",
        legendgroup="symbols",
        legend="legend2",
        showlegend=True,
        hoverinfo="skip",
        uid="legend-symbol-stop",
    ))

    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            size=14,
            symbol="circle",
            color="white",
            line=dict(color=symbol_interchange_color, width=2.5),
        ),
        name="Interchange (shared stop)",
        legendgroup="symbols",
        legend="legend2",
        showlegend=True,
        hoverinfo="skip",
        uid="legend-symbol-interchange",
    ))

    fig.add_trace(go.Scatter(
        x=[None, None],
        y=[None, None],
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0.01),
        name="Station name (text)",
        legendgroup="symbols",
        legend="legend2",
        showlegend=True,
        hoverinfo="skip",
        uid="legend-symbol-text",
    ))

    # ------------------------------------------------------------
    # VECTOR LANDMARKS
    # ------------------------------------------------------------
    add_landmarks_to_transit_figure(fig, selected_landmarks, icon_size_deg=landmark_icon_size_deg)

    # ------------------------------------------------------------
    # FINAL LAYOUT
    # ------------------------------------------------------------
    lon_min, lon_max = min(map_lons), max(map_lons)
    lat_min, lat_max = min(map_lats), max(map_lats)

    lon_padding = max((lon_max - lon_min) * 0.36, 0.012)
    lat_padding = max((lat_max - lat_min) * 0.36, 0.012)

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=title_text,
            font=dict(size=24, color="#111111"),
            x=0.5,
            xanchor="center",
            yanchor="top",
        ),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#111111"),
        legend=dict(
            orientation="v",
            bgcolor="rgba(255,255,255,0.94)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
            font=dict(color="#111111", size=11),
            title=dict(
                text="<b>Routes</b>",
                font=dict(size=12, color="#111111"),
                side="top",
            ),
            xref="paper",
            yref="paper",
            x=0.99,
            y=0.02,
            xanchor="right",
            yanchor="bottom",
            groupclick="togglegroup",
            itemsizing="trace",
            tracegroupgap=2,
        ),
        # Symbols live in their own legend column (top-right) so the
        # legend area reads as two columns: Routes | Symbols.
        legend2=dict(
            orientation="v",
            bgcolor="rgba(255,255,255,0.94)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
            font=dict(color="#111111", size=11),
            title=dict(
                text="<b>Symbols</b>",
                font=dict(size=12, color="#111111"),
                side="top",
            ),
            xref="paper",
            yref="paper",
            x=0.99,
            y=0.98,
            xanchor="right",
            yanchor="top",
            itemsizing="trace",
            tracegroupgap=2,
        ),
        xaxis=dict(
            visible=False,
            range=[lon_min - lon_padding, lon_max + lon_padding],
            scaleanchor="y",
            scaleratio=0.89,
            fixedrange=False,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            visible=False,
            range=[lat_min - lat_padding, lat_max + lat_padding],
            fixedrange=False,
            showgrid=False,
            zeroline=False,
        ),
        autosize=True,
        height=860,
        margin=dict(t=90, b=45, l=45, r=45),
        hovermode="closest",
        dragmode="pan",
        uirevision=",".join(sorted(selected_routes)),
    )


    return fig


@st.cache_data
def hubs():
    engine = get_engine()
    try:
        return pd.read_sql(
            "SELECT osm_latitude, osm_longitude FROM hub",
            engine
        )
    except:
        return pd.DataFrame(columns=["osm_latitude", "osm_longitude"])

    # ================= COMMON STOPS =================
@st.cache_data
def common_stops(route_ids):

    if len(route_ids) < 2:
        return pd.DataFrame()

    engine = get_engine()

    route_list = ",".join([f"'{r}'" for r in route_ids])

    query = f"""
        SELECT
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon,
            COUNT(DISTINCT t.route_id) AS route_count
        FROM stops s
        JOIN stop_times st
            ON s.stop_id = st.stop_id
        JOIN trips t
            ON st.trip_id = t.trip_id
        WHERE t.route_id IN ({route_list})
        GROUP BY
            s.stop_id,
            s.stop_name,
            s.stop_lat,
            s.stop_lon
        HAVING COUNT(DISTINCT t.route_id) = {len(route_ids)}
    """
    return pd.read_sql(query, engine)

# ================= ROUTE DURATION =================
@st.cache_data
def route_durations():
    return pd.read_sql("""
        SELECT
    t.route_id,
    t.trip_id,
    (
        EXTRACT(EPOCH FROM MAX(st.arrival_time)::time) -
        EXTRACT(EPOCH FROM MIN(st.departure_time)::time)
    ) / 60 AS duration
FROM trips t
JOIN stop_times st ON t.trip_id = st.trip_id
GROUP BY t.route_id, t.trip_id
ORDER BY duration DESC;
    """, get_engine())

# ============================================================
# LOOM TRANSIT MAP
# ============================================================

LOOM_DIR_WSL = "/home/neetu/loom/build"
LOOM_DIR_NATIVE = os.getenv(
    "LOOM_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "loom-binaries"),
)
GTFS_ROUTE_TYPE = "bus"


def loom_uses_wsl():
    return platform.system() == "Windows"


def loom_binary_path(binary):
    return os.path.join(LOOM_DIR_NATIVE, binary)


def run_loom_command(command):
    if loom_uses_wsl():
        result = subprocess.run(
            ["wsl", "bash", "-lc", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        result = subprocess.run(
            ["bash", "-lc", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    if result.returncode != 0:
        raise RuntimeError(
            "LOOM command failed.\n\n"
            f"COMMAND:\n{command}\n\nERROR:\n{result.stderr}"
        )
    return result.stdout


def run_wsl_command(command):
    """Backward-compatible wrapper for older callers."""
    result = subprocess.run(
        ["wsl", "bash", "-lc", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "LOOM command failed.\n\n"
            f"COMMAND:\n{command}\n\nERROR:\n{result.stderr}"
        )
    return result.stdout


def windows_path_to_wsl(path):
    if not loom_uses_wsl():
        return os.path.abspath(path)
    path = os.path.abspath(path)
    return f"/mnt/{path[0].lower()}{path[2:].replace(chr(92), '/') }"


def _sql_values(values):
    return ",".join(
        "'" + str(value).replace("'", "''") + "'"
        for value in values
    )


def normalize_gtfs_date(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if len(value) == 8 and value.isdigit():
        return value
    try:
        return pd.to_datetime(value).strftime("%Y%m%d")
    except Exception:
        return value


@st.cache_data(show_spinner=False)
def create_filtered_gtfs(selected_routes_tuple):
    selected_routes = list(selected_routes_tuple)
    if not selected_routes:
        raise ValueError("No route was selected.")

    engine = get_engine()
    route_values = _sql_values(selected_routes)
    routes_df = pd.read_sql(
        f"SELECT * FROM routes WHERE route_id IN ({route_values})", engine
    )
    trips_df = pd.read_sql(
        f"SELECT * FROM trips WHERE route_id IN ({route_values})", engine
    )
    if routes_df.empty:
        raise ValueError("Selected route(s) were not found in routes table.")
    if trips_df.empty:
        raise ValueError("No trips found for selected route(s).")

    trip_values = _sql_values(trips_df["trip_id"].dropna().unique())
    stop_times_df = pd.read_sql(
        f"SELECT * FROM stop_times WHERE trip_id IN ({trip_values}) "
        "ORDER BY trip_id, stop_sequence",
        engine,
    )
    if stop_times_df.empty:
        raise ValueError("No stop_times found for selected route(s).")

    stop_values = _sql_values(stop_times_df["stop_id"].dropna().unique())
    stops_df = pd.read_sql(
        f"SELECT * FROM stops WHERE stop_id IN ({stop_values})", engine
    )
    if stops_df.empty:
        raise ValueError("No stops found for selected route(s).")

    tables = {
        "routes": routes_df,
        "trips": trips_df,
        "stop_times": stop_times_df,
        "stops": stops_df,
    }

    if routes_df["route_id"].isna().any():
        raise ValueError("Selected routes contain an empty route_id.")
    if "route_type" not in routes_df:
        routes_df["route_type"] = 3
    else:
        routes_df["route_type"] = pd.to_numeric(
            routes_df["route_type"], errors="coerce"
        ).fillna(3).astype(int)

    if "agency_id" not in routes_df or routes_df["agency_id"].isna().any():
        raise ValueError("Selected routes contain a missing agency_id.")
    if "service_id" not in trips_df or trips_df["service_id"].isna().any():
        raise ValueError("Selected trips contain a missing service_id.")

    _, route_hex_map = get_route_color_maps()
    routes_df["route_color"] = (
        routes_df["route_id"]
        .map(route_hex_map)
        .fillna("#1d4ed8")
        .astype(str)
        .str.lstrip("#")
        .str.upper()
    )
    routes_df["route_text_color"] = "FFFFFF"

    shapes_df = pd.DataFrame()

    if "wheelchair_boarding" in stops_df:
        stops_df["wheelchair_boarding"] = pd.to_numeric(
            stops_df["wheelchair_boarding"], errors="coerce"
        ).fillna(0).astype(int)
        stops_df.loc[
            ~stops_df["wheelchair_boarding"].isin([0, 1, 2]),
            "wheelchair_boarding",
        ] = 0
    else:
        stops_df["wheelchair_boarding"] = 0

    if "location_type" in stops_df:
        stops_df["location_type"] = pd.to_numeric(
            stops_df["location_type"], errors="coerce"
        ).fillna(0).astype(int)
        stops_df.loc[
            ~stops_df["location_type"].isin([0, 1, 2, 3, 4]),
            "location_type",
        ] = 0
    else:
        stops_df["location_type"] = 0

    if "parent_station" in stops_df:
        stops_df["parent_station"] = stops_df["parent_station"].fillna("")
    else:
        stops_df["parent_station"] = ""

    for column in ("stop_lat", "stop_lon"):
        stops_df[column] = pd.to_numeric(stops_df[column], errors="coerce")
    stops_df = stops_df.dropna(subset=["stop_lat", "stop_lon"])

    for column in ("stop_sequence", "pickup_type", "drop_off_type"):
        if column in stop_times_df:
            stop_times_df[column] = pd.to_numeric(
                stop_times_df[column], errors="coerce"
            ).fillna(0).astype(int)

    if "shape_id" in trips_df:
        shape_values = trips_df["shape_id"].dropna().unique()
        if len(shape_values):
            shapes_df = pd.read_sql(
                f"SELECT * FROM shapes WHERE shape_id IN ({_sql_values(shape_values)}) "
                "ORDER BY shape_id, shape_pt_sequence",
                engine,
            )

    if not shapes_df.empty:
        for column in ("shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"):
            if column in shapes_df:
                shapes_df[column] = pd.to_numeric(
                    shapes_df[column], errors="coerce"
                )
        if "shape_pt_sequence" in shapes_df:
            shapes_df["shape_pt_sequence"] = (
                shapes_df["shape_pt_sequence"].fillna(0).astype(int)
            )
        coordinate_columns = [
            column for column in ("shape_pt_lat", "shape_pt_lon")
            if column in shapes_df
        ]
        if coordinate_columns:
            shapes_df = shapes_df.dropna(subset=coordinate_columns)
        tables["shapes"] = shapes_df

    if "agency_id" in routes_df:
        agency_df = pd.read_sql(
            f"SELECT * FROM agency WHERE agency_id IN "
            f"({_sql_values(routes_df['agency_id'].dropna().unique())})",
            engine,
        )
        if agency_df.empty:
            raise ValueError("No agency records found for selected routes.")

        required_agency_defaults = {
            "agency_name": "Kathmandu Transit",
            "agency_url": "https://example.com/",
            "agency_timezone": "Asia/Kathmandu",
        }
        for column, default in required_agency_defaults.items():
            if column not in agency_df:
                agency_df[column] = default
            else:
                agency_df[column] = agency_df[column].fillna("").astype(str).str.strip()
                agency_df.loc[agency_df[column] == "", column] = default
        tables["agency"] = agency_df

    if "service_id" in trips_df:
        service_values = _sql_values(trips_df["service_id"].dropna().unique())
        for table in ("calendar", "calendar_dates"):
            try:
                tables[table] = pd.read_sql(
                    f"SELECT * FROM {table} WHERE service_id IN ({service_values})",
                    engine,
                )
            except Exception:
                pass

    if "calendar" in tables:
        for column in ("start_date", "end_date"):
            if column in tables["calendar"]:
                tables["calendar"][column] = tables["calendar"][column].apply(
                    normalize_gtfs_date
                )

    if "calendar_dates" in tables and "date" in tables["calendar_dates"]:
        tables["calendar_dates"]["date"] = tables["calendar_dates"]["date"].apply(
            normalize_gtfs_date
        )

    temp_dir = tempfile.mkdtemp(prefix="loom_gtfs_")
    try:
        for table_name, dataframe in tables.items():
            for column in dataframe.select_dtypes(include=["object", "string"]):
                dataframe[column] = dataframe[column].fillna("").astype(str)
            dataframe.to_csv(
                os.path.join(temp_dir, f"{table_name}.txt"),
                index=False,
                na_rep="",
            )

        zip_path = os.path.join(tempfile.gettempdir(), "loom_selected_routes.zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename in os.listdir(temp_dir):
                zip_file.write(
                    os.path.join(temp_dir, filename),
                    arcname=filename,
                )
        return zip_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def check_loom_installation():
    binaries = ("gtfs2graph", "topo", "loom", "octi", "transitmap")
    if loom_uses_wsl():
        if shutil.which("wsl") is None:
            raise RuntimeError(
                "LOOM requires WSL on Windows, but the 'wsl' command was not found."
            )
        missing = []
        for binary in binaries:
            result = subprocess.run(
                [
                    "wsl", "bash", "-lc",
                    f"test -x {shlex.quote(LOOM_DIR_WSL + '/' + binary)}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode:
                missing.append(binary)
    else:
        missing = [
            binary for binary in binaries
            if not os.access(loom_binary_path(binary), os.X_OK)
        ]
    if missing:
        raise RuntimeError(
            "LOOM executable(s) not found: " + ", ".join(missing) +
            (f". Check LOOM_DIR_WSL ({LOOM_DIR_WSL})." if loom_uses_wsl()
             else (
                 ". Streamlit Cloud does not include the LOOM C++ binaries. "
                 f"Build them during deployment or set LOOM_DIR to a directory "
                 f"containing the executables ({LOOM_DIR_NATIVE})."
             ))
        )

    if not loom_uses_wsl():
        dependency_errors = []
        if shutil.which("ldd") is None:
            raise RuntimeError(
                "LOOM dependency check requires ldd, but it was not found."
            )

        for binary in binaries:
            path = loom_binary_path(binary)
            result = subprocess.run(
                ["ldd", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            missing_libraries = [
                line.strip()
                for line in result.stdout.splitlines()
                if "not found" in line
            ]
            if result.returncode != 0 or missing_libraries:
                details = "\n".join(missing_libraries) or result.stdout.strip()
                dependency_errors.append(f"{binary}:\n{details}")

        if dependency_errors:
            raise RuntimeError(
                "\n\n".join(dependency_errors)
            )


def get_octi_help():
    check_loom_installation()
    loom_dir = shlex.quote(LOOM_DIR_WSL if loom_uses_wsl() else LOOM_DIR_NATIVE)
    return run_loom_command(f"{loom_dir}/octi -h 2>&1")


def get_transitmap_help():
    """Run `transitmap -h` against the available Loom build."""
    check_loom_installation()
    loom_dir = shlex.quote(LOOM_DIR_WSL if loom_uses_wsl() else LOOM_DIR_NATIVE)
    return run_loom_command(f"{loom_dir}/transitmap -h 2>&1")
def raise_labels_above_markers(svg):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    def tag_local(el):
        return el.tag.split('}')[-1] if '}' in el.tag else el.tag

    def reorder(el):
        children = list(el)
        if children:
            non_text = [c for c in children if tag_local(c) != 'text']
            text_els = [c for c in children if tag_local(c) == 'text']
            if text_els and non_text:
                for c in children:
                    el.remove(c)
                for c in non_text + text_els:
                    el.append(c)
        for c in el:
            reorder(c)

    reorder(root)
    return ET.tostring(root, encoding="unicode")


def scale_label_font_size(svg, scale_factor=1.5):
    """Scale font sizes encoded in LOOM SVG elements and inline styles."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    def scale_size(match):
        value = float(match.group(1)) * scale_factor
        unit = match.group(2) or ""
        return f"{value:.2f}{unit}"

    def scale_element(element):
        font_size = element.get("font-size")
        if font_size:
            element.set(
                "font-size",
                re.sub(r"([\d.]+)([a-zA-Z%]*)", scale_size, font_size, count=1),
            )

        style = element.get("style")
        if style and re.search(r"font-size\s*:", style):
            style = re.sub(
                r"font-size\s*:\s*([\d.]+)([a-zA-Z%]*)",
                lambda match: f"font-size:{scale_size(match)}",
                style,
            )
            element.set("style", style)

        for child in element:
            scale_element(child)

    scale_element(root)

    # ---- per-glyph tspan fix -----------------------------------------

    text_tag = root.tag.split('}')[0] + '}text' if root.tag.startswith('{') else 'text'
    tspan_tag = text_tag.rsplit('}', 1)[0] + '}tspan' if '}' in text_tag else 'tspan'

    for text in root.iter(text_tag):
        for attr in ('textLength', 'lengthAdjust'):
            text.attrib.pop(attr, None)

        tspans = text.findall(tspan_tag)
        for tspan in tspans:
            for attr in ('textLength', 'lengthAdjust'):
                tspan.attrib.pop(attr, None)

        try:
            anchor_x = float(text.get('x')) if text.get('x') is not None else None
        except (TypeError, ValueError):
            anchor_x = None
        if anchor_x is None:
            for tspan in tspans:
                if tspan.get('x') is not None:
                    try:
                        anchor_x = float(tspan.get('x'))
                        break
                    except (TypeError, ValueError):
                        continue

        for tspan in tspans:
            x_val = tspan.get('x')
            if x_val is not None and anchor_x is not None:
                try:
                    fx = float(x_val)
                    tspan.set('x', f'{anchor_x + (fx - anchor_x) * scale_factor:g}')
                except (TypeError, ValueError):
                    pass
            dx_val = tspan.get('dx')
            if dx_val is not None:
                try:
                    tspan.set('dx', f'{float(dx_val) * scale_factor:g}')
                except (TypeError, ValueError):
                    pass
            dy_val = tspan.get('dy')
            if dy_val is not None:
                try:
                    tspan.set('dy', f'{float(dy_val) * scale_factor:g}')
                except (TypeError, ValueError):
                    pass

    # ---- textPath label-path stretch fix ------------------------------
    textpath_tag = text_tag.rsplit('}', 1)[0] + '}textPath' if '}' in text_tag else 'textPath'
    xlink_href = '{http://www.w3.org/1999/xlink}href'

    path_map = {}
    for el in root.iter():
        if el.tag.rsplit('}', 1)[-1] == 'path' and el.get('id'):
            path_map[el.get('id')] = el

    for text in root.iter(text_tag):
        for tp in text.findall(textpath_tag):
            href = tp.get(xlink_href) or tp.get('href')
            if not href:
                continue
            path_el = path_map.get(href.split('#')[-1])
            if path_el is None:
                continue
            d = path_el.get('d')
            if not d:
                continue
            segs = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
            if len(segs) < 2:
                continue
            pts = [(float(a), float(b)) for _, a, b in segs]
            cmds = [s[0] for s in segs]

            anchor = (tp.get('text-anchor') or text.get('text-anchor') or '').strip().lower()
            offset = (tp.get('startOffset') or '').strip().lower()
            if anchor == 'end' or offset in ('100%', 'end'):
                ref = pts[-1]                      # keep station-side end fixed
            elif anchor == 'middle' or offset == '50%':
                ref = ((pts[0][0] + pts[-1][0]) / 2.0,
                       (pts[0][1] + pts[-1][1]) / 2.0)  # grow both ways
            else:
                ref = pts[0]                       # keep start fixed


            path_stretch = scale_factor * 1.5

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if (max(xs) - min(xs)) >= (max(ys) - min(ys)):
                # horizontal label: stretch x around ref, keep baselines
                newd = ' '.join(
                    f"{c} {ref[0] + (x - ref[0]) * path_stretch:.3f} {y:.3f}"
                    for c, (x, y) in zip(cmds, pts)
                )
            else:
                # vertical label: stretch y around ref
                newd = ' '.join(
                    f"{c} {x:.3f} {ref[1] + (y - ref[1]) * path_stretch:.3f}"
                    for c, (x, y) in zip(cmds, pts)
                )
            path_el.set('d', newd)

    return ET.tostring(root, encoding="unicode")


def remove_line_labels(svg):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    xlink_href = '{http://www.w3.org/1999/xlink}href'
    used_path_ids = set()

    removed = 0
    for parent in root.iter():
        for text in list(parent):
            if text.tag.rsplit('}', 1)[-1] == 'text' and \
                    'line-label' in (text.get('class') or ''):
                for tp in text.iter():
                    if tp.tag.rsplit('}', 1)[-1] == 'textPath':
                        href = tp.get(xlink_href) or tp.get('href')
                        if href:
                            used_path_ids.add(href.split('#')[-1])
                parent.remove(text)
                removed += 1

    if removed:
        for parent in root.iter():
            for path in list(parent):
                if path.tag.rsplit('}', 1)[-1] == 'path' and \
                        path.get('id') in used_path_ids:
                    parent.remove(path)

    return ET.tostring(root, encoding='unicode')


def orient_octilinear_labels(svg):
    """Make station-label reading direction consistent per octilinear angle
    family (0/45/90/135 degrees + their opposites), instead of flattening
    or re-placing labels.

    transitmap -l already picks good label *positions* on octilinear maps
    (see generate_loom_svg's comment on why separate_station_labels() was
    disabled) -- the problem is only which *end* of the label path LOOM
    treats as the start. That can flip independently per stop, so two
    labels sitting at the same visual incline (e.g. two 45-degree labels)
    can end up reading in opposite directions, and one looks upside-down
    or mirrored relative to the other.

    This pass leaves every path's two endpoints, length and midpoint
    untouched -- it only reverses point order (start <-> end) so that:
      - all horizontal labels read left-to-right
      - all vertical labels read bottom-to-top
      - all "/" diagonal labels read bottom-left-to-top-right
      - all "\\" diagonal labels read top-left-to-bottom-right
    which keeps LOOM's native placement/collision-avoidance intact while
    making same-angle labels look uniform.
    """
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    xlink_href = '{http://www.w3.org/1999/xlink}href'
    ns = root.tag.split('}')[0] if root.tag.startswith('{') else ''
    text_tag = ns + '}text' if ns else 'text'
    textpath_tag = ns + '}textPath' if ns else 'textPath'

    path_map = {}
    for el in root.iter():
        if el.tag.rsplit('}', 1)[-1] == 'path' and el.get('id'):
            path_map[el.get('id')] = el

    for text in root.iter(text_tag):
        if 'station-label' not in (text.get('class') or ''):
            continue
        for tp in text.findall(textpath_tag):
            href = tp.get(xlink_href) or tp.get('href')
            if not href:
                continue
            path_el = path_map.get(href.split('#')[-1])
            if path_el is None:
                continue

            d = path_el.get('d') or ''
            segs = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
            if len(segs) < 2:
                continue

            cmds = [s[0] for s in segs]
            pts = [(float(a), float(b)) for _, a, b in segs]
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                continue

            # Canonical rule: the path should point generally rightward
            # (dx > 0). For the pure-vertical case (dx == 0) it should
            # point upward on screen (dy < 0, since SVG y grows downward).
            needs_flip = dx < -1e-6 or (abs(dx) <= 1e-6 and dy > 0)
            if needs_flip:
                rev_pts = list(reversed(pts))
                new_d = ' '.join(
                    f"{c} {x:.3f} {y:.3f}"
                    for c, (x, y) in zip(cmds, rev_pts)
                )
                path_el.set('d', new_d)

    return ET.tostring(root, encoding='unicode')


def shorten_station_labels(svg, max_chars=24):
    """Shorten only displayed station-label text while preserving LOOM label paths."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    def tag_local(el):
        return el.tag.split("}")[-1] if "}" in el.tag else el.tag

    def compact_name(name):
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) <= max_chars:
            return name
        # Prefer the meaningful part before a descriptive suffix.
        for sep in [",", " - ", " – ", " — ", "(", "/"]:
            if sep in name:
                first = name.split(sep, 1)[0].strip()
                if len(first) >= 8:
                    return (first[:max_chars-1].rstrip() + "…") if len(first) > max_chars else first
        # Otherwise keep whole words and add an ellipsis.
        out = ""
        for word in name.split():
            candidate = word if not out else out + " " + word
            if len(candidate) > max_chars - 1:
                break
            out = candidate
        if not out:
            out = name[:max_chars-1].rstrip()
        return out.rstrip(" ,-/–—") + "…"

    for text_el in root.iter():
        if tag_local(text_el) != "text" or "station-label" not in (text_el.get("class") or ""):
            continue
        original = "".join(text_el.itertext()).strip()
        if not original:
            continue
        shortened = compact_name(original)
        if shortened == original:
            continue

        title = ET.Element("{http://www.w3.org/2000/svg}title")
        title.text = original
        text_el.insert(0, title)

        changed = False
        for child in list(text_el):
            if tag_local(child) in ("textPath", "tspan"):
                child.text = shortened
                changed = True
                break
        if not changed:
            text_el.text = shortened

    return ET.tostring(root, encoding="unicode")

def separate_station_labels(svg):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    xlink_href = '{http://www.w3.org/1999/xlink}href'

    path_map = {}
    for el in root.iter():
        if el.tag.rsplit('}', 1)[-1] == 'path' and el.get('id'):
            path_map[el.get('id')] = el

    ns = root.tag.split('}')[0] if root.tag.startswith('{') else ''
    text_tag = ns + '}text' if ns else 'text'
    textpath_tag = ns + '}textPath' if ns else 'textPath'

    labels = []
    for text in root.iter(text_tag):
        if 'station-label' not in (text.get('class') or ''):
            continue
        fs_match = re.search(r'([\d.]+)', text.get('font-size') or '')
        if not fs_match:
            continue
        fs = float(fs_match.group(1))
        for tp in text.findall(textpath_tag):
            href = tp.get(xlink_href) or tp.get('href')
            if not href:
                continue
            path_el = path_map.get(href.split('#')[-1])
            if path_el is None:
                continue
            d = path_el.get('d') or ''
            segs = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
            if len(segs) < 2:
                continue
            pts = [(float(a), float(b)) for _, a, b in segs]
            label_text = ''.join(text.itertext()).strip()
            labels.append({
                'path_el': path_el,
                'pts': pts,
                'cmds': [s[0] for s in segs],
                'fs': fs,
                'text': label_text,
            })

    # Keep every station name horizontal and left-to-right. LOOM can emit
    # label paths in different directions depending on the route geometry.
    for label in labels:
        points = label['pts']
        if len(points) < 2:
            continue

        path_length = sum(
            math.hypot(x2 - x1, y2 - y1)
            for (x1, y1), (x2, y2) in zip(points, points[1:])
        )
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        center_x = (start_x + end_x) / 2
        center_y = (start_y + end_y) / 2
        half_length = max(path_length / 2, label['fs'])
        normalized_points = [
            (center_x - half_length, center_y),
            (center_x + half_length, center_y),
        ]
        label['path_el'].set(
            'd',
            f'M {normalized_points[0][0]:.3f} {normalized_points[0][1]:.3f} '
            f'L {normalized_points[1][0]:.3f} {normalized_points[1][1]:.3f}',
        )
        label['pts'] = normalized_points
        label['cmds'] = ['M', 'L']

    def bbox(lb):
        xs = [p[0] for p in lb['pts']]
        ys = [p[1] for p in lb['pts']]
        horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
        if horiz:
            path_width = max(xs) - min(xs)
            text_width = max(len(lb['text']) * lb['fs'] * 0.62, lb['fs'])
            half_width = max(path_width, text_width) / 2
            center_x = (min(xs) + max(xs)) / 2
            center_y = (min(ys) + max(ys)) / 2
            return (
                center_x - half_width,
                center_y - lb['fs'] * 1.25,
                center_x + half_width,
                center_y + lb['fs'] * 0.25,
                True,
            )
        return min(xs) - lb['fs'], min(ys), max(xs) + lb['fs'], max(ys), False

    def shift(lb, horiz, delta):
        pts = lb['pts']
        if horiz:
            newd = ' '.join(
                f"{c} {x:.3f} {y + delta:.3f}"
                for c, (x, y) in zip(lb['cmds'], pts)
            )
        else:
            newd = ' '.join(
                f"{c} {x + delta:.3f} {y:.3f}"
                for c, (x, y) in zip(lb['cmds'], pts)
            )
        lb['path_el'].set('d', newd)
        lb['pts'] = [(x + (0 if horiz else delta),
                      y + (delta if horiz else 0)) for x, y in pts]

    boxes = []
    for lb in labels:
        x0, y0, x1, y1, horiz = bbox(lb)
        boxes.append({'lb': lb, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                      'horiz': horiz})


    def overlaps(a, b):
        return (a['x0'] < b['x1'] and b['x0'] < a['x1'] and
                a['y0'] < b['y1'] and b['y0'] < a['y1'])

    horiz_boxes = [bx for bx in boxes if bx['horiz']]
    vert_boxes = [bx for bx in boxes if not bx['horiz']]

    for group, axis in ((horiz_boxes, 'y'), (vert_boxes, 'x')):
        group.sort(key=lambda bx: (bx['y0'] + bx['y1']) / 2 if axis == 'y'
                   else (bx['x0'] + bx['x1']) / 2)
        placed = []
        for bx in group:
            fs = bx['lb']['fs']
            step = fs * 1.8
            guard = 0
            while any(overlaps(bx, p) for p in placed) and guard < 40:
                shift(bx['lb'], bx['horiz'], step)
                if axis == 'y':
                    bx['y0'] += step
                    bx['y1'] += step
                else:
                    bx['x0'] += step
                    bx['x1'] += step
                guard += 1
            placed.append(bx)

    return ET.tostring(root, encoding='unicode')


def expand_label_clip_paths(svg, scale_factor=1.5):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    def tag_local(element):
        return element.tag.split('}')[-1] if '}' in element.tag else element.tag

    id_map = {element.get('id'): element for element in root.iter() if element.get('id')}
    parent_map = {child: parent for parent in root.iter() for child in parent}

    def find_clip_id(element):
        current = element
        while current is not None:
            clip_value = current.get('clip-path')
            if not clip_value:
                style = current.get('style', '')
                match = re.search(r'clip-path\s*:\s*url\(#([^)]+)\)', style)
                if match:
                    clip_value = f'url(#{match.group(1)})'
            if clip_value:
                match = re.search(r'url\(#([^)]+)\)', clip_value)
                if match:
                    return match.group(1)
            current = parent_map.get(current)
        return None

    expanded = set()
    for element in root.iter():
        if tag_local(element) != 'text':
            continue
        clip_id = find_clip_id(element)
        clip_path = id_map.get(clip_id) if clip_id else None
        if clip_path is None or clip_id in expanded:
            continue

        for shape in clip_path:
            if tag_local(shape) != 'rect':
                continue
            try:
                x = float(shape.get('x', 0))
                y = float(shape.get('y', 0))
                width = float(shape.get('width', 0))
                height = float(shape.get('height', 0))
            except (TypeError, ValueError):
                continue
            new_width = width * scale_factor
            new_height = height * scale_factor
            shape.set('x', str(x - (new_width - width) / 2))
            shape.set('y', str(y - (new_height - height) / 2))
            shape.set('width', str(new_width))
            shape.set('height', str(new_height))
        expanded.add(clip_id)

    return ET.tostring(root, encoding="unicode")


def bring_labels_to_front(svg):
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    def tag_local(element):
        return element.tag.split('}')[-1] if '}' in element.tag else element.tag

    namespace = root.tag.split('}')[0] + '}' if root.tag.startswith('{') else ''
    root.attrib.pop('clip-path', None)
    root_style = root.get('style')
    if root_style:
        root_style = re.sub(
            r'(^|;)\s*clip-path\s*:\s*url\(#[^)]+\)\s*;?',
            r'\1',
            root_style,
        ).strip('; ')
        if root_style:
            root.set('style', root_style)
        else:
            root.attrib.pop('style', None)
    moved = []

    def walk(element, transform_chain):
        for child in list(element):
            if tag_local(child) == 'text':
                element.remove(child)
                child.attrib.pop('clip-path', None)
                style = child.get('style')
                if style:
                    style = re.sub(
                        r'(^|;)\s*clip-path\s*:\s*url\(#[^)]+\)\s*;?',
                        r'\1',
                        style,
                    ).strip('; ')
                    if style:
                        child.set('style', style)
                    else:
                        child.attrib.pop('style', None)
                moved.append((transform_chain, child))
                continue

            child_transform = child.get('transform')
            next_transform = transform_chain
            if child_transform:
                next_transform = (transform_chain + ' ' + child_transform).strip()
            walk(child, next_transform)

    walk(root, '')

    for transform_chain, text_element in moved:
        if transform_chain:
            wrapper = ET.Element(namespace + 'g')
            wrapper.set('transform', transform_chain)
            wrapper.append(text_element)
            root.append(wrapper)
        else:
            root.append(text_element)

    return ET.tostring(root, encoding="unicode")


def pad_svg_viewbox(svg, pad=150):

    vb_match = re.search(
        r'viewBox="([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)"', svg
    )
    w_match = re.search(r'width="([\d.]+)', svg)
    h_match = re.search(r'height="([\d.]+)', svg)

    if vb_match:
        x, y, w, h = (float(g) for g in vb_match.groups())
        new_x, new_y = x - pad, y - pad
        new_w, new_h = w + 2 * pad, h + 2 * pad
        svg = re.sub(
            r'viewBox="[\-\d.]+\s+[\-\d.]+\s+[\-\d.]+\s+[\-\d.]+"',
            f'viewBox="{new_x} {new_y} {new_w} {new_h}"',
            svg,
            count=1,
        )
    elif w_match and h_match:
        w, h = float(w_match.group(1)), float(h_match.group(1))
        new_w, new_h = w + 2 * pad, h + 2 * pad
        svg = re.sub(
            r'(<svg\b(?![^>]*viewBox))',
            rf'\1 viewBox="-{pad} -{pad} {new_w} {new_h}"',
            svg,
            count=1,
        )
    else:
        return svg

    if w_match:
        w = float(w_match.group(1))
        svg = re.sub(r'width="[\d.]+"', f'width="{w + 2 * pad}"', svg, count=1)
    if h_match:
        h = float(h_match.group(1))
        svg = re.sub(r'height="[\d.]+"', f'height="{h + 2 * pad}"', svg, count=1)

    return svg


# ============================================================
# MANUAL LABEL OVERRIDES (NEW FEATURE)
# ============================================================

def get_svg_label_texts(svg):
    """Return [{'text', 'cx', 'cy'}] for every station-label in the SVG,
    used to populate the 'which label do you want to fix' dropdown."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return []

    def tag_local(el):
        return el.tag.split('}')[-1] if '}' in el.tag else el.tag

    xlink_href = '{http://www.w3.org/1999/xlink}href'
    path_map = {
        el.get('id'): el for el in root.iter()
        if tag_local(el) == 'path' and el.get('id')
    }

    labels = []
    for text in root.iter():
        if tag_local(text) != 'text' or 'station-label' not in (text.get('class') or ''):
            continue
        label_text = ''.join(text.itertext()).strip()
        if not label_text:
            continue

        cx = cy = None
        for tp in text:
            if tag_local(tp) == 'textPath':
                href = tp.get(xlink_href) or tp.get('href')
                path_el = path_map.get((href or '').split('#')[-1])
                if path_el is not None:
                    d = path_el.get('d') or ''
                    segs = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
                    if segs:
                        xs = [float(a) for _, a, b in segs]
                        ys = [float(b) for _, a, b in segs]
                        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

        if cx is None:
            try:
                cx, cy = float(text.get('x') or 0), float(text.get('y') or 0)
            except (TypeError, ValueError):
                cx, cy = 0.0, 0.0

        labels.append({'text': label_text, 'cx': cx, 'cy': cy})

    return labels


def apply_manual_label_overrides(svg, label_overrides):
    """
    label_overrides: {label_text: {'rotate': deg, 'dx': px, 'dy': px}}
    Wraps only the matching <text class="station-label"> (and its textPath
    path, if it has one) in its own <g transform="..."> so it moves/rotates
    independently of everything else LOOM drew.
    """
    if not label_overrides:
        return svg
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return svg

    ns = root.tag.split('}')[0] + '}' if root.tag.startswith('{') else ''

    def tag_local(el):
        return el.tag.split('}')[-1] if '}' in el.tag else el.tag

    parent_map = {c: p for p in root.iter() for c in p}
    xlink_href = '{http://www.w3.org/1999/xlink}href'
    path_map = {
        el.get('id'): el for el in root.iter()
        if tag_local(el) == 'path' and el.get('id')
    }

    for text in list(root.iter()):
        if tag_local(text) != 'text' or 'station-label' not in (text.get('class') or ''):
            continue
        label_text = ''.join(text.itertext()).strip()
        override = label_overrides.get(label_text)
        if not override:
            continue

        parent = parent_map.get(text)
        if parent is None:
            continue

        cx = cy = 0.0
        owned_path = None
        for tp in text:
            if tag_local(tp) == 'textPath':
                href = tp.get(xlink_href) or tp.get('href')
                owned_path = path_map.get((href or '').split('#')[-1])
                if owned_path is not None:
                    d = owned_path.get('d') or ''
                    segs = re.findall(r'([A-Za-z])\s*(-?[\d.eE+]+)[\s,]+(-?[\d.eE+]+)', d)
                    if segs:
                        xs = [float(a) for _, a, b in segs]
                        ys = [float(b) for _, a, b in segs]
                        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

        if cx == 0 and cy == 0:
            try:
                cx = float(text.get('x') or 0)
                cy = float(text.get('y') or 0)
            except (TypeError, ValueError):
                pass

        angle = override.get('rotate', 0)
        dx = override.get('dx', 0)
        dy = override.get('dy', 0)

        wrapper = ET.Element(ns + 'g')
        wrapper.set('transform', f'translate({dx},{dy}) rotate({angle} {cx:.2f} {cy:.2f})')

        parent.remove(text)
        wrapper.append(text)

        if owned_path is not None:
            path_parent = parent_map.get(owned_path)
            if path_parent is not None:
                path_parent.remove(owned_path)
                wrapper.append(owned_path)

        parent.append(wrapper)

    return ET.tostring(root, encoding='unicode')


@st.cache_data(show_spinner=False)
def generate_loom_svg(
    selected_routes_tuple,
    schematic=True,
    octi_extra_args="",
    line_width=40,
    line_spacing=20,
    label_pad=150,
    label_font_scale=1.0,
    selected_landmarks=(),
    landmark_icon_size=28,
):
    if not selected_routes_tuple:
        raise ValueError("Please select at least one route.")
    check_loom_installation()
    gtfs_wsl = windows_path_to_wsl(create_filtered_gtfs(selected_routes_tuple))
    loom_dir = shlex.quote(LOOM_DIR_WSL if loom_uses_wsl() else LOOM_DIR_NATIVE)

    octi_cmd = f"{loom_dir}/octi"
    if octi_extra_args and octi_extra_args.strip():
        octi_cmd += f" {octi_extra_args.strip()}"


    transitmap_cmd = (
        f"{loom_dir}/transitmap -l "
        f"--line-width {line_width} --line-spacing {line_spacing}"
    )

    command = (
        "set -o pipefail; "
        f"{loom_dir}/gtfs2graph -m {shlex.quote(GTFS_ROUTE_TYPE)} "
        f"{shlex.quote(gtfs_wsl)} | {loom_dir}/topo | {loom_dir}/loom | "
        + (f"{octi_cmd} | " if schematic else "")
        + transitmap_cmd
    )
    svg = run_loom_command(command)
    if not svg or "<svg" not in svg.lower():
        raise RuntimeError(
            f"LOOM did not return a valid SVG.\n\nOutput:\n{svg[:2000]}"
        )

    svg = raise_labels_above_markers(svg)
    svg = bring_labels_to_front(svg)

    if label_font_scale and label_font_scale != 1.0:
        svg = scale_label_font_size(svg, scale_factor=label_font_scale)
        svg = expand_label_clip_paths(svg, scale_factor=label_font_scale)
        svg = bring_labels_to_front(svg)  # re-raise labels above enlarged glyphs/markers

    svg = remove_line_labels(svg)

    # IMPORTANT: transitmap -l already computes label paths/placement.
    # Do not flatten/re-place station labels after transitmap has placed
    # them. The old separate_station_labels() pass converted every label to
    # a horizontal path and then shifted labels in data-space, which was
    # the main cause of bad/misaligned labels on octilinear maps.
    # Keep transitmap -l's native label geometry (position/length) intact --
    # only normalize which direction each label path reads in, so labels
    # sharing the same octilinear angle (0/45/90/135 degrees) all face the
    # same way instead of some appearing upside-down/mirrored relative to
    # others at the same incline.
    if schematic:
        svg = orient_octilinear_labels(svg)

    if selected_landmarks:
        svg = add_landmarks_to_loom_svg(
            svg,
            selected_routes_tuple,
            selected_landmarks,
            icon_size=landmark_icon_size,
            schematic=schematic,
        )

    # Landmarks were injected after the first bring_labels_to_front() pass,
    # so run it again to guarantee landmark icons/labels render above the
    # transit lines instead of the lines painting over them.
    svg = raise_labels_above_markers(svg)
    svg = bring_labels_to_front(svg)

    if label_pad and label_pad > 0:
        svg = pad_svg_viewbox(svg, pad=label_pad)

    return svg


def add_route_title_to_svg(
    svg, selected_routes, route_name_map, title_text="Transit Map of Kathmandu Valley"
):
    return svg


def _content_y_bounds(root):
    """Best-effort TIGHT bounding box (in the SVG's own coordinate
    space) of everything actually drawn inside root. Returns
    (min_x, min_y, max_x, max_y) -- the x bounds are used to crop the
    wide empty side margins LOOM bakes into its canvas so the exported
    PNG fills the full width, the y bounds to crop top/bottom padding.

    generate_loom_svg() pads the LOOM output's viewBox by a fixed amount
    (label_pad, 150px by default) on every side so labels near the edge
    never clip. That's a good safety margin for a large, dense map, but
    for a small map (few routes selected) that same fixed padding is a
    much bigger fraction of the total height, which shows up as a big
    empty gap above/below the map. This walks the tree and returns the
    real min/max y of the drawn geometry so the composite can crop back
    to it instead of trusting the padded viewBox. Returns None if it
    can't confidently determine anything (caller then falls back to the
    declared viewBox, so this is purely an enhancement, never required).
    """
    ys = []
    xs = []
    num_re = re.compile(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', re.IGNORECASE)

    def local(tag):
        return tag.split('}')[-1] if '}' in tag else tag

    def walk(el, tx=0.0, ty=0.0, scale=1.0):
        transform = el.get('transform', '') or ''
        for m in re.finditer(r'translate\(\s*(-?[\d.eE+]+)[ ,]+(-?[\d.eE+]+)', transform):
            tx += float(m.group(1)) * scale
            ty += float(m.group(2)) * scale
        for m in re.finditer(r'scale\(\s*(-?[\d.]+)', transform):
            scale *= float(m.group(1))

        tag = local(el.tag)
        try:
            if tag == 'circle' or tag == 'ellipse':
                cx = float(el.get('cx', 0))
                cy = float(el.get('cy', 0))
                r = float(el.get('rx', el.get('r', 0)))
                ry = float(el.get('ry', el.get('r', 0)))
                xs.append(tx + (cx - r) * scale)
                xs.append(tx + (cx + r) * scale)
                ys.append(ty + (cy - ry) * scale)
                ys.append(ty + (cy + ry) * scale)
            elif tag == 'rect' or tag == 'image':
                x = float(el.get('x', 0))
                y = float(el.get('y', 0))
                w_ = float(el.get('width', 0))
                h_ = float(el.get('height', 0))
                xs.append(tx + x * scale)
                xs.append(tx + (x + w_) * scale)
                ys.append(ty + y * scale)
                ys.append(ty + (y + h_) * scale)
            elif tag in ('text', 'tspan'):
                y = el.get('y')
                x = el.get('x')
                if y is not None:
                    try:
                        ys.append(ty + float(y.split(',')[0].split()[0]) * scale)
                    except (ValueError, IndexError):
                        pass
                if x is not None:
                    try:
                        xs.append(tx + float(x.split(',')[0].split()[0]) * scale)
                    except (ValueError, IndexError):
                        pass
            elif tag in ('path', 'polyline', 'polygon'):
                d = el.get('d') or el.get('points') or ''
                nums = [float(n) for n in num_re.findall(d)]
                # (x, y) pairs -- even indices are x, odd are y.
                for i in range(0, len(nums) - 1, 2):
                    xs.append(tx + nums[i] * scale)
                for i in range(1, len(nums), 2):
                    ys.append(ty + nums[i] * scale)
        except (ValueError, TypeError):
            pass

        for child in list(el):
            walk(child, tx, ty, scale)

    walk(root)
    if len(ys) < 2 or len(xs) < 2:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def build_composite_svg(
    svg, selected_routes, route_name_map, route_color_hex_map,
    route_agency_map=None,
    title_text="Transit Map of Kathmandu Valley"
):

    w_match = re.search(r'width="([\d.]+)', svg)
    h_match = re.search(r'height="([\d.]+)', svg)
    w = float(w_match.group(1)) if w_match else 1200.0
    h = float(h_match.group(1)) if h_match else 800.0

    header_h = 64
    map_legend_gap = 36
    legend_header_h = 56
    legend_row_h = 46
    legend_bottom_pad = 28
    legend_top_pad = 18

    # Symbols column: fixed-width block pinned to the right edge of the
    # canvas, sized to comfortably fit its longest label at the enlarged
    # font size below so the text never runs past the canvas edge and
    # gets clipped.
    symbol_col_w = 340
    symbol_glyph_w = 30
    symbol_right_margin = 30

    # Column-wise legend: each ROUTE gets its own column (heading + entry),
    # flowing left-to-right and wrapping into multiple rows of columns.
    # Reserve the Symbols column's width so route columns never run under it.
    legend_col_w = 195
    total_w = max(w, 760.0)  # wide enough for legend + symbols side by side
    route_area_w = max(total_w - 40 - symbol_col_w - 20, legend_col_w)
    legend_cols_per_row = max(1, int(route_area_w // legend_col_w))
    route_list = list(selected_routes)
    legend_row_count = max(1, -(-len(route_list) // legend_cols_per_row))

    symbol_row_count = 5

    inner_svg = None
    vb_x, vb_y, h_eff = 0.0, 0.0, h
    try:
        inner_root = ET.fromstring(svg)
        vb = (inner_root.get('viewBox') or '').replace(',', ' ').split()
        vb_x, vb_y, vb_w, vb_h = 0.0, 0.0, w, h
        if len(vb) == 4:
            try:
                vb_x, vb_y, vb_w, vb_h = (float(v) for v in vb)
            except ValueError:
                pass

        # Crop back the fixed edge padding generate_loom_svg() baked in
        # (see _content_y_bounds' docstring) so a small map doesn't sit
        # inside a big empty box -- keep a modest fixed margin around the
        # real content instead of the full, size-independent pad.
        content_margin = 24
        bounds = _content_y_bounds(inner_root)
        if bounds:
            x_min, y_min, x_max, y_max = bounds
            new_left = max(x_min - content_margin, vb_x)
            new_right = min(x_max + content_margin, vb_x + vb_w)
            new_top = max(y_min - content_margin, vb_y)
            new_bottom = min(y_max + content_margin, vb_y + vb_h)
            if new_bottom - new_top > 80 and new_right - new_left > 80:
                vb_x, vb_y = new_left, new_top
                vb_w = new_right - new_left
                vb_h = new_bottom - new_top
            h_eff = vb_h
        else:
            h_eff = vb_h

        inner_parts = [
            ET.tostring(child, encoding='unicode')
            for child in list(inner_root)
        ]
        # Scale the (cropped) map content so it fills the FULL canvas
        # width -- the exported PNG then renders the map wide instead of
        # shrinking it inside leftover side margins. Height grows with the
        # same factor so nothing is distorted; the legend panel below is
        # laid out using the scaled height (h_eff). Everything stays
        # visible because we scale the whole viewBox, never clip it.
        fit_w = max(w, 760.0)
        fit_scale = fit_w / max(vb_w, 1.0)
        h_eff = vb_h * fit_scale
        inner_svg = (
            f'<g transform="translate({-vb_x * fit_scale:.3f},'
            f'{header_h - vb_y * fit_scale:.3f}) '
            f'scale({fit_scale:.4f})">'
            + ''.join(inner_parts)
            + '</g>'
        )
    except ET.ParseError:
        inner_svg = None
    h = h_eff

    # Route columns (left) | Symbols (right). The block height is driven by
    # whichever side is taller.
    legend_h = (
        legend_top_pad
        + legend_header_h
        + legend_row_h * max(legend_row_count, symbol_row_count)
        + legend_bottom_pad
    )
    total_h = h + header_h + map_legend_gap + legend_h

    if not inner_svg:
        inner_open = re.search(r'<svg\b[^>]*>', svg)
        if inner_open:
            inner_content = svg[inner_open.end():].rsplit('</svg>', 1)[0]
            inner_svg = f'<g transform="translate(0,{header_h})">{inner_content}</g>'
        else:
            inner_svg = f'<g transform="translate(0,{header_h})">{svg}</g>'

    legend_panel_top = h + header_h + map_legend_gap
    legend_top = legend_panel_top + legend_top_pad
    symbol_stop_color = route_color_hex_map.get(
        next(iter(selected_routes), ""), "#1d4ed8"
    )

    # Vertical divider between the Routes columns and the Symbols column.
    divider_x = total_w - symbol_col_w - 20

    sym_top = legend_top + legend_header_h
    sym_x_glyph = total_w - symbol_right_margin - symbol_col_w + symbol_glyph_w
    sym_x_text = sym_x_glyph + symbol_glyph_w
    # "Symbols" heading sits in the same header row as "Routes" (which is
    # drawn further below), so both columns start at the same height.
    symbol_rows_svg = (
        f'<text x="{sym_x_glyph}" y="{legend_top + 28}" '
        f'font-family="Arial, sans-serif" font-size="19" font-weight="700" '
        f'fill="#111111">Symbols</text>'
        # route line
        f'<rect x="{sym_x_glyph}" y="{sym_top + 20}" width="20" height="5" '
        f'fill="{symbol_stop_color}"/>'
        f'<text x="{sym_x_text}" y="{sym_top + 27}" '
        f'font-family="Arial, sans-serif" font-size="15" fill="#111111">'
        f'Route line (color = route)</text>'
        # bus stop
        f'<circle cx="{sym_x_glyph + 10}" cy="{sym_top + 55}" r="4.5" '
        f'fill="#ffffff" stroke="{symbol_stop_color}" stroke-width="2.5"/>'
        f'<text x="{sym_x_text}" y="{sym_top + 60}" '
        f'font-family="Arial, sans-serif" font-size="15" fill="#111111">'
        f'Bus stop / station</text>'
        # interchange
        f'<circle cx="{sym_x_glyph + 10}" cy="{sym_top + 87}" r="8" '
        f'fill="#ffffff" stroke="{symbol_stop_color}" stroke-width="2.5"/>'
        f'<text x="{sym_x_text}" y="{sym_top + 92}" '
        f'font-family="Arial, sans-serif" font-size="15" fill="#111111">'
        f'Interchange (shared stop)</text>'
        # station name text
        f'<text x="{sym_x_text}" y="{sym_top + 119}" '
        f'font-family="Arial, sans-serif" font-size="15" fill="#111111">'
        f'Text beside a stop = stop name</text>'
    )

    def _fit_svg_text(text, max_w_px, font_px=14):
        """Truncate text with an ellipsis so it fits max_w_px at font_px.
        Arial averages ~0.52*font_px per character; estimate conservatively
        (0.58) to leave a safety margin between columns."""
        text = str(text)
        max_chars = max(4, int(max_w_px / (font_px * 0.58)))
        if len(text) <= max_chars:
            return html.escape(text)
        return html.escape(text[: max_chars - 1].rstrip() + "…")

    legend_items_svg = []
    for idx, rid in enumerate(route_list):
        col = idx % legend_cols_per_row
        row = idx // legend_cols_per_row
        x = 20 + col * legend_col_w
        y = legend_top + legend_header_h + row * legend_row_h
        color = route_color_hex_map.get(rid, "#1d4ed8")
        agency = (route_agency_map or {}).get(rid, "Unknown Agency")
        name = str(route_name_map.get(rid, rid))
        legend_items_svg.append(
            f'<text x="{x}" y="{y - 4}" font-family="Arial, sans-serif" '
            f'font-size="13" font-weight="700" fill="#374151">'
            f'{_fit_svg_text(agency, legend_col_w - 8, 13)}</text>'
            f'<rect x="{x}" y="{y + 10}" width="20" height="5" fill="{color}"/>'
            f'<text x="{x + 28}" y="{y + 18}" font-family="Arial, sans-serif" '
            f'font-size="15" font-weight="400" fill="#111111">'
            f'{_fit_svg_text(name, legend_col_w - 36, 15)}</text>'
        )
    legend_svg = "".join(legend_items_svg)

    escaped_title = html.escape(title_text)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">
  <rect x="0" y="0" width="{total_w}" height="{total_h}" fill="#ffffff"/>
  <text x="{total_w / 2}" y="{header_h / 2 + 15}" text-anchor="middle"
        font-family="Arial, sans-serif" font-size="44" font-weight="700"
        fill="#111111">{escaped_title}</text>
  {inner_svg}
  <line x1="0" y1="{h + header_h + map_legend_gap / 2:.1f}"
        x2="{total_w}" y2="{h + header_h + map_legend_gap / 2:.1f}"
        stroke="#e5e7eb" stroke-width="1"/>
  <rect x="0" y="{legend_panel_top:.1f}" width="{total_w}"
        height="{legend_h}" fill="#fafafa"/>
  <text x="20" y="{legend_top + 28}" font-family="Arial, sans-serif"
        font-size="19" font-weight="700" fill="#111111">Routes</text>
  {legend_svg}
  <line x1="{divider_x}" y1="{legend_panel_top + 12:.1f}"
        x2="{divider_x}" y2="{legend_panel_top + legend_h - 12:.1f}"
        stroke="#e0e0e0" stroke-width="1"/>
  {symbol_rows_svg}
</svg>'''


def display_loom_svg(svg, selected_routes, route_name_map, route_agency_map=None):

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")

    # ---- build the export (composite) SVG -----------------------------
    composite_svg = build_composite_svg(
        svg,
        selected_routes,
        route_name_map,
        route_color_hex_map,
        route_agency_map=route_agency_map,
        title_text="Transit Map of Kathmandu Valley",
    )

    composite_b64 = base64.b64encode(
        composite_svg.encode("utf-8")
    ).decode("ascii")

    # Pull the composite's own declared size so the on-screen viewer can
    # size itself to the map's real aspect ratio (see loomFitContainer
    # below) instead of guessing from a rendered element.
    _cw_match = re.search(r'width="([\d.]+)"', composite_svg)
    _ch_match = re.search(r'height="([\d.]+)"', composite_svg)
    composite_w = float(_cw_match.group(1)) if _cw_match else 1600.0
    composite_h = float(_ch_match.group(1)) if _ch_match else 1200.0

    legend_groups = {}
    for route_id in selected_routes:
        agency = (route_agency_map or {}).get(route_id, "Unknown Agency")
        legend_groups.setdefault(agency, []).append(route_id)

    # Column-per-route legend: each route is its own fixed-width column
    # (agency name above the swatch + route name), flowing left-to-right
    # and wrapping onto new rows. Long route names wrap inside their own
    # column instead of running into the next one -- the old nowrap rows
    # made every entry melt together into one unreadable line when two
    # agencies had routes of similar names.
    legend_items = "".join(
        f'<div style="display:flex; flex-direction:column; '
        f'align-items:flex-start; margin:0 14px 8px 0; padding:0; '
        f'width:180px; flex:0 0 180px; box-sizing:border-box;">'
        f'<div style="font-size:10px; font-weight:600; line-height:1.2; '
        f'color:#666; margin-bottom:3px; white-space:nowrap; '
        f'overflow:hidden; text-overflow:ellipsis; max-width:100%; '
        f'letter-spacing:0.03em;">'
        f'{html.escape(str(agency))}'
        f'</div>'
        f'<div style="display:flex; align-items:flex-start; gap:7px; '
        f'padding:0; font-size:12px; font-weight:400; line-height:1.3; '
        f'color:#222; width:100%; box-sizing:border-box;">'
        f'<span style="width:16px; height:4px; flex:0 0 16px; '
        f'margin-top:5px; '
        f'background:{html.escape(str(route_color_hex_map.get(route_id, "#1d4ed8")))}; '
        f'display:inline-block; border-radius:2px;"></span>'
        f'<span style="margin:0; padding:0; font-weight:400; '
        f'overflow-wrap:break-word; word-break:break-word; min-width:0; flex:1 1 auto;">'
        f'{html.escape(str(route_name_map.get(route_id, route_id)))}</span></div>'
        f'</div>'
        for route_id in selected_routes
    )
    legend_items = (
        f'<div style="display:flex; flex-wrap:wrap; align-items:flex-start; '
        f'max-width:100%;">{legend_items}</div>'
    )

    symbol_stop_color = html.escape(str(
        route_color_hex_map.get(
            next(iter(selected_routes), ""), "#1d4ed8"
        )
    ))
    symbol_items = (
        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:12px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        f'<span style="width:16px; height:4px; flex:0 0 16px; '
        f'background:{symbol_stop_color}; display:inline-block; border-radius:2px;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Route line</span></div>'

        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:12px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        '<span style="width:8px; height:8px; flex:0 0 8px; '
        'border-radius:50%; background:#fff; '
        f'border:2px solid {symbol_stop_color}; box-sizing:border-box; '
        'display:inline-block;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Bus stop / station</span></div>'

        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:12px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        '<span style="width:14px; height:14px; flex:0 0 14px; '
        'border-radius:50%; background:#fff; '
        f'border:2px solid {symbol_stop_color}; box-sizing:border-box; '
        'display:inline-block;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Interchange</span></div>'

        '<div style="margin:2px 0; padding:0; font-size:12px; '
        'font-weight:400; line-height:1.2; color:#222;">Station name</div>'
    )

    html_code = f"""
    <div id="loom-wrapper" style="position:relative; background:#ffffff;
         border-radius:8px; overflow:hidden; border:1px solid #ddd;">
      <style>
        /* Make the LOOM SVG itself fill the wrapper width so the map
           renders as a wide frame, not a small fixed-width image. */
        #loom-img svg {{ width: 100% !important; height: auto !important; display: block; }}
      </style>
      <div id="loom-toolbar" style="display:flex; gap:6px; align-items:center;
           flex-wrap:wrap; padding:6px 10px; background:#f3f4f6; border-bottom:1px solid #ddd;">
        <button onclick="loomZoom(1.25)"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">➕ Zoom In</button>

        <button onclick="loomZoom(0.8)"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">➖ Zoom Out</button>
        <button onclick="loomReset()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">↺ Reset</button>
        <span style="width:1px; height:22px; background:#ccc; margin:0 4px;"></span>
        <button onclick="loomDownloadSVG()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">⬇ SVG</button>
        <button onclick="loomDownloadPNG()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">⬇ PNG</button>
        <button onclick="loomFullscreen()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff; margin-left:auto;">
                ⛶ Full Screen</button>
      </div>
     <div id="loom-scroll" style="position:relative; overflow:auto; width:100%; height:760px;
         background:#fff; padding:24px 28px 24px 28px; box-sizing:border-box;">
        <div id="loom-img"
             style="display:block; width:100%; max-width:100%; margin:0 auto;
                    transform-origin:0 0; transition:transform 0.15s ease;
                    cursor:grab; user-select:none; touch-action:none;">
          {composite_svg}
        </div>
      </div>
    </div>
    <script>
      // Base64 of the raw LOOM transit map SVG — exports are just the map,
      // with no extra title or legend baked in.
      const loomCompositeSvgDataUrl = "data:image/svg+xml;base64,{composite_b64}";

      // The composite's own aspect ratio (map + title + legend), used
      // below to size the viewer so the whole map is visible on load
      // instead of forcing a scroll to see the bottom of it.
      const LOOM_COMPOSITE_W = {composite_w};
      const LOOM_COMPOSITE_H = {composite_h};

      // Grow (or shrink) #loom-scroll so the composite renders at its
      // natural, unzoomed height within the current width -- capped so
      // it never takes over the whole browser window. Only applies at
      // scale 1 with no pan; once the user zooms in, panning/scrolling
      // inside the fixed-height viewport takes over as normal.
      function loomFitContainer() {{
        const scrollEl = document.getElementById('loom-scroll');
        const img = document.getElementById('loom-img');
        if (!scrollEl || !img) return;
        const isFs = !!(document.fullscreenElement || document.webkitFullscreenElement);
        // The SVG fills #loom-img at width:100%, and #loom-img itself can
        // be forced wider than the viewport (see loomFullscreen's
        // min-width), so measure the image's real rendered width rather
        // than assuming it matches the scroll container.
        const imgW = img.getBoundingClientRect().width || (scrollEl.clientWidth - 56);
        const naturalH = imgW * (LOOM_COMPOSITE_H / LOOM_COMPOSITE_W);
        const capH = window.innerHeight * (isFs ? 0.92 : 0.85);
        scrollEl.style.height = Math.max(360, Math.min(naturalH + 94, capH)) + 'px';
      }}

      // Keep the map inside a predictable desktop/full-screen range.
      // 1.0 = normal size; users can zoom from 0.85x to 2.5x.
      const LOOM_MIN_SCALE = 0.85;
      const LOOM_MAX_SCALE = 2.50;
      let loomScale = 1.0;
      let loomPanX = 0;
      let loomPanY = 0;
      let loomDragging = false;
            let loomDragStartX = 0;
            let loomDragStartY = 0;
            let loomStartPanX = 0;
            let loomStartPanY = 0;

            function loomClampPan() {{
                const img = document.getElementById('loom-img');
                const viewport = document.getElementById('loom-scroll');
                if (!img || !viewport) return;

                const vw = Math.max(viewport.clientWidth - 40, 1);
                const vh = Math.max(viewport.clientHeight - 55, 1);
                const iw = Math.max(img.offsetWidth, 1) * loomScale;
                const ih = Math.max(img.offsetHeight, 1) * loomScale;

                // Never allow the transformed image to be panned completely
                // outside the visible desktop/full-screen viewport.
                const maxX = Math.max(0, (iw - vw) / 2 + 120);
                const maxY = Math.max(0, (ih - vh) / 2 + 120);

                loomPanX = Math.min(Math.max(loomPanX, -maxX), maxX);
                loomPanY = Math.min(Math.max(loomPanY, -maxY), maxY);
            }}

            function loomApplyTransform() {{
                const img = document.getElementById('loom-img');
                if (!img) return;
                loomClampPan();
                img.style.transform =
                    'translate(' + loomPanX + 'px, ' + loomPanY + 'px) scale(' + loomScale + ')';
                // Expand the scrollable area to the SCALED size of the map
                // (the CSS transform alone doesn't create scrollable
                // overflow, which is why zooming used to clip the map).
                // The margins grow/shrink with the zoom level, so the
                // scrollbars always span the whole map and every edge of
                // it stays reachable while zoomed in.
                const iw = Math.max(img.offsetWidth, 1) * loomScale;
                const ih = Math.max(img.offsetHeight, 1) * loomScale;
                img.style.marginRight = Math.max(0, iw - img.offsetWidth) + 'px';
                img.style.marginBottom = Math.max(0, ih - img.offsetHeight) + 'px';
            }}

      function loomZoom(factor) {{
        const oldScale = loomScale;
        loomScale = Math.min(Math.max(loomScale * factor, LOOM_MIN_SCALE), LOOM_MAX_SCALE);
        if (loomScale === oldScale) return;
        loomApplyTransform();
      }}

      function loomReset() {{
        loomScale = 1;
                loomPanX = 0;
                loomPanY = 0;
                loomFitContainer();
                loomApplyTransform();
                document.getElementById('loom-scroll').scrollTo(0, 0);
      }}

      window.addEventListener('resize', loomFitContainer);

            const loomImg = document.getElementById('loom-img');

            // Landmark names are hidden until hover/touch/click.
            const landmarkGroups = Array.from(document.querySelectorAll('#loom-img .loom-landmark'));
            function hideLandmarkLabels(exceptGroup) {{
                landmarkGroups.forEach(function(group) {{
                    if (group === exceptGroup) return;
                    const label = group.querySelector('.landmark-label');
                    if (label) label.setAttribute('visibility', 'hidden');
                    group.classList.remove('landmark-active');
                }});
            }}
            function showLandmarkLabel(group) {{
                const label = group.querySelector('.landmark-label');
                if (!label) return;
                hideLandmarkLabels(group);
                label.setAttribute('visibility', 'visible');
                group.classList.add('landmark-active');
            }}
            landmarkGroups.forEach(function(group) {{
                group.addEventListener('mouseenter', function() {{ showLandmarkLabel(group); }});
                group.addEventListener('mouseleave', function() {{
                    if (!group.classList.contains('landmark-pinned')) {{
                        const label = group.querySelector('.landmark-label');
                        if (label) label.setAttribute('visibility', 'hidden');
                        group.classList.remove('landmark-active');
                    }}
                }});
                group.addEventListener('click', function(event) {{
                    event.stopPropagation();
                    const pinned = group.classList.contains('landmark-pinned');
                    landmarkGroups.forEach(function(g) {{ g.classList.remove('landmark-pinned'); }});
                    if (!pinned) {{ showLandmarkLabel(group); group.classList.add('landmark-pinned'); }}
                    else {{ const label=group.querySelector('.landmark-label'); if(label) label.setAttribute('visibility','hidden'); group.classList.remove('landmark-active'); }}
                }});
                group.addEventListener('touchstart', function(event) {{ event.stopPropagation(); showLandmarkLabel(group); group.classList.add('landmark-pinned'); }}, {{passive:true}});
                group.addEventListener('focus', function() {{ showLandmarkLabel(group); }});
            }});

            // Size the viewer to the map's own aspect ratio, then apply
            // the initial (unzoomed) transform, so the whole map is
            // visible without needing to scroll first.
            loomFitContainer();
            loomApplyTransform();

            // mouse-wheel zoom (zoom towards the cursor)
            document.getElementById('loom-scroll').addEventListener('wheel', function(event) {{
                if (!event.ctrlKey && !event.metaKey && Math.abs(event.deltaY) < 2) return;
                event.preventDefault();
                const factor = event.deltaY < 0 ? 1.15 : 1 / 1.15;
                const rect = loomImg.getBoundingClientRect();
                const cx = event.clientX - rect.left;
                const cy = event.clientY - rect.top;
                const newScale = Math.min(Math.max(loomScale * factor, LOOM_MIN_SCALE), LOOM_MAX_SCALE);
                loomPanX = cx - (cx - loomPanX) * (newScale / loomScale);
                loomPanY = cy - (cy - loomPanY) * (newScale / loomScale);
                loomScale = newScale;
                loomClampPan();
                loomApplyTransform();
            }}, {{ passive: false }});

            loomImg.addEventListener('pointerdown', function(event) {{
                loomDragging = true;
                loomDragStartX = event.clientX;
                loomDragStartY = event.clientY;
                loomStartPanX = loomPanX;
                loomStartPanY = loomPanY;
                loomImg.setPointerCapture(event.pointerId);
                loomImg.style.cursor = 'grabbing';
                loomImg.style.transition = 'none';
                event.preventDefault();
            }});

            loomImg.addEventListener('pointermove', function(event) {{
                if (!loomDragging) return;
                loomPanX = loomStartPanX + event.clientX - loomDragStartX;
                loomPanY = loomStartPanY + event.clientY - loomDragStartY;
                loomApplyTransform();
                event.preventDefault();
            }});

            function loomStopDragging(event) {{
                if (!loomDragging) return;
                loomDragging = false;
                loomImg.style.cursor = 'grab';
                loomImg.style.transition = 'transform 0.15s ease';
                if (event && loomImg.hasPointerCapture(event.pointerId)) {{
                    loomImg.releasePointerCapture(event.pointerId);
                }}
            }}

            loomImg.addEventListener('pointerup', loomStopDragging);
            loomImg.addEventListener('pointercancel', loomStopDragging);

      function loomTriggerDownload(url, filename) {{
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }}

      // Export the bare transit map (same SVG displayed on screen).
      async function loomDownloadSVG() {{
        try {{
          const res = await fetch(loomCompositeSvgDataUrl);
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          loomTriggerDownload(url, 'loom_transit_map.svg');
          setTimeout(() => URL.revokeObjectURL(url), 2000);
        }} catch (e) {{
          alert('SVG download failed: ' + e);
        }}
      }}

      // PNG export rasterizes the composite SVG (map + title + legend +
      // symbols), so the exported file matches the full panel.
      async function loomDownloadPNG() {{
        try {{
          // Render at FULL-SCREEN-SIZE resolution: at least 3x the map's
          // natural size, and wide enough to match a 1920px-wide screen,
          // so the downloaded PNG is a crisp, whole-map poster image.
          const scale = 4;

          // Parse the explicit width/height out of the composite SVG so we
          // never depend on naturalWidth (which some browsers report as 0
          // for large SVG data URLs).
          const svgText = atob(loomCompositeSvgDataUrl.split(',')[1]);
          const wMatch = svgText.match(/width="([\\d.]+)/);
          const hMatch = svgText.match(/height="([\\d.]+)/);
          const fallbackW = wMatch ? parseFloat(wMatch[1]) : 1600;
          const fallbackH = hMatch ? parseFloat(hMatch[1]) : 1200;

          const tempImg = new Image();
          tempImg.crossOrigin = 'anonymous';

          tempImg.onload = function() {{
            let w = tempImg.naturalWidth || fallbackW;
            let h = tempImg.naturalHeight || fallbackH;
            const canvas = document.createElement('canvas');
            canvas.width = Math.round(w * scale);
            canvas.height = Math.round(h * scale);
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(tempImg, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(function(blob) {{
              if (!blob) {{ alert('PNG export failed.'); return; }}
              const url = URL.createObjectURL(blob);
              loomTriggerDownload(url, 'loom_transit_map.png');
              setTimeout(() => URL.revokeObjectURL(url), 2000);
            }}, 'image/png');
          }};

          tempImg.onerror = function() {{
            alert('PNG download failed: could not rasterize the composite SVG.');
          }};

          tempImg.src = loomCompositeSvgDataUrl;
        }} catch (e) {{
          alert('PNG download failed: ' + e);
        }}
      }}

      function loomFullscreen() {{
        const el = document.getElementById('loom-wrapper');
        const scrollEl = document.getElementById('loom-scroll');
        const isFs = document.fullscreenElement || document.webkitFullscreenElement;

        function applyFullscreenStyle(on) {{
          if (on) {{
            el.style.position = 'fixed';
            el.style.top = '0'; el.style.left = '0';
            el.style.width = '100vw'; el.style.height = '100vh';
            el.style.zIndex = '99999';
            el.style.background = '#ffffff';
            scrollEl.style.width = '100vw';
            scrollEl.style.padding = '18px 24px 24px 24px';
            loomImg.style.width = '96vw';
            loomImg.style.minWidth = '0';
            loomImg.style.maxWidth = 'none';
            loomImg.style.margin = '0 auto';
          }} else {{
            el.style.position = 'relative';
            el.style.width = 'auto'; el.style.height = 'auto';
            el.style.zIndex = 'auto';
            scrollEl.style.width = '100%';
            scrollEl.style.padding = '24px 28px 24px 28px';
            loomImg.style.width = '96%';
            loomImg.style.minWidth = '0';
            loomImg.style.maxWidth = 'none';
          }}
          // Re-measure and refit after the layout above takes effect.
          requestAnimationFrame(loomFitContainer);
        }}

        if (!isFs) {{
          loomPanX = 0;
          loomPanY = 0;
          loomScale = 1.0;
          loomApplyTransform();
          const req = el.requestFullscreen || el.webkitRequestFullscreen;
          if (req) {{
            req.call(el).then(() => applyFullscreenStyle(true))
                         .catch(() => applyFullscreenStyle(true)); // fallback if blocked
          }} else {{
            applyFullscreenStyle(true); // fallback: fill the viewport via CSS only
          }}
        }} else {{
          const exit = document.exitFullscreen || document.webkitExitFullscreen;
          if (exit) {{ exit.call(document); }}
          applyFullscreenStyle(false);
        }}
      }}

      document.addEventListener('fullscreenchange', () => {{
        if (!document.fullscreenElement) {{
          const el = document.getElementById('loom-wrapper');
          el.style.position = 'relative';
          el.style.width = 'auto'; el.style.height = 'auto';
        }}
        requestAnimationFrame(loomFitContainer);
      }});
    </script>

    """
    st.components.v1.html(html_code, height=830, scrolling=True)


def build_map_legend_html(selected_routes, route_name_map, route_color_hex_map,
                           route_agency_map=None):
    """Build the Routes/Symbols legend markup shared by the Transit Map and
    the LOOM map, so both views show exactly the same legend.

    Each route gets its own small column (agency name above a colored
    swatch + route name); columns flow left-to-right and wrap onto new
    rows as needed, instead of stacking every route in one long list.
    """

    legend_items = "".join(
        f'<div style="display:flex; flex-direction:column; '
        f'align-items:flex-start; margin:0 20px 10px 0; padding:0; '
        f'width:190px; flex:0 0 190px; box-sizing:border-box;">'
        f'<div style="font-size:11px; font-weight:400; line-height:1.2; '
        f'color:#666; margin-bottom:3px; white-space:nowrap; '
        f'overflow:hidden; text-overflow:ellipsis; max-width:100%;">'
        f'{html.escape(str((route_agency_map or {}).get(route_id, "Unknown Agency")))}'
        f'</div>'
        f'<div style="display:flex; align-items:flex-start; gap:7px; '
        f'padding:0; font-size:13px; font-weight:400; line-height:1.3; '
        f'color:#222; width:100%; box-sizing:border-box;">'
        f'<span style="width:16px; height:4px; flex:0 0 16px; '
        f'margin-top:5px; '
        f'background:{html.escape(str(route_color_hex_map.get(route_id, "#1d4ed8")))}; '
        f'display:inline-block; border-radius:2px;"></span>'
        f'<span style="margin:0; padding:0; font-weight:400; '
        f'overflow-wrap:break-word; word-break:break-word; min-width:0; flex:1 1 auto;">'
        f'{html.escape(str(route_name_map.get(route_id, route_id)))}</span></div>'
        f'</div>'
        for route_id in selected_routes
    )
    legend_items = (
        f'<div style="display:flex; flex-wrap:wrap; align-items:flex-start; '
        f'max-width:660px;">{legend_items}</div>'
    )

    symbol_stop_color = html.escape(str(
        route_color_hex_map.get(next(iter(selected_routes), ""), "#1d4ed8")
    ))
    symbol_items = (
        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:13px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        f'<span style="width:16px; height:4px; flex:0 0 16px; '
        f'background:{symbol_stop_color}; display:inline-block; border-radius:2px;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Route line</span></div>'

        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:13px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        '<span style="width:8px; height:8px; flex:0 0 8px; '
        'border-radius:50%; background:#fff; '
        f'border:2px solid {symbol_stop_color}; box-sizing:border-box; '
        'display:inline-block;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Bus stop / station</span></div>'

        '<div style="display:flex; align-items:center; gap:7px; '
        'margin:2px 0; padding:0; font-size:13px; font-weight:400; '
        'line-height:1.2; color:#222;">'
        '<span style="width:14px; height:14px; flex:0 0 14px; '
        'border-radius:50%; background:#fff; '
        f'border:2px solid {symbol_stop_color}; box-sizing:border-box; '
        'display:inline-block;"></span>'
        '<span style="margin:0; padding:0; font-weight:400;">Interchange</span></div>'

        '<div style="margin:2px 0; padding:0; font-size:13px; '
        'font-weight:400; line-height:1.2; color:#222;">Station name</div>'
    )

    return legend_items, symbol_items


def _build_map_legend_rows(selected_routes, route_name_map, route_color_hex_map,
                           route_agency_map=None):
    """Return the Routes/Symbols legend as plain JSON-able data, used by the
    Transit Map's PNG export to draw the legend directly onto the export
    canvas (html2canvas chokes on malformed selectors Plotly injects into
    the page CSS, so we avoid rasterizing the live legend DOM entirely)."""

    legend_groups = {}
    for route_id in selected_routes:
        agency = (route_agency_map or {}).get(route_id, "Unknown Agency")
        legend_groups.setdefault(agency, []).append(route_id)

    groups = [
        {
            "agency": str(agency),
            "routes": [
                {
                    "name": str(route_name_map.get(route_id, route_id)),
                    "color": str(route_color_hex_map.get(route_id, "#1d4ed8")),
                }
                for route_id in route_ids
            ],
        }
        for agency, route_ids in legend_groups.items()
    ]

    symbol_stop_color = str(
        route_color_hex_map.get(next(iter(selected_routes), ""), "#1d4ed8")
    )
    symbols = [
        {"type": "line", "color": symbol_stop_color, "label": "Route line"},
        {"type": "circle", "radius": 4, "color": symbol_stop_color,
         "label": "Bus stop / station"},
        {"type": "circle", "radius": 7, "color": symbol_stop_color,
         "label": "Interchange"},
        {"type": "text", "color": symbol_stop_color, "label": "Station name"},
    ]

    return {"groups": groups, "symbols": symbols}


def display_transit_map(fig, selected_routes, route_name_map, route_color_hex_map,
                         route_agency_map=None, height=720):
    """Render the Plotly Transit Map with a fixed Routes/Symbols legend box,
    styled and positioned the same way as the LOOM map's legend.

    The legend is a plain HTML overlay sitting on top of the Plotly div
    (not part of the Plotly figure), so it never moves, grows into, or
    hides behind anything when the map is zoomed or panned -- it just
    stays put in its own corner. Because it sits above the plot in the
    stacking order, scrolling or dragging while the pointer is over the
    legend never reaches the map underneath; everywhere else on the map,
    zoom and pan keep working as before. In full screen, the legend
    stretches to span the screen from edge to edge instead of staying a
    small corner box.
    """

    # The overlay legend replaces Plotly's own legend, so switch that off
    # -- otherwise the routes and symbols would show up twice.
    fig.update_layout(showlegend=False)

    plot_html = pio.to_html(
        fig,
        include_plotlyjs="cdn",
        full_html=False,
        div_id="transit-plot-div",
        config={
            "scrollZoom": True,
            "responsive": True,
            "displayModeBar": True,
            "displaylogo": False,
            # Plotly's own built-in camera/download button only captures the
            # chart's internal SVG canvas, not the HTML legend sitting on
            # top of it, so it would silently export a map with no legend.
            # Remove it in favor of the "PNG" button above, which captures
            # both together.
            "modeBarButtonsToRemove": ["toImage"],
        },
    )

    legend_items, symbol_items = build_map_legend_html(
        selected_routes, route_name_map, route_color_hex_map, route_agency_map
    )

    # Structured legend data (as JSON) for the JavaScript PNG exporter,
    # so it can draw the legend directly on the export canvas without
    # relying on html2canvas (which chokes on Plotly's injected CSS).
    legend_rows_json = json.dumps(
        _build_map_legend_rows(
            selected_routes, route_name_map, route_color_hex_map, route_agency_map
        ),
        ensure_ascii=False,
    )

    html_code = f"""
    <div id="transit-wrapper" style="position:relative; background:#ffffff;
         border-radius:8px; overflow:hidden; border:1px solid #ddd;">
      <div id="transit-toolbar" style="display:flex; gap:6px; align-items:center;
           flex-wrap:wrap; padding:6px 10px; background:#f3f4f6; border-bottom:1px solid #ddd;">
        <span style="font-size:13px; color:#555; margin-right:auto;">Transit Map of Kathmandu Valley</span>
        <button onclick="transitDownloadPNG()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">⬇ PNG</button>
        <button onclick="transitFullscreen()"
                style="padding:4px 10px; cursor:pointer; border-radius:6px;
                       border:1px solid #ccc; background:#fff;">⛶ Full Screen</button>
      </div>
      <div id="transit-plot-container" style="position:relative; width:100%; height:{height}px;">
        {plot_html}
        <div id="transit-legend" style="position:absolute; left:18px; bottom:14px; z-index:5;
             background:rgba(255,255,255,0.97); border:1px solid #d0d0d0;
             padding:10px 14px; color:#222; font:13px Arial,sans-serif;
             line-height:1.2; box-shadow:0 1px 4px rgba(0,0,0,.12);
             display:flex; gap:18px; align-items:flex-start; box-sizing:border-box;
             max-width:min(94%, 780px);">
          <div style="min-width:120px;">
            <div style="font-weight:700; font-size:15px; margin:0 0 6px; padding:0;
                        color:#111; line-height:1.2;">Routes</div>
            {legend_items}
          </div>
          <div style="min-width:130px; border-left:1px solid #ddd; padding-left:14px;">
            <div style="font-weight:700; font-size:15px; margin:0 0 6px; padding:0;
                        color:#111; line-height:1.2;">Symbols</div>
            {symbol_items}
          </div>
        </div>
      </div>
    </div>
    <script>
      // The legend sits on top of the plot in the stacking order already,
      // so a wheel/drag that starts on it never reaches the map behind it.
      // Stopping propagation here just makes that explicit and stops the
      // page itself from scrolling while the pointer is over the legend.
      (function() {{
        const legend = document.getElementById('transit-legend');
        legend.addEventListener('wheel', function(e) {{ e.stopPropagation(); }}, {{ passive: false }});
        legend.addEventListener('mousedown', function(e) {{ e.stopPropagation(); }});
        legend.addEventListener('touchstart', function(e) {{ e.stopPropagation(); }}, {{ passive: true }});
      }})();

      function transitResizePlot() {{
        const gd = document.getElementById('transit-plot-div');
        if (gd && window.Plotly) {{
          window.Plotly.Plots.resize(gd);
        }}
      }}

      // Landmark names are interactive on touch/click as well as Plotly hover.
      // The invisible landmark hit-area traces carry customdata with the name.
      (function() {{
        const gd = document.getElementById('transit-plot-div');
        if (!gd) return;

        const tip = document.createElement('div');
        tip.id = 'transit-landmark-touch-label';
        tip.style.cssText = 'position:absolute;display:none;z-index:20;background:#fff;color:#111;border:1px solid #bbb;border-radius:6px;padding:6px 9px;font:600 13px Arial,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.18);pointer-events:none;white-space:nowrap;';
        document.getElementById('transit-plot-container').appendChild(tip);

        gd.on('plotly_click', function(eventData) {{
          const point = eventData && eventData.points && eventData.points[0];
          if (!point || !point.customdata || !point.customdata[0]) return;

          const name = point.customdata[0];
          tip.textContent = name;
          tip.style.display = 'block';

          const rect = gd.getBoundingClientRect();
          const px = Number(point.event && point.event.clientX) - rect.left;
          const py = Number(point.event && point.event.clientY) - rect.top;
          tip.style.left = Math.max(8, px + 10) + 'px';
          tip.style.top = Math.max(8, py - 34) + 'px';
        }});

        gd.addEventListener('mouseleave', function() {{
          tip.style.display = 'none';
        }});
      }})();

      // Composites the Plotly map and the HTML legend into one PNG, so
      // the legend actually shows up in the downloaded image -- Plotly's
      // own export only rasterizes its own SVG canvas and never touches
      // the legend overlay sitting on top of it.
      function transitTriggerDownload(url, filename) {{
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }}

      async function transitDownloadPNG() {{
        try {{
          const gd = document.getElementById('transit-plot-div');
          const legend = document.getElementById('transit-legend');
          const container = document.getElementById('transit-plot-container');
          if (!gd || !window.Plotly) {{
            alert('The map is still loading -- try again in a moment.');
            return;
          }}

          const scale = 2;
          const w = container.offsetWidth;
          const h = container.offsetHeight;
          // The Plotly figure already renders its own title, so the export
          // canvas is exactly the map + legend -- no extra title band.

          const legendData = {legend_rows_json};

          const mapDataUrl = await window.Plotly.toImage(
            gd, {{ format: 'png', width: w, height: h, scale: scale }}
          );

          const mapImg = new Image();
          mapImg.onload = function() {{
            const canvas = document.createElement('canvas');
            canvas.width = w * scale;
            canvas.height = h * scale;
            const ctx = canvas.getContext('2d');

            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.drawImage(mapImg, 0, 0, w * scale, h * scale);

            // Draw the legend box manually (html2canvas is unreliable here
            // because Plotly injects malformed CSS selectors into the page).
            // Column widths are measured from the actual text so long route
            // names never spill into the Symbols column.
            const fs = 13 * scale;
            const headFs = 15 * scale;
            const rowH = 20 * scale;
            const gap = 8 * scale;
            const colGap = 20 * scale;
            const padX = 14 * scale;
            const padTop = 12 * scale;
            const glyphW = 26 * scale;

            function textWAt(t, fontPx, weight) {{
              ctx.font = (weight ? weight + ' ' : '') + fontPx + 'px Arial, sans-serif';
              return ctx.measureText(t).width;
            }}

            // Greedy word-wrap: breaks `text` into lines that each fit
            // within maxW at the currently-set ctx.font, so a long route
            // name wraps inside its own column instead of overflowing
            // into the neighboring one.
            function wrapText(text, maxW) {{
              const words = String(text).split(' ');
              const lines = [];
              let line = '';
              words.forEach(function(word) {{
                const test = line ? line + ' ' + word : word;
                if (ctx.measureText(test).width > maxW && line) {{
                  lines.push(line);
                  line = word;
                }} else {{
                  line = test;
                }}
              }});
              if (line) lines.push(line);
              return lines.length ? lines : [''];
            }}

            function truncateText(text, maxW) {{
              let t = String(text);
              if (ctx.measureText(t).width <= maxW) return t;
              while (t.length > 1 && ctx.measureText(t + '…').width > maxW) {{
                t = t.slice(0, -1);
              }}
              return t + '…';
            }}

            // Flatten the agency groups into one route-per-column entry
            // list, each column showing its agency name above a swatch +
            // route name -- mirrors the on-screen legend's layout. Every
            // column uses the SAME fixed width, and text wraps/truncates
            // to fit inside it, so columns can never bleed into each other.
            const agencyFs = 11 * scale;
            const routeFs = fs;
            const colW = 190 * scale;
            const colGapX = 20 * scale;
            const colGapY = 10 * scale;
            const glyphW2 = 22 * scale;
            const routesMaxRowW = 660 * scale;
            const lineGap = 2 * scale;

            const agencyLineH = agencyFs * 1.3;
            const routeLineH = routeFs * 1.3;

            const routeEntries = [];
            legendData.groups.forEach(function(group) {{
              group.routes.forEach(function(route) {{
                ctx.font = agencyFs + 'px Arial, sans-serif';
                const agencyText = truncateText(group.agency, colW);
                ctx.font = routeFs + 'px Arial, sans-serif';
                const nameLines = wrapText(route.name, colW - glyphW2);
                routeEntries.push({{
                  agencyText: agencyText,
                  nameLines: nameLines,
                  color: route.color,
                  colW: colW,
                  entryH: agencyLineH + 3 * scale
                    + nameLines.length * routeLineH
                    + (nameLines.length - 1) * lineGap,
                }});
              }});
            }});

            // Flow the fixed-width columns left-to-right, wrapping onto
            // new rows; each row's height is set by its tallest entry.
            const legendRows = [];
            let curRow = [];
            let curW = 0;
            routeEntries.forEach(function(e) {{
              const addW = colW + (curRow.length ? colGapX : 0);
              if (curRow.length && curW + addW > routesMaxRowW) {{
                legendRows.push(curRow);
                curRow = [];
                curW = 0;
              }}
              curW += colW + (curRow.length ? colGapX : 0);
              curRow.push(e);
            }});
            if (curRow.length) legendRows.push(curRow);

            const rowHeights = legendRows.map(function(r) {{
              return Math.max.apply(null, r.map(function(e) {{ return e.entryH; }}));
            }});

            let colW1 = textWAt('Routes', headFs, '700');
            legendRows.forEach(function(r) {{
              const rowW = r.length * colW + (r.length - 1) * colGapX;
              colW1 = Math.max(colW1, rowW);
            }});
            const routesBlockH = rowHeights.length
              ? rowHeights.reduce(function(a, b) {{ return a + b; }}, 0)
                + (rowHeights.length - 1) * colGapY
              : 0;

            // Measure Symbols column.
            let colW2 = textWAt('Symbols', headFs, '700');
            legendData.symbols.forEach(function(symbol) {{
              colW2 = Math.max(colW2, glyphW + textWAt(symbol.label, fs));
            }});
            colW2 += glyphW;

            const symbolsBlockH = legendData.symbols.length * rowH;
            const boxW = padX * 2 + colW1 + colGap + colW2;
            const boxH = padTop * 2 + headFs + gap + Math.max(routesBlockH, symbolsBlockH);
            const boxX = 18 * scale;
            const boxY = canvas.height - boxH - 14 * scale;

            ctx.fillStyle = 'rgba(255,255,255,0.97)';
            ctx.fillRect(boxX, boxY, boxW, boxH);
            ctx.strokeStyle = '#d0d0d0';
            ctx.lineWidth = 1 * scale;
            ctx.strokeRect(boxX, boxY, boxW, boxH);

            ctx.textAlign = 'left';
            ctx.fillStyle = '#111111';
            const x1 = boxX + padX;
            const x2 = x1 + colW1 + colGap;
            const headY = boxY + padTop + headFs;

            ctx.font = '700 ' + headFs + 'px Arial, sans-serif';
            ctx.fillText('Routes', x1, headY);
            ctx.fillText('Symbols', x2, headY);

            let yRow = headY + gap + agencyLineH * 0.8;
            legendRows.forEach(function(r, rowIdx) {{
              let xCol = x1;
              r.forEach(function(e) {{
                ctx.font = agencyFs + 'px Arial, sans-serif';
                ctx.fillStyle = '#666666';
                ctx.fillText(e.agencyText, xCol, yRow);

                const swatchY = yRow + 3 * scale + routeLineH * 0.7;
                ctx.fillStyle = e.color;
                ctx.fillRect(xCol, swatchY - 4 * scale, 16 * scale, 4 * scale);
                ctx.font = routeFs + 'px Arial, sans-serif';
                ctx.fillStyle = '#222222';
                e.nameLines.forEach(function(line, lineIdx) {{
                  ctx.fillText(line, xCol + glyphW2, swatchY + lineIdx * (routeLineH + lineGap));
                }});

                xCol += e.colW + colGapX;
              }});
              yRow += rowHeights[rowIdx] + colGapY;
            }});

            ctx.font = fs + 'px Arial, sans-serif';
            let yS = headY + gap + rowH * 0.75;
            legendData.symbols.forEach(function(symbol) {{
              const cx = x2 + 8 * scale;
              if (symbol.type === 'line') {{
                ctx.fillStyle = symbol.color;
                ctx.fillRect(x2, yS - 5 * scale, 16 * scale, 4 * scale);
              }} else if (symbol.type === 'circle') {{
                ctx.beginPath();
                ctx.arc(cx, yS - 3.5 * scale, symbol.radius * scale, 0, Math.PI * 2);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
                ctx.strokeStyle = symbol.color;
                ctx.lineWidth = 2 * scale;
                ctx.stroke();
              }}
              ctx.fillStyle = '#222222';
              ctx.fillText(symbol.label, x2 + glyphW, yS);
              yS += rowH;
            }});

            canvas.toBlob(function(blob) {{
              if (!blob) {{ alert('PNG export failed.'); return; }}
              const url = URL.createObjectURL(blob);
              transitTriggerDownload(url, 'transit_map.png');
              setTimeout(() => URL.revokeObjectURL(url), 2000);
            }}, 'image/png');
          }};
          mapImg.onerror = function() {{
            alert('PNG download failed: could not rasterize the map.');
          }};
          mapImg.src = mapDataUrl;
        }} catch (e) {{
          alert('PNG download failed: ' + e);
        }}
      }}

      function transitSetLegendFullWidth(on) {{
        const legend = document.getElementById('transit-legend');
        if (on) {{
          legend.style.left = '0';
          legend.style.right = '0';
          legend.style.bottom = '0';
          legend.style.width = '100%';
          legend.style.borderRadius = '0';
          legend.style.justifyContent = 'center';
          legend.style.padding = '10px 32px';
        }} else {{
          legend.style.right = 'auto';
          legend.style.left = '18px';
          legend.style.bottom = '14px';
          legend.style.width = 'auto';
          legend.style.borderRadius = '0';
          legend.style.justifyContent = 'flex-start';
          legend.style.padding = '9px 12px';
        }}
      }}

      function transitFullscreen() {{
        const el = document.getElementById('transit-wrapper');
        const container = document.getElementById('transit-plot-container');
        const isFs = document.fullscreenElement || document.webkitFullscreenElement;

        function applyFullscreenStyle(on) {{
          if (on) {{
            el.style.position = 'fixed';
            el.style.top = '0'; el.style.left = '0';
            el.style.width = '100vw'; el.style.height = '100vh';
            el.style.zIndex = '99999';
            el.style.background = '#ffffff';
            container.style.height = 'calc(100vh - 40px)';
            container.style.width = '100vw';
          }} else {{
            el.style.position = 'relative';
            el.style.width = 'auto'; el.style.height = 'auto';
            el.style.zIndex = 'auto';
            container.style.height = '{height}px';
            container.style.width = '100%';
          }}
          // Legend spans the full width of the screen edge-to-edge only
          // while in full screen; back to its normal corner box otherwise.
          transitSetLegendFullWidth(on);
          setTimeout(transitResizePlot, 200);
        }}

        if (!isFs) {{
          const req = el.requestFullscreen || el.webkitRequestFullscreen;
          if (req) {{
            req.call(el).then(() => applyFullscreenStyle(true))
                         .catch(() => applyFullscreenStyle(true));
          }} else {{
            applyFullscreenStyle(true);
          }}
        }} else {{
          const exit = document.exitFullscreen || document.webkitExitFullscreen;
          if (exit) {{ exit.call(document); }}
          applyFullscreenStyle(false);
        }}
      }}

      document.addEventListener('fullscreenchange', () => {{
        if (!document.fullscreenElement) {{
          const el = document.getElementById('transit-wrapper');
          const container = document.getElementById('transit-plot-container');
          el.style.position = 'relative';
          el.style.width = 'auto'; el.style.height = 'auto';
          container.style.height = '{height}px';
          container.style.width = '100%';
          transitSetLegendFullWidth(false);
          transitResizePlot();
        }}
      }});

      window.addEventListener('resize', transitResizePlot);
      setTimeout(transitResizePlot, 200);
    </script>
    """
    st.components.v1.html(html_code, height=height + 60, scrolling=False)



# =========================================================
# APP
# =========================================================

def img_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""
img = img_to_base64("KTM Vallery.png")

# ================= TOP CONTAINER (HERO BANNER) =================
with st.container(border=True):
    if img:
        st.markdown(
            f"""
            <style>
                .hero-container {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    padding: 1rem;
                    width: 100%;
                }}
                .hero-img {{
                    max-width: 100%;
                    max-height: 350px; /* Limits height so it doesn't push data too far down */
                    border-radius: 12px;
                    object-fit: cover;
                    margin-bottom: 1.5rem;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .hero-title {{
                    font-size:3rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                    color: inherit; /* Adapts to Streamlit's dark/light theme */
                }}
                .hero-subtitle {{
                    font-size: 1rem;
                    letter-spacing: 2px;
                    opacity: 0.8;
                    font-weight: 500;
                }}
            </style>

            <div class="hero-container">
                <img src="data:image/png;base64,{img}" class="hero-img">
                <div class="hero-title">KATHMANDU VALLEY MOBILITY INSIGHT DASHBOARD</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <h1>KATHMANDU VALLEY MOBILITY INSIGHT DASHBOARD</h1>
                <p style="letter-spacing: 2px; opacity: 0.8;"> • KTM VALLEY  • GTFS FEED 2026</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ================= LOAD DATA =================
df_cong = fetch_congestion()
df_dur = route_durations()
df_agency = routes_per_agency()
df_start = fetch_starting_stops()
kpi = fetch_kpi()

longest = df_dur.loc[df_dur["duration"].idxmax()]
shortest = df_dur.loc[df_dur["duration"].idxmin()]

# ================= KPI CARDS =================
with st.container(border=True):
    c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,2,2,2])
    with c1:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#3b82f6">
        <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill">operators</span>
            </div>
            <div class="kpi-label">AGENCIES</div>
            <div class="kpi-val">{kpi["agency"]}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub info">● All active</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#14b8a6">
            <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill">Network</span>
            </div>
            <div class="kpi-label">ROUTES</div>
            <div class="kpi-val">{kpi["routes"]}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub info">↑ Route Network</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        cong_val = round(df_cong["congestion_index"].max(), 1)
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#ef4444">
            <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill kpi-pill-red">HIGH</span>
            </div>
            <div class="kpi-label">PEAK CONGESTION</div>
            <div class="kpi-val" style="color:#ef4444">{cong_val}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub warn">⚠ 10 AM midday peak</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        leader      = df_agency.iloc[0]
        leader_name = leader["agency_name"]
        leader_pct  = leader["percentage"]
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#f59e0b">
            <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill kpi-pill-amber">{leader_pct}%</span>
            </div>
            <div class="kpi-label">MARKET LEADER</div>
            <div class="kpi-val kpi-val-sm">{leader_name}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub up">↑ Highest route share</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#a78bfa">
            <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill kpi-pill-purple">{longest['duration']:.0f} min</span>
            </div>
            <div class="kpi-label">LONGEST ROUTE</div>
            <div class="kpi-val kpi-val-sm">{longest['route_id']}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub purple">🕐 {int(longest['duration'])//60}h {int(longest['duration'])%60}m</div>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:#22c55e">
            <div class="kpi-icon-row">
                <span class="kpi-icon"></span>
                <span class="kpi-pill kpi-pill-green">{shortest['duration']:.1f} min</span>
            </div>
            <div class="kpi-label">SHORTEST ROUTE</div>
            <div class="kpi-val kpi-val-sm">{shortest['route_id']}</div>
            <div class="kpi-divider"></div>
            <div class="kpi-sub up">↑ Most efficient</div>
        </div>
        """, unsafe_allow_html=True)

col_filter, col_map1, col_map2 = st.columns([1.5, 3, 1.5])

# =========================================================
# ROUTE COLORS (GLOBAL COLOR MAP) — single source of truth,
# shared with the LOOM SVG map via create_filtered_gtfs()
# =========================================================
color_emoji_map = COLOR_EMOJI_MAP

# ALL ROUTES
all_routes_df = fetch_routes()

# FIXED COLOR MAP (name + hex), same assignment used everywhere
route_color_map, route_color_hex_map = get_route_color_maps()

route_agency_map = get_route_agency_map()

route_name_map = {
    route_id: route_short_name
    for route_id, route_short_name in zip(
        all_routes_df["route_id"], all_routes_df["route_short_name"]
    )
}

# =========================================================
# FILTER PANEL CONTAINER
# =========================================================
with col_filter:
        with st.container(border=True):
            st.markdown("###### Agencies & Routes")

            agencies = fetch_agencies()
            routes_df = fetch_routes()

            selected_routes = []
            selected_agencies = []

            with st.container(height=750):

                for _, agency_row in agencies.iterrows():

                    agency_id = agency_row["agency_id"]
                    agency_name = agency_row["agency_name"]

                    with st.expander(f"{agency_name}", expanded=False):

                        agency_routes = routes_df[
                            routes_df["agency_id"] == agency_id
                        ]

                        for _, route_row in agency_routes.iterrows():

                            route_id = route_row["route_id"]
                            route_name = route_row["route_short_name"]

                            # COLOR
                            route_color = route_color_map[route_id]
                            color_icon = color_emoji_map.get(route_color, "🔴")

                            route_checked = st.checkbox(
                                f"{color_icon} {route_name}",
                                key=f"route_{route_id}"
                            )

                            if route_checked:
                                if route_id not in selected_routes:
                                    selected_routes.append(route_id)

                                if agency_id not in selected_agencies:
                                    selected_agencies.append(agency_id)

# =========================================================
# MAP CONTAINER
# =========================================================
with col_map1:
        with st.expander("Route Map", expanded=True):

            # ================= CHECK ROUTES =================
            if not selected_routes:

                st.info("👈 Select an agency and route")

            else:

                # ================= VIEW MODE TOGGLE (NEW FEATURE) =================
                view_mode = st.radio(
                    "View",
                    ["🗺️ Live Map", "🚇 Transit Map", "🧵 LOOM Map (SVG)"],
                    horizontal=True,
                    key="map_view_mode",
                    label_visibility="collapsed"
                )

                selected_landmarks = st.multiselect(
                    "Vector landmarks",
                    list(LANDMARKS.keys()),
                    default=[name for name in DEFAULT_LANDMARKS if name in LANDMARKS],
                    key="selected_vector_landmarks",
                    help=(
                        "Vector landmarks are anchored to geographic coordinates. "
                        "Their geometry follows the map when zooming and panning."
                    ),
                )

                if selected_landmarks:
                    show_landmark_status = st.checkbox(
                        "🔍 Show landmark icon status",
                        value=False,
                        key="show_landmark_status",
                    )
                    if show_landmark_status:
                        with st.container(border=True):
                            for lm_name in selected_landmarks:
                                lm_record = dict(LANDMARKS.get(lm_name, {}))
                                lm_record["name"] = lm_name
                                status = get_landmark_custom_svg_status(lm_record)
                                if status["ok"]:
                                    st.markdown(f"✅ **{lm_name}** — {status['reason']}")
                                elif lm_record.get("svg"):
                                    st.markdown(
                                        f"⚠️ **{lm_name}** — falling back to the "
                                        f"generic shape. {status['reason']}"
                                    )
                                else:
                                    st.markdown(
                                        f"ℹ️ **{lm_name}** — no custom SVG set, "
                                        f"using the built-in shape (normal)."
                                    )

                landmark_icon_scale = 3.0

                if view_mode == "🗺️ Live Map":

                    # ================= INTERSECTION DATA =================
                    intersection_df = pd.DataFrame()

                    if len(selected_routes) >= 2:
                        intersection_df = common_stops(selected_routes)

                    # ================= BASE MAP =================
                    m1 = folium.Map(location=[27.7, 85.3],zoom_start=12,tiles=None
                    )

                    folium.TileLayer("OpenStreetMap",name="Openstreet",show=True
                    ).add_to(m1)

                    folium.TileLayer("CartoDB positron",name="Light",show=False
                    ).add_to(m1)

                    folium.TileLayer("CartoDB dark_matter",name="Dark",show=False
                    ).add_to(m1)

                    # ================= ROUTES =================
                    for route_id in selected_routes:

                        color = route_color_map[route_id]
                        geom = route_geom(route_id)

                        route_layer = folium.FeatureGroup(
                            name=f"Route {route_id}",
                            show=True
                        )

                        for _, row in geom.iterrows():
                            if row["path"]:
                                coords = [
                                    (lat, lon)
                                    for lon, lat in row["path"]
                                ]

                                folium.PolyLine(coords,color="gray",weight=2,opacity=0.3
                                ).add_to(route_layer)

                                AntPath(locations=coords,color=color,weight=4,delay=800
                                ).add_to(route_layer)

                        route_layer.add_to(m1)

                        # ================= STOPS =================
                        stops_df = stops(route_id)

                        stops_layer = folium.FeatureGroup(
                            name=f"Stops {route_id}",
                            show=True
                        )

                        for _, r in stops_df.iterrows():
                            name = r["stop_name"]
                            folium.CircleMarker(
                                location=[r["stop_lat"], r["stop_lon"]],
                                radius=3,
                                color=color,
                                fill=True,
                                fill_opacity=1,
                                popup=folium.Popup(
                                    f"""
                                    <b>Stop Name:</b><br>{name}<br>

                                    """,
                                    max_width=250

                                ),
                                tooltip=name
                            ).add_to(stops_layer)

                        stops_layer.add_to(m1)

                    # ================= HUBS =================
                    hubs_df = hubs()

                    hub_heat = [
                        [r["osm_latitude"], r["osm_longitude"]]
                        for _, r in hubs_df.iterrows()
                    ]

                    hub_layer = folium.FeatureGroup(
                        name="Hubs",
                        show=True
                    )

                    if len(hub_heat) > 0:

                        HeatMap(
                            hub_heat,
                            radius=15,
                            blur=20,
                            min_opacity=0.4,
                            max_zoom=10
                        ).add_to(hub_layer)

                    hub_layer.add_to(m1)

                    # ================= INTERSECTION STOPS =================
                    if not intersection_df.empty:

                        intersection_layer = folium.FeatureGroup(
                            name="🔄 Interchange Stops",
                            show=True
                        )

                        for _, r in intersection_df.iterrows():
                            folium.CircleMarker(
                                location=[r["stop_lat"], r["stop_lon"]],
                                radius=9,
                                color="red",
                                fill=True,
                                fill_color="red",
                                fill_opacity=0.95,
                                popup=folium.Popup(
                                    f"""
                                    <b>🔄 Interchange Stop</b><br>
                                    {r['stop_name']}<br>
                                    Routes Passing: {r['route_count']}
                                    """,
                                    max_width=250
                                )
                            ).add_to(intersection_layer)

                        intersection_layer.add_to(m1)

                    # ================= LAYER CONTROL =================
                    folium.LayerControl(collapsed=True).add_to(m1)

                    # ================= RENDER MAP =================
                    st_folium(
                        m1,
                        use_container_width=True,
                        height=750
                    )

                elif view_mode == "🚇 Transit Map":

                    # ---- NEW: declutter controls -----------------------
                    tm_col1, tm_col2, tm_col3 = st.columns([1.3, 1.3, 1])
                    with tm_col1:
                        tm_label_density = st.selectbox(
                            "Label density",
                            [
                                "Major exchanges only",
                                "Terminals & interchanges only",
                                "Every other stop",
                                "All stops",
                            ],
                            key="tm_label_density",
                            help="Thin out station-name labels on busy, "
                                 "multi-route selections.",
                        )
                    with tm_col2:
                        tm_separate_routes = st.checkbox(
                            "Separate overlapping routes",
                            value=True,
                            key="tm_separate_routes",
                            help="Fans routes that share a corridor into "
                                 "parallel lines instead of drawing them "
                                 "on top of each other. Slightly shifts "
                                 "lines/stops from their exact coordinates "
                                 "for readability.",
                        )
                        tm_route_spacing = st.slider(
                            "Spacing", 0.5, 3.0, 1.0, 0.25,
                            key="tm_route_spacing",
                            disabled=not tm_separate_routes,
                        )
                    with tm_col3:
                        tm_show_markers = st.checkbox(
                            "Show stop markers",
                            value=True,
                            key="tm_show_markers",
                        )

                    label_options = sorted({
                        re.sub(r"\s+\d+\s*$", "", str(stop_name).strip()).strip()
                        or str(stop_name).strip()
                        for route_id in selected_routes
                        for stop_name in route_stops_ordered(route_id)["stop_name"]
                        if not pd.isna(stop_name) and str(stop_name).strip()
                    })
                    tm_hidden_labels = st.multiselect(
                        "Hide labels",
                        label_options,
                        key="tm_hidden_labels",
                        help="Select stop labels to remove from the map. "
                             "Markers and route lines remain visible.",
                    )

                    fig_transit = build_transit_map(
                        selected_routes,
                        route_color_map,
                        route_name_map,
                        route_agency_map=route_agency_map,
                        title_text="Transit Map of Kathmandu Valley",
                        separate_overlapping_routes=tm_separate_routes,
                        route_spacing=tm_route_spacing,
                        label_density=tm_label_density,
                        show_stop_markers=tm_show_markers,
                        hidden_label_names=tuple(tm_hidden_labels),
                        selected_landmarks=tuple(selected_landmarks),
                        landmark_icon_size_deg=0.0026 * landmark_icon_scale,
                    )

                    display_transit_map(
                        fig_transit,
                        selected_routes,
                        route_name_map,
                        route_color_hex_map,
                        route_agency_map=route_agency_map,
                    )



                else:  # LOOM Map (SVG)

                    st.markdown("### LOOM Transit Map")

                    schematic = st.checkbox(
                        "Schematic (octilinear) layout",
                        value=False,  
                        key="loom_schematic_toggle",
                        help=(
                            "On: octi schematic map (metro-style, may distort "
                            "long/sparse routes into exaggerated zig-zags "
                            "unless tuned). Off: geographically accurate map."
                        ),
                    )

                    octi_extra_args = ""
                    if schematic:
                        with st.container(border=True):
                            st.markdown("**Advanced: octi tuning flags**")
                            st.caption(
                                "octi's default grid/cell size can be too coarse "
                                "for long, sparse routes, causing the zig-zag "
                                "distortion. Run the help output below to see "
                                "your build's real flag names (e.g. for cell "
                                "size or base grid type), then paste the flag "
                                "you want into the box."
                            )
                            if st.button("Show `octi -h` output", key="octi_help_btn"):
                                try:
                                    st.code(get_octi_help())
                                except Exception as help_error:
                                    st.error(f"Couldn't fetch octi help: {help_error}")

                            octi_extra_args = st.text_input(
                                "Extra flags to pass to octi",
                                value="",
                                key="octi_extra_args",
                                placeholder="e.g. -b octilinear <cell-size flag> <value>",
                            )

                    lw_col, ls_col = st.columns(2)
                    with lw_col:
                        loom_line_width = st.slider(
                            "Line width",
                            min_value=10, max_value=100, value=40, step=5,
                            key="loom_line_width",
                        )
                    with ls_col:
                        loom_line_spacing = st.slider(
                            "Line spacing (parallel routes)",
                            min_value=5, max_value=60, value=20, step=5,
                            key="loom_line_spacing",
                        )

                    # ---- NEW: label padding control (fixes incomplete /
                    # clipped station names) -------------------------------
                    show_label_advanced = st.checkbox(
                        "Show advanced station label settings",
                        value=False,
                        key="show_label_advanced",
                    )
                    if show_label_advanced:

                        st.caption(
                            "LOOM sizes the map canvas from the route-line "
                            "geometry only, not from how wide station-name "
                            "text is. Labels near the edge of the map can "
                            "therefore run past that canvas and get clipped "
                            "('incomplete' stop names). Increasing this pads "
                            "the canvas so labels have room to render fully."
                        )
                        loom_label_pad = st.slider(
                            "Label padding (px)",
                            min_value=0, max_value=300, value=100, step=25,
                            key="loom_label_pad",
                        )
                        loom_label_font_scale = st.slider(
                            "Label font size x",
                            min_value=0.75, max_value=3.0, value=2, step=0.05,
                            key="loom_label_font_scale",
                            help="Multiplies the font size in LOOM station labels.",
                        )
                    else:
                        loom_label_pad = st.session_state.get("loom_label_pad", 100)
                        loom_label_font_scale = st.session_state.get(
                            "loom_label_font_scale", 1.25
                        )

                    if schematic and selected_landmarks:
                        st.info(
                            "In schematic LOOM mode, landmarks are anchored to "
                            "their nearest transit stop's actual position on the "
                            "octilinear layout (real lon/lat can't be placed "
                            "directly, since octi distorts it). A landmark whose "
                            "nearest stop isn't identifiable in the rendered map "
                            "is left off rather than placed somewhere misleading."
                        )

                    try:
                        with st.spinner("Running LOOM pipeline..."):
                            svg = generate_loom_svg(
                                tuple(selected_routes),
                                schematic=schematic,
                                octi_extra_args=octi_extra_args,
                                line_width=loom_line_width,
                                line_spacing=loom_line_spacing,
                                label_pad=loom_label_pad,
                                label_font_scale=loom_label_font_scale,
                                selected_landmarks=tuple(selected_landmarks),
                                landmark_icon_size=28 * landmark_icon_scale,
                            )

                        display_loom_svg(
                            svg,
                            selected_routes,
                            route_name_map,
                            route_agency_map,
                        )
                        st.success("LOOM map generated successfully.")
                    except Exception as error:
                        st.error("LOOM map generation failed.")
                        st.exception(error)


# =========================================================
# CHART CONTAINER
# =========================================================
with col_map2:
        # ================= ROUTES BY AGENCY =================
        with st.expander("Routes by Agency", expanded=True):

            df_agency = routes_per_agency()

            fig_small = px.bar(
                df_agency,
                x="route_count",
                y="agency_name",
                orientation="h",
                color="route_count",
                color_continuous_scale="turbo"
            )
            fig_small.update_layout(
                width=700,   # increase graph width
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),  # reduce margins
                xaxis_title="Route_Count",
                yaxis_title="Agency_Name",
            )

            st.plotly_chart(fig_small, use_container_width=True)

        # ================= STARTING STOPS =================
        with st.expander("Major Starting Stops", expanded=True):

            top_start = (
                df_start.sort_values("trips_starting_at_stop", ascending=False)
                .head(5)
            )

            fig_start = px.line(
                top_start,
                x="stop_name",
                y="trips_starting_at_stop",
                markers=True,
                text="trips_starting_at_stop"
            )

            fig_start.update_layout(
                height=290,
                xaxis_title="Starting Stops",
                yaxis_title="Trips from Stop",
                xaxis_tickangle=-45,
                font=dict(family="Inter", size=14)
            )

            st.plotly_chart(fig_start, use_container_width=True)

# ================= CONGESTION VISUALS ================
left_container, right_container = st.columns([3,1])

# =========================================================
# LEFT CONTAINER -> COL1 + COL2
# =========================================================
with left_container:

    with st.container(border=True):

        col3, col4 = st.columns([1.2, 1.6])

        # ================= TOP 5 =================
        top5 = (
            df_dur
            .sort_values("duration", ascending=False)
            .head(5)
        )

        if "selected_route_id" not in st.session_state:
            st.session_state.selected_route_id = top5.iloc[0]["route_id"]

        # -------------------------------------------------
        # COL 3 -> PIE
        # -------------------------------------------------
        with col3:
            with st.expander("Top 5 Longest Routes"):
                st.write("""
    This visualization shows the 5 routes with the highest trip duration.
    It helps to analyze:
    - Long distance routes
    - Slow-moving transit lines
    - Operational efficiency issues
    """)

            fig_pie = px.pie(
                top5,
                names="route_id",
                values="duration",
                color_discrete_sequence=px.colors.sequential.Turbo,
                hole=0
            )

            fig_pie.update_layout(
                height=450,
                margin=dict(t=30, b=10, l=20, r=20),
                font=dict(family="Inter", size=14)
            )

            fig_pie.update_traces(
                textinfo='percent',
                pull=[
                    0.2 if r == st.session_state.selected_route_id else 0
                    for r in top5["route_id"]
                ]
            )

            selected_points = plotly_events(
                fig_pie,
                click_event=True,
                key="pie_click"
            )

            if selected_points:

                idx = selected_points[0]["pointNumber"]

                st.session_state.selected_route_id = (
                    top5.iloc[idx]["route_id"]
                )

        # -------------------------------------------------
        # COL 4 -> ROUTE DETAILS
        # -------------------------------------------------
        with col4:
            with st.expander("Route Details"):
                st.write("""
    This visualization shows the route duration and path for the selected route from the pie chart.
    It helps to analyze:
    - Route length and travel time
    - Geographical coverage
    """)

            selected_route_id = st.session_state.selected_route_id
            sel = df_dur[
                df_dur["route_id"] == selected_route_id
            ].iloc[0]

            st.markdown(f"""
            **Route ID:** {sel['route_id']}
            **Duration:** {sel['duration']:.1f} min
            """)

            m_preview = folium.Map(location=[27.7, 85.3], zoom_start=12, tiles=None)
            folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=True).add_to(m_preview)
            geom = route_geom(selected_route_id)

            for _, row in geom.iterrows():

                if row["path"]:

                    folium.PolyLine(
                        locations=[
                            (lat, lon)
                            for lon, lat in row["path"]
                        ],
                        color="blue",
                        weight=4
                    ).add_to(m_preview)

            stops_df = stops(selected_route_id)

            for _, r in stops_df.iterrows():
                name = r["stop_name"]

                folium.CircleMarker(
                    [r["stop_lat"], r["stop_lon"]],
                    radius=3,
                    color="red",
                    fill=True,
                    popup=folium.Popup(
                                f"""
                                <b>Stop Name:</b><br>{name}<br>

                                """,
                                max_width=250

                            ),
                            tooltip=name
                ).add_to(m_preview)

            st_folium(
    m_preview,
    use_container_width=True,
    height=640
)

# RIGHT COLUMN -> CONGESTION

with right_container:
    with st.container(border=True):
        with st.expander("Congestion Trend"):
            st.write("""
This line chart shows congestion index and average speed by hour.
It helps to analyze:
- Peak congestion hours
- Correlation between speed and congestion

The maximum congestion rate was **62.02**, observed at **10 AM**, while the minimum congestion rate was **18.13**, occurring after **8 PM**. The lowest average speed recorded was **0.00 km/h**, primarily during the early hours of the day between **1 AM and 5 AM**, whereas the highest average speed of **20.19 km/h** was observed during the morning period between **5 AM and 9 AM**. Overall, the congestion index and average speed exhibit an inverse relationship, where congestion levels increase during peak traffic hours while average vehicle speed decreases significantly during the same periods.
            """)

        # ================= CONGESTION MAX/MIN =================
        max_cong = df_cong.loc[df_cong["congestion_index"].idxmax()]
        min_cong = df_cong.loc[df_cong["congestion_index"].idxmin()]

        # ================= SPEED MAX/MIN =================
        max_speed = df_cong.loc[df_cong["avg_speed"].idxmax()]
        min_speed = df_cong.loc[df_cong["avg_speed"].idxmin()]

        # ================= FIGURE =================
        fig = px.line(
            df_cong,
            x="hour",
            y="congestion_index",
            markers=True,
            # title="Congestion Trend"
        )

        # Avg speed line
        fig.add_scatter(
            x=df_cong["hour"],
            y=df_cong["avg_speed"],
            mode="lines+markers",
            name="Avg Speed"
        )

        fig.update_layout(xaxis_title="Hour",
                yaxis_title="Congestion_Index",
                height=300)
        st.plotly_chart(fig, use_container_width=True)

# ================= BAR CHART =================
    with st.container(border=True):
        with st.expander("Congestion by Time"):
            st.write("""This bar chart shows the average congestion index for different time blocks of the day.
It helps to analyze:
- Congestion patterns during morning, midday, evening, and night
- Identifying critical time periods for traffic management .

The highest congestion rate was observed during the midday period between 10 AM and 3 PM, with an average congestion index of 58.2, corresponding to peak urban activity hours when most offices, schools, and commercial centers are operational. In contrast, the lowest congestion levels occurred during nighttime, particularly between 8 PM and 4 AM, when traffic volume is considerably lower. The analysis further indicates that average vehicle speed decreases significantly during highly congested periods and increases during low-traffic hours, demonstrating an inverse relationship between congestion intensity and traffic speed.
    """)

        block = df_cong.groupby("time_block", as_index=False)["congestion_index"].mean()

        fig1 = px.bar(
            block,
            x="time_block",
            y="congestion_index",
            color="congestion_index",
            text="congestion_index"
        )

        fig1.update_traces(
    texttemplate='%{text:.1f}',
    textposition='outside',
    width=0.9,
    cliponaxis=False  # 👉 increases bar thickness (0–1 range for categorical charts)
)

        fig1.update_layout(
            xaxis_title="Time Block",
            yaxis_title="Congestion_Index",
            height=300
        )
        st.plotly_chart(fig1, use_container_width=True)