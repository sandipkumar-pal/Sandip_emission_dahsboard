import json
from pathlib import Path
from typing import Tuple

import folium
from folium import plugins
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

ZONE_COLOR = {"ECA": "#E03C31", "Non-ECA": "#2980B9"}


def load_geojson(path: str) -> dict | None:
    geo_path = Path(path)
    if not geo_path.exists():
        return None
    return json.loads(geo_path.read_text())


def render_map(df: pd.DataFrame, port_center: Tuple[float, float] = (1.264, 103.822)) -> None:
    st.markdown('<div class="section-header">Spatial Operations View</div>', unsafe_allow_html=True)
    with st.spinner("Rendering maritime situational view..."):
        fmap = folium.Map(location=port_center, zoom_start=11, tiles="CartoDB dark_matter")

        geojson = load_geojson("assets/eca_boundary.geojson")
        if geojson:
            folium.GeoJson(
                geojson,
                style_function=lambda feature: {
                    "fillColor": "#E03C31",
                    "color": "#E03C31",
                    "weight": 2,
                    "fillOpacity": 0.18,
                },
                highlight_function=lambda feature: {
                    "weight": 3,
                    "color": "#FFFFFF",
                },
                name="ECA Boundary",
            ).add_to(fmap)

        heat_data = [
            [row["Lat"], row["Lon"], float(row["CO2_tons"])] for _, row in df.iterrows()
        ]
        if heat_data:
            plugins.HeatMap(heat_data, radius=18, blur=24, min_opacity=0.4).add_to(fmap)

        for _, row in df.iterrows():
            tooltip = (
                f"<strong>{row['Vessel_Name']}</strong><br>"
                f"IMO: {row['IMO_Number']}<br>"
                f"Zone: {row['Zone']}<br>CO₂: {row['CO2_tons']} t<br>"
                f"Speed: {row['Speed_knots']} kn • Dwell {row['Dwell_Time_hr']} hr<br>"
                f"Timestamp: {row['Date'].strftime('%Y-%m-%d')}"
            )
            folium.CircleMarker(
                location=(row["Lat"], row["Lon"]),
                radius=6,
                color=ZONE_COLOR.get(row["Zone"], "#FFFFFF"),
                fill=True,
                fill_color=ZONE_COLOR.get(row["Zone"], "#FFFFFF"),
                fill_opacity=0.9,
                tooltip=tooltip,
            ).add_to(fmap)

        folium.LayerControl().add_to(fmap)
        html(fmap._repr_html_(), height=520)

        st.caption("Heatmap weights scaled by CO₂ emissions. Boundary overlay approximates current ECA draft.")
