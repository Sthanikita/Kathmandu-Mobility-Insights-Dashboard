import streamlit as st
from streamlit_folium import st_folium
from streamlit_plotly_events import plotly_events
import folium
from folium.plugins import HeatMap,AntPath
import pandas as pd
import sqlalchemy
import plotly.express as px

# ================= STYLE FIX =================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ================= DB =================
def get_engine():
    return sqlalchemy.create_engine(
        "postgresql://postgres:Shresthaniki9742@localhost:5432/GTFS_KATHMANDU"
    )

# ================= DATA =================
@st.cache_data
def fetch_kpi():
    engine = get_engine()
    return {
        "routes": pd.read_sql("SELECT COUNT(*) FROM routes", engine).iloc[0, 0],
        "trips": pd.read_sql("SELECT COUNT(*) FROM trips", engine).iloc[0, 0],
        "stops": pd.read_sql("SELECT COUNT(*) FROM stops", engine).iloc[0, 0],
        "agency": pd.read_sql("SELECT COUNT(*) FROM agency", engine).iloc[0, 0],
    }

# ================= MARKET SHARE =================
@st.cache_data
def routes_per_agency():
    engine = get_engine()
    return pd.read_sql("""
        SELECT 
            COALESCE(a.agency_name, 'Unknown') AS agency_name,
            COUNT(r.route_id) AS route_count
        FROM routes r
        LEFT JOIN agency a ON r.agency_id = a.agency_id
        GROUP BY a.agency_name
        ORDER BY route_count DESC
    """, engine)

def market_share_calc(df):
    total = df["route_count"].sum()
    df["percentage"] = (df["route_count"] / total) * 100
    top = df.iloc[0]
    return top["agency_name"], top["percentage"]

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
    engine = get_engine()

    df = pd.read_sql("""
        SELECT 
            t.route_id,
            MIN(st.departure_time) AS start_time,
            MAX(st.arrival_time) AS end_time
        FROM trips t
        JOIN stop_times st ON t.trip_id = st.trip_id
        GROUP BY t.route_id
    """, engine)

    def to_minutes(t):
        try:
            h, m, s = map(int, str(t).split(":"))
            return h * 60 + m + s / 60
        except:
            return None

    df["start_min"] = df["start_time"].apply(to_minutes)
    df["end_min"] = df["end_time"].apply(to_minutes)
    df["duration"] = df["end_min"] - df["start_min"]

    return df.dropna(subset=["duration"])

# ================= APP =================
st.set_page_config(layout="wide")
st.title("🚌 Advanced GTFS Dashboard (Kathmandu)")

# ---------- KPI ----------
kpi = fetch_kpi()
df_agency = routes_per_agency()
top_agency, top_percent = market_share_calc(df_agency)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Agency", kpi["agency"])
c2.metric("Routes", kpi["routes"])
c3.metric("Stops", kpi["stops"])
c4.metric("Trips", kpi["trips"])
c5.metric("📊 Market Leader", top_agency, f"{top_percent:.1f}% share")

# ================= DATA =================
df_dur = route_durations()

# ================= LONGEST vs SHORTEST =================
st.markdown("### ⚖️ Longest vs Shortest Route")

longest = df_dur.loc[df_dur["duration"].idxmax()]
shortest = df_dur.loc[df_dur["duration"].idxmin()]

colA, colB = st.columns(2)
colA.metric("🚀 Longest Route", longest["route_id"], f"{longest['duration']:.1f} min")
colB.metric("⚡ Shortest Route", shortest["route_id"], f"{shortest['duration']:.1f} min")

# ================= TOP 5 =================
top5 = df_dur.sort_values("duration", ascending=False).head(5)

if "selected_route_id" not in st.session_state:
    st.session_state.selected_route_id = top5.iloc[0]["route_id"]

st.markdown("<br>", unsafe_allow_html=True)

# ================= PIE + DETAILS =================
col1, col2 = st.columns([0.8, 1.2])

with col1:
    st.markdown("### 🏆 Top 5 Longest Routes")

    fig_pie = px.pie(
        top5,
        names="route_id",
        values="duration",
        color_discrete_sequence=px.colors.sequential.Turbo,
        hole=0
    )

    fig_pie.update_layout(height=350, margin=dict(t=30, b=10, l=10, r=10))

    fig_pie.update_traces(
        textinfo='percent+label',
        pull=[0.2 if r == st.session_state.selected_route_id else 0 for r in top5["route_id"]]
    )

    selected_points = plotly_events(fig_pie, click_event=True, key="pie_click")

    if selected_points:
        idx = selected_points[0]["pointNumber"]
        st.session_state.selected_route_id = top5.iloc[idx]["route_id"]

with col2:
    st.markdown("### 🚏 Route Details")

    selected_route_id = st.session_state.selected_route_id
    sel = df_dur[df_dur["route_id"] == selected_route_id].iloc[0]

    left, right = st.columns([1, 1.4])

    with left:
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

        st_folium(m_preview, width=350, height=290)

    with right:
        st.markdown("#### 📊 Routes by Agency")

        df_agency = routes_per_agency()

        fig_small = px.bar(
            df_agency,
            x="route_count",
            y="agency_name",
            orientation="h",
            color="route_count",
            color_continuous_scale="turbo"
        )

        fig_small.update_layout(height=300, margin=dict(l=5, r=5, t=20, b=5))
        st.plotly_chart(fig_small, use_container_width=True)

# ================= FILTER =================
# ================= FILTER =================
st.markdown("## 🧭 Dashboard Control Panel")
col_filter, col_map1, col_map2 = st.columns([1, 1.5, 1])

with col_filter:
    st.markdown("### 🏢 Agencies & Routes")

    agencies = fetch_agencies()
    routes_df = fetch_routes()

    selected_routes = []
    selected_agencies = []

    # Use a container to keep the list scrollable if it gets too long
    with st.container(height=600): 
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
        m1 = folium.Map(location=[27.7, 85.3], zoom_start=12)

        geom = route_geom(route_id)

        for _, row in geom.iterrows():
            if row["path"]:
                coords = [(lat, lon) for lon, lat in row["path"]]

                # faint base line
                folium.PolyLine(
                    coords,
                    color="gray",
                    weight=2,
                    opacity=0.3
                ).add_to(m1)

                # 🔥 ANIMATED FLOW
                AntPath(
                    locations=coords,
                    color="blue",
                    weight=4,
                    delay=800
                ).add_to(m1)

        stops_df = stops(route_id)

        for _, r in stops_df.iterrows():
            folium.CircleMarker(
                [r["stop_lat"], r["stop_lon"]],
                radius=3,
                color="red",
                fill=True
            ).add_to(m1)

        heat = [[r["stop_lat"], r["stop_lon"]] for _, r in stops_df.iterrows()]
        if heat:
            HeatMap(heat, radius=8).add_to(m1)

        st_folium(m1, width=800, height=650)

    else:
        st.info("👈 Select an agency and route")
# ================= HUB MAP =================
with col_map2:
    st.markdown("### 🔥 Hub Heatmap")

    m2 = folium.Map(location=[27.7,85.3], zoom_start=12)
    hubs_df = hubs()

    heat = [[r["osm_latitude"], r["osm_longitude"]] for _, r in hubs_df.iterrows()]

    if heat:
        HeatMap(heat).add_to(m2)

    # Increased width from 500 to 700 to match your map size
    st_folium(m2, width=700, height=500)
