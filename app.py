import streamlit as st
import csv
from datetime import datetime
import pandas as pd
import json
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "transcript_key" not in st.session_state:
    st.session_state["transcript_key"] = "transcript_0"

if "has_run" not in st.session_state:
    st.session_state["has_run"] = False

def clear_transcript():
    st.session_state["transcript_box"] = ""

# =========================================================
# SESSION STRUCTURE
# =========================================================
TEMPLATE_FILE = "templates.json"
def save_templates():
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(st.session_state.templates, f, indent=2)

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
st.title("Khatabook AI Auditor – Phase 1 POC")
st.write("CSS TEST")
st.markdown("""
    <style>
    /* Rich burgundy gradient background - more pronounced */
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(115deg, rgba(255,120,120,0.16) 0%, transparent 32%),
            linear-gradient(295deg, rgba(220,50,70,0.18) 0%, transparent 38%),
            radial-gradient(ellipse at 75% 18%, rgba(255,110,110,0.22) 0%, transparent 48%),
            radial-gradient(ellipse at 20% 85%, rgba(200,40,60,0.18) 0%, transparent 50%),
            linear-gradient(135deg, #4a1f2a 0%, #6b2737 25%, #8b454e 50%, #6b2737 75%, #5c2e3e 100%);
    }
    
    .block-container {
        max-width: 90%;
        padding-left: 5%;
        padding-right: 5%;
        background: rgba(255, 245, 235, 0.06) !important;
        backdrop-filter: blur(6px);
        border-radius: 12px;

    }
    
    /* Scale down all fonts globally */
    html, body, .stApp {
        font-size: 13px !important;
    }
    
    h1 {
        font-size: 1.8rem !important;
        color: #f5ebe0 !important;
    }
    
    h2, h3 {
        font-size: 1.3rem !important;
        color: #f5ebe0 !important;
    }
    
    /* Input fields styling - smaller with cream colors */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #e6e6e6 !important;  /* light grey */
        border: 2px solid #d4a574 !important;
        border-radius: 6px !important;
        color: #6b2737 !important;             /* burgundy */
        font-weight: 500;
        font-size: 13px !important;
        padding: 6px 10px !important;
    }
    
    .stTextArea textarea {
        min-height: 60px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: #d4a574 !important;
        box-shadow: 0 0 0 2px rgba(212, 165, 116, 0.3) !important;
    }
    
    /* Prompt delete/add buttons - MUCH smaller, centered icons, beige icons */
    .small-button button {
        height: 20px !important;
        min-height: 20px !important;
        padding: 2px !important;
        font-size: 11px !important;
        min-width: 22px !important;
        max-width: 22px !important;
        width: 22px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
    }
    
    /* Delete button - gradient with beige icon */
    .small-button button:first-child {
        background: linear-gradient(135deg, #6b2737 0%, #8b454e 100%) !important;
        color: #f5ebe0 !important;
        box-shadow: 0 1px 3px rgba(107, 39, 55, 0.4) !important;
    }
    
    .small-button button:first-child:hover {
        background: linear-gradient(135deg, #5c2e3e 0%, #6b2737 100%) !important;
        box-shadow: 0 2px 6px rgba(107, 39, 55, 0.5) !important;
    }
    
    /* Add button - gradient with beige icon */
    .small-button button:last-child {
        background: linear-gradient(135deg, #8b454e 0%, #6b2737 100%) !important;
        color: #f5ebe0 !important;
        box-shadow: 0 1px 3px rgba(139, 69, 78, 0.4) !important;
    }
    
    .small-button button:last-child:hover {
        background: linear-gradient(135deg, #6b2737 0%, #5c2e3e 100%) !important;
        box-shadow: 0 2px 6px rgba(139, 69, 78, 0.5) !important;
    }
    
    /* Parameter buttons - HALF size with gradient and beige text */
    div[data-testid="column"] > div > div > button {
        background: linear-gradient(135deg, #6b2737 0%, #8b454e 100%) !important;
        color: #f5ebe0 !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 5px 10px !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(107, 39, 55, 0.4) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="column"] > div > div > button:hover {
        background: linear-gradient(135deg, #5c2e3e 0%, #6b2737 100%) !important;
        box-shadow: 0 3px 8px rgba(107, 39, 55, 0.5) !important;
    }
    
    /* Save Templates button - HALF size with gradient and beige text */
    .stButton > button:first-child {
        background: linear-gradient(135deg, #8b454e 0%, #6b2737 100%) !important;
        color: #f5ebe0 !important;
        border-radius: 5px !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        padding: 5px 10px !important;
        box-shadow: 0 2px 6px rgba(139, 69, 78, 0.4) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stButton > button:first-child:hover {
        background: linear-gradient(135deg, #6b2737 0%, #5c2e3e 100%) !important;
        box-shadow: 0 3px 8px rgba(139, 69, 78, 0.5) !important;
    }
    
    /* Labels and text - cream colors for visibility */
    .stMarkdown {
        color: #f5ebe0 !important;
        font-size: 13px !important;
    }
    
    label {
        color: #f5ebe0 !important;
        font-weight: 500;
        font-size: 13px !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(245, 235, 224, 0.3) !important;
    }
    
    /* Number input styling - smaller */
    .stNumberInput input {
        background-color: #f5ebe0 !important;
        border: 2px solid #d4a574 !important;
        border-radius: 6px !important;
        color: #5c2e3e !important;
        font-size: 13px !important;
        padding: 6px 10px !important;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        font-size: 13px !important;
    }
    
    /* Selectbox styling */
    .stSelectbox label {
        font-size: 13px !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background-color: #f5ebe0 !important;
        border-radius: 6px !important;
        font-size: 12px !important;
    }
    
    /* Table text */
    table {
        font-size: 12px !important;
    }
    
    /* Reduce spacing */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    /* Force dropdown box colors to match text inputs */
    div[data-baseweb="select"] > div {
        background-color: #e6e6e6 !important;  /* light grey */
        color: #6b2737 !important;             /* burgundy */
    }
    /* Force beige color for checkbox side text (Streamlit new structure) */
    div[data-testid="stCheckbox"] p {
        color: #f5ebe0 !important;
    }
    /* 🔴 force Streamlit main background transparent */
    /* 🔥 hard override final Streamlit layer */
    [data-testid="stAppViewContainer"] > div:first-child {
        background: transparent !important;
    }
    
    [data-testid="stAppViewContainer"] section {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("💾 Save Templates"):
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(st.session_state.templates, f, indent=2)
    st.success("Templates saved.")

st.divider()
st.subheader("Audit Rule Engine")

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
        
        save_templates()  # auto-save rename
        st.rerun()

with col_add:
    if st.button("➕", use_container_width=True):
        st.session_state.templates["New Template"] = {"active": False, "parameters": []}
        st.session_state.current_template = "New Template"

        save_templates()  # auto-save
        st.rerun()

with col_del:
    if st.button("🗑", use_container_width=True):

        # Prevent deleting last template
        if len(st.session_state.templates) <= 1:
            st.warning("At least one template must exist.")
        else:
            del st.session_state.templates[st.session_state.current_template]

            st.session_state.current_template = list(st.session_state.templates.keys())[0]

            save_templates()  # <-- important production fix
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

    is_flag = param["type"] == "Flag"
    
    with col2:
        param["fatal"] = st.checkbox(
            "Fatal",
            value=param["fatal"],
            key=f"fatal_{selected_template}_{idx}",
            disabled=is_flag
        )
    
    with col3:
        param["score"] = st.number_input(
            "Score",
            min_value=0,
            step=1,
            value=param["score"],
            key=f"score_{selected_template}_{idx}",
            label_visibility="collapsed",
            disabled=is_flag
        )
    
    # Calculate column widths to give more space to prompts
    # For each prompt: large prompt column, tiny button column, medium logic column
    col_widths = []
    for p_idx in range(len(param["prompts"])):
        col_widths.append(10)  # Prompt - larger
        col_widths.append(1)   # Buttons - tiny
        if p_idx < len(param["prompts"]) - 1:
            col_widths.append(2)  # AND/OR - medium
    
    cols = st.columns(col_widths)

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
                    height=100,
                    label_visibility="collapsed",
                    placeholder="Enter Prompt"
                )

        c += 1

        # DELETE BUTTON (only show for non-last prompts OR if more than 1 prompt)
        with cols[c]:
            st.markdown('<div class="small-button">', unsafe_allow_html=True)
            # Show delete button for all prompts if more than 1 exists
            if len(param["prompts"]) > 1:
                if st.button(
                    "🗑",
                    key=f"del_prompt_{selected_template}_{idx}_{p_idx}",
                    use_container_width=False
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
                    use_container_width=False
                ):
                    param["prompts"].append("")
                    param["logic"].append("AND")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
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
transcript = st.text_area(
    "Paste transcript here",
    key=st.session_state["transcript_key"]
)

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

    ai_results = None
    # Build audit definition to send to AI
    audit_payload = []
    
    for template_name, template in st.session_state.templates.items():
    
        if not template.get("active"):
            continue
    
        for param in template["parameters"]:
            audit_payload.append({
                "template": template_name,
                "name": param["title"],
                "type": param["type"],
                "fatal": param["fatal"],
                "prompts": param["prompts"],
                "logic": param["logic"]
            })


    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a strict call audit evaluator.
                    
                    Your task:
                    Evaluate the call transcript against the provided audit parameters.
                    
                    Rules:
                    - Use ONLY the transcript.
                    - Do NOT assume anything not spoken.
                    - Each parameter must return:
                      - result → "YES" or "NO"
                      - reasoning → short, strong justification
                      - timestamps → list of transcript timestamps proving the reasoning
                    - If parameter type = "Flag":
                      - Return only YES or NO.
                      - Ignore fatal and score impact.
                    - If parameter is fatal and result = NO:
                      - Mark result = "FATAL".
                    - Output MUST be valid JSON.
                    - No extra text.
                    
                    JSON format:
                    
                    {
                      "parameters": [
                        {
                          "name": "<parameter name>",
                          "result": "YES | NO | FATAL",
                          "reasoning": "<clear reasoning>",
                          "timestamps": ["mm:ss", "mm:ss"]
                        }
                      ]
                    }
                    """
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "transcript": transcript,
                        "audit_parameters": audit_payload
                    })
                }

            ],
            temperature=0
        )

        ai_results = response.choices[0].message.content

    except Exception as e:
        st.error(f"OpenAI error: {e}")

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

            # --- FLAG handling (no score, no fatal impact) ---
            if param["type"] == "Flag":
                final_result = "YES" if param_yes else "NO"
                score = 0
            
            else:
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
    num = int(st.session_state["transcript_key"].split("_")[-1]) + 1
    st.session_state["transcript_key"] = f"transcript_{num}"
    st.rerun()
    

# =========================================================
# HISTORY
# =========================================================
