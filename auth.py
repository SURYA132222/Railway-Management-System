# auth.py

import streamlit as st
import pandas as pd
import hashlib
import os

USER_FILE = "users.csv"

# ========== Utility Functions ==========

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def load_users():
    if os.path.exists(USER_FILE):
        if os.path.getsize(USER_FILE) > 0:
            df = pd.read_csv(USER_FILE)
            if "username" in df.columns and "password" in df.columns:
                return df.set_index("username").T.to_dict()
            else:
                os.remove(USER_FILE)  # Reset corrupted file
                return {}
        else:
            return {}
    return {}

def save_user(username, password):
    df = pd.DataFrame([[username, hash_password(password)]], columns=["username", "password"])
    if os.path.exists(USER_FILE):
        df.to_csv(USER_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(USER_FILE, index=False)

# ========== Predefined Admin Credentials ==========
ADMINS = {
    "admin": {"password": hash_password("admin123"), "role": "Admin"}
}

# ========== Main Login/Signup UI Handler ==========
def auth_ui():
    users = load_users()

    st.sidebar.title("🔐 Authentication")
    tab = st.sidebar.radio("Select Option", ["Sign In", "Sign Up"])

    if tab == "Sign In":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            if username in ADMINS and verify_password(ADMINS[username]['password'], password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = ADMINS[username]['role']
                st.success(f"Welcome Admin {username}!")
                st.rerun()

            elif username in users and verify_password(users[username]['password'], password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "User"
                st.success(f"Welcome {username}!")
                st.rerun()

            else:
                st.error("Invalid credentials.")

    elif tab == "Sign Up":
        new_user = st.sidebar.text_input("Choose Username")
        new_pass = st.sidebar.text_input("Choose Password", type="password")

        if st.sidebar.button("Register"):
            if new_user in users or new_user in ADMINS:
                st.warning("Username already taken.")
            elif not new_user or not new_pass:
                st.warning("Please fill all fields.")
            else:
                save_user(new_user, new_pass)
                st.success("Registration successful! Please sign in.")

    st.stop()
