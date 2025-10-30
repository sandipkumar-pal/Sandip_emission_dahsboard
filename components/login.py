from pathlib import Path
from typing import Optional, Tuple

import streamlit as st


ROLES = ["Admin", "Analyst", "Ops Manager", "Regulator"]


def load_logo(path: Optional[Path]) -> bytes | None:
    if path is None or not path.exists():
        return None
    return path.read_bytes()


def render_login(logo_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    authenticated = st.session_state.get("authenticated", False)
    active_role = st.session_state.get("role") if authenticated else None

    if authenticated and active_role:
        st.markdown(
            """
            <div style="text-align:center;margin-top:1.5rem;margin-bottom:2rem;">
                <h2 style="color:#E0E0E0;">Access granted</h2>
                <p style="color:#BBBBBB;">Use the sidebar to navigate the analytics modules.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return authenticated, active_role

    st.markdown("""
        <div style="text-align:center;margin-top:3rem;">
            <h1 style="color:#E0E0E0;">Port Emission Intelligence – ESG M&amp;T</h1>
            <p style="color:#BBBBBB;">Secure analytics environment for port authority stakeholders</p>
        </div>
    """, unsafe_allow_html=True)

    logo_bytes = load_logo(Path(logo_path) if logo_path else None)
    if logo_bytes:
        st.image(logo_bytes, width=120)
    else:
        st.markdown(
            "<p style='color:#E03C31;font-weight:600;'>Port Authority Dashboard</p>",
            unsafe_allow_html=True,
        )

    st.write("### Authenticate")
    username = st.text_input("User ID", placeholder="firstname.lastname")
    password = st.text_input("Passcode", type="password", placeholder="••••••••")
    role = st.selectbox("Role", ROLES)

    login = st.button("Enter Dashboard", use_container_width=True)

    if login and username and password:
        st.session_state["authenticated"] = True
        st.session_state["role"] = role
        st.toast(f"Welcome {username} – {role}", icon="✅")
        st.rerun()

    authenticated = st.session_state.get("authenticated", False)
    active_role = st.session_state.get("role") if authenticated else None
    return authenticated, active_role
