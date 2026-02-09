import streamlit as st
import csv
from datetime import datetime
import pandas as pd
import json

# =========================================================
# SESSION STRUCTURE
# =========================================================
TEMPLATE_FILE = "templates.json"

if "templates" not in st.session_state:
    try:
        with open(TEMPLATE_FILE, "r") as f:
            st.session_state.templates = json.load(f)
    except:
        st.session_state.templates = {
            "Default Template": {
                "active": True,
                "parameters": []
            }
        }

if "current_template" not in st.session_state:
    st.session_state.current_template = (
        list(st.session_state.templates.keys())[0]
        if st.session_state.templates else None
    )

# =========================================================
# PAGE HEADER
# =========================================================
st.title("AI Call Audit – Phase 1 POC")

if st.button("💾 Save Templates"):
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(st.session_state.templates, f, indent=2)
    st.success("Templates saved.")

st.divider()
st.subheader("Audit Parameter Designer")

# =========================================================
# TEMPLATE TOOLBAR
# =========================================================
col_dd, col_edit, col_add, col_del = st.columns([6, 1, 1, 1])

template_names = list(st.session_state.templates.keys())

with col_dd:
    selected_template = st.selectbox(
        "Template",
        template_names,
        index=template_names.index(st.session_state.current_template)
        if st.session_state.current_template in template_names else 0,
        label_visibility="collapsed"
    )
    st.session_state.current_template = selected_template

if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = False

with col_edit:
    if st.button("✏️", use_container_width=True):
        st.session_state.rename_mode = not st.session_state.rename_mode

if st.session_state.rename_mode:
    new_name = st.text_input(
        "Rename Template",
        value=st.session_state.current_template,
        key="rename_input"
    )
    if new_name and new_name != st.session_state.current_template:
        st.session_state.templates[new_name] = st.session_state.templates.pop(
            st.session_state.current_template
        )
        st.session_state.current_template = new_name
        st.session_state.rename_mode = False
        st.rerun()

with col_add:
    if st.button("➕", use_container_width=True):
        st.session_state.templates["New Template"] = {"active": False, "parameters": []}
        st.session_state.current_template = "New Template"
        st.rerun()

with col_del:
    if st.button("🗑", use_container_width=True):
        if st.session_state.current_template in st.session_state.templates:
            del st.session_state.templates[st.session_state.current_template]
        st.session_state.current_template = (
            list(st.session_state.templates.keys())[0]
            if st.session_state.templates else None
        )
        st.rerun()

# =========================================================
# STOP IF NO TEMPLATE
# =========================================================
if not st.session_state.templates:
    st.info("No templates available.")
    if st.button("➕ Add New Template"):
        st.session_state.templates["New Template"] = {"active": True, "parameters": []}
        st.session_state.current_template = "New Template"
        st.rerun()
    st.stop()

# =========================================================
# TEMPLATE ACTIVE FLAG
# =========================================================
template_data = st.session_state.templates[st.session_state.current_template]
template_data["active"] = st.checkbox("Template Active", value=template_data.get("active", True))

# =========================================================
# ENSURE PARAMETER EXISTS
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
# PARAMETERS UI
# =========================================================
st.divider()

for idx, param in enumerate(template_data["parameters"]):

    st.markdown("---")  # simple clean separator instead of container

    # TITLE
    param["title"] = st.text_input(
        "Title",
        value=param["title"],
        key=f"title_{selected_template}_{idx}",
        label_visibility="collapsed",
        placeholder="Parameter title"
    )

    # TYPE / FATAL / SCORE
    col1, col2, col3 = st.columns([3, 1, 1])

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

    # ---------- HORIZONTAL PROMPTS ----------
    total_cols = len(param["prompts"]) * 3 - 1
    cols = st.columns(total_cols)

    c = 0
    for p_idx in range(len(param["prompts"])):

        # PROMPT INPUT
        with cols[c]:
            param_titles = [p["title"] for p in template_data["parameters"][:idx]]

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
                param["prompts"][p_idx] = st.text_area(
                    "Prompt",
                    value=param["prompts"][p_idx],
                    key=f"prompt_{selected_template}_{idx}_{p_idx}",
                    height=70,
                    label_visibility="collapsed",
                    placeholder="Enter Prompt"
                )

        c += 1

        # DELETE BUTTON (only show for non-last prompts OR if more than 1 prompt)
        with cols[c]:
            st.markdown(
                """
                <style>
                div[data-testid="stButton"] > button {
                    height: 34px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            # Show delete button for all prompts if more than 1 exists
            if len(param["prompts"]) > 1:
                if st.button(
                    "🗑",
                    key=f"del_prompt_{selected_template}_{idx}_{p_idx}",
                    use_container_width=True
                ):
                    param["prompts"].pop(p_idx)
                    if p_idx < len(param["logic"]):
                        param["logic"].pop(p_idx)
                    st.rerun()
            
            # Show ADD button ONLY on the last prompt
            if p_idx == len(param["prompts"]) - 1:
                if st.button(
                    "➕",
                    key=f"add_prompt_{selected_template}_{idx}_{p_idx}",
                    use_container_width=True
                ):
                    param["prompts"].append("")
                    param["logic"].append("AND")
                    st.rerun()
        
        c += 1
        
        # AND / OR (show for all prompts EXCEPT the last one)
        if p_idx < len(param["prompts"]) - 1:
            with cols[c]:
                param["logic"][p_idx] = st.selectbox(
                    "",
                    ["AND", "OR"],
                    index=["AND", "OR"].index(param["logic"][p_idx])
                    if p_idx < len(param["logic"]) else 0,
                    key=f"logic_{selected_template}_{idx}_{p_idx}"
                )
            c += 1

    # ADD / DELETE PARAMETER
    col_add, col_del = st.columns(2)

    with col_add:
        if st.button("➕ Add Parameter", key=f"add_param_{idx}", use_container_width=True):
            template_data["parameters"].insert(idx + 1, {
                "title": "Parameter",
                "type": "Regular",
                "fatal": False,
                "score": 0,
                "prompts": [""],
                "logic": []
            })
            st.rerun()

    with col_del:
        if st.button("🗑 Delete Parameter", key=f"delete_param_{idx}", use_container_width=True) and len(template_data["parameters"]) > 1:
            template_data["parameters"].pop(idx)
            st.rerun()

# =========================================================
# TRANSCRIPT + RUN
# =========================================================
transcript = st.text_area("Paste transcript here")

col1, col2 = st.columns(2)
run = col1.button("Run Audit")
reset = col2.button("Reset")

# =========================================================
# RULE ENGINE (UNCHANGED)
# =========================================================
if run:

    if transcript.strip() == "":
        st.error("Paste transcript first.")
        st.stop()

    for template_name, template in st.session_state.templates.items():

        if not template.get("active"):
            continue

        results = []
        fatal_triggered = False
        template_total = 0

        for param in template["parameters"]:

            matches = []
            checks = []

            for prompt in param["prompts"]:

                if param["type"] == "Conditional":
                    found = any(
                        r["Parameter"] == prompt and r["Result"] == "YES"
                        for r in results
                    )
                else:
                    found = prompt and prompt.lower() in transcript.lower()

                checks.append(found)

                if found:
                    matches.append(prompt)

            if not checks:
                param_yes = False
            else:
                result = checks[0]
                for i, logic in enumerate(param["logic"]):
                    if i + 1 >= len(checks):
                        break
                    result = result and checks[i + 1] if logic == "AND" else result or checks[i + 1]
                param_yes = result

            if param_yes:
                final_result = "YES"
                score = param["score"]
            else:
                if param["fatal"]:
                    final_result = "FATAL"
                    score = 0
                    fatal_triggered = True
                else:
                    final_result = "NO"
                    score = 0

            template_total += score
            evidence = ", ".join(matches) if matches else "—"

            results.append({
                "Parameter": param["title"],
                "Result": final_result,
                "Score": score,
                "Evidence": evidence
            })

        if fatal_triggered:
            template_total = 0

        if results:
            st.subheader(f"Template: {template_name}")
            df = pd.DataFrame(results)
            st.table(df)
            st.markdown(f"**Total Score: {template_total}**")

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
