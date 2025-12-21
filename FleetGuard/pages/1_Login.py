"""
Login Page for FleetGuard
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth_manager import AuthManager

# Page config
st.set_page_config(
    page_title="כניסה - FleetGuard",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# RTL support
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
</style>
""", unsafe_allow_html=True)

# Initialize auth manager
auth = AuthManager()

# If already authenticated, redirect
if auth.is_authenticated():
    st.success("✅ אתה כבר מחובר!")
    if st.button("למעבר לדשבורד"):
        st.query_params.clear()
        st.rerun()
    st.stop()

st.title("🔐 כניסה למערכת")
st.markdown("---")

# Login form
with st.form("login_form"):
    st.subheader("התחברות")
    
    username = st.text_input("שם משתמש", placeholder="הזן שם משתמש")
    password = st.text_input("סיסמה", type="password", placeholder="הזן סיסמה")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        submit_button = st.form_submit_button("התחבר", use_container_width=True)
    with col2:
        if st.form_submit_button("עדיין לא רשום? הרשם כאן", use_container_width=True):
            st.query_params.page = "register"
            st.rerun()
    
    if submit_button:
        if username and password:
            success, message, user_data = auth.login_user(username, password)
            
            if success:
                st.session_state['authenticated'] = True
                st.session_state['user_data'] = user_data
                st.success(f"✅ {message}")
                st.info(f"ברוך הבא, {user_data.get('full_name', user_data.get('username', ''))}!")
                st.balloons()
                
                # Redirect to main page - clear query params
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"❌ {message}")
        else:
            st.warning("⚠️ נא למלא את כל השדות")

# Link to registration
st.markdown("---")
st.markdown("עדיין לא רשום? [הרשם כאן](?page=register)")

