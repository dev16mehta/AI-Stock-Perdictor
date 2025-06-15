import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import re
import time

# Configure Streamlit page settings
st.set_page_config(
    page_title="Login | QuantView AI", 
    page_icon="🔐",
    layout="centered"
)

# Initialise Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Handle both local development and deployed environments
        if 'firebase_service_account' in st.secrets:
            cred_dict = dict(st.secrets["firebase_service_account"])
        else:
            cred_dict = "firebase_service_account.json"
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase initialization failed. Ensure your secrets are configured correctly. Error: {e}")
        st.stop()

# Initialise session state variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'email' not in st.session_state:
    st.session_state['email'] = ''
if 'uid' not in st.session_state:
    st.session_state['uid'] = ''

# Custom CSS for improved UI layout and styling
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

def is_valid_email(email):
    """Validate email format using regex pattern."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def navigate_to(page):
    """Update the current page in session state and trigger a rerun."""
    st.session_state.page = page
    st.rerun()

def page_login():
    """Render the login page with email and password inputs."""
    st.title("🔐 QuantView AI")
    
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
                        # Note: Password verification is simplified for demo purposes
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

def page_signup():
    """Render the signup page with email and password registration form."""
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

# Main application routing logic
if st.session_state.get('logged_in', False):
    st.switch_page("pages/1_Analyser.py")
else:
    if st.session_state.page == 'login':
        page_login()
    elif st.session_state.page == 'signup':
        page_signup()
    else:
        page_login() # Default to login page
