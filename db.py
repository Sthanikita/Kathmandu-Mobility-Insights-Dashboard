import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
import sqlalchemy

# ---------------- DB CONNECTION ----------------
def get_engine():
    return sqlalchemy.create_engine(
        "postgresql://postgres:Shresthaniki9742@localhost:5432/GTFS_KATHMANDU"
    )

# ---------------- ROUTES ----------------
def fetch_routes():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM routes", engine)

# ---------------- TRIPS ----------------
def fetch_trips():
    engine = get_engine()
    return pd.read_sql(
        "SELECT trip_id, route_id, shape_id, direction_id FROM trips",
        engine
    )

# ---------------- SHAPES ----------------
def load_shapes():
    engine = get_engine()

    query = """
    SELECT shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence
    FROM shapes
    ORDER BY shape_id, shape_pt_sequence
    """

    df = pd.read_sql(query, engine)
    df["shape_pt_sequence"] = pd.to_numeric(df["shape_pt_sequence"], errors="coerce")

    return df

# ---------------- ROUTE GEOMETRY ----------------
def fetch_route_geometry(route_id=None):
    shapes_df = load_shapes()
    trips_df = fetch_trips()

    if route_id is not None:
        trips_df = trips_df[trips_df["route_id"] == route_id]

    lines = []

    if "direction_id" not in trips_df.columns:
        trips_df["direction_id"] = 0

    for direction_id, trip_group in trips_df.groupby("direction_id"):

        shape_ids = trip_group["shape_id"].dropna().unique()
        df = shapes_df[shapes_df["shape_id"].isin(shape_ids)]

        for shape_id, group in df.groupby("shape_id"):
            group = group.sort_values("shape_pt_sequence")

            coords = list(zip(group["shape_pt_lon"], group["shape_pt_lat"]))
            coords = [c for c in coords if pd.notnull(c[0]) and pd.notnull(c[1])]

            if len(coords) > 1:

                if coords[0] > coords[-1]:
                    coords = coords[::-1]

                lines.append({
                    "shape_id": shape_id,
                    "direction": direction_id,
                    "geometry": LineString(coords)
                })

    gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs="EPSG:4326")
    gdf["path"] = gdf["geometry"].apply(lambda g: list(g.coords))

    return gdf

# ---------------- STOPS ----------------
def fetch_stops():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM stops", engine)

# ---------------- STOPS FILTERED BY ROUTE ----------------
def fetch_stops_from_stoptimes(route_id=None):
    engine = get_engine()

    if route_id is None:
        df = pd.read_sql("SELECT DISTINCT stop_id FROM stop_times", engine)
    else:
        query = """
        SELECT DISTINCT st.stop_id
        FROM stop_times st
        JOIN trips t ON st.trip_id = t.trip_id
        WHERE t.route_id = %s
        """
        df = pd.read_sql(query, engine, params=(route_id,))

    stops = fetch_stops()
    return stops[stops["stop_id"].isin(df["stop_id"])]

# ---------------- STOP GEOMETRY ----------------
def get_stop_geometries(route_id=None):
    stops_df = fetch_stops_from_stoptimes(route_id)

    return gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df["stop_lon"], stops_df["stop_lat"]),
        crs="EPSG:4326"
    )

# ---------------- HUBS (INDEPENDENT TABLE) ----------------
def fetch_hubs():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM hub", engine)

def get_hub_geometries():
    hub_df = fetch_hubs()

    return gpd.GeoDataFrame(
        hub_df,
        geometry=gpd.points_from_xy(hub_df["osm_longitude"], hub_df["osm_latitude"]),
        crs="EPSG:4326"
    )

# ---------------- KPI ----------------
def fetch_kpi_stats():
    engine = get_engine()

    return {
        "routes": len(fetch_routes()),
        "trips": len(fetch_trips()),
        "stops": len(fetch_stops()),
        "hubs": len(fetch_hubs()),
        "stop_times": pd.read_sql("SELECT COUNT(*) FROM stop_times", engine).iloc[0, 0]
    }