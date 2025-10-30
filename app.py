from pathlib import Path

import pandas as pd
import streamlit as st

from components.admin import render_admin_panel
from components.comparative_insights import render_comparative_insights
from components.compliance_alerts import render_compliance_alerts
from components.dashboard_overview import render_overview
from components.login import render_login
from components.map_view import render_map
from components.reports import render_reports
from components.vessel_analytics import render_vessel_table
from components.zone_analytics import render_zone_analytics
from data_simulation import (
    build_emission_summary,
    calculate_kpis,
    fuel_mix,
    generate_time_series,
    generate_vessel_dataframe,
    role_header,
)

st.set_page_config(
    page_title="Port Emission Intelligence – ESG M&T",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=900)
def load_simulated_data() -> dict[str, pd.DataFrame]:
    df = generate_vessel_dataframe()
    zone_summary = df.groupby("Zone")["CO2_tons"].sum().reset_index()
    time_series = generate_time_series(df)
    fuel_summary = fuel_mix(df)
    return {
        "vessels": df,
        "zone_summary": zone_summary,
        "time_series": time_series,
        "fuel_summary": fuel_summary,
    }


def load_css(path: str = "assets/custom.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

logo_path = Path("assets/port_logo.png")
logo_for_login = str(logo_path) if logo_path.exists() else None

authenticated, role = render_login(logo_for_login)

if not authenticated or not role:
    st.stop()

if logo_path.exists():
    st.sidebar.image(str(logo_path), width=100)
else:
    st.sidebar.markdown(
        "<p style='color:#E03C31;font-weight:600;'>Port Emission Intelligence</p>",
        unsafe_allow_html=True,
    )

st.sidebar.title("Navigation")
role_badge = f"<span class='badge'>{role}</span>"
st.sidebar.markdown(f"**Role:** {role_badge}", unsafe_allow_html=True)

nav_items = [
    "Overview",
    "Zone Analytics",
    "Map View",
    "Vessel Analytics",
    "Comparative Insights",
    "Compliance & Alerts",
    "Reports",
]
if role == "Admin":
    nav_items.append("Admin")

selection = st.sidebar.radio("", nav_items)
if st.sidebar.button("Log out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["role"] = None
    st.rerun()

st.title(role_header(role))

payload = load_simulated_data()
df = payload["vessels"]

if selection == "Overview":
    kpis = calculate_kpis(df)
    render_overview(kpis)
elif selection == "Zone Analytics":
    render_zone_analytics(payload["zone_summary"], payload["time_series"], payload["fuel_summary"], df)
elif selection == "Map View":
    render_map(df)
elif selection == "Vessel Analytics":
    render_vessel_table(df)
elif selection == "Comparative Insights":
    render_comparative_insights(df)
elif selection == "Compliance & Alerts":
    render_compliance_alerts(df)
elif selection == "Reports":
    summary = build_emission_summary(df)
    render_reports(summary)
elif selection == "Admin":
    render_admin_panel()

st.sidebar.markdown("---")
st.sidebar.caption("Data refreshed every 15 minutes with simulated telemetry signals.")
