import streamlit as st

st.title("AI Call Audit – Phase 1 POC")

transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)

run = col1.button("Run Audit")
reset = col2.button("Reset")

if run:
    st.subheader("Transcript Preview")
    st.write(transcript)

if reset:
    st.experimental_rerun()
