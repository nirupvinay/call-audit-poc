import streamlit as st
import csv
from datetime import datetime
import pandas as pd

# ---------- TEMPLATE DATA ----------
if "templates" not in st.session_state:
    st.session_state.templates = {
        "Default Template": {
            "parameters": []
        }
    }

if "current_template" not in st.session_state:
    st.session_state.current_template = "Default Template"


st.title("AI Call Audit – Phase 1 POC")

st.divider()
st.subheader("Audit Parameter Designer")

# ---------- TEMPLATE SELECT ----------
template_names = list(st.session_state.templates.keys())

selected_template = st.selectbox(
    "Select Template",
    template_names,
    index=template_names.index(st.session_state.current_template)
)

st.session_state.current_template = selected_template

# ---------- RENAME ----------
new_name = st.text_input("Rename current template", value=selected_template)

if new_name != selected_template and new_name not in st.session_state.templates:
    st.session_state.templates[new_name] = st.session_state.templates.pop(selected_template)
    st.session_state.current_template = new_name
    st.rerun()

# ---------- NEW TEMPLATE ----------
if st.button("➕ New Template"):
    st.session_state.templates["New Template"] = {"parameters": []}
    st.session_state.current_template = "New Template"
    st.rerun()

# ---------- DELETE TEMPLATE ----------
if st.button("🗑 Delete Template") and len(st.session_state.templates) > 1:
    del st.session_state.templates[st.session_state.current_template]
    st.session_state.current_template = list(st.session_state.templates.keys())[0]
    st.rerun()


# ---------- PARAMETERS ----------
st.markdown("### Parameters")

template_data = st.session_state.templates[st.session_state.current_template]

# ensure at least one parameter
if len(template_data["parameters"]) == 0:
    template_data["parameters"].append({
        "title": "Parameter",
        "type": "Regular",
        "fatal": False,
        "score": 0,
        "prompts": [""],
        "logic": []
    })


# ---------- PARAMETER LOOP ----------
for idx, param in enumerate(template_data["parameters"]):

    st.markdown("---")  # clear visual separation

    # ---------- HEADER ----------
    col_h1, col_h2 = st.columns([5, 1])

    with col_h1:
        param["title"] = st.text_input(
            "Parameter Title",
            value=param["title"],
            key=f"title_{selected_template}_{idx}"
        )

    with col_h2:
        if st.button("🗑", key=f"del_param_{idx}") and len(template_data["parameters"]) > 1:
            template_data["parameters"].pop(idx)
            st.rerun()

    # ---------- TYPE ----------
    param["type"] = st.selectbox(
        "Parameter Type",
        ["Regular", "Conditional", "Flag"],
        index=["Regular", "Conditional", "Flag"].index(param["type"]),
        key=f"type_{selected_template}_{idx}"
    )

    # ---------- FATAL + SCORE ----------
    col1, col2 = st.columns(2)

    with col1:
        param["fatal"] = st.checkbox(
            "Fatal",
            value=param["fatal"],
            key=f"fatal_{selected_template}_{idx}"
        )

    with col2:
        param["score"] = st.number_input(
            "Score",
            min_value=0,
            step=1,
            value=param["score"],
            key=f"score_{selected_template}_{idx}"
        )

    # ---------- PROMPTS ----------
    st.markdown("**Prompts**")

    # horizontal prompt chain
    cols = st.columns(len(param["prompts"]) * 2 - 1)

    col_i = 0

    for p_idx in range(len(param["prompts"])):

        # prompt box
        with cols[col_i]:
            param["prompts"][p_idx] = st.text_input(
                f"Prompt {p_idx+1}",
                value=param["prompts"][p_idx],
                key=f"prompt_{selected_template}_{idx}_{p_idx}"
            )

            c1, c2 = st.columns(2)

            # add prompt
            with c1:
                if st.button("➕", key=f"add_prompt_{idx}_{p_idx}"):
                    param["prompts"].insert(p_idx + 1, "")
                    param["logic"].insert(p_idx, "AND")
                    st.rerun()

            # delete prompt
            with c2:
                if st.button("🗑", key=f"del_prompt_{idx}_{p_idx}") and len(param["prompts"]) > 1:
                    param["prompts"].pop(p_idx)
                    if p_idx < len(param["logic"]):
                        param["logic"].pop(p_idx)
                    st.rerun()

        col_i += 1

        # AND / OR selector
        if p_idx < len(param["prompts"]) - 1:
            with cols[col_i]:
                param["logic"][p_idx] = st.selectbox(
                    "",
                    ["AND", "OR"],
                    index=["AND", "OR"].index(param["logic"][p_idx]) if p_idx < len(param["logic"]) else 0,
                    key=f"logic_{selected_template}_{idx}_{p_idx}"
                )
            col_i += 1

    # ---------- ADD PARAMETER BELOW ----------
    if st.button("➕ Add Parameter Below", key=f"add_param_{idx}"):
        template_data["parameters"].insert(idx + 1, {
            "title": "Parameter",
            "type": "Regular",
            "fatal": False,
            "score": 0,
            "prompts": [""],
            "logic": []
        })
        st.rerun()


st.divider()

# ---------- TRANSCRIPT ----------
transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)
run = col1.button("Run Audit")
reset = col2.button("Reset")

# ---------- RUN (still dummy Phase-1) ----------
if run:
    if transcript.strip() == "":
        st.error("Please paste a transcript before running the audit.")
        st.stop()

    total_score = 0

    for param in template_data["parameters"]:
        total_score += param["score"]

    st.subheader(f"Final Score (Dummy): {total_score}")

# ---------- RESET ----------
if reset:
    with open("audit_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), transcript])

    st.rerun()

# ---------- HISTORY ----------
st.subheader("Saved Audit History")

try:
    df = pd.read_csv("audit_log.csv")
    st.dataframe(df)
except FileNotFoundError:
    st.write("No audits saved yet.")
