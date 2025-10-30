from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from data_simulation import PORT_COORDINATES, comparative_view, regression_dataset


PORT_OPTIONS = list(PORT_COORDINATES.keys())


def _regression_trace(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    coeffs = np.polyfit(df["Speed_knots"], df["CO2_tons"], 1)
    x_vals = np.linspace(df["Speed_knots"].min(), df["Speed_knots"].max(), 50)
    y_vals = coeffs[0] * x_vals + coeffs[1]
    return x_vals, y_vals


def render_comparative_insights(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Comparative Insights</div>', unsafe_allow_html=True)

    tabs = st.tabs(["Port Benchmark", "Speed vs CO₂ Regression"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        port_a = col1.selectbox("Primary Port", PORT_OPTIONS, index=0)
        port_b = col2.selectbox("Benchmark Port", PORT_OPTIONS, index=1)

        comparison = comparative_view(df)
        pivot = comparison.pivot(index="Date", columns="Zone", values="CO2_tons").fillna(0)
        pivot["Port"] = port_a
        benchmark = pivot.copy()
        benchmark["Port"] = port_b
        combined = pd.concat([pivot, benchmark])

        bar_fig = px.bar(
            combined.reset_index(),
            x="Date",
            y=["ECA", "Non-ECA"],
            color_discrete_map={"ECA": "#E03C31", "Non-ECA": "#2980B9"},
            barmode="group",
            facet_row="Port",
            height=500,
        )
        bar_fig.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
        st.plotly_chart(bar_fig, use_container_width=True)

    with tabs[1]:
        regression_df, corr = regression_dataset(df)
        scatter_fig = px.scatter(
            regression_df,
            x="Speed_knots",
            y="CO2_tons",
            color_discrete_sequence=["#2980B9"],
            labels={"Speed_knots": "Speed (knots)", "CO2_tons": "CO₂ (t)"},
        )
        x_vals, y_vals = _regression_trace(regression_df)
        scatter_fig.add_traces(
            px.line(x=x_vals, y=y_vals, labels={"x": "Speed", "y": "CO₂"}).update_traces(
                line=dict(color="#E03C31", width=3), showlegend=False
            ).data
        )
        scatter_fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#121212",
            paper_bgcolor="#121212",
            title=f"Speed vs CO₂ Regression (r = {corr})",
        )
        st.plotly_chart(scatter_fig, use_container_width=True)
        st.caption("Correlation computed using Pearson method on simulated dataset.")
