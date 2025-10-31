from __future__ import annotations

from datetime import datetime
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
    FilterSet,
    apply_filters,
    build_emission_summary,
    calculate_kpis,
    generate_vessel_dataframe,
    get_default_filters,
    quick_insight,
)

st.set_page_config(
    page_title="Port Emission Intelligence – ESG M&T",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=900)
def load_simulated_data() -> pd.DataFrame:
    return generate_vessel_dataframe()


def load_css(path: str = "assets/custom.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

authenticated, role = render_login()
if not authenticated or not role:
    st.stop()


@st.cache_data(ttl=600)
def get_data_snapshot() -> pd.DataFrame:
    return load_simulated_data()


def init_filter_state(df: pd.DataFrame) -> None:
    if "filter_start" not in st.session_state:
        defaults = get_default_filters(df)
        st.session_state["filter_start"] = defaults.start.date()
        st.session_state["filter_end"] = defaults.end.date()
        st.session_state["filter_zones"] = list(defaults.zones)
        st.session_state["filter_vessel_types"] = list(defaults.vessel_types)
        st.session_state["filter_fuel_types"] = list(defaults.fuel_types)


def build_filter_set() -> FilterSet:
    return FilterSet(
        start=pd.Timestamp(st.session_state["filter_start"]),
        end=pd.Timestamp(st.session_state["filter_end"]),
        zones=st.session_state["filter_zones"],
        vessel_types=st.session_state["filter_vessel_types"],
        fuel_types=st.session_state["filter_fuel_types"],
    )


def role_header(role_name: str) -> str:
    mapping = {
        "Admin": "Enterprise Control Tower",
        "Analyst": "Advanced Analytics Studio",
        "Ops Manager": "Operational Performance Room",
        "Regulator": "Compliance Assurance Desk",
    }
    return mapping.get(role_name, "Port Emission Intelligence")


def role_caption(role_name: str) -> str:
    hints = {
        "Admin": "Manage boundaries, guardrails, and user roles.",
        "Analyst": "Explore high-resolution emission intelligence.",
        "Ops Manager": "Track berth efficiency and tactical insights.",
        "Regulator": "Monitor compliance and trigger enforcement workflows.",
    }
    return hints.get(role_name, "Port Authority situational awareness console.")


def render_header(role_name: str) -> None:
    now = datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")
    st.markdown(
        f"""
        <div class="app-header">
            <div class="brand-cluster">
                <div class="brand-logo">S&amp;P<span>Global</span></div>
                <div>
                    <h1>Port Emission Intelligence Dashboard</h1>
                    <p class="subtitle">{role_header(role_name)}</p>
                </div>
            </div>
            <div class="status-cluster">
                <div class="status-pill">
                    <span class="label">User Role</span>
                    <span class="value">{role_name}</span>
                </div>
                <div class="status-pill">
                    <span class="label">Data Timestamp</span>
                    <span class="value">{now}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(df: pd.DataFrame, role_name: str) -> None:
    st.sidebar.markdown("### Filters")
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(st.session_state["filter_start"], st.session_state["filter_end"]),
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        st.session_state["filter_start"], st.session_state["filter_end"] = date_range

    zones = st.sidebar.multiselect(
        "Zone",
        options=sorted(df["Zone"].unique().tolist()),
        default=st.session_state["filter_zones"],
    )
    if zones:
        st.session_state["filter_zones"] = zones

    vessel_types = st.sidebar.multiselect(
        "Vessel Type",
        options=sorted(df["Vessel_Type"].unique().tolist()),
        default=st.session_state["filter_vessel_types"],
    )
    if vessel_types:
        st.session_state["filter_vessel_types"] = vessel_types

    fuel_types = st.sidebar.multiselect(
        "Fuel Type",
        options=sorted(df["Fuel_Type"].unique().tolist()),
        default=st.session_state["filter_fuel_types"],
    )
    if fuel_types:
        st.session_state["filter_fuel_types"] = fuel_types

    if st.sidebar.button("Reset Filters"):
        defaults = get_default_filters(df)
        st.session_state["filter_start"] = defaults.start.date()
        st.session_state["filter_end"] = defaults.end.date()
        st.session_state["filter_zones"] = list(defaults.zones)
        st.session_state["filter_vessel_types"] = list(defaults.vessel_types)
        st.session_state["filter_fuel_types"] = list(defaults.fuel_types)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(role_caption(role_name))
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["role"] = None
        st.rerun()


with st.spinner("Syncing telemetry..."):
    master_df = get_data_snapshot()

init_filter_state(master_df)
render_sidebar(master_df, role)
render_header(role)

filters = build_filter_set()
filtered_df = apply_filters(master_df, filters)

if filtered_df.empty:
    st.warning("No data available for the selected filters. Adjust parameters to continue.")
    st.stop()

kpis = calculate_kpis(filtered_df)
insight_text = quick_insight(filtered_df)

tab_labels = [
    "Dashboard Overview",
    "Zone Analytics",
    "Emission Map",
    "Vessel Analytics",
    "Comparative Insights",
    "Compliance & Alerts",
    "Reports",
]
if role == "Admin":
    tab_labels.append("Admin Console")

tabs = st.tabs(tab_labels)
tab_iter = iter(tabs)
overview_tab = next(tab_iter)
zone_tab = next(tab_iter)
map_tab = next(tab_iter)
vessel_tab = next(tab_iter)
comparative_tab = next(tab_iter)
compliance_tab = next(tab_iter)
reports_tab = next(tab_iter)
admin_tab = next(tab_iter, None)

with overview_tab:
    render_overview(kpis, filtered_df, insight_text)

with zone_tab:
    render_zone_analytics(filtered_df)

with map_tab:
    render_map(filtered_df)

with vessel_tab:
    render_vessel_table(filtered_df)

with comparative_tab:
    render_comparative_insights(filtered_df)

with compliance_tab:
    render_compliance_alerts(filtered_df)

with reports_tab:
    summary_payload = build_emission_summary(filtered_df)
    render_reports(summary_payload)

if admin_tab is not None:
    with admin_tab:
        render_admin_panel()
