import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from data_simulation import generate_sankey_data, hex_to_rgba

COLOR_MAP = {"ECA": "#E03C31", "Non-ECA": "#2980B9"}


def render_zone_analytics(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">ECA vs Non-ECA Analytics</div>', unsafe_allow_html=True)

    time_series = (
        df.groupby(["Date", "Zone"])["CO2_tons"].sum().reset_index().pivot_table(
            index="Date", columns="Zone", values="CO2_tons", fill_value=0
        )
    ).reset_index()

    diff = time_series.get("ECA", 0) - time_series.get("Non-ECA", 0)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=time_series["Date"],
            y=time_series.get("ECA", 0),
            mode="lines",
            fill="tozeroy",
            name="ECA",
            line=dict(color=COLOR_MAP["ECA"], width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=time_series["Date"],
            y=time_series.get("Non-ECA", 0),
            mode="lines",
            fill="tozeroy",
            name="Non-ECA",
            line=dict(color=COLOR_MAP["Non-ECA"], width=2.5),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=time_series["Date"],
            y=diff,
            mode="lines+markers",
            name="Δ ECA-Non-ECA",
            line=dict(color="#27AE60", dash="dash"),
            hovertemplate="Δ %{y:.2f} t<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#121212",
        paper_bgcolor="#121212",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=50, l=50, r=50),
    )
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="CO₂ tons", secondary_y=False)
    fig.update_yaxes(title="Δ tons", secondary_y=True, showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    fuel_mix = (
        df.groupby(["Fuel_Type", "Zone"])["CO2_tons"].sum().reset_index()
    )
    total_mix = fuel_mix.groupby("Fuel_Type")["CO2_tons"].sum().reset_index()
    donut = px.pie(
        total_mix,
        names="Fuel_Type",
        values="CO2_tons",
        hole=0.48,
        title="Fuel Mix Distribution",
        color="Fuel_Type",
        color_discrete_sequence=["#E03C31", "#2980B9", "#4A4A4A", "#27AE60"],
    )
    donut.update_traces(textinfo="percent+label", pull=[0.05, 0, 0, 0])
    donut.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")

    zone_bar = px.bar(
        fuel_mix,
        x="Fuel_Type",
        y="CO2_tons",
        color="Zone",
        color_discrete_map=COLOR_MAP,
        barmode="group",
        title="Fuel Type by Zone",
    )
    zone_bar.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(donut, use_container_width=True)
    with col2:
        st.plotly_chart(zone_bar, use_container_width=True)

    sankey_data = generate_sankey_data(df)
    with st.expander("Fuel → Zone → Emission Flow"):
        if sankey_data["values"]:
            link_colors = sankey_data.get("link_colors")
            if not link_colors:
                node_labels = sankey_data.get("nodes", [])
                link_colors = []
                for target in sankey_data["targets"]:
                    label = node_labels[target] if target < len(node_labels) else ""
                    zone = "ECA" if "ECA" in label else "Non-ECA"
                    link_colors.append(hex_to_rgba(COLOR_MAP.get(zone, "#4A4A4A"), 0.45))
            sankey_fig = go.Figure(
                data=[
                    go.Sankey(
                        arrangement="snap",
                        node=dict(
                            pad=15,
                            thickness=18,
                            line=dict(color="#1E1E1E", width=1),
                            label=sankey_data["nodes"],
                        ),
                        link=dict(
                            source=sankey_data["sources"],
                            target=sankey_data["targets"],
                            value=sankey_data["values"],
                            color=link_colors,
                        ),
                    )
                ]
            )
            sankey_fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="#121212",
                paper_bgcolor="#121212",
            )
            st.plotly_chart(sankey_fig, use_container_width=True)
        else:
            st.info("Sankey visualization requires fuel-zone combinations with positive emissions.")
