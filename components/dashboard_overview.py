from typing import Dict

import streamlit as st


def render_overview(kpis: Dict[str, float]) -> None:
    st.markdown('<div class="section-header">Executive Overview</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    col1.metric("Total CO₂ (t)", f"{kpis['total_co2']:,}")
    col2.metric("Avg CO₂ / Vessel", f"{kpis['avg_co2']:.2f}")
    col3.metric("% ECA", f"{kpis['eca_percent']:.1f}%", delta=f"Non-ECA {kpis['non_eca_percent']:.1f}%")
    col4.metric("Compliance Rate", f"{kpis['compliance_rate']:.1f}%")
    col5.metric("Active Alerts", kpis['alerts'], delta="CO₂>15 t")

    st.markdown(
        """
        <div class="metric-card" style="margin-top:1rem;">
            <h3>Decision Signals</h3>
            <p class="metric-subtext">
                Monitoring <span class="data-highlight">ECA</span> contributions safeguards ESG mandates. Analyst teams
                should review deviation clusters within the last 48 hours and ensure regulated notifications for
                repeat offenders.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
