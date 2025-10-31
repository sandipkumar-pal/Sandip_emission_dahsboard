from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Tuple

import pandas as pd
import streamlit as st

from streamlit.runtime.uploaded_file_manager import UploadedFile

import re

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
    get_default_filters,
    load_emission_dataset,
    quick_insight,
)

st.set_page_config(
    page_title="Port Emission Intelligence – ESG M&T",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=900)
def load_dataset(imo_filter: Tuple[int, ...]) -> pd.DataFrame:
    return load_emission_dataset(imo_whitelist=imo_filter)


def load_css(path: str = "assets/custom.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

authenticated, role = render_login()
if not authenticated or not role:
    st.stop()


@st.cache_data(ttl=600)
def get_data_snapshot(imo_filter: Tuple[int, ...]) -> pd.DataFrame:
    return load_dataset(imo_filter)


def init_filter_state(df: pd.DataFrame) -> None:
    if "filter_start" not in st.session_state:
        defaults = get_default_filters(df)
        st.session_state["filter_start"] = defaults.start.date()
        st.session_state["filter_end"] = defaults.end.date()
        st.session_state["filter_zones"] = list(defaults.zones)
        st.session_state["filter_vessel_types"] = list(defaults.vessel_types)
        st.session_state["filter_fuel_types"] = list(defaults.fuel_types)


def _as_utc_timestamp(value) -> pd.Timestamp:
    """Convert a date/datetime-like object to a UTC timestamp."""

    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def build_filter_set() -> FilterSet:
    return FilterSet(
        start=_as_utc_timestamp(st.session_state["filter_start"]),
        end=_as_utc_timestamp(st.session_state["filter_end"]),
        zones=st.session_state["filter_zones"],
        vessel_types=st.session_state["filter_vessel_types"],
        fuel_types=st.session_state["filter_fuel_types"],
    )


def _parse_manual_imo_input(raw: str) -> Tuple[int, ...]:
    tokens = re.split(r"[^0-9]+", raw or "")
    values = []
    for token in tokens:
        if not token:
            continue
        try:
            numeric = int(token)
        except ValueError:
            continue
        if numeric > 0:
            values.append(numeric)
    return tuple(sorted(set(values)))


def _imo_values_from_frame(frame: pd.DataFrame) -> Tuple[int, ...]:
    if frame.empty:
        return tuple()

    candidate_columns = [
        col
        for col in frame.columns
        if "imo" in col.lower() or frame[col].dtype.kind in {"i", "u"}
    ]
    if not candidate_columns:
        candidate_columns = list(frame.columns[:1])

    for column in candidate_columns:
        series = pd.to_numeric(frame[column], errors="coerce")
        imos = series.dropna().astype("int64")
        if not imos.empty:
            return tuple(sorted(set(imos.tolist())))
    return tuple()


def _parse_imo_file(uploaded: UploadedFile) -> Tuple[int, ...]:
    if uploaded is None:
        return tuple()

    name = uploaded.name.lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            frame = pd.read_excel(uploaded)
        else:
            frame = pd.read_csv(uploaded)
    except Exception as exc:
        st.sidebar.error(f"Unable to read IMO file: {exc}")
        uploaded.seek(0)
        return tuple()

    uploaded.seek(0)
    if frame.empty:
        return tuple()

    return _imo_values_from_frame(frame)


def ensure_sidebar_defaults() -> None:
    st.session_state.setdefault("imo_filter", tuple())
    st.session_state.setdefault("imo_manual_input", "")


def render_data_scope_controls() -> Tuple[Tuple[int, ...], Any]:
    ensure_sidebar_defaults()

    container = st.sidebar.container()
    with container:
        st.markdown("### Data Scope")
        st.caption(
            "Upload IMO numbers to query local parquet telemetry without loading the full dataset."
        )
        uploaded = st.file_uploader(
            "IMO list (CSV or Excel)", type=["csv", "txt", "xlsx"], accept_multiple_files=False
        )
        if uploaded is not None:
            imos = _parse_imo_file(uploaded)
            if imos:
                st.session_state["imo_filter"] = imos
                st.success(f"Loaded {len(imos)} IMO numbers from {uploaded.name}.")
            else:
                st.warning("No valid IMO numbers detected in the uploaded file.")

        manual_input = st.text_area(
            "Manual IMO list",
            value=st.session_state.get("imo_manual_input", ""),
            placeholder="9876543, 9876544, 9876545",
            help="Paste comma, space, or line-separated IMO identifiers.",
        )
        if manual_input != st.session_state.get("imo_manual_input", ""):
            st.session_state["imo_manual_input"] = manual_input

        if st.button("Apply manual IMO list", use_container_width=True):
            manual_values = _parse_manual_imo_input(st.session_state.get("imo_manual_input", ""))
            if manual_values:
                st.session_state["imo_filter"] = manual_values
                st.success(f"Applied {len(manual_values)} IMO numbers from manual entry.")
            else:
                st.warning("No valid IMO numbers found in the manual entry.")

        if st.button("Clear IMO filter", use_container_width=True):
            st.session_state["imo_filter"] = tuple()
            st.info("Cleared IMO filter – simulated data will be used until IMOs are provided.")

        active = st.session_state.get("imo_filter", tuple())
        if active:
            st.caption(f"Active IMO count: {len(active)}")
        else:
            st.caption("No IMO filter applied. Upload or enter IMOs to load parquet data.")

    st.sidebar.divider()
    return st.session_state.get("imo_filter", tuple()), container


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


imo_filter, scope_container = render_data_scope_controls()

with st.spinner("Syncing telemetry..."):
    master_df = get_data_snapshot(tuple(imo_filter))

load_context = master_df.attrs.get("load_context", "simulated")
with scope_container:
    if load_context == "parquet":
        st.success(
            f"Loaded {master_df['IMO_Number'].nunique()} vessels from local parquet telemetry."
        )
    elif load_context == "simulated-fallback":
        st.warning(
            "No matching records were found for the supplied IMOs – displaying simulated data instead."
        )
    else:
        st.info("Provide an IMO list to replace the simulated sample with local parquet data.")

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
