"""
Registration Page for FleetGuard
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth_manager import AuthManager

# Page config
st.set_page_config(
    page_title="הרשמה - FleetGuard",
    page_icon="📝",
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

st.title("📝 הרשמה למערכת")
st.markdown("---")

# Registration form
with st.form("register_form"):
    st.subheader("יצירת חשבון חדש")
    
    full_name = st.text_input("שם מלא", placeholder="הזן שם מלא (אופציונלי)")
    username = st.text_input("שם משתמש *", placeholder="הזן שם משתמש")
    email = st.text_input("כתובת אימייל *", placeholder="example@email.com")
    password = st.text_input("סיסמה *", type="password", placeholder="לפחות 6 תווים")
    password_confirm = st.text_input("אישור סיסמה *", type="password", placeholder="הזן שוב את הסיסמה")
    
    st.caption("* שדות חובה")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        submit_button = st.form_submit_button("הרשם", use_container_width=True)
    with col2:
        if st.form_submit_button("כבר רשום? התחבר כאן", use_container_width=True):
            st.query_params.page = "login"
            st.rerun()
    
    if submit_button:
        # Validation
        if not username or not email or not password:
            st.error("❌ נא למלא את כל השדות החובה")
        elif len(password) < 6:
            st.error("❌ הסיסמה חייבת להכיל לפחות 6 תווים")
        elif password != password_confirm:
            st.error("❌ הסיסמאות לא תואמות")
        else:
            success, message = auth.register_user(username, email, password, full_name)
            
            if success:
                st.success(f"✅ {message}")
                st.info("אנא התחבר עם הפרטים שיצרת")
                st.balloons()
                
                # Redirect to login
                st.query_params.page = "login"
                st.rerun()
            else:
                st.error(f"❌ {message}")

# Link to login
st.markdown("---")
st.markdown("כבר רשום? [התחבר כאן](?page=login)")

