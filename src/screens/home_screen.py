import os
import streamlit as st
from src.components.header import header_home
from src.components.footer import footer_home
from src.ui.base_layout import style_base_layout, style_background_home

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENT_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "student_portal.jpg")
TEACHER_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "teacher_portal.jpg")


def home_screen():
    header_home()
    style_background_home()
    style_base_layout()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.header("Student Portal")
        st.image(STUDENT_IMG, use_container_width=True)
        st.caption("Touchless FaceID check-in, course enrollments & personal attendance stats.")
        if st.button('Enter Student Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', use_container_width=True):
            st.session_state['login_type'] = 'student'
            st.rerun()

    with col2:
        st.header("Teacher Portal")
        st.image(TEACHER_IMG, use_container_width=True)
        st.caption("Automated classroom group photo scanning, subject management & logs.")
        if st.button('Enter Teacher Portal', type='primary', icon=':material/arrow_outward:', icon_position='right', use_container_width=True):
            st.session_state['login_type'] = 'teacher'
            st.rerun()

    footer_home()