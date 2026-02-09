import streamlit as st
import csv
from datetime import datetime
import pandas as pd

# ---------- TEMPLATE DATA STRUCTURE ----------
if "templates" not in st.session_state:
    st.session_state.templates = {
        "Default Template": {
            "active": True,
            "parameters": []
        }
    }

if "current_template" not in st.session_state:
    st.session_state.current_template = "Default Template"


st.title("AI Call Audit – Phase 1 POC")

st.divider()
st.subheader("Audit Parameter Designer (Phase-1 UI)")
# ---------- TEMPLATE SELECTOR ----------
template_names = list(st.session_state.templates.keys())

selected_template = st.selectbox(
    "Select Template",
    template_names,
    index=template_names.index(st.session_state.current_template)
)

st.session_state.current_template = selected_template
new_name = st.text_input("Rename current template", value=selected_template)
if new_name != selected_template and new_name not in st.session_state.templates:
    st.session_state.templates[new_name] = st.session_state.templates.pop(selected_template)
    st.session_state.current_template = new_name
    st.rerun()

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

# ---------- SESSION STATE ----------
if "p1_prompts" not in st.session_state:
    st.session_state.p1_prompts = [""]

if "p1_logic" not in st.session_state:
    st.session_state.p1_logic = []

# ---------- HORIZONTAL PROMPTS ----------
if "p1_prompts" not in st.session_state:
    st.session_state.p1_prompts = [""]

if "p1_logic" not in st.session_state:
    st.session_state.p1_logic = []

cols = st.columns(len(st.session_state.p1_prompts) * 2 - 1)

col_index = 0

for i in range(len(st.session_state.p1_prompts)):
    with cols[col_index]:
        st.session_state.p1_prompts[i] = st.text_input(
            f"Prompt {i+1}",
            value=st.session_state.p1_prompts[i],
            key=f"p1_prompt_{i}"
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("➕", key=f"add_{i}"):
                st.session_state.p1_prompts.insert(i + 1, "")
                st.session_state.p1_logic.insert(i, "AND")
                st.rerun()

        with c2:
            if st.button("🗑", key=f"del_{i}") and len(st.session_state.p1_prompts) > 1:
                st.session_state.p1_prompts.pop(i)
                if i < len(st.session_state.p1_logic):
                    st.session_state.p1_logic.pop(i)
                st.rerun()

    col_index += 1

    if i < len(st.session_state.p1_prompts) - 1:
        with cols[col_index]:
            st.session_state.p1_logic[i] = st.selectbox(
                " ",
                ["AND", "OR"],
                key=f"logic_{i}"
            )
        col_index += 1

st.divider()


# ---------- TRANSCRIPT ----------
transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)
run = col1.button("Run Audit")
reset = col2.button("Reset")

# ---------- RUN AUDIT ----------
if run:
    if transcript.strip() == "":
        st.error("Please paste a transcript before running the audit.")
        st.stop()

    st.subheader("Transcript Preview")
    st.write(transcript)

    st.subheader("Audit Result (From Parameter 1)")

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

# ---------- RESET ----------
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

# ---------- HISTORY ----------
st.subheader("Saved Audit History")

try:
    df = pd.read_csv("audit_log.csv")
    st.dataframe(df)
except FileNotFoundError:
    st.write("No audits saved yet.")
