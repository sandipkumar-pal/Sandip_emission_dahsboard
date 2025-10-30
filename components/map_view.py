import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html


ZONE_COLOR = {"ECA": "#E03C31", "Non-ECA": "#2980B9"}


def load_geojson(path: str) -> dict | None:
    geo_path = Path(path)
    if not geo_path.exists():
        return None
    return json.loads(geo_path.read_text())


def render_map(df: pd.DataFrame, port_center: tuple[float, float] = (1.264, 103.822)) -> None:
    st.markdown('<div class="section-header">Spatial Operations View</div>', unsafe_allow_html=True)
    fmap = folium.Map(location=port_center, zoom_start=11, tiles="CartoDB dark_matter")

    geojson = load_geojson("assets/eca_boundary.geojson")
    if geojson:
        folium.GeoJson(
            geojson,
            style_function=lambda feature: {
                "fillColor": "#E03C3133",
                "color": "#E03C31",
                "weight": 2,
                "fillOpacity": 0.2,
            },
            name="ECA Boundary",
        ).add_to(fmap)

    for _, row in df.iterrows():
        tooltip = (
            f"IMO: {row['IMO_Number']}<br>"
            f"Zone: {row['Zone']}<br>CO₂: {row['CO2_tons']} t<br>"
            f"Timestamp: {row['Date'].strftime('%Y-%m-%d %H:%M')}"
        )
        folium.CircleMarker(
            location=(row["Lat"], row["Lon"]),
            radius=6,
            color=ZONE_COLOR.get(row["Zone"], "#FFFFFF"),
            fill=True,
            fill_color=ZONE_COLOR.get(row["Zone"], "#FFFFFF"),
            fill_opacity=0.85,
            tooltip=tooltip,
        ).add_to(fmap)

    html(fmap._repr_html_(), height=480)
