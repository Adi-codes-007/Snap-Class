import streamlit as st


def footer_home():
    st.markdown("""
        <div style="margin-top:2.5rem; display:flex; justify-content:center; align-items:center;">
            <p style="font-size:0.85rem; color:#A5B4FC; text-align:center; margin:0; letter-spacing:0.3px;">
                &copy; 2026 SnapClass AI &bull; Smart Campus Attendance System
            </p>
        </div>
    """, unsafe_allow_html=True)


def footer_dashboard():
    st.markdown("""
        <div style="margin-top:2.5rem; display:flex; justify-content:center; align-items:center;">
            <p style="font-size:0.85rem; color:#64748B; text-align:center; margin:0; letter-spacing:0.3px;">
                &copy; 2026 SnapClass AI &bull; Smart Campus Attendance System
            </p>
        </div>
    """, unsafe_allow_html=True)
