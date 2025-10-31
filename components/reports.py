import streamlit as st

from data_simulation import pdf_placeholder


def render_reports(summary: dict) -> None:
    st.markdown('<div class="section-header">Reports & Briefings</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("ECA Total", f"{summary['eca_total']:.1f} t")
    col2.metric("Non-ECA Total", f"{summary['non_eca_total']:.1f} t")
    col3.metric("Compliance", f"{summary['compliance']:.1f}%")

    st.markdown(
        """
        <div class="metric-card">
            <h3>Top Emitters</h3>
            <p class="metric-subtext">Focus joint inspections on repeated ECA offenders breaching carbon limits.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not summary["top_emitters"].empty:
        st.dataframe(summary["top_emitters"], hide_index=True, use_container_width=True)
    else:
        st.info("No emitters breached reporting threshold for the period.")

    pdf_bytes = pdf_placeholder(summary)
    st.download_button(
        "Download PDF Brief",
        data=pdf_bytes,
        file_name="port_emission_brief.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.caption("PDF export is a structured text brief. Integrate with enterprise report engines for branded layouts.")
