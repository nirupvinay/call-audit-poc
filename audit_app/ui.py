import json
import uuid

import pandas as pd
import streamlit as st
from openai import OpenAI

from audit_app.audit_engine import AuditResponseParseError, build_audit_payload, run_openai_audit
from audit_app.styles import (
    APP_STYLES,
    BACKEND_COMPACT_STYLES,
    LOGIC_DROPDOWN_STYLES,
    PARAMETER_DIVIDER,
    SIDEBAR_NAV_STYLES,
)
from audit_app.template_store import ensure_minimum_parameter, initialize_session_state, save_templates


def render_template_action_bar() -> None:
    col_save, col_download, col_upload = st.columns(3)

    with col_save:
        if st.button("💾 Save Templates", use_container_width=True):
            save_templates()
            st.success("Templates saved successfully!")

    with col_download:
        st.download_button(
            label="⬇️ Download Templates",
            data=json.dumps(st.session_state.templates, indent=2),
            file_name="templates_backup.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_upload:
        uploaded_file = st.file_uploader(
            " ",
            type=["json"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode("utf-8")
                data = json.loads(content)

                if not isinstance(data, dict):
                    raise ValueError("Invalid format")

                st.session_state.templates = data
                st.session_state.current_template = list(data.keys())[0]

                save_templates()
                st.success("Templates restored and saved.")
                st.rerun()

            except Exception:
                st.error("Invalid file.")


def render_template_selector() -> tuple[str, dict]:
    empty1, col_dd, col_edit, col_add, col_del, empty2 = st.columns([2, 3, 1, 1, 1, 2])
    template_names = list(st.session_state.templates.keys())

    with col_dd:
        selected_template = st.selectbox(
            "Template",
            template_names,
            index=template_names.index(st.session_state.current_template)
            if st.session_state.current_template in template_names
            else 0,
            label_visibility="collapsed",
        )
        st.session_state.current_template = selected_template

    with col_edit:
        if st.button("✏️", use_container_width=True):
            st.session_state.rename_mode = not st.session_state.rename_mode

    if st.session_state.rename_mode:
        new_name = st.text_input(
            "Rename Template",
            value=st.session_state.current_template,
            key="rename_input",
        )
        if new_name and new_name != st.session_state.current_template:
            st.session_state.templates[new_name] = st.session_state.templates.pop(
                st.session_state.current_template
            )
            st.session_state.current_template = new_name
            st.session_state.rename_mode = False
            save_templates()
            st.rerun()

    with col_add:
        if st.button("➕", use_container_width=True):
            st.session_state.templates["New Template"] = {"active": False, "parameters": []}
            st.session_state.current_template = "New Template"
            save_templates()
            st.rerun()

    with col_del:
        if st.button("🗑", use_container_width=True):
            if len(st.session_state.templates) <= 1:
                st.warning("At least one template must exist.")
            else:
                del st.session_state.templates[st.session_state.current_template]
                st.session_state.current_template = list(st.session_state.templates.keys())[0]
                save_templates()
                st.rerun()

    if not st.session_state.templates:
        st.info("No templates available.")
        if st.button("➕ Add New Template"):
            st.session_state.templates["New Template"] = {"active": True, "parameters": []}
            st.session_state.current_template = "New Template"
            save_templates()
            st.rerun()
        st.stop()

    template_data = st.session_state.templates[st.session_state.current_template]
    return selected_template, template_data


def render_parameters(selected_template: str, template_data: dict) -> None:
    ensure_minimum_parameter(template_data)

    for idx, param in enumerate(template_data["parameters"]):
        
        param_id = param.get("id", idx)

        title_col, empty_col = st.columns([3, 9])
        with title_col:
            param["title"] = st.text_input(
                "Title",
                value=param["title"],
                key=f"title_{selected_template}_{idx}",
                label_visibility="collapsed",
                placeholder="Parameter title",
                max_chars=100,
            )

        col1, empty_type, col2, col3 = st.columns([1.5, 5.5, 1, 1])

        with col1:
            param["type"] = st.selectbox(
                "Type",
                ["Regular", "Conditional", "Flag"],
                index=["Regular", "Conditional", "Flag"].index(param["type"]),
                key=f"type_{selected_template}_{idx}",
                label_visibility="collapsed",
            )

        is_flag = param["type"] == "Flag"

        with col2:
            param["fatal"] = st.checkbox(
                "Fatal",
                value=param["fatal"],
                key=f"fatal_{selected_template}_{idx}",
                disabled=is_flag,
            )

        with col3:
            score_col, empty_score = st.columns([1, 2])
            with score_col:
                param["score"] = st.number_input(
                    "Score",
                    min_value=0,
                    max_value=999,
                    step=1,
                    value=param["score"],
                    key=f"score_{selected_template}_{idx}",
                    label_visibility="collapsed",
                    disabled=is_flag,
                )

        for p_idx in range(len(param["prompts"])):
            empty_left, prompt_col, button_col, empty_right = st.columns([2, 5, 1, 4])

            with prompt_col:
                param_titles = [p["title"] for p in template_data["parameters"][:idx]]

                if param["type"] == "Conditional" and param_titles:
                    param["prompts"][p_idx] = st.selectbox(
                        "Cond",
                        param_titles,
                        index=param_titles.index(param["prompts"][p_idx])
                        if param["prompts"][p_idx] in param_titles
                        else 0,
                        key=f"prompt_{selected_template}_{idx}_{p_idx}",
                        label_visibility="collapsed",
                    )
                else:
                    param["prompts"][p_idx] = st.text_area(
                        "Prompt",
                        value=param["prompts"][p_idx],
                        key=f"prompt_{selected_template}_{idx}_{p_idx}",
                        height=60,
                        label_visibility="collapsed",
                        placeholder="Enter Prompt",
                    )

            with button_col:
                if len(param["prompts"]) > 1 and st.button(
                    "🗑",
                    key=f"del_prompt_{selected_template}_{idx}_{p_idx}",
                    use_container_width=True,
                ):
                    param["prompts"].pop(p_idx)
                    if p_idx < len(param["logic"]):
                        param["logic"].pop(p_idx)
                    save_templates()
                    st.rerun()

                if p_idx == len(param["prompts"]) - 1 and st.button(
                    "➕",
                    key=f"add_prompt_{selected_template}_{idx}_{p_idx}",
                    use_container_width=True,
                ):
                    param["prompts"].append("")
                    param["logic"].append("AND")
                    save_templates()
                    st.rerun()

            if p_idx < len(param["prompts"]) - 1:
                st.write("")
                empty1, logic_col, empty2 = st.columns([4, 2, 6])
                with logic_col:
                    st.markdown(LOGIC_DROPDOWN_STYLES, unsafe_allow_html=True)
                    param["logic"][p_idx] = st.selectbox(
                        "Prompt Logic",
                        ["AND", "OR"],
                        index=["AND", "OR"].index(param["logic"][p_idx])
                        if p_idx < len(param["logic"])
                        else 0,
                        key=f"logic_{selected_template}_{idx}_{p_idx}",
                        label_visibility="collapsed",
                    )
                st.write("")

        col_add, col_del = st.columns(2)

        with col_add:
            if st.button("➕ Add Parameter", key=f"add_param_{param_id}", use_container_width=True):
                template_data["parameters"].insert(
                    idx + 1,
                    {
                        "id": str(uuid.uuid4()),
                        "title": "Parameter",
                        "type": "Regular",
                        "fatal": False,
                        "score": 0,
                        "prompts": [""],
                        "logic": [],
                    },
                )
                save_templates()
                st.rerun()

        with col_del:
            if st.button(
                "🗑 Delete Parameter",
                key=f"delete_param_{param_id}",
                use_container_width=True,
            ) and len(template_data["parameters"]) > 1:
                template_data["parameters"].pop(idx)
                save_templates()
                st.rerun()

        st.markdown(PARAMETER_DIVIDER, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_results(template_name: str, template_results: list[dict], template_total: int) -> None:
    st.subheader(f"Template: {template_name}")
    df = pd.DataFrame(template_results).reset_index(drop=True)
    st.dataframe(df, use_container_width=True)
    st.markdown(f"**Total Score: {template_total}**")


def evaluate_and_render(client, transcript: str) -> None:
    if transcript.strip() == "":
        st.error("Paste transcript first.")
        st.stop()

    st.markdown(
        """
        <div style="font-size:12px; font-weight:500; color:#C0C0C0;">
            ⚙️ Running audit…! Please be patient, I'm new to this!
        </div>
        """,
        unsafe_allow_html=True,
    )

    audit_payload = build_audit_payload(st.session_state.templates)
    ai_results = None

    try:
        ai_results = run_openai_audit(client, transcript, audit_payload)
    except AuditResponseParseError as e:
        st.error("AI returned unreadable JSON.")
        st.code(e.raw_response)
        st.stop()
    except Exception as e:
        st.error(f"OpenAI error: {e}")
        st.stop()

    if not isinstance(ai_results, dict) or "parameters" not in ai_results:
        st.error("AI JSON missing 'parameters' field.")
        st.code(json.dumps(ai_results, indent=2))
        st.stop()

    if not isinstance(ai_results["parameters"], list):
        st.error("'parameters' must be a list.")
        st.stop()

    for template_name, template in st.session_state.templates.items():
        if not template.get("active"):
            continue

        results = []
        fatal_triggered = False
        template_total = 0

        for param in template["parameters"]:
            ai_param = next((p for p in ai_results["parameters"] if p["name"] == param["title"]), None)

            if not ai_param:
                final_result = "NO"
                score = 0
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

            template_total += score
            reason = ai_param.get("reasoning", "—") if ai_param else "—"

            results.append(
                {
                    "Parameter": param["title"],
                    "Result": final_result,
                    "Score": score,
                    "Reason": reason,
                }
            )

        if fatal_triggered:
            template_total = 0

        if results:
            render_results(template_name, results, template_total)



def render_shared_header() -> None:
    st.title("Khatabook AI Auditor – Phase 1 (The Brain)")


def render_workspace_selector() -> str:
    st.markdown(SIDEBAR_NAV_STYLES, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### ")
        page = st.radio(
            "Workspace",
            ["Audit", "Rule Engine"],
            format_func=lambda x: "🧾" if x == "Audit" else "⚙️",
            label_visibility="collapsed",
            key="app_page",
        )
    return page


def render_backend_page() -> None:
    st.subheader("Audit Rule Engine")
    st.divider()
    st.markdown(BACKEND_COMPACT_STYLES, unsafe_allow_html=True)

    render_template_action_bar()
    selected_template, template_data = render_template_selector()

    new_active_state = st.checkbox("Template Active", value=template_data.get("active", True))
    if new_active_state != template_data.get("active", True):
        template_data["active"] = new_active_state
        save_templates()
    else:
        template_data["active"] = new_active_state

    render_parameters(selected_template, template_data)


def render_frontend_page(client) -> None:
    st.subheader("Audit")
    st.divider()

    transcript = st.text_area("Paste transcript here", key=st.session_state["transcript_key"])

    col1, col2 = st.columns(2)
    run = col1.button("Run Audit")
    reset = col2.button("Reset")

    if run:
        evaluate_and_render(client, transcript)

    if reset:
        num = int(st.session_state["transcript_key"].split("_")[-1]) + 1
        st.session_state["transcript_key"] = f"transcript_{num}"
        st.rerun()

def run_app() -> None:
    st.set_page_config(layout="wide")
    initialize_session_state()

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    st.markdown(APP_STYLES, unsafe_allow_html=True)
    render_shared_header()
    page = render_workspace_selector()

    if page == "Audit":
        render_frontend_page(client)
    else:
        render_backend_page()
