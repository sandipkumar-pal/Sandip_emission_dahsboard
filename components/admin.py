import platform
from datetime import datetime

import streamlit as st


def render_admin_panel() -> None:
    st.markdown('<div class="section-header">Administration Console</div>', unsafe_allow_html=True)

    with st.expander("Threshold Management", expanded=True):
        st.write("Configure policy guardrails for emission alerts and compliance escalation.")
        threshold = st.number_input(
            "Default CO₂ Threshold (t)",
            min_value=5.0,
            max_value=30.0,
            value=st.session_state.get("co2_threshold", 15.0),
            step=0.5,
        )
        st.session_state["co2_threshold"] = threshold
        st.multiselect(
            "Authorized Roles for Override",
            options=["Admin", "Analyst", "Ops Manager", "Regulator"],
            default=["Admin", "Regulator"],
            help="Select who can update live thresholds during disruption events.",
        )

    with st.expander("Role Management"):
        st.write("Maintain user registry for enterprise single sign-on integration (mockup).")
        st.text_input("Add user email", placeholder="user@portauthority.gov")
        st.selectbox("Assign role", options=["Admin", "Analyst", "Ops Manager", "Regulator"])
        st.button("Queue Provisioning", use_container_width=True)

    with st.expander("Boundary Layers"):
        st.write("Upload refreshed ECA polygons or switch between archived boundaries.")
        st.file_uploader("ECA GeoJSON", type="geojson")
        st.selectbox("Active Boundary Version", ["2024-Q3 Baseline", "2024-Q2 Legacy", "Sandbox Scenario"])

    with st.expander("System Diagnostics"):
        st.write(f"Last data refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        st.write("App version: v0.2.0")
        st.write(f"Python: {platform.python_version()}")
        st.write("Session state keys: " + ", ".join(sorted(st.session_state.keys())))
