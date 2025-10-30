import platform
from datetime import datetime

import streamlit as st

from data_simulation import PORT_COORDINATES


def render_admin_panel() -> None:
    st.markdown('<div class="section-header">Administration</div>', unsafe_allow_html=True)

    with st.expander("Threshold Management", expanded=True):
        st.write("Configure default policy guardrails for emission alerts and notifications.")
        st.number_input(
            "Default CO₂ Threshold",
            min_value=5.0,
            max_value=30.0,
            value=st.session_state.get("co2_threshold", 15.0),
            step=0.5,
            key="co2_threshold",
        )
        st.multiselect(
            "Authorized Roles",
            options=["Admin", "Analyst", "Ops Manager", "Regulator"],
            default=["Admin", "Regulator"],
        )

    with st.expander("ECA Boundary Ingestion"):
        st.write("Upload updated geojson files from IMO bulletins for automated redeployment.")
        st.file_uploader("ECA GeoJSON", type="geojson")
        st.selectbox("Default Port Focus", options=list(PORT_COORDINATES.keys()))

    with st.expander("System Diagnostics"):
        st.write(f"Last data refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        st.write(f"App version: v0.1.0")
        st.write(f"Python: {platform.python_version()}")
        st.write("Session state keys: " + ", ".join(st.session_state.keys()))
