import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_simulation import generate_sankey_data


COLOR_MAP = {"ECA": "#E03C31", "Non-ECA": "#2980B9"}


def render_zone_analytics(
    zone_summary: pd.DataFrame,
    time_series: pd.DataFrame,
    fuel_summary: pd.DataFrame,
    df: pd.DataFrame,
) -> None:
    st.markdown('<div class="section-header">ECA vs Non-ECA Analytics</div>', unsafe_allow_html=True)
    bar_fig = px.bar(
        zone_summary,
        x="Zone",
        y="CO2_tons",
        color="Zone",
        color_discrete_map=COLOR_MAP,
        title="Emission Load by Zone",
        text_auto=".2f",
    )
    bar_fig.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
    st.plotly_chart(bar_fig, use_container_width=True)

    st.write("#### 30-day Daily Emissions")
    ts_fig = px.line(
        time_series,
        x="Date",
        y=[col for col in time_series.columns if col != "Date"],
        markers=True,
        color_discrete_map=COLOR_MAP,
    )
    ts_fig.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
    st.plotly_chart(ts_fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        pie_fig = px.pie(
            fuel_summary,
            names="Fuel_Type",
            values="CO2_tons",
            title="Fuel Mix Contribution",
            color="Fuel_Type",
            color_discrete_sequence=["#E03C31", "#2980B9", "#4A4A4A", "#27AE60"],
        )
        pie_fig.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
        st.plotly_chart(pie_fig, use_container_width=True)

    with col2:
        sankey = generate_sankey_data(df)
        if sankey["values"]:
            sankey_fig = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=20,
                            line=dict(color="#1E1E1E", width=0.5),
                            label=sankey["nodes"],
                            color=["#E03C31", "#2980B9", "#4A4A4A", "#27AE60", "#E03C31", "#2980B9", "#2980B9"],
                        ),
                        link=dict(
                            source=sankey["sources"],
                            target=sankey["targets"],
                            value=sankey["values"],
                        ),
                    )
                ]
            )
            sankey_fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="#121212",
                paper_bgcolor="#121212",
                title_text="Fuel Type → Zone → Emissions",
            )
            st.plotly_chart(sankey_fig, use_container_width=True)
        else:
            st.info("Sankey view requires fuel-zone combinations with positive emissions.")
