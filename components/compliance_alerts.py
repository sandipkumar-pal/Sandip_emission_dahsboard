import pandas as pd
import streamlit as st


THRESHOLD_KEY = "co2_threshold"
DEFAULT_THRESHOLD = 15.0


def render_compliance_alerts(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Compliance & Alerts</div>', unsafe_allow_html=True)
    threshold = st.session_state.get(THRESHOLD_KEY, DEFAULT_THRESHOLD)
    st.slider(
        "Alert Threshold (CO₂ tons)",
        min_value=5.0,
        max_value=25.0,
        value=threshold,
        key=THRESHOLD_KEY,
        help="Adjust to model tolerance bands for emission breaches.",
    )

    threshold = st.session_state[THRESHOLD_KEY]
    alerts = df[df["CO2_tons"] > threshold]

    if alerts.empty:
        st.markdown(
            '<div class="success-banner">All monitored vessels are within regulatory limits.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="alert-banner">{len(alerts)} vessels exceeding CO₂ threshold of {threshold:.1f} t</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(alerts[[
            "IMO_Number",
            "Vessel_Name",
            "Zone",
            "Fuel_Type",
            "CO2_tons",
            "Compliance_Flag",
            "Date",
        ]], use_container_width=True, hide_index=True)
