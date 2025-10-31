import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from data_simulation import DEFAULT_ALERT_THRESHOLD, compliance_summary


def render_compliance_alerts(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Compliance & Alerts</div>', unsafe_allow_html=True)

    summary = compliance_summary(df)
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=summary["rate"],
            number={"suffix": "%"},
            delta={"reference": 92, "increasing": {"color": "#27AE60"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#E03C31"},
                "steps": [
                    {"range": [0, 70], "color": "#E03C3133"},
                    {"range": [70, 90], "color": "#F39C1233"},
                    {"range": [90, 100], "color": "#27AE6033"},
                ],
                "threshold": {"line": {"color": "#27AE60", "width": 4}, "value": 95},
            },
            title={"text": "Monthly Compliance", "font": {"size": 18}},
        )
    )
    gauge.update_layout(template="plotly_dark", plot_bgcolor="#121212", paper_bgcolor="#121212")
    st.plotly_chart(gauge, use_container_width=True)

    alerts_df = summary["alerts"]
    st.markdown(
        f"""
        <div class="metric-card">
            <h4>Active Non-Compliance</h4>
            <p class="metric-subtext">Threshold set at {DEFAULT_ALERT_THRESHOLD} t CO₂. {len(alerts_df)} vessels flagged.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if alerts_df.empty:
        st.success("All tracked vessels operate within emission limits.")
    else:
        st.dataframe(alerts_df, hide_index=True, use_container_width=True)
        st.info("Ops teams notified. Escalate to regulator desk if breach persists beyond 6 hours.")
