from io import StringIO

import pandas as pd
import streamlit as st


ZONE_FILTERS = ["All", "ECA", "Non-ECA"]


def render_vessel_table(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Vessel & Voyage Analytics</div>', unsafe_allow_html=True)
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    zone = filter_col1.selectbox("Zone", ZONE_FILTERS)
    vessels = filter_col2.multiselect("Vessel", sorted(df["Vessel_Name"].unique()))
    date_range = filter_col3.date_input(
        "Date Range",
        value=(df["Date"].min().date(), df["Date"].max().date()),
    )

    filtered = df.copy()
    if zone != "All":
        filtered = filtered[filtered["Zone"] == zone]
    if vessels:
        filtered = filtered[filtered["Vessel_Name"].isin(vessels)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["Date"].dt.date >= start) & (filtered["Date"].dt.date <= end)]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    csv_buffer = StringIO()
    filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        "Export CSV",
        data=csv_buffer.getvalue(),
        file_name="port_emission_extract.csv",
        mime="text/csv",
        use_container_width=True,
    )
