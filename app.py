import streamlit as st

pwd = st.text_input("Enter password to open app", type="password")

if pwd != st.secrets["APP_PASSWORD"]:
    st.stop()

from audit_app.ui import run_app


if __name__ == "__main__":
    run_app()
