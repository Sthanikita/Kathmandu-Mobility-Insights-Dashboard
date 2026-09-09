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
import base64
import html
import shlex
import re
import math
import platform
import xml.etree.ElementTree as ET
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
    return sqlalchemy.create_engine(st.secrets["DB_URL"])

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
# Every route gets ONE color name + ONE hex value, assigned here and reused
# everywhere: the sidebar checkboxes/emoji swatches, the Live folium map,
# the Plotly "Transit Map", and the LOOM SVG map. This is what makes the
# LOOM map's colors match the route colors the user selects in the sidebar.
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
    return pd.read_sql(f"""
        SELECT ARRAY_AGG(ARRAY[shape_pt_lon, shape_pt_lat]) AS path
        FROM shapes
        WHERE shape_id IN (
            SELECT DISTINCT shape_id
            FROM trips
            WHERE route_id = '{route_id}'
        )
    """, engine)

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


def build_transit_map(selected_routes, route_color_map, route_name_map,
                       route_agency_map=None,
                       title_text="Transit Map of Kathmandu Valley"):
    fig = go.Figure()

    any_data = False
    labeled_stops = set()
    label_points = []
    map_lons = []
    map_lats = []
    label_annotations = []

    LABEL_POSITIONS = [
        # (xshift, yshift, xanchor, yanchor)
        (0,   20, "center", "bottom"),   # top
        (0,  -20, "center", "top"),      # bottom
        (-18, 0,  "right",  "middle"),   # left
        (18,  0,  "left",   "middle"),   # right
        (-14, 16, "right",  "bottom"),   # top-left
        (14,  16, "left",   "bottom"),   # top-right
        (-14,-16, "right",  "top"),      # bottom-left
        (14, -16, "left",   "top"),      # bottom-right
    ]
    label_cycle = 0

    def next_label_position():
        nonlocal label_cycle
        position = LABEL_POSITIONS[label_cycle % len(LABEL_POSITIONS)]
        label_cycle += 1
        return position

    def format_stop_name(stop_name, max_chars=16):
        """Wrap stop names without removing any characters."""
        if pd.isna(stop_name):
            return ""

        stop_name = str(stop_name).strip()
        if not stop_name:
            return ""

        words = stop_name.split()
        lines = []
        current_line = ""

        for word in words:
            if len(word) > max_chars:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                lines.append(word)
                continue

            if not current_line:
                current_line = word
                continue

            proposed_line = current_line + " " + word
            if len(proposed_line) <= max_chars:
                current_line = proposed_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return "<br>".join(lines)

    for route_id in selected_routes:
        ordered = route_stops_ordered(route_id)
        if ordered.empty:
            continue

        any_data = True
        map_lons.extend(pd.to_numeric(ordered["stop_lon"], errors="coerce").dropna().tolist())
        map_lats.extend(pd.to_numeric(ordered["stop_lat"], errors="coerce").dropna().tolist())
        base_color = route_color_map.get(route_id, "blue")
        color = ROUTE_COLOR_HEX.get(base_color, base_color)
        route_label = route_name_map.get(route_id, route_id)
        agency_label = (route_agency_map or {}).get(route_id, "Unknown Agency")
        agency_group = f"agency-{agency_label}"
        first_agency_route = not any(
            trace.legendgroup == agency_group for trace in fig.data
        )

        if first_agency_route:
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=1, color="rgba(0,0,0,0)"),
                name=f"<b>{html.escape(str(agency_label))}</b>",
                legendgroup=agency_group,
                hoverinfo="skip",
                uid=f"agency-{agency_label}",
            ))

        # route line connecting stops in sequence
        fig.add_trace(go.Scatter(
            x=ordered["stop_lon"],
            y=ordered["stop_lat"],
            mode="lines",
            line=dict(color=color, width=8),  # thicker line (was 4)
            name=route_label,
            hoverinfo="skip",
            legendgroup=agency_group,
            uid=f"line-{route_id}",
            cliponaxis=False,  # don't hard-clip the line right at the axis edge
        ))

        display_texts = []
        for _, stop_row in ordered.iterrows():
            stop_name = "" if pd.isna(stop_row["stop_name"]) else str(stop_row["stop_name"]).strip()
            stop_lat = float(stop_row["stop_lat"])
            stop_lon = float(stop_row["stop_lon"])
            stop_key = (
                stop_name.casefold(),
                round(stop_lat, 6),
                round(stop_lon, 6),
            )
            is_near_existing_label = any(
                abs(stop_lat - label_lat) < 0.0015
                and abs(stop_lon - label_lon) < 0.0015
                for label_lat, label_lon in label_points
            )
            if stop_key in labeled_stops or is_near_existing_label:
                display_texts.append("")
            else:
                display_texts.append(format_stop_name(stop_name))
                labeled_stops.add(stop_key)
                label_points.append((stop_lat, stop_lon))

        fig.add_trace(go.Scatter(
            x=ordered["stop_lon"],
            y=ordered["stop_lat"],
            mode="markers",
            marker=dict(
                size=9,
                color="white",
                line=dict(color=color, width=3),
            ),
            hovertext=ordered["stop_name"],
            hovertemplate="<b>%{hovertext}</b><extra></extra>",
            showlegend=False,
            legendgroup=agency_group,
            cliponaxis=False,
            uid=f"stops-{route_id}",
        ))

        for index, (_, stop_row) in enumerate(ordered.iterrows()):
            label = display_texts[index]
            if not label:
                continue
            xshift, yshift, xanchor, yanchor = next_label_position()
            label_annotations.append(dict(
                x=float(stop_row["stop_lon"]),
                y=float(stop_row["stop_lat"]),
                xref="x",
                yref="y",
                text=label,
                showarrow=False,
                xshift=xshift,
                yshift=yshift,
                xanchor=xanchor,
                yanchor=yanchor,
                align="center",
                # soft white pill so the text stays readable over lines
                bgcolor="rgba(255,255,255,0.72)",
                bordercolor="rgba(0,0,0,0.08)",
                borderwidth=1,
                borderpad=2,
                font=dict(size=11, color="#111111", family="Arial, sans-serif"),
            ))

    fig.update_layout(
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
            title="Routes",
            orientation="h",
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(color="#111111"),
            xref="paper",
            yref="paper",
            x=0.0,
            y=-0.14,
            xanchor="left",
            yanchor="top",
        ),
        xaxis=dict(
            visible=False,
            autorange=True,
        ),
        yaxis=dict(
            visible=False,
            autorange=True,
        ),
        autosize=True,
        height=700,
        margin=dict(t=100, b=120, l=90, r=90),
        annotations=label_annotations,
        hovermode="closest",
        dragmode="pan",
        uirevision=",".join(sorted(selected_routes)),
    )

    if map_lons and map_lats:
        lon_min, lon_max = min(map_lons), max(map_lons)
        lat_min, lat_max = min(map_lats), max(map_lats)

        lon_padding = max((lon_max - lon_min) * 0.18, 0.006)
        lat_padding = max((lat_max - lat_min) * 0.18, 0.006)
        fig.update_xaxes(range=[lon_min - lon_padding, lon_max + lon_padding])
        fig.update_yaxes(range=[lat_min - lat_padding, lat_max + lat_padding])

    if not any_data:
        fig.add_annotation(
            text="No stop-sequence data found for the selected route(s).",
            showarrow=False,
            font=dict(size=14, color="#666666"),
            xref="paper", yref="paper",
            x=0.5, y=0.5
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

    def bbox(lb):
        xs = [p[0] for p in lb['pts']]
        ys = [p[1] for p in lb['pts']]
        horiz = (max(xs) - min(xs)) >= (max(ys) - min(ys))
        if horiz:
            return min(xs), min(ys) - lb['fs'], max(xs), max(ys), True
        return min(xs) - lb['fs'], min(ys), max(xs), max(ys), False

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
            step = fs * 1.35
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


@st.cache_data(show_spinner=False)
def generate_loom_svg(
    selected_routes_tuple,
    schematic=True,
    octi_extra_args="",
    line_width=40,
    line_spacing=20,
    label_pad=150,
    label_font_scale=1.0,
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
    svg = separate_station_labels(svg)

    if label_pad and label_pad > 0:
        svg = pad_svg_viewbox(svg, pad=label_pad)

    return svg


def add_route_title_to_svg(
    svg, selected_routes, route_name_map, title_text="Transit Map of Kathmandu Valley"
):
    return svg


def build_composite_svg(
    svg, selected_routes, route_name_map, route_color_hex_map,
    route_agency_map=None,
    title_text="Transit Map of Kathmandu Valley"
):

    w_match = re.search(r'width="([\d.]+)', svg)
    h_match = re.search(r'height="([\d.]+)', svg)
    w = float(w_match.group(1)) if w_match else 1200.0
    h = float(h_match.group(1)) if h_match else 800.0

    header_h = 55
    legend_header_h = 50
    legend_row_h = 26
    legend_bottom_pad = 20

    legend_groups = {}
    for rid in selected_routes:
        agency = (route_agency_map or {}).get(rid, "Unknown Agency")
        legend_groups.setdefault(agency, []).append(rid)
    legend_row_count = sum(1 + len(route_ids) for route_ids in legend_groups.values())
    legend_h = legend_header_h + legend_row_h * max(legend_row_count, 1) + legend_bottom_pad
    total_w = w
    total_h = h + header_h + legend_h

    encoded_inner = base64.b64encode(svg.encode("utf-8")).decode("ascii")

    legend_top = h + header_h  # y where the legend block begins
    legend_items_svg = []
    row_index = 0
    for agency, route_ids in legend_groups.items():
        y = legend_top + legend_header_h + row_index * legend_row_h
        legend_items_svg.append(
            f'<text x="20" y="{y - 4}" font-family="Arial, sans-serif" '
            f'font-size="13" font-weight="700" fill="#111111">'
            f'{html.escape(str(agency))}</text>'
        )
        row_index += 1
        for rid in route_ids:
            y = legend_top + legend_header_h + row_index * legend_row_h
            color = route_color_hex_map.get(rid, "#1d4ed8")
            name = html.escape(str(route_name_map.get(rid, rid)))
            legend_items_svg.append(
                f'<rect x="34" y="{y - 10}" width="18" height="5" fill="{color}"/>'
                f'<text x="60" y="{y - 4}" font-family="Arial, sans-serif" '
                f'font-size="13" fill="#111111">{name}</text>'
            )
            row_index += 1
    legend_svg = "".join(legend_items_svg)

    escaped_title = html.escape(title_text)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">
  <rect x="0" y="0" width="{total_w}" height="{total_h}" fill="#ffffff"/>
  <text x="{total_w / 2}" y="{header_h / 2 + 8}" text-anchor="middle"
        font-family="Arial, sans-serif" font-size="24" font-weight="700"
        fill="#111111">{escaped_title}</text>
  <image x="0" y="{header_h}" width="{w}" height="{h}"
         xlink:href="data:image/svg+xml;base64,{encoded_inner}"/>
  <text x="20" y="{legend_top + 24}" font-family="Arial, sans-serif"
        font-size="14" font-weight="700" fill="#111111">Routes</text>
  {legend_svg}
</svg>'''


def display_loom_svg(svg, selected_routes, route_name_map, route_agency_map=None):
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    composite_svg = build_composite_svg(
        svg, selected_routes, route_name_map, route_color_hex_map,
        route_agency_map=route_agency_map,
    )
    composite_b64 = base64.b64encode(composite_svg.encode("utf-8")).decode("ascii")

    legend_groups = {}
    for route_id in selected_routes:
        agency = (route_agency_map or {}).get(route_id, "Unknown Agency")
        legend_groups.setdefault(agency, []).append(route_id)

    legend_items = "".join(
        f'<div style="font-weight:700; margin:6px 0 2px;">'
        f'{html.escape(str(agency))}</div>'
        + "".join(
            f'<div style="display:flex; align-items:center; gap:7px; margin:3px 0; padding-left:10px;">'
            f'<span style="width:12px; height:4px; background:{html.escape(str(route_color_hex_map.get(route_id, "#1d4ed8")))}; display:inline-block;"></span>'
            f'<span>{html.escape(str(route_name_map.get(route_id, route_id)))}</span></div>'
            for route_id in route_ids
        )
        for agency, route_ids in legend_groups.items()
    )
    html_code = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <div id="loom-wrapper" style="position:relative; background:#ffffff;
         border-radius:8px; overflow:hidden; border:1px solid #ddd;">
            <div style="padding:14px 18px 10px; background:#ffffff; color:#111111;
                     text-align:center; font-family:Arial,sans-serif;">
                <div style="font-size:24px; font-weight:700;">Transit Map of Kathmandu Valley</div>
            </div>
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
     <div id="loom-scroll" style="position:relative; overflow:auto; width:100%; height:680px;
         background:#fff; padding:24px 28px 70px 28px; box-sizing:border-box;">
        <img id="loom-img"
             src="data:image/svg+xml;base64,{encoded}"
             alt="LOOM Transit Map"
             style="display:block; width:88%; max-width:88%; height:auto;
                    margin:0 auto; transform-origin:0 0; transition:transform 0.15s ease;
                    cursor:grab; user-select:none; touch-action:none;">
                <div style="position:absolute; right:18px; bottom:14px; z-index:2;
                         background:rgba(255,255,255,0.96); border:1px solid #bbb;
                         padding:8px 12px; color:#111; font:12px Arial,sans-serif;
                         box-shadow:0 1px 4px rgba(0,0,0,.18);">
                    <div style="font-weight:700; margin-bottom:4px;">Routes</div>
                    {legend_items}
                </div>
      </div>
    </div>
    <script>
      // Base64 of a complete, standalone SVG that already contains the
      // title, subtitle, map, and legend baked in as native SVG elements.
      // Both download buttons below use THIS (not the bare <img> src) so
      // exported files match what's on screen.
      const loomCompositeSvgDataUrl = "data:image/svg+xml;base64,{composite_b64}";

      let loomScale = 1;
            let loomPanX = 0;
            let loomPanY = 0;
            let loomDragging = false;
            let loomDragStartX = 0;
            let loomDragStartY = 0;
            let loomStartPanX = 0;
            let loomStartPanY = 0;

            function loomApplyTransform() {{
                const img = document.getElementById('loom-img');
                img.style.transform = 'translate(' + loomPanX + 'px, ' + loomPanY + 'px) scale(' + loomScale + ')';
            }}

      function loomZoom(factor) {{
        loomScale = Math.min(Math.max(loomScale * factor, 0.3), 8);
                loomApplyTransform();
      }}

      function loomReset() {{
        loomScale = 1;
                loomPanX = 0;
                loomPanY = 0;
                loomApplyTransform();
                document.getElementById('loom-scroll').scrollTo(0, 0);
      }}

            const loomImg = document.getElementById('loom-img');
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

      // FIX: previously fetched document.getElementById('loom-img').src,
      // which is just the bare LOOM map with no title/legend. Now uses the
      // composite SVG (title + subtitle + map + legend) built server-side.
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

      // FIX: previously drew only the <img> (bare map) onto a canvas, so
      // the exported PNG had no title/legend either. Now rasterizes the
      // same composite SVG used for the SVG download, guaranteeing the
      // PNG and SVG exports always match and both include the header
      // and legend.
      async function loomDownloadPNG() {{
        try {{
          const scale = 3; // render at higher resolution than on-screen size
          const tempImg = new Image();
          tempImg.crossOrigin = 'anonymous';

          tempImg.onload = function() {{
            const w = tempImg.naturalWidth * scale;
            const h = tempImg.naturalHeight * scale;
            const canvas = document.createElement('canvas');
            canvas.width = w;
            canvas.height = h;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, w, h);
            ctx.drawImage(tempImg, 0, 0, w, h);

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
            scrollEl.style.height = 'calc(100vh - 44px)';
          }} else {{
            el.style.position = 'relative';
            el.style.width = 'auto'; el.style.height = 'auto';
            el.style.zIndex = 'auto';
            scrollEl.style.height = '680px';
          }}
        }}

        if (!isFs) {{
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
          document.getElementById('loom-scroll').style.height = '680px';
        }}
      }});
    </script>
    """
    st.components.v1.html(html_code, height=750, scrolling=True)


# ================= APP =================

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

# ROUTE ID -> ROUTE NAME MAP (for transit map legend, e.g. "Payuntar to Kantipath")
# ROUTE ID -> AGENCY NAME MAP (new feature: shown alongside the route name
# in every legend so it's clear which operator runs which route)
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

                    fig_transit = build_transit_map(
                        selected_routes,
                        route_color_map,
                        route_name_map,
                        route_agency_map=route_agency_map,
                        title_text="Transit Map of Kathmandu Valley",
                    )

                    st.plotly_chart(
                        fig_transit,
                        use_container_width=True,
                        config={
                            "scrollZoom": True,
                            "responsive": True,
                            "displayModeBar": True,
                            "displaylogo": False,
                        }
                    )

                else:  # LOOM Map (SVG)

                    st.markdown("### LOOM Transit Map")

                    schematic = st.checkbox(
                        "Schematic (octilinear) layout",
                        value=False,  # default OFF: shows the geographically
                                      # accurate shape, which avoids the
                                      # over-distorted zig-zag look
                        key="loom_schematic_toggle",
                        help=(
                            "On: octi schematic map (metro-style, may distort "
                            "long/sparse routes into exaggerated zig-zags "
                            "unless tuned). Off: geographically accurate map."
                        ),
                    )

                    octi_extra_args = ""
                    if schematic:
                        with st.expander("Advanced: octi tuning flags"):
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
                    st.markdown("**Advanced: station label spacing**")
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
                        min_value=0, max_value=400, value=150, step=25,
                        key="loom_label_pad",
                    )
                    loom_label_font_scale = st.slider(
                        "Label font size x",
                        min_value=0.5, max_value=3.0, value=2.0, step=0.1,
                        key="loom_label_font_scale",
                        help="Multiplies the font size in LOOM station labels.",
                    )
                    if st.button("Show `transitmap -h` output", key="transitmap_help_btn"):
                        try:
                            st.code(get_transitmap_help())
                        except Exception as help_error:
                            st.error(f"Couldn't fetch transitmap help: {help_error}")

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
            # OpenStreetMap doesn't need an API key (CartoDB now returns a
            # 'API key required' error image without one)
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