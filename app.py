import streamlit as st

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Khatabook AI Auditor", layout="wide")

# ---------- GLOBAL STYLING (BURGUNDY THEME) ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #5a1f2b, #7a2d3a);
    color: #F5E6D3;
}

h1, h2, h3, h4, h5, h6, label, p {
    color: #F5E6D3 !important;
}

/* Center login container */
.login-card {
    max-width: 420px;
    margin: 140px auto;
    padding: 40px 35px;
    border-radius: 18px;
    background: linear-gradient(145deg, #6b2737, #8b3a4a);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    text-align: center;
}
/* Login button styling */
.stButton > button {
    background: #F5E6D3;
    color: #000000;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    height: 42px;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #F5E6A8, #D4AF37);
    color: #5a1f2b;
}
</style>
""", unsafe_allow_html=True)


# ---------- LOGIN STATE ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# ---------- LOGIN SCREEN ----------
if not st.session_state.authenticated:

    st.markdown("""
    <div class="login-card">
        <h2>🔐 Khatabook AI Auditor</h2>
        <p>Authorized access only</p>
    </div>
    """, unsafe_allow_html=True)

    pwd = st.text_input("Enter Password", type="password")

    if st.button("Login", use_container_width=True):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()  # ⛔ BLOCK FULL APP BEFORE LOGIN


# ---------- MAIN APP LOADS AFTER LOGIN ----------
from audit_app.ui import run_app

run_app()
