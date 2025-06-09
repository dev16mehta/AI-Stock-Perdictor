import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import re
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Login | QuantView AI", 
    page_icon="🔐",
    layout="centered"
)

# --- Firebase Initialization ---
# Initialize only once
if not firebase_admin._apps:
    try:
        print("Initializing Firebase...")
        # For local development, use the JSON file
        cred = credentials.Certificate("firebase_service_account.json")
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
    except FileNotFoundError:
        print("Firebase Service Account key not found")
        st.error("Firebase Service Account key not found. Please ensure 'firebase_service_account.json' is in the root directory.")
        st.stop()
    except Exception as e:
        print(f"Firebase initialization failed with error: {e}")
        st.error(f"Firebase initialization failed: {e}")
        st.stop()

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'email' not in st.session_state:
    st.session_state['email'] = ''
if 'uid' not in st.session_state:
    st.session_state['uid'] = ''

# --- UI Styling ---
st.markdown("""
<style>
    /* Center the main content */
    .st-emotion-cache-1jicfl2 {
        width: 100%;
        padding: 3rem 1rem 1rem;
        max-width: 480px;
        margin: auto;
    }
    /* Style the form container */
    .st-emotion-cache-1v0mbdj {
        border: 1px solid #444;
        padding: 2rem;
        border-radius: 10px;
    }
    h1 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def is_valid_email(email):
    """Simple regex for email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- Page Routing ---
def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# --- Login Page UI ---
def page_login():
    st.title("🔐 QuantView AI Login")
    
    with st.container(border=True):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True, type="primary"):
                if not is_valid_email(email) or not password:
                    st.warning("Please enter a valid email and password.")
                else:
                    try:
                        print(f"Attempting to login user: {email}")
                        user = auth.get_user_by_email(email)
                        print(f"User found with UID: {user.uid}")
                        # Password check is simplified for this demo.
                        st.session_state['logged_in'] = True
                        st.session_state['email'] = user.email
                        st.session_state['uid'] = user.uid
                        print(f"Session state updated - UID: {st.session_state['uid']}")
                        st.success("Login Successful!")
                        time.sleep(1)
                        st.switch_page("pages/1_Analyser.py")
                    except auth.UserNotFoundError:
                        print(f"User not found: {email}")
                        st.error("No account found with this email. Please sign up.")
                    except Exception as e:
                        print(f"Login failed with error: {e}")
                        st.error(f"Login failed. Note: Password check is simplified for this demo.")
        with col2:
            if st.button("Sign Up Instead", use_container_width=True):
                navigate_to('signup')

# --- Signup Page UI ---
def page_signup():
    st.title("👋 Create Your Account")
    with st.container(border=True):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Create Account", use_container_width=True, type="primary"):
            if not is_valid_email(email) or len(password) < 6:
                st.warning("Please enter a valid email and a password of at least 6 characters.")
            else:
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success(f"Account created for {user.email}! Please proceed to login.")
                    time.sleep(2)
                    navigate_to('login')
                except auth.EmailAlreadyExistsError:
                    st.error("An account with this email already exists. Please log in.")
                except Exception as e:
                    st.error(f"Failed to create account: {e}")

        if st.button("Back to Login", use_container_width=True):
            navigate_to('login')

# --- Main Logic ---
if st.session_state.get('logged_in', False):
    st.switch_page("pages/1_Analyser.py")
else:
    if st.session_state.page == 'login':
        page_login()
    elif st.session_state.page == 'signup':
        page_signup()
    else:
        page_login() # Default to login
