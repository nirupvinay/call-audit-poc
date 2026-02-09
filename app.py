import streamlit as st

st.title("AI Call Audit – Phase 1 POC")

transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)

run = col1.button("Run Audit")
reset = col2.button("Reset")

if run:
    st.subheader("Transcript Preview")
    st.write(transcript)

    st.subheader("Audit Result (Dummy)")

    greeting_score = 10
    pitch_score = 20

    st.write("Greeting given: YES | Score:", greeting_score)
    st.write("Pitch explained: YES | Score:", pitch_score)

    total_score = greeting_score + pitch_score

    st.subheader(f"Overall Score: {total_score}")

if reset:
    st.experimental_rerun()

