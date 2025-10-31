from io import StringIO

import pandas as pd
import streamlit as st

from data_simulation import export_payload


def render_vessel_table(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Vessel & Voyage Analytics</div>', unsafe_allow_html=True)

    st.caption("Filter context inherited from sidebar. Apply additional vessel level focus below if required.")

    vessels = st.multiselect(
        "Highlight specific vessels",
        options=sorted(df["Vessel_Name"].unique()),
        help="Optional – focus table on vessels of interest.",
    )
    if vessels:
        filtered = df[df["Vessel_Name"].isin(vessels)]
    else:
        filtered = df

    if filtered.empty:
        st.warning("No voyages match the active filters.")
        return

    metrics = filtered[["CO2_tons", "SOx_tons", "NOx_tons", "Emission_Intensity"]].describe().loc[["mean", "max"]]
    st.write("#### Emission Distribution Snapshot")
    st.dataframe(metrics.rename(index={"mean": "Mean", "max": "Max"}), use_container_width=True)

    st.write("#### Voyage Level Records")
    display_df = filtered.sort_values("Date", ascending=False)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    downloads = export_payload(display_df)
    csv_io = StringIO(display_df.to_csv(index=False))

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Export CSV",
            data=csv_io.getvalue(),
            file_name="port_emission_extract.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "Export Excel",
            data=downloads["excel"],
            file_name="port_emission_extract.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="download-panel">
            <strong>Analyst Tip:</strong> Use Excel export to blend with bunker data & berth utilisation for cross-domain insight.
        </div>
        """,
        unsafe_allow_html=True,
    )
