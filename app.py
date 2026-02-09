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

    greeting_yes = True
    greeting_score = 10
    greeting_fatal = False

    pitch_yes = False
    pitch_score = 20
    pitch_fatal = True

    st.write(f"Greeting given: {greeting_yes} | Score: {greeting_score} | Fatal: {greeting_fatal}")
    st.write(f"Pitch explained: {pitch_yes} | Score: {pitch_score} | Fatal: {pitch_fatal}")

    total_score = greeting_score + pitch_score

    if (not greeting_yes and greeting_fatal) or (not pitch_yes and pitch_fatal):
        total_score = 0

    st.subheader(f"Final Score: {total_score}")


    st.subheader(f"Overall Score: {total_score}")

    st.subheader("ZTP / Compliance Check (Dummy)")

    ztp_status = "UNCERTAIN"
    ztp_reason = "Customer consent unclear in transcript."

    st.write(f"Status: {ztp_status}")
    st.write(f"Reason: {ztp_reason}")

    if ztp_status == "UNCERTAIN":
        st.subheader("Escalation")
        st.write("Sent to flagship model for final compliance decision.")
        st.write("Final Verdict: CLEAR (Dummy)")
        st.write("Explanation: Consent implied during conversation.")

if reset:
    st.experimental_rerun()

