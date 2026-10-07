import os
import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENT_CAMPUS_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "student_campus.jpg")
STUDENT_PORTRAIT_IMG = os.path.join(BASE_DIR, "..", "assets", "images", "student_portrait.jpg")

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        user_col, btn_col = st.columns([3, 1], vertical_alignment='center')
        with user_col:
            st.subheader(f"""Welcome, {student_data['name']} """)
        with btn_col:
            if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace", use_container_width=True):
                st.session_state['is_logged_in'] = False
                del st.session_state.student_data 
                st.rerun()

    hero_c1, hero_c2 = st.columns([1, 3], vertical_alignment='center')
    with hero_c1:
        st.image(STUDENT_PORTRAIT_IMG, use_container_width=True)
    with hero_c2:
        st.markdown(f"""
            <div style="background:white; border-radius:1.25rem; padding:1.25rem 1.5rem; box-shadow:0 4px 15px rgba(0,0,0,0.06);">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="background:#E0E7FF; color:#4338CA; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:9999px;">STUDENT PROFILE</span>
                    <span style="background:#DCFCE7; color:#15803D; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:9999px;">● ACTIVE</span>
                </div>
                <h3 style="margin:0.5rem 0 0.2rem 0; color:#0F172A;">{student_data['name']}</h3>
                <p style="margin:0; font-size:0.875rem; color:#64748B;">Student ID: <b>#{student_id}</b> &bull; Biometric FaceID Enabled</p>
            </div>
        """, unsafe_allow_html=True)


    st.space()

    c1, c2 = st.columns([3, 1], vertical_alignment='center')
    with c1:
        st.header('Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()


    st.divider()


    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] +=1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1


    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']


        stats = stats_map.get(sid,{"total":0, "attended": 0} )
        def unenroll_button():
                if st.button("Unenroll from tihs course", type='tertiary', width='stretch', icon=':material/delete_forever:'):
                    unenroll_student_to_subject(student_id, sid)
                    st.toast(f"Unenrolled from {sub['name']} successfully!")
                    st.rerun()

        with cols[i % 2]:

            subject_card(
                name = sub['name'],
                code =sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button
            )
    footer_dashboard()


def student_screen():


    style_background_dashboard()
    style_base_layout()


    if "student_data" in st.session_state:
        student_dashboard()
        return
    
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
        st.image(STUDENT_CAMPUS_IMG, use_container_width=True)
        st.markdown("""
            <div style="background:white; border-radius:1rem; padding:1.25rem; margin-top:0.75rem; box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                <h4 style="margin:0 0 0.4rem 0; color:#1E293B;">🎓 Student Biometric Check-In</h4>
                <p style="font-size:0.875rem; color:#64748B; margin-bottom:0.6rem;">
                    Position your face within the frame. Our AI automatically verifies your student profile and signs you into your portal.
                </p>
                <div style="font-size:0.825rem; color:#475569; display:flex; flex-direction:column; gap:4px;">
                    <span>⚡ <b>Instant Verification:</b> Sub-second recognition</span>
                    <span>🔒 <b>Biometric Privacy:</b> Secured landmark vector encodings</span>
                    <span>🎙️ <b>Multimodal:</b> Supports voice attendance backup</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader('FaceID Verification')
        show_registration = False
        photo_source = st.camera_input("Position your face in the center")

        if photo_source:
            img = np.array(Image.open(photo_source))

            with st.spinner('AI is scanning..'):
                detected, all_ids, num_faces = predict_attendance(img)

                if num_faces == 0:
                    st.warning('Face not found!')
                elif num_faces >1:
                    st.warning('Multiple faces found')
                else:
                    if detected:
                        student_id = list(detected.keys())[0]
                        all_students = get_all_students()
                        student = next((s for s in all_students if s['student_id']==student_id), None)

                        if student:
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = 'student'
                            st.session_state.student_data = student
                            st.toast(f"Welcome Back {student['name']}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info('Face not recognized! You might be a new student!')
                        show_registration = True
        if show_registration:
            with st.container(border=True):
                st.header('Register new Profile')
                new_name = st.text_input("Enter your name", placeholder='E.g. Hamza Rizvi')

                st.subheader('Optional : Voice Enrollment')
                st.info("Enroll your for voice only attendance")


                audio_data = None

                try:
                    audio_data = st.audio_input('Record a short phrase like I am present, My name is Akash.')
                except Exception:
                    st.error('Audio Data failed!')

                if st.button('Create Account', type='primary'):
                    if new_name:
                        with st.spinner('Creating profile..'):
                            img = np.array(Image.open(photo_source))
                            encodings= get_face_embeddings(img)
                            if encodings:
                                face_emb = encodings[0].tolist()

                                voice_emb = None
                                if audio_data:
                                    voice_emb = get_voice_embedding(audio_data.read())

                                response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                                if response_data:
                                    train_classifier()
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = response_data[0]
                                    st.toast(f'Profile Created! Hi {new_name}!')
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error('Couldnt capture your facial features for registration')

                    else:
                        st.warning('Please enter your name!')

    footer_dashboard()