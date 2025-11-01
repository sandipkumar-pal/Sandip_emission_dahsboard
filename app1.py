# -------------------------------------------------------------
#  Port Emission Intelligence Dashboard (Enterprise Edition)
#  Author: S&P Global Maritime Analytics / ESG M&T
# -------------------------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from faker import Faker
from datetime import datetime, timedelta
import random

# -------------------------------------------------------------
#  PAGE CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="Port Emission Intelligence – ESG M&T",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
#  APPLY ENTERPRISE DARK THEME
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    body, .stApp {background-color:#121212;color:#E0E0E0;font-family:'Inter',sans-serif;}
    .sidebar .sidebar-content {background-color:#1E1E1E;}
    .stButton>button {background-color:#E03C31;color:#fff;border-radius:8px;border:none;transition:0.3s;}
    .stButton>button:hover {background-color:#B53028;transform:scale(1.03);}
    div[data-testid="stMetricValue"] {color:#E03C31!important;font-weight:bold;}
    .stTabs [data-baseweb="tab"] {color:#E0E0E0;background-color:#1E1E1E;}
    h1,h2,h3,h4 {color:#E0E0E0;font-weight:600;}
    .card {background-color:#1E1E1E;border-left:4px solid #E03C31;padding:1rem;border-radius:10px;margin-bottom:1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
#  SIMULATED DATA GENERATION
# -------------------------------------------------------------
def generate_mock_data(n=300):
    fake = Faker()
    zones = ["ECA", "Non-ECA"]
    fuels = ["HFO", "MGO", "LNG", "Hybrid"]
    vessel_types = ["Bulk Carrier", "Container", "Tanker", "Passenger", "RoRo"]

    data = []
    for _ in range(n):
        zone = random.choice(zones)
        co2 = round(np.random.uniform(5, 20), 2)
        sox = round(np.random.uniform(0.1, 2.0), 2)
        nox = round(np.random.uniform(0.5, 3.0), 2)
        dwell = random.randint(12, 96)
        speed = round(np.random.uniform(8, 18), 2)
        compliance = np.random.choice([True, False], p=[0.85, 0.15])
        data.append(
            {
                "IMO_Number": random.randint(9300000, 9900000),
                "Vessel_Name": f"MV_{fake.word().capitalize()}_{random.randint(1,999)}",
                "Zone": zone,
                "Fuel_Type": random.choice(fuels),
                "Vessel_Type": random.choice(vessel_types),
                "CO2_tons": co2,
                "SOx_tons": sox,
                "NOx_tons": nox,
                "Speed_knots": speed,
                "Dwell_Time_hr": dwell,
                "Compliance_Flag": compliance,
                "Date": fake.date_between(start_date="-30d", end_date="today"),
                "Lat": np.random.uniform(1.20, 1.32),
                "Lon": np.random.uniform(103.6, 104.0),
            }
        )
    return pd.DataFrame(data)


df = generate_mock_data()

# -------------------------------------------------------------
#  SIDEBAR FILTERS
# -------------------------------------------------------------
st.sidebar.image("assets/port_logo.png", width=180)
st.sidebar.markdown("### 🔍 Filters")

zone_filter = st.sidebar.multiselect("Zone", options=df["Zone"].unique(), default=["ECA", "Non-ECA"])
fuel_filter = st.sidebar.multiselect("Fuel Type", options=df["Fuel_Type"].unique(), default=df["Fuel_Type"].unique())
vtype_filter = st.sidebar.multiselect("Vessel Type", options=df["Vessel_Type"].unique(), default=df["Vessel_Type"].unique())
date_range = st.sidebar.date_input(
    "Date Range",
    [df["Date"].min(), df["Date"].max()],
)

filtered = df[
    (df["Zone"].isin(zone_filter))
    & (df["Fuel_Type"].isin(fuel_filter))
    & (df["Vessel_Type"].isin(vtype_filter))
    & (df["Date"].between(date_range[0], date_range[-1]))
]

# -------------------------------------------------------------
#  MAIN HEADER
# -------------------------------------------------------------
st.title("🌊 Port Emission Intelligence Dashboard")
st.markdown("#### Enterprise-grade emission analytics for ECA & Non-ECA zones")

# -------------------------------------------------------------
#  KPI METRICS
# -------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)
total_co2 = filtered["CO2_tons"].sum()
avg_co2 = filtered["CO2_tons"].mean()
eca_share = (
    filtered[filtered["Zone"] == "ECA"]["CO2_tons"].sum() / total_co2 * 100
    if total_co2 > 0
    else 0
)
compliance_rate = filtered["Compliance_Flag"].mean() * 100
alerts = len(filtered[~filtered["Compliance_Flag"]])

col1.metric("Total CO₂ (t)", f"{total_co2:,.2f}")
col2.metric("Avg CO₂/Vessel (t)", f"{avg_co2:,.2f}")
col3.metric("% ECA Emission Share", f"{eca_share:.1f}%")
col4.metric("Compliance Rate", f"{compliance_rate:.1f}%")
col5.metric("Active Alerts", f"{alerts}")

# -------------------------------------------------------------
#  TABS
# -------------------------------------------------------------
tabs = st.tabs(
    ["📊 Overview", "🌍 Emission Map", "🚢 Vessel Analytics", "📈 Comparative Insights", "⚠ Compliance & Alerts"]
)

# -------------------------------------------------------------
#  TAB 1 – OVERVIEW
# -------------------------------------------------------------
with tabs[0]:
    st.subheader("Emission Trends by Zone")
    trend = filtered.groupby(["Date", "Zone"])["CO2_tons"].sum().reset_index()
    fig_trend = px.area(
        trend,
        x="Date",
        y="CO2_tons",
        color="Zone",
        color_discrete_map={"ECA": "#E03C31", "Non-ECA": "#2980B9"},
        template="plotly_dark",
        title="Daily Emissions (ECA vs Non-ECA)",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("Fuel Type Composition")
    fuel_comp = filtered.groupby(["Fuel_Type", "Zone"])["CO2_tons"].sum().reset_index()
    fig_pie = px.pie(
        fuel_comp,
        names="Fuel_Type",
        values="CO2_tons",
        color="Zone",
        hole=0.4,
        color_discrete_map={"ECA": "#E03C31", "Non-ECA": "#2980B9"},
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# -------------------------------------------------------------
#  TAB 2 – MAP
# -------------------------------------------------------------
with tabs[1]:
    st.subheader("Emission Hotspot Map")
    port_map = folium.Map(location=[1.27, 103.8], zoom_start=11, tiles="cartodb dark_matter")
    for _, row in filtered.iterrows():
        color = "#E03C31" if row["Zone"] == "ECA" else "#2980B9"
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=5,
            popup=(
                f"Vessel: {row['Vessel_Name']}<br>"
                f"Zone: {row['Zone']}<br>"
                f"CO₂: {row['CO2_tons']} t<br>"
                f"Speed: {row['Speed_knots']} kn"
            ),
            color=color,
            fill=True,
            fill_opacity=0.8,
        ).add_to(port_map)
    st_folium(port_map, width=1400, height=700)

# -------------------------------------------------------------
#  TAB 3 – VESSEL ANALYTICS
# -------------------------------------------------------------
with tabs[2]:
    st.subheader("Vessel-level Emission Data")
    st.dataframe(filtered, use_container_width=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "emission_data.csv", "text/csv")

# -------------------------------------------------------------
#  TAB 4 – COMPARATIVE INSIGHTS
# -------------------------------------------------------------
with tabs[3]:
    st.subheader("Speed vs CO₂ Correlation")
    fig_corr = px.scatter(
        filtered,
        x="Speed_knots",
        y="CO2_tons",
        color="Zone",
        size="Dwell_Time_hr",
        hover_data=["Vessel_Name", "Fuel_Type"],
        color_discrete_map={"ECA": "#E03C31", "Non-ECA": "#2980B9"},
        template="plotly_dark",
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# -------------------------------------------------------------
#  TAB 5 – COMPLIANCE & ALERTS
# -------------------------------------------------------------
with tabs[4]:
    st.subheader("Non-Compliant Vessels")
    non_compliant = filtered[~filtered["Compliance_Flag"]]
    st.dataframe(non_compliant, use_container_width=True)

    st.markdown(
        f"**⚠ {len(non_compliant)} vessels exceeded emission thresholds.**"
        if len(non_compliant) > 0
        else "✅ All vessels within compliance limits."
    )

# -------------------------------------------------------------
#  FOOTER
# -------------------------------------------------------------
st.markdown("---")
st.caption("© 2025 S&P Global Maritime Analytics | Port Emission Intelligence (Enterprise Edition)")
