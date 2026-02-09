import streamlit as st
import csv
from datetime import datetime
import pandas as pd
import json

TEMPLATE_FILE = "templates.json"


# =========================================================
# LOAD TEMPLATES FROM JSON (SAFE)
# =========================================================
try:
    with open(TEMPLATE_FILE, "r") as f:
        st.session_state.templates = json.load(f)
except:
    if "templates" not in st.session_state:
        st.session_state.templates = {
            "Default Template": {
                "active": True,
                "parameters": []
            }
        }

if "current_template" not in st.session_state:
    st.session_state.current_template = list(st.session_state.templates.keys())[0]


# =========================================================
# PAGE HEADER
# =========================================================
st.title("AI Call Audit – Phase 1 POC")

# ---------- SIDEBAR SAVE ----------
with st.sidebar:
    st.subheader("Storage")
    if st.button("💾 Save Templates"):
        with open(TEMPLATE_FILE, "w") as f:
            json.dump(st.session_state.templates, f, indent=2)
        st.success("Templates saved.")


st.divider()
st.subheader("Audit Parameter Designer")


# =========================================================
# TEMPLATE CONTROLS
# =========================================================
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

template_names = list(st.session_state.templates.keys())

with col1:
    selected_template = st.selectbox(
        "Template",
        template_names,
        index=template_names.index(st.session_state.current_template)
        if st.session_state.current_template in template_names else 0
    )
    st.session_state.current_template = selected_template

with col2:
    new_name = st.text_input("Rename", value=selected_template, label_visibility="collapsed")
    if new_name != selected_template and new_name not in st.session_state.templates:
        st.session_state.templates[new_name] = st.session_state.templates.pop(selected_template)
        st.session_state.current_template = new_name
        st.rerun()

with col3:
    if st.button("➕"):
        st.session_state.templates["New Template"] = {"active": False, "parameters": []}
        st.session_state.current_template = "New Template"
        st.rerun()

with col4:
    if st.button("🗑") and len(st.session_state.templates) > 1:
        del st.session_state.templates[st.session_state.current_template]
        st.session_state.current_template = list(st.session_state.templates.keys())[0]
        st.rerun()


# =========================================================
# TEMPLATE ACTIVE FLAG
# =========================================================
template_data = st.session_state.templates[st.session_state.current_template]
template_data["active"] = st.checkbox("Template Active", value=template_data.get("active", True))


# =========================================================
# ENSURE AT LEAST ONE PARAMETER
# =========================================================
if len(template_data["parameters"]) == 0:
    template_data["parameters"].append({
        "title": "Parameter",
        "type": "Regular",
        "fatal": False,
        "score": 0,
        "prompts": [""],
        "logic": []
    })


# =========================================================
# PARAMETER CARDS (COMPACT HORIZONTAL)
# =========================================================
st.divider()

for idx, param in enumerate(template_data["parameters"]):

    # ---------- HEADER ----------
    col_h1, col_h2 = st.columns([6, 1])

    with col_h1:
        param["title"] = st.text_input(
            "Title",
            value=param["title"],
            key=f"title_{selected_template}_{idx}",
            label_visibility="collapsed",
            placeholder="Parameter title"
        )

    with col_h2:
        if st.button("🗑", key=f"del_param_{idx}") and len(template_data["parameters"]) > 1:
            template_data["parameters"].pop(idx)
            st.rerun()

    # ---------- TYPE / FATAL / SCORE ----------
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        param["type"] = st.selectbox(
            "Type",
            ["Regular", "Conditional", "Flag"],
            index=["Regular", "Conditional", "Flag"].index(param["type"]),
            key=f"type_{selected_template}_{idx}",
            label_visibility="collapsed"
        )

    with col2:
        param["fatal"] = st.checkbox(
            "Fatal",
            value=param["fatal"],
            key=f"fatal_{selected_template}_{idx}"
        )

    with col3:
        param["score"] = st.number_input(
            "Score",
            min_value=0,
            step=1,
            value=param["score"],
            key=f"score_{selected_template}_{idx}",
            label_visibility="collapsed"
        )

    # ---------- PROMPTS ----------
    prompt_cols = st.columns(len(param["prompts"]) * 2 - 1)
    col_i = 0

    # titles of previous params (for conditional)
    param_titles = [p["title"] for p in template_data["parameters"][:idx]]

    for p_idx in range(len(param["prompts"])):

        with prompt_cols[col_i]:

            # ----- INPUT TYPE -----
            if param["type"] == "Conditional" and param_titles:
                param["prompts"][p_idx] = st.selectbox(
                    "Cond",
                    param_titles,
                    index=param_titles.index(param["prompts"][p_idx])
                    if param["prompts"][p_idx] in param_titles else 0,
                    key=f"prompt_{selected_template}_{idx}_{p_idx}",
                    label_visibility="collapsed"
                )
            else:
                param["prompts"][p_idx] = st.text_input(
                    "Prompt",
                    value=param["prompts"][p_idx],
                    key=f"prompt_{selected_template}_{idx}_{p_idx}",
                    label_visibility="collapsed"
                )

            c1, c2 = st.columns(2)

            with c1:
                if st.button("➕", key=f"add_prompt_{idx}_{p_idx}"):
                    param["prompts"].insert(p_idx + 1, "")
                    param["logic"].insert(p_idx, "AND")
                    st.rerun()

            with c2:
                if st.button("🗑", key=f"del_prompt_{idx}_{p_idx}") and len(param["prompts"]) > 1:
                    param["prompts"].pop(p_idx)
                    if p_idx < len(param["logic"]):
                        param["logic"].pop(p_idx)
                    st.rerun()

        col_i += 1

        if p_idx < len(param["prompts"]) - 1:
            with prompt_cols[col_i]:
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


# =========================================================
# TRANSCRIPT + RUN
# =========================================================
transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)
run = col1.button("Run Audit")
reset = col2.button("Reset")


# =========================================================
# RUN (PHASE-1 DUMMY ENGINE)
# =========================================================
if run:

    if transcript.strip() == "":
        st.error("Paste transcript first.")
        st.stop()

    total_score = 0

    for template in st.session_state.templates.values():
        if not template.get("active"):
            continue

        for param in template["parameters"]:
            total_score += param["score"]

    st.subheader(f"Final Score (Dummy): {total_score}")


# =========================================================
# RESET + LOG
# =========================================================
if reset:
    with open("audit_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), transcript])
    st.rerun()


# =========================================================
# HISTORY
# =========================================================
st.subheader("Saved Audit History")

try:
    df = pd.read_csv("audit_log.csv")
    st.dataframe(df)
except FileNotFoundError:
    st.write("No audits saved yet.")
