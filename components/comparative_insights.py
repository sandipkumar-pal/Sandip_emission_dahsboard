import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_simulation import comparative_port_profile, correlation_matrix, monthly_trend, speed_co2_relationship

COLOR_MAP = {"ECA": "#E03C31", "Non-ECA": "#2980B9"}


def render_comparative_insights(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Comparative Insights</div>', unsafe_allow_html=True)

    comparison = comparative_port_profile(df)
    trend_df = monthly_trend(df)
    relation = speed_co2_relationship(df)
    corr = correlation_matrix(df)

    col1, col2 = st.columns([2, 1])
    with col1:
        area = px.bar(
            comparison,
            x="Port",
            y="CO2_tons",
            color="Zone",
            color_discrete_map=COLOR_MAP,
            title="Peer Port Emission Benchmark",
        )
        area.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
        st.plotly_chart(area, use_container_width=True)
    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <h4>Key Takeaways</h4>
                <p class="metric-subtext">
                    Singapore maintains <span class="highlight-green">operational advantage</span> on Non-ECA corridors.
                    Jurong exhibits higher ECA exposure requiring targeted compliance sweeps.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    try:
        bubble = px.scatter(
            relation,
            x="Speed_knots",
            y="CO2_tons",
            size="Dwell_Time_hr",
            color="Zone",
            hover_data=["Vessel_Type", "Fuel_Type"],
            color_discrete_map=COLOR_MAP,
            trendline="ols",
            title="Speed vs CO₂ (Bubble size = Dwell Time)",
        )
    except Exception:
        bubble = px.scatter(
            relation,
            x="Speed_knots",
            y="CO2_tons",
            size="Dwell_Time_hr",
            color="Zone",
            hover_data=["Vessel_Type", "Fuel_Type"],
            color_discrete_map=COLOR_MAP,
            title="Speed vs CO₂ (Bubble size = Dwell Time)",
        )
    bubble.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
    st.plotly_chart(bubble, use_container_width=True)

    corr_fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale="Reds",
            zmin=-1,
            zmax=1,
            colorbar=dict(title="r"),
        )
    )
    corr_fig.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212", title="Correlation Matrix")
    st.plotly_chart(corr_fig, use_container_width=True)

    monthly_area = px.area(
        trend_df,
        x="Month",
        y="CO2_tons",
        color="Zone",
        color_discrete_map=COLOR_MAP,
        title="Monthly Emission Trend",
    )
    monthly_area.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
    st.plotly_chart(monthly_area, use_container_width=True)
