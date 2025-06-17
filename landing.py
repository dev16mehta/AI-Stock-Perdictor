import streamlit as st
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="QuantView AI",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Asset Loading ---
def load_css(file_path):
    """Loads a CSS file and returns its content."""
    with open(file_path) as f:
        return f.read()

# Inject custom CSS
css = load_css("styles.css")
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# --- SVG Icons ---
SVG_ICONS = {
    "analysis": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 16.5L12 9L16 12L21 8.5" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M4 12L12 4.5L16 7.5L21 4" stroke="#5B86E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M18 5H21V2" stroke="#5B86E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M18 9.5H21V6.5" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "insights": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M9 12C9 13.3807 10.3431 14.5 12 14.5C13.6569 14.5 15 13.3807 15 12C15 10.6193 13.6569 9.5 12 9.5C10.3431 9.5 9 10.6193 9 12Z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke="#8A2BE2"/>
    <path d="M2.45825 12C3.73252 7.94288 7.52281 5 12 5C16.4772 5 20.2675 7.94288 21.5418 12C20.2675 16.0571 16.4772 19 12 19C7.52281 19 3.73252 16.0571 2.45825 12Z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke="#8A2BE2"/>
    </svg>
    """,
    "charting": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 17L9 11L13 15L21 7" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M14 7H21V14" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "screener": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="11" cy="11" r="8" stroke="#5B86E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M21 21L16.65 16.65" stroke="#5B86E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M11 8V14" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M8 11H14" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "portfolio": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="#8A2BE2" stroke-width="2" stroke-miterlimit="10"/>
    <path d="M12 3V12C12 12 15.5 12.5 17 15" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,
    "secure": """
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 11L12 16" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M12 8.00001V8.01001" stroke="#36D1DC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#5B86E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """
}

# --- Background ---
st.markdown(
    """
    <div class="background-animation">
        <div class="shape shape1"></div>
        <div class="shape shape2"></div>
        <div class="shape shape3"></div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Two-Column Hero Layout ---
with st.container():
    col1, col2 = st.columns(spec=[1.2, 1], gap="large")

    with col1:
        st.markdown(
            """
            <div class="hero-text">
                <h1 class='hero-title'>Navigate the Market with AI-Powered Clarity</h1>
                <p class='hero-subtitle'>QuantView AI combines real-time data, news sentiment, and advanced AI to give you a complete picture of the stocks you care about. Move beyond the noise and make data-driven decisions.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Get Started For Free", type="primary"):
            st.switch_page("pages/Login.py")

    with col2:
        st.markdown(
            """
            <div class="image-showcase-container">
            """,
            unsafe_allow_html=True
        )
        st.image("assets/hero-image1.png", use_container_width=True)
        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# --- Features Section ---
st.markdown("<h2 class='features-title'>Everything You Need to Invest with Confidence</h2>", unsafe_allow_html=True)

def feature_card(icon, title, text):
    return f"""
    <div class="feature-card">
        <div class="icon-container">{icon}</div>
        <h3>{title}</h3>
        <p>{text}</p>
    </div>
    """

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(feature_card(SVG_ICONS["analysis"], "Side-by-Side Analysis", "Compare performance, financials, and news sentiment for multiple stocks on one screen."), unsafe_allow_html=True)
    st.markdown(feature_card(SVG_ICONS["screener"], "AI-Powered Stock Screener", "Use natural language to discover new investment opportunities based on your criteria."), unsafe_allow_html=True)

with c2:
    st.markdown(feature_card(SVG_ICONS["charting"], "Advanced Charting & Prediction", "Use technical indicators and AI-powered price forecasts to inform your strategy."), unsafe_allow_html=True)
    st.markdown(feature_card(SVG_ICONS["portfolio"], "Portfolio & Watchlist", "Track your personal holdings with real-time profit/loss and monitor your favorite stocks."), unsafe_allow_html=True)

with c3:
    st.markdown(feature_card(SVG_ICONS["insights"], "AI-Generated Insights", "Get simple summaries or expert 'Bull vs. Bear' cases, tailored to your investing style."), unsafe_allow_html=True)
    st.markdown(feature_card(SVG_ICONS["secure"], "Secure & Personalised", "Your data is your own. Secure login ensures your portfolio and watchlist remain private."), unsafe_allow_html=True)

st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)