import streamlit as st

from data_simulation import EmissionSummary


def render_reports(summary: EmissionSummary) -> None:
    st.markdown('<div class="section-header">Reports & Briefings</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("ECA Total", f"{summary.eca_total:.1f} t")
    col2.metric("Non-ECA Total", f"{summary.non_eca_total:.1f} t")
    col3.metric("Compliance", f"{summary.compliance_rate:.1f}%")

    st.markdown(
        """
        <div class="metric-card">
            <h3>Top Emitters</h3>
            <p class="metric-subtext">Prioritize inspections for vessels breaching ESG tolerance levels.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("\n".join([f"- {vessel}" for vessel in summary.top_emitters]))

    st.write("\n")
    st.button("Download PDF (coming soon)", disabled=True, use_container_width=True)
