import streamlit as st

st.title("AI Call Audit – Phase 1 POC")

st.text_area("Paste transcript here")

col1, col2 = st.columns(2)

with col1:
    st.button("Run Audit")

with col2:
    st.button("Reset")
