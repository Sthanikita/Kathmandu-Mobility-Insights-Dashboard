import streamlit as st 
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, AntPath 
import pandas as pd
import sqlalchemy
import plotly.express as px
import plotly.io as pio

# ================= CONFIG =================
st.set_page_config(layout="wide")
pio.templates.default = "plotly_dark"

# ================= CSS =================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #000000 !important;
    color: white !important;
}

.stApp {
    background-color: #000000 !important;
}

/* ================= HERO ================= */
.hero {
    position: relative;
    padding: 60px 50px;
    border-radius: 24px;
    background: linear-gradient(135deg, #0b1220, #111827, #1e293b);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 20px;
}

.hero-title {
    font-size: 52px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
}

.hero-title span {
    color: #60a5fa;
}

.hero-sub {
    margin-top: 12px;
    font-size: 16px;
    color: #9ca3af;
    max-width: 700px;
}

.hero-chip {
    display: inline-block;
    margin-top: 16px;
    margin-right: 10px;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: white;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ================= DB =================
def get_engine():
    return sqlalchemy.create_engine(st.secrets["DB_URL"])

# ================= DATA =================
@st.cache_data
def fetch_kpi():
    return pd.read_sql("""
        SELECT 
            (SELECT COUNT(*) FROM routes) AS routes,
            (SELECT COUNT(*) FROM trips) AS trips,
            (SELECT COUNT(*) FROM stops) AS stops,
            (SELECT COUNT(*) FROM agency) AS agency
    """, get_engine()).iloc[0].to_dict()

@st.cache_data
def fetch_agencies():
    return pd.read_sql("SELECT agency_id, agency_name FROM agency", get_engine())

@st.cache_data
def fetch_routes():
    return pd.read_sql("SELECT route_id, route_short_name, agency_id FROM routes", get_engine())

@st.cache_data
def route_geom(route_id):
    return pd.read_sql(f"""
        SELECT ARRAY_AGG(ARRAY[shape_pt_lon, shape_pt_lat]) AS path
        FROM shapes
        WHERE shape_id IN (
            SELECT DISTINCT shape_id FROM trips WHERE route_id = '{route_id}'
        )
    """, get_engine())

# ================= HERO =================
st.markdown("""
<div class="hero">
    <div class="hero-title">
        Kathmandu Valley <span>Mobility Insights</span>
    </div>

    <div class="hero-sub">
        Real-time GTFS transit intelligence platform for route analysis and visualization.
    </div>

    <div>
        <span class="hero-chip">🚌 GTFS Data</span>
        <span class="hero-chip">📍 Kathmandu</span>
        <span class="hero-chip">⚡ Live Dashboard</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
kpi = fetch_kpi()
agencies = fetch_agencies()
routes_df = fetch_routes()

# ================= KPI =================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Agencies", kpi["agency"])
c2.metric("Routes", kpi["routes"])
c3.metric("Trips", kpi["trips"])
c4.metric("Stops", kpi["stops"])

# ================= FILTER =================
col1, col2 = st.columns([1.5, 3])

selected_routes = []

with col1:
    st.subheader("Routes")

    for _, a in agencies.iterrows():
        with st.expander(a["agency_name"]):
            for _, r in routes_df[routes_df["agency_id"] == a["agency_id"]].iterrows():
                if st.checkbox(r["route_short_name"], key=r["route_id"]):
                    selected_routes.append(r["route_id"])

# ================= MAP =================
with col2:
    st.subheader("Map")

    if selected_routes:
        m = folium.Map(location=[27.7, 85.3], zoom_start=12)

        for route_id in selected_routes:
            geom = route_geom(route_id)

            for _, row in geom.iterrows():
                if row["path"]:
                    coords = [(lat, lon) for lon, lat in row["path"]]
                    folium.PolyLine(coords, color="blue", weight=3).add_to(m)

        st_folium(m, use_container_width=True, height=600)

    else:
        st.info("Select routes to display map")

# ================= SIMPLE CHART =================
st.subheader("Quick Overview")

df = pd.DataFrame({
    "Category": ["Routes", "Trips", "Stops"],
    "Value": [kpi["routes"], kpi["trips"], kpi["stops"]]
})

fig = px.bar(df, x="Category", y="Value", color="Category")
st.plotly_chart(fig, use_container_width=True)