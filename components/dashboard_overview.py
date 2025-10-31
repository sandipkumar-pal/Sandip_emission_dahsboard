from typing import Dict

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

from data_simulation import (
    fuel_mix,
    generate_time_series,
    highlight_anomalies,
    zone_snapshot,
)


def render_overview(kpis: Dict[str, float], df: pd.DataFrame, insight: str) -> None:
    st.markdown('<div class="section-header">Executive Overview</div>', unsafe_allow_html=True)

    metric_columns = st.columns(5)
    metric_config = [
        ("Total CO₂ (t)", f"{kpis['total_co2']:,}", f"Alerts {kpis['alerts']}")
        if kpis.get("alerts") is not None
        else ("Total CO₂ (t)", f"{kpis['total_co2']:,}", None),
        ("Avg CO₂ / Vessel", f"{kpis['avg_co2']:.2f}", None),
        ("ECA Share", f"{kpis['eca_percent']:.1f}%", f"vs Non-ECA {kpis['non_eca_percent']:.1f}%"),
        ("Compliance", f"{kpis['compliance_rate']:.1f}%", None),
        ("Emission Intensity", f"{kpis['emission_intensity']:.2f} t/day", f"Weekly Δ {kpis['eca_weekly_change']:+.1f}%"),
    ]

    for column, (label, value, delta) in zip(metric_columns, metric_config):
        if delta:
            column.metric(label, value, delta)
        else:
            column.metric(label, value)

    style_metric_cards(
        background_color="#1A1A1A",
        border_left_color="#E03C31",
        border_color="#2A2A2A",
        box_shadow="0 10px 30px rgba(0,0,0,0.3)",
    )

    upper_left, upper_right = st.columns([2.4, 1])

    with upper_left:
        time_series = generate_time_series(df)
        if not time_series.empty:
            area_fig = go.Figure()
            area_fig.add_trace(
                go.Scatter(
                    x=time_series["Date"],
                    y=time_series.get("ECA", 0),
                    mode="lines",
                    name="ECA",
                    fill="tozeroy",
                    line=dict(color="#E03C31", width=3),
                    hovertemplate="ECA %{x|%d %b}: %{y:.2f} t<extra></extra>",
                )
            )
            area_fig.add_trace(
                go.Scatter(
                    x=time_series["Date"],
                    y=time_series.get("Non-ECA", 0),
                    mode="lines",
                    name="Non-ECA",
                    fill="tozeroy",
                    line=dict(color="#2980B9", width=3),
                    hovertemplate="Non-ECA %{x|%d %b}: %{y:.2f} t<extra></extra>",
                )
            )
            differential = time_series.get("ECA", 0) - time_series.get("Non-ECA", 0)
            area_fig.add_trace(
                go.Scatter(
                    x=time_series["Date"],
                    y=differential,
                    mode="lines+markers",
                    name="Δ ECA vs Non-ECA",
                    line=dict(color="#27AE60", dash="dot"),
                    hovertemplate="Δ %{x|%d %b}: %{y:.2f} t<extra></extra>",
                )
            )
            area_fig.update_layout(
                template="plotly_dark",
                title="Emission Trend by Zone",
                plot_bgcolor="#121212",
                paper_bgcolor="#121212",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=60, l=40, r=30, b=40),
                hovermode="x unified",
            )
            area_fig.update_yaxes(title="CO₂ tons")
            st.plotly_chart(area_fig, use_container_width=True)
        else:
            st.info("Insufficient data to render emission trend.")

    with upper_right:
        st.markdown(
            f"""
            <div class="insight-panel">
                <div class="insight-title">Insight Panel</div>
                <p>{insight}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        zone_cards = zone_snapshot(df)
        for card in zone_cards:
            st.markdown(
                f"""
                <div class="micro-card">
                    <div class="micro-title">{card['zone']} Zone</div>
                    <div class="micro-metric">{card['co2']:.1f} t CO₂</div>
                    <div class="micro-subtext">Compliance {card['compliance']:.1f}% • Alerts {card['alerts']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        mix = fuel_mix(df)
        total_mix = mix.groupby("Fuel_Type")["CO2_tons"].sum().reset_index()
        if not total_mix.empty:
            donut = px.pie(
                total_mix,
                names="Fuel_Type",
                values="CO2_tons",
                hole=0.55,
                color="Fuel_Type",
                color_discrete_sequence=["#E03C31", "#2980B9", "#4A4A4A", "#27AE60"],
            )
            donut.update_traces(textposition="inside", textinfo="percent+label")
            donut.update_layout(
                template="plotly_dark",
                title="Fuel Type Composition",
                showlegend=False,
                plot_bgcolor="#1E1E1E",
                paper_bgcolor="#1E1E1E",
                margin=dict(t=50, l=10, r=10, b=10),
            )
            st.plotly_chart(donut, use_container_width=True)

    snapshot = zone_snapshot(df)
    if snapshot:
        st.markdown('<div class="section-header">Zone Signal Board</div>', unsafe_allow_html=True)
        st.markdown('<div class="zone-summary">', unsafe_allow_html=True)
        for card in snapshot:
            st.markdown(
                f"""
                <div class="zone-card">
                    <h4>{card['zone']}</h4>
                    <span class="small-caps">Total CO₂</span>
                    <p class="metric-subtext"><span class="data-highlight">{card['co2']:.1f} t</span></p>
                    <span class="small-caps">Emission Intensity</span>
                    <p class="metric-subtext">{card['intensity']:.2f} t/hr</p>
                    <span class="small-caps">Compliance</span>
                    <p class="metric-subtext">{card['compliance']:.1f}% • Alerts: {card['alerts']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    top_emitters = (
        df.sort_values("CO2_tons", ascending=False)
        .head(3)[["Vessel_Name", "IMO_Number", "Zone", "CO2_tons", "Fuel_Type"]]
    )
    anomalies = highlight_anomalies(df)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Top Emitters")
        st.dataframe(
            top_emitters,
            hide_index=True,
            use_container_width=True,
        )
    with col_right:
        st.markdown("#### Anomaly Watch (> 1.5σ)")
        if anomalies.empty:
            st.success("No emission anomalies detected in the selected view.")
        else:
            st.dataframe(
                anomalies,
                hide_index=True,
                use_container_width=True,
            )

    st.markdown(
        """
        <div class="metric-card" style="margin-top:1rem;">
            <h3>Operational Recommendation</h3>
            <p class="metric-subtext">
                Maintain proactive boarding inspections on <span class="data-highlight">high-intensity ECA callers</span>.
                Align Ops Managers and Regulators on next-week convoy allocations to absorb projected traffic increases.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
