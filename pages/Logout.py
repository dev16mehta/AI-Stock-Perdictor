import streamlit as st
import time

# --- This page is dedicated to performing the logout action ---

st.set_page_config(
    page_title="Logging Out...",
    page_icon="👋",
    layout="centered"
)

st.title("Logging Out...")
st.write("You are being securely logged out. Please wait.")
progress_bar = st.progress(0)

# Clear the user's session state
st.session_state.logged_in = False
st.session_state.email = ""
st.session_state.uid = ""

# Set a flag to show the logout message on the landing page
st.session_state.just_logged_out = True

# Animate the progress bar and add a short delay for UX
for i in range(100):
    time.sleep(0.01)
    progress_bar.progress(i + 1)

# Immediately switch to the landing page
st.switch_page("landing.py")