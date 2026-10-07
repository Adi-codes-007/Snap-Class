
import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog
from src.database.config import is_supabase_configured

def main():
    st.set_page_config(
        page_title='SnapClass - Making Attendance faster using AI',
        page_icon= "https://i.ibb.co/YTYGn5qV/logo.png"
    )

    if not is_supabase_configured():
        st.warning("⚙️ **Supabase Database Not Connected**")
        st.info(
            "Please add your Supabase credentials to **Streamlit Cloud Settings → Secrets**:\n\n"
            "```toml\n"
            "SUPABASE_URL = \"https://aykbldmekqlavaaiidxe.supabase.co\"\n"
            "SUPABASE_KEY = \"sb_publishable_GNPey206AWdIWKiNiN4Y5g_QOUPkbyf\"\n"
            "```"
        )
        st.stop()

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()
        
        case None:
            home_screen()


    join_code = st.query_params.get('join-code')
    if join_code:
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
            auto_enroll_dialog(join_code)
main()