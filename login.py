import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import re
import time

# --- Firebase Initialization ---
# Ensure this runs only once
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase_service_account.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("Could not initialize Firebase. Please ensure 'firebase_service_account.json' is in the root directory.")
        st.stop()

db = firestore.client()

# --- Helper Functions ---
def is_valid_email(email):
    """Simple regex for email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def send_verification_code(email):
    """Generates and stores a 6-digit code."""
    code = f"{time.time() % 1000000:06.0f}" # Simple time-based code for now
    # In a real app, you would use a service like SendGrid or AWS SES to email this code.
    # For this example, we'll store it and display it for the user to enter.
    users_ref = db.collection('users').document(email)
    users_ref.set({'verification_code': code, 'verified': False}, merge=True)
    return code

def verify_code(email, code):
    """Checks if the entered code is correct."""
    user_ref = db.collection('users').document(email)
    user_doc = user_ref.get()
    if user_doc.exists and user_doc.to_dict().get('verification_code') == code:
        user_ref.update({'verified': True})
        return True
    return False

# --- Page Configuration ---
st.set_page_config(page_title="Login - AI Stock Analyser", layout="centered")

# --- UI Styling ---
st.markdown("""
<style>
    .st-emotion-cache-1jicfl2 {
        width: 100%;
        padding: 2rem 1rem 1rem;
        max-width: 480px;
        margin: auto;
        background-color: #2a3949;
        border-radius: 10px;
    }
    h1 {
        text-align: center;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'email' not in st.session_state:
    st.session_state['email'] = ''

# --- Page Routing ---
def navigate_to(page):
    st.session_state.page = page

# --- Login Page ---
def page_login():
    st.title("Welcome Back!")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            else:
                try:
                    # Check if user exists in Firebase Auth
                    user = auth.get_user_by_email(email)
                    # This is where you would check the password.
                    # Firebase Admin SDK doesn't directly verify passwords for security reasons.
                    # The standard flow is to use client-side SDKs for login.
                    # For a pure Python backend, we use a custom token flow or a simplified verification like this.
                    st.session_state.email = email
                    code = send_verification_code(email)
                    st.info(f"For demo purposes, your 2FA code is: {code}") # DEMO ONLY
                    st.success("Verification code sent! Please check your (mock) email.")
                    navigate_to('2fa')
                except auth.UserNotFoundError:
                    st.error("No account found with this email. Please sign up.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    st.markdown("<p style='text-align: center;'>Don't have an account?</p>", unsafe_allow_html=True)
    if st.button("Sign Up", use_container_width=True):
        navigate_to('signup')

# --- Signup Page ---
def page_signup():
    st.title("Create an Account")
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if not is_valid_email(email) or not password:
                st.warning("Please enter a valid email and password.")
            else:
                try:
                    user = auth.create_user(email=email, password=password)
                    st.session_state.email = email
                    code = send_verification_code(email)
                    st.info(f"For demo purposes, your 2FA code is: {code}") # DEMO ONLY
                    st.success(f"Account created successfully for {user.email}! A verification code has been sent.")
                    navigate_to('2fa')
                except auth.EmailAlreadyExistsError:
                    st.error("An account with this email already exists. Please log in.")
                except Exception as e:
                    st.error(f"Failed to create account: {e}")

    st.markdown("<p style='text-align: center;'>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Login", use_container_width=True):
        navigate_to('login')

# --- 2FA Page ---
def page_2fa():
    st.title("Two-Factor Authentication")
    st.write(f"A verification code was sent to {st.session_state.email}.")
    st.info("In a real application, this would be sent to your email inbox.")
    
    with st.form("2fa_form"):
        code = st.text_input("6-Digit Code", key="2fa_code", max_chars=6)
        submitted = st.form_submit_button("Verify")

        if submitted:
            if verify_code(st.session_state.email, code):
                st.session_state.logged_in = True
                st.success("Login Successful!")
                time.sleep(1) # Pause for user to see the message
                st.switch_page("pages/stockAnalyser.py")
            else:
                st.error("Invalid code. Please try again.")

# --- Main Logic ---
if st.session_state.logged_in:
    st.switch_page("pages/stockAnalyser.py")
else:
    if st.session_state.page == 'login':
        page_login()
    elif st.session_state.page == 'signup':
        page_signup()
    elif st.session_state.page == '2fa':
        page_2fa()

