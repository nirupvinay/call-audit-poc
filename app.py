import streamlit as st
import csv
from datetime import datetime
import pandas as pd
import json
from openai import OpenAI

st.set_page_config(layout="wide")

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
st.title("Khatabook AI Auditor – Phase 1 (The Brain)")
# ===== TEMPLATE ACTION BAR =====
col_save, col_download, col_upload = st.columns(3)

with col_save:
    if st.button("💾 Save Templates", use_container_width=True):
        st.success("Templates ready for download backup.")

with col_download:
    st.download_button(
        label="⬇️ Download Templates",
        data=json.dumps(st.session_state.templates, indent=2),
        file_name="templates_backup.json",
        mime="application/json",
        use_container_width=True
    )

with col_upload:
    uploaded_file = st.file_uploader(
        " ",
        type=["json"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)

            if not isinstance(data, dict):
                raise ValueError("Invalid format")

            st.session_state.templates = data
            st.session_state.current_template = list(data.keys())[0]

            st.success("Templates restored.")
            st.rerun()

        except Exception:
            st.error("Invalid file.")
# ===============================
st.subheader("Audit Rule Engine")
st.divider()
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


    # ---------- HORIZONTAL PROMPTS ----------
    # Custom CSS for smaller prompt buttons and 90% width container
    st.markdown("""
        <style>
        /* Rich burgundy gradient background - more pronounced */
        .stApp {
            background: linear-gradient(135deg, #4a1f2a 0%, #6b2737 25%, #8b454e 50%, #6b2737 75%, #5c2e3e 100%);
            background-attachment: fixed;
        }
        
        .block-container {
            max-width: none !important;   /* remove width restriction */
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* allow full page horizontal scroll */
        html, body, .stApp {
            overflow-x: auto !important;
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
        /* Make table text beige */
        table, th, td {
            color: #f5ebe0 !important;
        }
        /* ===== Audit Table Styling ===== */

        /* Center all column headers */
        thead tr th {
            text-align: center !important;
        }
        
        /* Column alignments */
        tbody tr td:nth-child(1) {  /* Parameter */
            text-align: left !important;
        }
        
        tbody tr td:nth-child(2),  /* Result */
        tbody tr td:nth-child(3),  /* Score */
        tbody tr td:nth-child(4) { /* Evidence */
            text-align: center !important;
        }
        
        /* Reason column left for readability */
        tbody tr td:nth-child(5) {
            text-align: left !important;
        }
        /* ===== Make download button match normal buttons ===== */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #8b454e 0%, #6b2737 100%) !important;
            color: #f5ebe0 !important;
            border: none !important;
            border-radius: 5px !important;
            font-weight: 500 !important;
            font-size: 12px !important;
            padding: 5px 10px !important;
            box-shadow: 0 2px 6px rgba(139, 69, 78, 0.4) !important;
        }
        
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, #6b2737 0%, #5c2e3e 100%) !important;
            box-shadow: 0 3px 8px rgba(139, 69, 78, 0.5) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Calculate column widths to give more space to prompts
    # For each prompt: large prompt column, tiny button column, medium logic column
    col_widths = []
    for p_idx in range(len(param["prompts"])):
        col_widths.append(6)  # Prompt - larger
        col_widths.append(1)   # Buttons - tiny
        if p_idx < len(param["prompts"]) - 1:
            col_widths.append(1)  # AND/OR - medium
    
    scroll_container = st.container()

    with scroll_container:
        st.markdown(
            '<div style="overflow-x:auto; white-space:nowrap;">',
            unsafe_allow_html=True
        )

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

            # DELETE / ADD BUTTONS
            with cols[c]:
                st.markdown('<div class="small-button">', unsafe_allow_html=True)

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

            # AND / OR DROPDOWN
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

        # CLOSE SCROLL DIV  ✅ (this is the important one)
        st.markdown('</div>', unsafe_allow_html=True)

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

    st.markdown(
        """
        <div style="font-size:12px; font-weight:500; color:#C0C0C0;">
            ⚙️ Running audit…! Please be patient, I'm new to this!
        </div>
        """,
        unsafe_allow_html=True
    )

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
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
                You are a STRICT, deterministic AI Call Audit Evaluator.
                
                Your job is to evaluate a call transcript against structured audit parameters
                and return ONLY factual, transcript-grounded compliance decisions.
                
                You must behave like a compliance engine, not a conversational AI.
                
                --------------------------------------------------
                CORE EVALUATION PRINCIPLES
                --------------------------------------------------
                
                1. Use ONLY spoken transcript evidence.
                2. Never guess missing information.
                3. Never assume intent without clear linguistic signal.
                4. If evidence is unclear or absent → result MUST be NO.
                5. Determinism is mandatory. Same input → same output.
                
                --------------------------------------------------
                UNIVERSAL LANGUAGE HANDLING
                --------------------------------------------------
                
                • The transcript may contain ANY language:
                  Hindi, Hinglish, English, mixed speech, broken grammar, STT errors, fillers.
                
                • Interpret SEMANTIC meaning, not grammar perfection.
                
                • Imperfect wording is VALID evidence if intent is clear.
                
                • Do NOT fail due to:
                  pronunciation issues, partial sentences, fillers, informal tone.
                
                • If meaning itself is uncertain → return NO.
                
                --------------------------------------------------
                CONTROLLED CONTEXT INFERENCE
                --------------------------------------------------
                
                You MAY infer intent ONLY when:
                
                • Meaning is strongly implied by nearby words, AND  
                • A human auditor would reach the same conclusion, AND  
                • No equally likely alternative interpretation exists.
                
                If uncertainty exists → DO NOT infer → return NO.
                
                Never create facts not present in transcript.
                
                --------------------------------------------------
                MULTI-PROMPT LOGIC EXECUTION
                --------------------------------------------------
                
                Each parameter may contain multiple prompts.
                
                You MUST:
                
                1. Evaluate EVERY prompt independently using transcript evidence.
                2. Apply provided logic strictly:
                
                   AND → all prompts must be satisfied  
                   OR  → any one satisfied is enough  
                
                3. Final result MUST follow this logic exactly.
                4. Never skip prompts.
                5. Never merge reasoning across unrelated prompts.
                
                --------------------------------------------------
                RESULT RULES
                --------------------------------------------------
                
                Allowed outputs per parameter:
                
                YES  
                NO  
                FATAL → only when:
                        parameter.fatal = true
                        AND final logical result = NO
                
                No other labels allowed.
                
                --------------------------------------------------
                EVIDENCE & REASONING RULES
                --------------------------------------------------
                
                • Reasoning MUST reference real transcript wording or clear meaning.
                • No generic QA language.
                • No speculation.
                • Keep reasoning concise and factual.
                • Write reasoning in natural human audit language.
                • Do NOT mention prompts, parameters, rules, or evaluation logic.
                • Explain only what happened in the conversation.
                • Do NOT use jargons.
                
                Provide timestamps when detectable.
                If unavailable → return empty list.
                
                --------------------------------------------------
                STRICT OUTPUT FORMAT (JSON ONLY)
                --------------------------------------------------
                
                Return ONLY valid JSON:
                
                {
                  "parameters": [
                    {
                      "name": "<exact parameter name>",
                      "result": "YES | NO | FATAL",
                      "reasoning": "<concise transcript-grounded justification>",
                      "timestamps": ["mm:ss"]
                    }
                  ]
                }
                    
                    --------------------------------------------------
                    ABSOLUTE PROHIBITIONS
                    --------------------------------------------------
                    
                    Do NOT:
                    
                    • Add commentary outside JSON  
                    • Explain reasoning process  
                    • Invent evidence  
                    • Use probability words (“maybe”, “likely”, etc.)
                    
                    You are a deterministic audit engine.
                    Return structured compliance decisions only.
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
            )

        raw_ai = response.choices[0].message.content
        # --- SAFE JSON EXTRACTION ---
        try:
            # Handle extra text before/after JSON
            start = raw_ai.find("{")
            end = raw_ai.rfind("}") + 1
            cleaned = raw_ai[start:end]
        
            ai_results = json.loads(cleaned)
        
        except Exception as e:
            st.error("AI returned unreadable JSON.")
            st.code(raw_ai)
            st.stop()
        
        # --- STRUCTURE VALIDATION ---
        if not isinstance(ai_results, dict) or "parameters" not in ai_results:
            st.error("AI JSON missing 'parameters' field.")
            st.code(raw_ai)
            st.stop()
        
        if not isinstance(ai_results["parameters"], list):
            st.error("'parameters' must be a list.")
            st.stop()


    except Exception as e:
        st.error(f"OpenAI error: {e}")
    
    if not ai_results:
        st.stop()
        
    for template_name, template in st.session_state.templates.items():

        if not template.get("active"):
            continue

        results = []
        fatal_triggered = False
        template_total = 0

        for param in template["parameters"]:

            ai_param = next(
                (p for p in ai_results["parameters"] if p["name"] == param["title"]),
                None
            )
        
            if not ai_param:
                final_result = "NO"
                score = 0
                timestamps = []

        
            else:
                result = ai_param["result"]
        
                if param["type"] == "Flag":
                    final_result = result
                    score = 0
        
                elif result == "YES":
                    final_result = "YES"
                    score = param["score"]
        
                elif result == "FATAL":
                    final_result = "FATAL"
                    score = 0
                    fatal_triggered = True
        
                else:
                    final_result = "NO"
                    score = 0

                timestamps = ai_param.get("timestamps", [])

            template_total += score
            
            evidence = ", ".join(timestamps) if timestamps else "—"
            
            reason = ai_param.get("reasoning", "—") if ai_param else "—"

            results.append({
                "Parameter": param["title"],
                "Result": final_result,
                "Score": score,
                "Evidence": evidence,
                "Reason": reason
            })


        if fatal_triggered:
            template_total = 0

        if results:
            st.subheader(f"Template: {template_name}")
            df = pd.DataFrame(results).reset_index(drop=True)
            st.dataframe(df, use_container_width=True)
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
