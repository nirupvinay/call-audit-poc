import streamlit as st
import csv
from datetime import datetime
import streamlit as st

st.title("AI Call Audit – Phase 1 POC")

st.divider()
st.subheader("Audit Parameter Designer (Phase-1 UI)")
st.markdown("### Parameter 1")

param_title = st.text_input("Opening / Title", key="p1_title")

param_type = st.selectbox(
    "Parameter Type",
    ["Regular", "Conditional", "Flag"],
    key="p1_type"
)

colp1, colp2 = st.columns(2)

with colp1:
    p1_fatal = st.checkbox("Fatal", key="p1_fatal")

with colp2:
    p1_score = st.number_input("Score", min_value=0, step=1, key="p1_score")

st.markdown("**Prompt**")
p1_prompt = st.text_input("Enter prompt", key="p1_prompt")

st.divider()


transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)

run = col1.button("Run Audit")
reset = col2.button("Reset")

if run:
    st.subheader("Transcript Preview")
    st.write(transcript)

    st.subheader("Audit Result (From Parameter 1)")

    if transcript.strip() == "":
        p1_yes = False
    else:
        p1_yes = True

    st.write(f"{param_title or 'Parameter 1'}: {p1_yes} | Score: {p1_score} | Fatal: {p1_fatal}")

    total_score = p1_score if p1_yes else 0

    if not p1_yes and p1_fatal:
        total_score = 0

    st.subheader(f"Final Score: {total_score}")

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
    saved_score = total_score if 'total_score' in locals() else 0
    saved_ztp = ztp_status if 'ztp_status' in locals() else "NA"

    with open("audit_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(),
            transcript,
            saved_score,
            saved_ztp
        ])

    st.rerun()
    
import pandas as pd

st.subheader("Saved Audit History")

try:
    df = pd.read_csv("audit_log.csv")
    st.dataframe(df)
except FileNotFoundError:
    st.write("No audits saved yet.")


