import folium

def create_osm_map(gdf_routes, gdf_stops=None, gdf_hubs=None):

    m = folium.Map(location=[27.7, 85.3], zoom_start=12, tiles="OpenStreetMap")

    # ---------------- ROUTES ----------------
    for _, row in gdf_routes.iterrows():
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in row["path"]],
            color="green" if row["direction"] == 0 else "red",
            weight=3,
            opacity=0.8
        ).add_to(m)

    # ---------------- STOPS ----------------
    if gdf_stops is not None:
        for _, row in gdf_stops.iterrows():
            folium.CircleMarker(
                location=[row["stop_lat"], row["stop_lon"]],
                radius=2,
                color="blue",
                fill=True,
                fill_opacity=0.6
            ).add_to(m)

    # ---------------- HUBS ----------------
    if gdf_hubs is not None:
        for _, row in gdf_hubs.iterrows():
            folium.Marker(
                location=[row["osm_latitude"], row["osm_longitude"]],
                popup=row.get("hub_name", "Hub"),
                icon=folium.Icon(color="orange", icon="star")
            ).add_to(m)

    folium.LayerControl().add_to(m)

    return m