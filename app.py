import streamlit as st

st.markdown("### 🔐 Khatabook AI Auditor Login")
pwd = st.text_input("Enter Password", type="password")

if pwd != st.secrets["APP_PASSWORD"]:
    st.stop()

from audit_app.ui import run_app


if __name__ == "__main__":
    run_app()
