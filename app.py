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
# GLOBAL CLASSY CSS (ONLY VISUAL)
# =========================================================
st.markdown("""
<style>

/* ===== TEXT COLORS ===== */
.beige-text { color: #f5ebe0 !important; }
.burgundy-text { color: #6b2737 !important; }

/* ===== INPUT SIZING ===== */
.template-dd select { max-width: 33% !important; color: #6b2737 !important; }
.param-title input { max-width: 33% !important; background: white !important; color: #6b2737 !important; }
.param-type select { max-width: 33% !important; color: #6b2737 !important; }
.score-box input { max-width: 16% !important; background: white !important; }
.prompt-box textarea { max-width: 16% !important; background: white !important; }
.transcript-box textarea { max-width: 25% !important; height: 200px !important; color: black !important; }

/* ===== BUTTON SIZE ===== */
.run-btn button, .reset-btn button {
    width: 200px !important;
    height: 60px !important;
    font-size: 18px !important;
}

/* ===== RESULT TABLE ===== */
table { color: #f5ebe0 !important; }
.yes { color: #4ade80 !important; font-weight: bold; }
.no { color: #facc15 !important; font-weight: bold; }
.fatal { color: #f87171 !important; font-weight: bold; }

</style>
""", unsafe_allow_html=True)

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
col_dd, col_edit, col_add, col_del = st.columns([3, 1, 1, 1])

template_names = list(st.session_state.templates.keys())

with col_dd:
    st.markdown('<div class="template-dd">', unsafe_allow_html=True)
    selected_template = st.selectbox(
        "Template",
        template_names,
        index=template_names.index(st.session_state.current_template)
        if st.session_state.current_template in template_names else 0,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.current_template = selected_template

if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = False

with col_edit:
    if st.button("✏️"):
        st.session_state.rename_mode = not st.session_state.rename_mode

if st.session_state.rename_mode:
    new_name = st.text_input("Rename Template", value=st.session_state.current_template)
    if new_name and new_name != st.session_state.current_template:
        st.session_state.templates[new_name] = st.session_state.templates.pop(
            st.session_state.current_template
        )
        st.session_state.current_template = new_name
        st.session_state.rename_mode = False
        st.rerun()

with col_add:
    if st.button("➕"):
        st.session_state.templates["New Template"] = {"active": False, "parameters": []}
        st.session_state.current_template = "New Template"
        st.rerun()

with col_del:
    if st.button("🗑"):
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
st.markdown('<span class="beige-text">Template Active</span>', unsafe_allow_html=True)
template_data["active"] = st.checkbox("", value=template_data.get("active", True))

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

    st.markdown("---")

    st.markdown('<div class="param-title">', unsafe_allow_html=True)
    param["title"] = st.text_input("", value=param["title"], key=f"title_{idx}")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown('<div class="param-type">', unsafe_allow_html=True)
        param["type"] = st.selectbox("", ["Regular", "Conditional", "Flag"],
                                     index=["Regular", "Conditional", "Flag"].index(param["type"]),
                                     key=f"type_{idx}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<span class="beige-text">Fatal</span>', unsafe_allow_html=True)
        param["fatal"] = st.checkbox("", value=param["fatal"], key=f"fatal_{idx}")

    with col3:
        st.markdown('<div class="score-box">', unsafe_allow_html=True)
        param["score"] = st.number_input("", min_value=0, step=1,
                                         value=param["score"], key=f"score_{idx}")
        st.markdown('</div>', unsafe_allow_html=True)

    # PROMPTS
    for p_idx in range(len(param["prompts"])):
        st.markdown('<div class="prompt-box">', unsafe_allow_html=True)
        param["prompts"][p_idx] = st.text_area("", value=param["prompts"][p_idx],
                                               key=f"prompt_{idx}_{p_idx}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ADD / DELETE PARAMETER
    col_add, col_del = st.columns(2)
    with col_add:
        if st.button("➕ Add Parameter", key=f"add_param_{idx}"):
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
        if st.button("🗑 Delete Parameter", key=f"delete_param_{idx}") and len(template_data["parameters"]) > 1:
            template_data["parameters"].pop(idx)
            st.rerun()

# =========================================================
# TRANSCRIPT + BUTTONS (RIGHT SIDE)
# =========================================================
col_t, col_btn = st.columns([1, 1])

with col_t:
    st.markdown('<div class="transcript-box">', unsafe_allow_html=True)
    transcript = st.text_area("Paste transcript here")
    st.markdown('</div>', unsafe_allow_html=True)

with col_btn:
    st.markdown('<div class="run-btn">', unsafe_allow_html=True)
    run = st.button(">> Run Audit")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    reset = st.button("🔄 Reset")
    st.markdown('</div>', unsafe_allow_html=True)

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
                found = prompt and prompt.lower() in transcript.lower()
                checks.append(found)
                if found:
                    matches.append(prompt)

            param_yes = all(checks) if checks else False

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
