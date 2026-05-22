import streamlit as st 
from streamlit_folium import st_folium
from streamlit_plotly_events import plotly_events
import folium
from folium.plugins import HeatMap,AntPath
import pandas as pd
import sqlalchemy
import plotly.express as px
import plotly.io as pio
st.set_page_config(layout="wide")
pio.templates.default = "plotly_dark"
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

.kpi-icon {
    font-size: 20px;
    line-height: 1;
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
    font-size: 14px !important;
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
   HERO IMAGE
========================================================= */
.hero-wrapper {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    overflow: hidden;
}

.hero-img {
    width: 100vw;
    height: 450px;
    object-fit: contain;
    display: block;

    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
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
   SCROLLBAR
========================================================= */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #050505;
}

::-webkit-scrollbar-thumb {
    background: #2b2b2b;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #3d3d3d;
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

# ================= APP =================
import base64

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = img_to_base64("KTM Vallery.png")

# ================= CONTAINER =================
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
                    font-size: 2rem;
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
                <h2>KATHMANDU VALLEY MOBILITY INSIGHT DASHBOARD</h2>
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

# ---------- KPI ----------
st.set_page_config(layout="wide")
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
# ROUTE COLORS (GLOBAL COLOR MAP)
# =========================================================
route_colors = [
    "blue","red","green","purple","orange","black","brown","yellow"
]

color_emoji_map = {
    "blue": "🟦",
    "red": "🟥",
    "green": "🟩",
    "purple": "🟪",
    "orange": "🟧",
    "black": "⬛",
    "brown": "🟫",
    "yellow": "🟨"
    
}

# ALL ROUTES
all_routes_df = fetch_routes()

# FIXED COLOR MAP
route_color_map = {
    route_id: route_colors[i % len(route_colors)]
    for i, route_id in enumerate(all_routes_df["route_id"])
}

# =========================================================
# FILTER PANEL CONTAINER
# =========================================================
with col_filter:
        with st.expander("Agencies & Routes", expanded=True):

            agencies = fetch_agencies()
            routes_df = fetch_routes()

            selected_routes = []
            selected_agencies = []

            with st.container(height=650):

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

                    # ================= STOPS HEATMAP =================
                    stops_heat = [
                        [r["stop_lat"], r["stop_lon"]]
                        for _, r in stops_df.iterrows()
                    ]

                    stops_heat_layer = folium.FeatureGroup(
                        name="Stops Heatmap",
                        show=True
                    )

                    if len(stops_heat) > 0:
                        HeatMap(
                            stops_heat,
                            radius=8
                        ).add_to(stops_heat_layer)

                    stops_heat_layer.add_to(m1)

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
                    height=650
                )
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
                height=270,
                margin=dict(l=5, r=5, t=20, b=5)
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
                yaxis_title="Stops_Count",
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

            m_preview = folium.Map(location=[27.7, 85.3],zoom_start=12,tiles="CartoDB positron")
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
    
# =========================================================
# RIGHT COLUMN -> CONGESTION
# =========================================================
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

        fig.update_layout(height=300)
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

        fig1.update_traces(texttemplate='%{text:.1f}', textposition='outside')

        fig1.update_layout(height=300)

        st.plotly_chart(fig1, use_container_width=True) 