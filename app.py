import streamlit as st 
from streamlit_folium import st_folium
from streamlit_plotly_events import plotly_events
import folium
from folium.plugins import HeatMap,AntPath
import pandas as pd
import sqlalchemy
import plotly.express as px

# ================= STYLE FIX =================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}
.leaflet-control-layers {
    font-family: 'Inter', sans-serif !important;
}
.block-container {
    padding-top: 1rem;
}
            /* Plotly */
.js-plotly-plot, .plotly, .plot-container {
    font-family: 'Inter', sans-serif !important;
}

/* Leaflet */
.leaflet-container,
.leaflet-popup-content,
.leaflet-control {
    font-family: 'Inter', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.leaflet-control-layers {
    z-index: 9999 !important;
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
        SELECT DISTINCT stop_lat, stop_lon
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

# ================= ROUTE DURATION =================
@st.cache_data
def route_durations():
    return pd.read_sql("""
        SELECT 
            t.route_id,
            (
                EXTRACT(EPOCH FROM MAX(st.arrival_time)::time) -
                EXTRACT(EPOCH FROM MIN(st.departure_time)::time)
            ) / 60 AS duration
        FROM trips t
        JOIN stop_times st ON t.trip_id = st.trip_id
        GROUP BY t.route_id
        HAVING 
            MIN(st.departure_time) IS NOT NULL 
            AND MAX(st.arrival_time) IS NOT NULL
    """, get_engine())

# ================= APP =================
st.set_page_config(layout="wide")
st.title("🚌 Kathmandu Valley Mobility Insights Dashboard")

# ================= LOAD DATA =================
df_cong = fetch_congestion()
df_dur = route_durations()
df_agency = routes_per_agency()
df_start = fetch_starting_stops() 
kpi = fetch_kpi()

# ---------- KPI ----------

c1, c2, c3, c4, c5,c6 = st.columns(6)

c1.metric("Agency", kpi["agency"])
c2.metric("Routes", kpi["routes"])
c3.metric("Stops", kpi["stops"])
c4.metric("Trips", kpi["trips"])
c5.metric("Peak Congestion", round(df_cong["congestion_index"].max(), 1))
c6.metric("📊 Market Leader", df_agency.iloc[0]["agency_name"], f"{df_agency.iloc[0]['percentage']}%")

# ================= DATA =================
df_dur = route_durations()

# ================= LONGEST vs SHORTEST =================
st.markdown("## ⚖️ Longest vs Shortest Route")

longest = df_dur.loc[df_dur["duration"].idxmax()]
shortest = df_dur.loc[df_dur["duration"].idxmin()]

colA, colB = st.columns(2)
colA.metric("🚀 Longest Route", longest["route_id"], f"{longest['duration']:.1f} min")
colB.metric("⚡ Shortest Route", shortest["route_id"], f"{shortest['duration']:.1f} min")

# ================= CONGESTION VISUALS =================

st.markdown("## 🚦 Congestion Intelligence Dashboard")


col1, col2 = st.columns(2)
# -------- TREND --------
with col1:
    st.markdown("### 📈 Congestion Trend")

    fig = px.line(df_cong, x="hour", y="congestion_index", markers=True)

    fig.add_scatter(
        x=df_cong["hour"],
        y=df_cong["avg_speed"],
        mode="lines+markers",
        name="Avg Speed"
    )
    fig.update_layout(font=dict(family="Inter", size=14))

    st.plotly_chart(fig, use_container_width=True)
# -------- 1. TIME BLOCK BAR --------

with col2:
    st.markdown("### 📊 Congestion by Time Block")

    block = df_cong.groupby("time_block", as_index=False)["congestion_index"].mean()

    fig1 = px.bar(
        block,
        x="time_block",
        y="congestion_index",
        color="congestion_index",
        text="congestion_index"
    )

    fig1.update_layout(font=dict(family="Inter", size=14))
    fig1.update_traces(texttemplate='%{text:.1f}', textposition='outside')

    st.plotly_chart(fig1, use_container_width=True)

st.markdown("## GTFS Analysis")
# ================= TOP 5 =================
top5 = df_dur.sort_values("duration", ascending=False).head(5)

if "selected_route_id" not in st.session_state:
    st.session_state.selected_route_id = top5.iloc[0]["route_id"]

st.markdown("<br>", unsafe_allow_html=True)

# ================= 4 COLUMNS =================
col1, col2, col3, col4 = st.columns([1.2, 0.8, 1.2, 1.2])

# ================= COL 1: PIE =================
with col1:
    st.markdown("### 🏆 Top 5 Longest Routes")

    fig_pie = px.pie(
        top5,
        names="route_id",
        values="duration",
        color_discrete_sequence=px.colors.sequential.Turbo,
        hole=0
    )

    fig_pie.update_layout(height=400, margin=dict(t=30, b=10, l=20, r=20))

    fig_pie.update_traces(
        textinfo='percent+label',
        pull=[0.2 if r == st.session_state.selected_route_id else 0 for r in top5["route_id"]]
    )
    
    fig_pie.update_layout(font=dict(family="Inter", size=14))

    selected_points = plotly_events(fig_pie, click_event=True, key="pie_click")

    if selected_points:
        idx = selected_points[0]["pointNumber"]
        st.session_state.selected_route_id = top5.iloc[idx]["route_id"]

# ================= COL 2: ROUTE DETAILS =================
with col2:
    st.markdown("### 🚏 Route Details")

    selected_route_id = st.session_state.selected_route_id
    sel = df_dur[df_dur["route_id"] == selected_route_id].iloc[0]

    st.markdown(f"""
    **Route ID:** {sel['route_id']}  
    **Duration:** {sel['duration']:.1f} min
    """)

    m_preview = folium.Map(location=[27.7, 85.3], zoom_start=12)

    geom = route_geom(selected_route_id)
    for _, row in geom.iterrows():
        if row["path"]:
            folium.PolyLine(
                locations=[(lat, lon) for lon, lat in row["path"]],
                color="blue",
                weight=4
            ).add_to(m_preview)

    stops_df = stops(selected_route_id)
    for _, r in stops_df.iterrows():
        folium.CircleMarker(
            [r["stop_lat"], r["stop_lon"]],
            radius=3,
            color="red",
            fill=True
        ).add_to(m_preview)

    st_folium(m_preview, width=350, height=340)

# ================= COL 3: AGENCY BAR =================
with col3:
    st.markdown("### 📊 Routes by Agency")

    df_agency = routes_per_agency()

    fig_small = px.bar(
        df_agency,
        x="route_count",
        y="agency_name",
        orientation="h",
        color="route_count",
        color_continuous_scale="turbo"
    )
    
    fig_small.update_layout(font=dict(family="Inter", size=14))

    fig_small.update_layout(height=400, margin=dict(l=5, r=5, t=20, b=5))
    st.plotly_chart(fig_small, use_container_width=True)

# ================= COL 4: STARTING STOPS =================
with col4:
    st.markdown("### 🚌 Major Starting Stops of Routes")

    top_start = df_start.copy()

    # keep only top 5 by frequency
    top_start = top_start.sort_values("trips_starting_at_stop", ascending=False).head(5)

    fig_start = px.line(
        top_start,
        x="stop_name",
        y="trips_starting_at_stop",
        markers=True,
        text="trips_starting_at_stop"
    )

    fig_start.update_traces(
        line=dict(color="#e9f420", width=6),
        marker=dict(size=10),
        textposition="top center"
    )

    fig_start.update_layout(
        height=400,
        xaxis_title="Starting Stops",
        yaxis_title="Count",
        xaxis_tickangle=-45
    )

    fig_start.update_layout(font=dict(family="Inter", size=14))
    st.plotly_chart(fig_start, use_container_width=True)

# ================= FILTER =================
st.markdown("## 🧭 Dashboard Control Panel")
col_filter, col_map1 = st.columns([1,3])

with col_filter:
    st.markdown("### 🏢 Agencies & Routes")

    agencies = fetch_agencies()
    routes_df = fetch_routes()

    selected_routes = []
    selected_agencies = []

    # Use a container to keep the list scrollable if it gets too long
    with st.container(height=800): 
        for _, agency_row in agencies.iterrows():
            agency_id = agency_row["agency_id"]
            agency_name = agency_row["agency_name"]

            # Using an expander to group routes cleanly without extra white space
            with st.expander(f"🏢 {agency_name}", expanded=False):
                agency_routes = routes_df[routes_df["agency_id"] == agency_id]

                for _, route_row in agency_routes.iterrows():
                    # Individual checkbox for each route
                    route_checked = st.checkbox(
                        f"🛣️ {route_row['route_short_name']}",
                        key=f"route_{route_row['route_id']}"
                    )

                    if route_checked:
                        selected_routes.append(route_row["route_id"])
                        if agency_id not in selected_agencies:
                            selected_agencies.append(agency_id)

# ================= ROUTE =================
if selected_routes:
    route_id = selected_routes[0]
elif selected_agencies:
    route_id = routes_df[routes_df["agency_id"] == selected_agencies[0]].iloc[0]["route_id"]
else:
    route_id = None

# ================= MAIN MAP (WITH ANIMATION) =================
with col_map1:
    st.markdown("### 🗺️ Route Map")

    if route_id:
        # IMPORTANT: no default tiles
        m1 = folium.Map(location=[27.7, 85.3], zoom_start=13, tiles=None)

        # ================= TILE LAYERS =================
        folium.TileLayer(tiles="OpenStreetMap",name="Openstreet", show=True).add_to(m1)
        folium.TileLayer( "CartoDB positron",name="Light", show=False).add_to(m1)
        folium.TileLayer("CartoDB dark_matter",name="Dark", show=False).add_to(m1)
        folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite",attr="Esri", show=False).add_to(m1)

        # ================= ROUTE LAYER =================
        geom = route_geom(route_id)
        route_layer = folium.FeatureGroup(name="Route", show=True)

        for _, row in geom.iterrows():
            if row["path"]:
                coords = [(lat, lon) for lon, lat in row["path"]]

                folium.PolyLine(
                    coords,
                    color="gray",
                    weight=2,
                    opacity=0.3
                ).add_to(route_layer)

                AntPath(
                    locations=coords,
                    color="blue",
                    weight=4,
                    delay=800
                ).add_to(route_layer)

        route_layer.add_to(m1)

        # ================= STOPS LAYER =================
        stops_df = stops(route_id)

        stops_layer = folium.FeatureGroup(name="Stops", show=True)

        for _, r in stops_df.iterrows():
            folium.CircleMarker(
                [r["stop_lat"], r["stop_lon"]],
                radius=3,
                color="red",
                fill=True
            ).add_to(stops_layer)

        stops_layer.add_to(m1)

        # ================= STOPS HEATMAP (FIXED) =================
        stops_heat = [
            [r["stop_lat"], r["stop_lon"]]
            for _, r in stops_df.iterrows()
        ]

        stops_heat_layer = folium.FeatureGroup(name="Stops Heatmap", show=True)

        if len(stops_heat) > 0:
            HeatMap(stops_heat, radius=8).add_to(stops_heat_layer)

        stops_heat_layer.add_to(m1)

        # ================= HUBS =================
        hubs_df = hubs()

        hub_heat = [
            [r["osm_latitude"], r["osm_longitude"]]
            for _, r in hubs_df.iterrows()
        ]

        hub_layer = folium.FeatureGroup(name="Hubs", show=True)

        if hub_heat:
            HeatMap(hub_heat, radius=15, blur=20, min_opacity=0.4,  max_zoom=10,       
).add_to(hub_layer)

        hub_layer.add_to(m1)

        # ================= LAYER CONTROL =================
        folium.LayerControl(collapsed=False).add_to(m1)

        # ================= RENDER =================
        st_folium(m1, use_container_width=True, height=800)

    else:
        st.info("👈 Select an agency and route")