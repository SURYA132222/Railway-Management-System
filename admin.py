# admin.py

import streamlit as st
import hashlib

# Predefined Admin Credentials
ADMINS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest()
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin(username, password):
    if username in ADMINS:
        return ADMINS[username] == hash_password(password)
    return False

def admin_login_ui():
    st.subheader("🛠️ Admin Login")
    username = st.text_input("Admin Username")
    password = st.text_input("Admin Password", type="password")

    if st.button("Login as Admin"):
        if verify_admin(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = "Admin"
            st.success(f"Welcome Admin {username}!")
            st.rerun()
        else:
            st.error("Invalid admin credentials.")
