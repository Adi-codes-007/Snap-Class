import os
import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher, safe_execute
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
import numpy as np

from datetime import datetime

import pandas as pd

from src.database.config import supabase

from src.components.dialog_voice_attendance import voice_attendance_dialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEACHER_PORTAL_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "teacher_portal.jpg")
TEACHER_CLASSROOM_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "teacher_classroom.jpg")
TEACHER_PORTRAIT_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "teacher_portrait.jpg")


def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        user_col, btn_col = st.columns([3, 1], vertical_alignment='center')
        with user_col:
            st.subheader(f"""Welcome, {teacher_data['name']} """)
        with btn_col:
            if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace", use_container_width=True):
                st.session_state['is_logged_in'] = False
                del st.session_state.teacher_data 
                st.rerun()

    hero_c1, hero_c2 = st.columns([1, 3], vertical_alignment='center')
    with hero_c1:
        st.image(TEACHER_PORTRAIT_IMG, use_container_width=True)
    with hero_c2:
        st.markdown(f"""
            <div style="background:white; border-radius:1.25rem; padding:1.25rem 1.5rem; box-shadow:0 4px 15px rgba(0,0,0,0.06);">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="background:#EEF2FF; color:#4F46E5; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:9999px;">FACULTY WORKSPACE</span>
                    <span style="background:#DCFCE7; color:#15803D; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:9999px;">● ACTIVE</span>
                </div>
                <h3 style="margin:0.5rem 0 0.2rem 0; color:#0F172A;">Prof. {teacher_data['name']}</h3>
                <p style="margin:0; font-size:0.875rem; color:#64748B;">Faculty Username: <b>@{teacher_data['username']}</b> &bull; Automated Attendance Management</p>
            </div>
        """, unsafe_allow_html=True)


    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    tab1, tab2, tab3 = st.columns(3)


    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()


    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    


    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')


    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You havent created any subjects yet! Please create one to begin!')
        return
    
    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3,1], vertical_alignment='bottom')

    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))

    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_prints:', width='stretch'):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    if st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4 ]:
                st.image(img, width='stretch', caption=f'Photo {idx+1}')
    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()


    with c2:
        
        if st.button('Run Face Analysis', width='stretch', type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep scanning classroom photos...'):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendance(img_np)


                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)

                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                enrolled_res = safe_execute(supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_subject_id))
                enrolled_students = enrolled_res.data

                if not enrolled_students:
                    st.warning('No students are enrolled in this course yet! Please share the course join code so students can enroll.')
                else:
                    results, attendance_to_log  = [], []

                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(int(student['student_id']), [])
                        is_present = len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })

                        attendance_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        })

                    attendance_result_dialog(pd.DataFrame(results), attendance_to_log)

    with c3:
        if st.button('Use Voice Attendance', type='primary', width='stretch', icon=':material/mic:'):
            voice_attendance_dialog(selected_subject_id)











def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns([3, 1], vertical_alignment='center')
    with col1:
        st.header('Manage Subjects', width='stretch')

    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        cols = st.columns(2)
        for i, sub in enumerate(subjects):
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
            def share_btn(curr_sub=sub):
                if st.button(f"Share Code: {curr_sub['name']}", key=f"share_{curr_sub['subject_code']}", icon=":material/share:"):
                    share_subject_dialog(curr_sub['name'], curr_sub['subject_code'])
                st.space()

            with cols[i % 2]:
                subject_card(
                    name = sub['name'],
                    code = sub['subject_code'],
                    section = sub['section'],
                    stats=stats,
                    footer_callback=share_btn
                )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
    st.header('Attendance Records')

    teacher_id = st.session_state.teacher_data['teacher_id']

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        return
    
    data = []

    for r in records:
        ts = r.get('timestamp')

        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N'A",
            "Subject": r['subjects']['name'],
            "Subject Code":r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })


    df = pd.DataFrame(data)



    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])
        .agg(
            Present_Count = ('is_present', 'sum'),
            Total_Count =('is_present', 'count')
        ).reset_index()

    )

    summary['Attendance Stats'] = (
        "✅ " + summary['Present_Count'].astype(str) + " /"
        + summary['Total_Count'].astype(str) + ' Students'
    )

    display_df = ( summary.sort_values(by='ts_group' ,ascending=False)
                  [['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
                  )
    
    st.dataframe(display_df, width='stretch', hide_index=True)


def login_teacher(username, password):
    if not username or not password:
        return False, "Please enter both username and password."
    try:
        teacher = teacher_login(username, password)
        if teacher:
            st.session_state.user_role = 'teacher'
            st.session_state.teacher_data = teacher
            st.session_state.is_logged_in = True
            return True, "Login successful"
        return False, "Invalid username and password combo"
    except Exception as e:
        return False, f"Database connection error: {e}"

def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.divider()

    col_left, col_right = st.columns([1, 1], gap='large')

    with col_left:
        st.image(TEACHER_CLASSROOM_IMG, use_container_width=True)
        st.markdown("""
            <div style="background:white; border-radius:1rem; padding:1.25rem; margin-top:0.75rem; box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                <h4 style="margin:0 0 0.4rem 0; color:#1E293B;">👩‍🏫 Educator & Faculty Portal</h4>
                <p style="font-size:0.875rem; color:#64748B; margin-bottom:0.6rem;">
                    Eliminate roll calls. Capture or upload a single classroom snapshot to detect all attending students concurrently.
                </p>
                <div style="font-size:0.825rem; color:#475569; display:flex; flex-direction:column; gap:4px;">
                    <span>📸 <b>Multi-Face Detection:</b> Concurrent matching against course roster</span>
                    <span>📊 <b>Real-time Analytics:</b> Attendance rate metrics and logs</span>
                    <span>🔑 <b>Code Sharing:</b> Instant join codes for fast student onboarding</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader('Faculty Login')
        teacher_username = st.text_input("Enter username", placeholder='ananyaroy')
        teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")

        st.divider()

        btnc1, btnc2 = st.columns(2)

        with btnc1:
            if st.button('Login', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
                success, msg = login_teacher(teacher_username, teacher_pass)
                if success:
                    st.toast("welcome back!", icon="👋")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

        with btnc2:
            if st.button('Register Instead', type="primary", icon=':material/passkey:', width='stretch'):
                st.session_state.teacher_login_type = 'register'
                st.rerun()

    footer_dashboard()



def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All Fields are required!"
    try:
        if check_teacher_exists(teacher_username):
            return False, "Username already taken"
    except Exception as e:
        return False, f"Network timeout checking username: {e}"
    if teacher_pass != teacher_pass_confirm:
        return False, "Password doesn't match"
    
    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Sucessfully Created! Login Now"
    except Exception as e:
        return False, f"Registration failed: {e}"
    

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.divider()

    col_left, col_right = st.columns([1, 1], gap='large')

    with col_left:
        st.image(TEACHER_PORTAL_IMG, use_container_width=True)
        st.markdown("""
            <div style="background:white; border-radius:1rem; padding:1.25rem; margin-top:0.75rem; box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                <h4 style="margin:0 0 0.4rem 0; color:#1E293B;">🏛️ Join Faculty Network</h4>
                <p style="font-size:0.875rem; color:#64748B; margin-bottom:0.6rem;">
                    Register your faculty account to create course subjects, manage student enrollments, and access automated AI attendance logs.
                </p>
                <div style="font-size:0.825rem; color:#475569; display:flex; flex-direction:column; gap:4px;">
                    <span>⚡ <b>Quick Setup:</b> Ready in under 1 minute</span>
                    <span>🔒 <b>Secure Authentication:</b> Encrypted credential store</span>
                    <span>📑 <b>Automated Records:</b> Exportable attendance sheets</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader('Register Faculty Account')

        teacher_username = st.text_input("Enter username", placeholder='ananyaroy')
        teacher_name = st.text_input("Enter name", placeholder='Ananya Roy')
        teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")
        teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Enter password")

        st.divider()

        btnc1, btnc2 = st.columns(2)

        with btnc1:
            if st.button('Register now', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
                success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
                if success:
                    st.success(message)
                    import time
                    time.sleep(2)
                    st.session_state.teacher_login_type = "login"
                    st.rerun()
                else:
                    st.error(message)

        with btnc2:
            if st.button('Login Instead', type="primary", icon=':material/passkey:', width='stretch'):
                st.session_state.teacher_login_type = 'login'
                st.rerun()

    footer_dashboard()