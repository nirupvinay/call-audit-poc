import json
from pathlib import Path

import pandas as pd
import streamlit as st
from openai import OpenAI

from audit_app.audit_engine import (
    AuditResponseParseError,
    build_audit_payload,
    run_openai_audit,
    run_openai_lead_classifier,
)
from audit_app.styles import (
    APP_STYLES,
    BACKEND_COMPACT_STYLES,
    LOGIC_DROPDOWN_STYLES,
    PARAMETER_DIVIDER,
    PRIORITIZATION_PAGE_STYLES,
    SIDEBAR_NAV_STYLES,
)
from audit_app.template_store import (
    ensure_minimum_parameter,
    initialize_session_state,
    load_json_with_backup,
    save_json_with_backup,
    save_templates,
)

PRIORITIZATION_TEMPLATE_FILE = Path("prioritization_templates.json")


def _default_prioritization_templates() -> dict:
    return {
        "Default Template": {
            "active": True,
            "prioritization_logic": "Classify the lead as HOT, WARM, or COLD based on intent and readiness.",
        }
    }


def save_prioritization_templates() -> None:
    save_json_with_backup(PRIORITIZATION_TEMPLATE_FILE.name, st.session_state.prioritization_templates)


def initialize_prioritization_state() -> None:
    if "prioritization_templates" not in st.session_state:
        try:
            loaded = load_json_with_backup(PRIORITIZATION_TEMPLATE_FILE.name)
            if not isinstance(loaded, dict) or not loaded:
                raise ValueError("Invalid prioritization templates")
            st.session_state.prioritization_templates = loaded
        except Exception:
            st.session_state.prioritization_templates = _default_prioritization_templates()

    if "prioritization_current_template" not in st.session_state:
        st.session_state.prioritization_current_template = next(
            iter(st.session_state.prioritization_templates.keys())
        )

    if st.session_state.prioritization_current_template not in st.session_state.prioritization_templates:
        st.session_state.prioritization_current_template = next(
            iter(st.session_state.prioritization_templates.keys())
        )

    if "prioritization_transcript_key" not in st.session_state:
        st.session_state.prioritization_transcript_key = "prioritization_transcript_0"

    if "prioritization_rename_mode" not in st.session_state:
        st.session_state.prioritization_rename_mode = False




def _rule_engine_key_prefix(selected_template: str) -> str:
    rev = st.session_state.get("rule_engine_form_rev", 0)
    return f"{selected_template}_{rev}"


def _bump_rule_engine_form_rev() -> None:
    st.session_state["rule_engine_form_rev"] = st.session_state.get("rule_engine_form_rev", 0) + 1


def _sync_rule_engine_from_state(template_data: dict, key_prefix: str) -> None:
    for idx, param in enumerate(template_data.get("parameters", [])):
        title_key = f"title_{key_prefix}_{idx}"
        type_key = f"type_{key_prefix}_{idx}"
        fatal_key = f"fatal_{key_prefix}_{idx}"
        score_key = f"score_{key_prefix}_{idx}"

        if title_key in st.session_state:
            param["title"] = st.session_state[title_key]
        if type_key in st.session_state:
            param["type"] = st.session_state[type_key]
        if fatal_key in st.session_state:
            param["fatal"] = st.session_state[fatal_key]
        if score_key in st.session_state:
            param["score"] = st.session_state[score_key]

        for p_idx in range(len(param.get("prompts", []))):
            prompt_key = f"prompt_{key_prefix}_{idx}_{p_idx}"
            if prompt_key in st.session_state:
                param["prompts"][p_idx] = st.session_state[prompt_key]

            if p_idx < len(param.get("logic", [])):
                logic_key = f"logic_{key_prefix}_{idx}_{p_idx}"
                if logic_key in st.session_state:
                    param["logic"][p_idx] = st.session_state[logic_key]


def set_flash_toast(message: str, icon: str = "✅", duration: int = 2) -> None:
    st.session_state["_flash_toast"] = {
        "message": message,
        "icon": icon,
        "duration": duration,
    }


def render_flash_toast() -> None:
    payload = st.session_state.pop("_flash_toast", None)
    if payload:
        st.toast(
            payload.get("message", ""),
            icon=payload.get("icon"),
            duration=payload.get("duration", 2),
        )


def start_card(card_class: str = "ui-card") -> None:
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)


def end_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_result_badge(result: str) -> str:
    palette = {
        "YES": ("#d3eadb", "#224f35", "#3f8f63"),
        "NO": ("#ebd6da", "#6f2b37", "#9c4e5e"),
        "FATAL": ("#ead1d1", "#5f1f24", "#a45f5f"),
        "RED FLAG": ("#f0d7dc", "#7a1f31", "#b4576c"),
        "GREEN FLAG": ("#d4e9dc", "#1f5a3b", "#4a9b6f"),
    }
    bg, text, border = palette.get(result, ("#e8dccd", "#563d2d", "#9c7b56"))
    return (
        f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;"
        f"font-weight:700;font-size:12px;background:{bg};color:{text};"
        f"border:1px solid {border};letter-spacing:0.2px;'>{result}</span>"
    )


def render_template_action_bar() -> None:
    col_save, col_download, col_upload = st.columns(3)

    with col_save:
        if st.button("💾 Save Templates", use_container_width=True):
            save_templates()
            st.toast("Templates saved successfully!", icon="✅", duration=2)

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
            key="rule_upload_templates",
        )

        if uploaded_file is not None:
            current_signature = f"{uploaded_file.name}:{uploaded_file.size}"
            if current_signature != st.session_state.get("rule_upload_signature", ""):
                try:
                    content = uploaded_file.read().decode("utf-8")
                    data = json.loads(content)

                    if not isinstance(data, dict):
                        raise ValueError("Invalid format")

                    st.session_state.templates = data
                    st.session_state.current_template = list(data.keys())[0]

                    save_templates()
                    st.session_state["rule_upload_signature"] = current_signature
                    set_flash_toast("Templates restored and saved.", icon="✅", duration=2)
                    st.rerun()

                except Exception:
                    st.session_state["rule_upload_signature"] = current_signature
                    st.toast("Invalid file.", icon="⚠️", duration=2)


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
    key_prefix = _rule_engine_key_prefix(selected_template)

    for idx, param in enumerate(template_data["parameters"]):
        title_col, empty_col = st.columns([3, 9])
        with title_col:
            param["title"] = st.text_input(
                "Title",
                value=param["title"],
                key=f"title_{key_prefix}_{idx}",
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
                key=f"type_{key_prefix}_{idx}",
                label_visibility="collapsed",
            )

        is_flag = param["type"] == "Flag"

        with col2:
            param["fatal"] = st.checkbox(
                "Fatal",
                value=param["fatal"],
                key=f"fatal_{key_prefix}_{idx}",
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
                    key=f"score_{key_prefix}_{idx}",
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
                        key=f"prompt_{key_prefix}_{idx}_{p_idx}",
                        label_visibility="collapsed",
                    )
                else:
                    param["prompts"][p_idx] = st.text_area(
                        "Prompt",
                        value=param["prompts"][p_idx],
                        key=f"prompt_{key_prefix}_{idx}_{p_idx}",
                        height=60,
                        label_visibility="collapsed",
                        placeholder="Enter Prompt",
                    )

            with button_col:
                if len(param["prompts"]) > 1 and st.button(
                    "🗑",
                    key=f"del_prompt_{key_prefix}_{idx}_{p_idx}",
                    use_container_width=True,
                ):
                    _sync_rule_engine_from_state(template_data, key_prefix)
                    param["prompts"].pop(p_idx)
                    if p_idx < len(param["logic"]):
                        param["logic"].pop(p_idx)
                    save_templates()
                    _bump_rule_engine_form_rev()
                    st.rerun()

                if p_idx == len(param["prompts"]) - 1 and st.button(
                    "➕",
                    key=f"add_prompt_{key_prefix}_{idx}_{p_idx}",
                    use_container_width=True,
                ):
                    _sync_rule_engine_from_state(template_data, key_prefix)
                    param["prompts"].append("")
                    param["logic"].append("AND")
                    save_templates()
                    _bump_rule_engine_form_rev()
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
                        key=f"logic_{key_prefix}_{idx}_{p_idx}",
                        label_visibility="collapsed",
                    )
                st.write("")

        col_add, col_del = st.columns(2)

        with col_add:
            if st.button("➕ Add Parameter", key=f"add_param_{key_prefix}_{idx}", use_container_width=True):
                _sync_rule_engine_from_state(template_data, key_prefix)
                template_data["parameters"].insert(
                    idx + 1,
                    {
                        "title": "Parameter",
                        "type": "Regular",
                        "fatal": False,
                        "score": 0,
                        "prompts": [""],
                        "logic": [],
                    },
                )
                save_templates()
                _bump_rule_engine_form_rev()
                st.rerun()

        with col_del:
            if st.button(
                "🗑 Delete Parameter",
                key=f"delete_param_{key_prefix}_{idx}",
                use_container_width=True,
            ) and len(template_data["parameters"]) > 1:
                _sync_rule_engine_from_state(template_data, key_prefix)
                template_data["parameters"].pop(idx)
                save_templates()
                _bump_rule_engine_form_rev()
                st.rerun()

        st.markdown(PARAMETER_DIVIDER, unsafe_allow_html=True)


def render_results(template_name: str, template_results: list[dict], template_total: int) -> None:
    st.subheader(f"Template: {template_name}")
    df = pd.DataFrame(template_results).reset_index(drop=True)
    styled_df = df.style.map(
        lambda value: (
            "background-color:#d3eadb;color:#224f35;font-weight:700;border-radius:999px;"
            if value == "YES"
            else "background-color:#ebd6da;color:#6f2b37;font-weight:700;border-radius:999px;"
            if value == "NO"
            else "background-color:#ead1d1;color:#5f1f24;font-weight:700;border-radius:999px;"
            if value == "FATAL"
            else "background-color:#f0d7dc;color:#7a1f31;font-weight:700;border-radius:999px;"
            if value == "RED FLAG"
            else "background-color:#d4e9dc;color:#1f5a3b;font-weight:700;border-radius:999px;"
            if value == "GREEN FLAG"
            else ""
        ),
        subset=["Result"],
    )
    st.dataframe(styled_df, use_container_width=True)
    badge_counts = df["Result"].value_counts().to_dict()
    badge_html = " ".join(
        render_result_badge(name)
        + f" <span style='color:#f5ebe0;font-weight:600;margin-right:8px;'>{count}</span>"
        for name, count in badge_counts.items()
    )
    if badge_html:
        st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown(f"**Total Score: {template_total}**")


def evaluate_and_render(client, transcript: str) -> None:
    if transcript.strip() == "":
        st.error("Paste transcript first.")
        st.stop()

    audit_payload = build_audit_payload(st.session_state.templates)
    ai_results = None

    try:
        with st.spinner("Running audit..."):
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
        export_rows = []
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
                    if result == "YES":
                        final_result = "RED FLAG"
                    elif result == "NO":
                        final_result = "GREEN FLAG"
                    else:
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
            export_rows.append(
                {
                    "Template": template_name,
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

            existing_rows = st.session_state.get("audit_result_export_rows", [])
            st.session_state["audit_result_export_rows"] = existing_rows + export_rows


def render_shared_header() -> None:
    st.title("Khatabook AI Auditor – Phase 1 (The Brain)")


def render_workspace_selector() -> str:
    st.markdown(SIDEBAR_NAV_STYLES, unsafe_allow_html=True)

    legacy_page_map = {
        "🧾 Audit": "Audit",
        "⚙️ Rule Engine": "Rule Engine",
        "🔥 Prioritization Model": "Prioritization Model",
        "Audit": "Audit",
        "Rule Engine": "Rule Engine",
        "Prioritization Model": "Prioritization Model",
    }

    if "app_page_nav" not in st.session_state:
        legacy = st.session_state.get("app_page")
        st.session_state["app_page_nav"] = legacy_page_map.get(legacy, "Audit")
    else:
        st.session_state["app_page_nav"] = legacy_page_map.get(
            st.session_state["app_page_nav"],
            "Audit",
        )

    with st.sidebar:
        st.markdown("### Workspace")
        workspace_display_map = {
            "▣ Audit": "Audit",
            "⚙ Rule Engine": "Rule Engine",
            "◆ Prioritization Model": "Prioritization Model",
        }
        selected_workspace = st.radio(
            "Workspace",
            list(workspace_display_map.keys()),
            index=list(workspace_display_map.values()).index(st.session_state["app_page_nav"]),
            key="app_page_nav_display",
            label_visibility="collapsed",
        )
    page = workspace_display_map[selected_workspace]
    st.session_state["app_page_nav"] = page
    return page


def render_app_access_gate() -> bool:
    app_password = str(st.secrets.get("APP_PASSWORD", "")).strip()
    if not app_password:
        return True

    if "app_authenticated" not in st.session_state:
        st.session_state.app_authenticated = False

    if st.session_state.app_authenticated:
        return True

    st.markdown(
        """
        <div style="
            max-width: 460px;
            padding: 16px;
            border-radius: 10px;
            border: 1px solid rgba(212,165,116,0.45);
            background: rgba(20, 24, 33, 0.35);
            margin-bottom: 8px;
        ">
            <div style="font-size: 22px; font-weight: 700; color: #f5ebe0; margin-bottom: 6px;">Protected Access</div>
            <div style="font-size: 13px; color: #f5ebe0;">Enter app password to access Audit, Rule Engine, and Prioritization Model.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    entered_password = st.text_input(
        "App Password",
        type="password",
        key="app_password_input",
        placeholder="Enter app password",
    )
    unlock = st.button("Unlock App", key="unlock_app")
    if unlock:
        if entered_password == app_password:
            st.session_state.app_authenticated = True
            st.rerun()
        else:
            st.error("Invalid app password.")
    return False


def render_backend_page() -> None:
    st.subheader("Audit Rule Engine")
    st.divider()
    st.markdown(BACKEND_COMPACT_STYLES, unsafe_allow_html=True)

    start_card()
    render_template_action_bar()
    selected_template, template_data = render_template_selector()
    end_card()

    start_card("ui-card ui-card-tight")
    new_active_state = st.checkbox("Template Active", value=template_data.get("active", True))
    if new_active_state != template_data.get("active", True):
        template_data["active"] = new_active_state
        save_templates()
    else:
        template_data["active"] = new_active_state

    render_parameters(selected_template, template_data)
    end_card()


def render_frontend_page(client) -> None:
    st.subheader("Audit")
    st.divider()

    start_card()
    transcript = st.text_area("Paste transcript here", key=st.session_state["transcript_key"])

    col1, col2 = st.columns(2)
    run = col1.button("Run Audit")
    reset = col2.button("Reset")

    if run:
        st.session_state["audit_result_export_rows"] = []
        evaluate_and_render(client, transcript)

    export_rows = st.session_state.get("audit_result_export_rows", [])
    if export_rows:
        export_df = pd.DataFrame(export_rows)
        st.download_button(
            "⬇️ Download Results",
            data=export_df.to_csv(index=False),
            file_name="audit_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    end_card()

    if reset:
        num = int(st.session_state["transcript_key"].split("_")[-1]) + 1
        st.session_state["transcript_key"] = f"transcript_{num}"
        st.rerun()


def render_prioritization_template_controls() -> dict:
    col_save, col_download, col_upload = st.columns(3)

    with col_save:
        if st.button("💾 Save Templates", key="prior_save_templates", use_container_width=True):
            save_prioritization_templates()
            st.toast("Templates saved successfully!", icon="✅", duration=2)

    with col_download:
        st.download_button(
            label="⬇️ Download Templates",
            data=json.dumps(st.session_state.prioritization_templates, indent=2),
            file_name="prioritization_templates_backup.json",
            mime="application/json",
            use_container_width=True,
            key="prior_download_templates",
        )

    with col_upload:
        uploaded_file = st.file_uploader(
            " ",
            type=["json"],
            label_visibility="collapsed",
            key="prior_upload_templates",
        )

        if uploaded_file is not None:
            current_signature = f"{uploaded_file.name}:{uploaded_file.size}"
            if current_signature != st.session_state.get("prior_upload_signature", ""):
                try:
                    content = uploaded_file.read().decode("utf-8")
                    data = json.loads(content)
                    if not isinstance(data, dict) or not data:
                        raise ValueError("Invalid format")

                    for template_value in data.values():
                        if not isinstance(template_value, dict):
                            raise ValueError("Invalid format")
                        if "active" not in template_value:
                            template_value["active"] = True
                        if "prioritization_logic" not in template_value:
                            template_value["prioritization_logic"] = ""

                    st.session_state.prioritization_templates = data
                    st.session_state.prioritization_current_template = next(iter(data.keys()))
                    save_prioritization_templates()
                    st.session_state["prior_upload_signature"] = current_signature
                    set_flash_toast("Templates restored and saved.", icon="✅", duration=2)
                    st.rerun()
                except Exception:
                    st.session_state["prior_upload_signature"] = current_signature
                    st.toast("Invalid file.", icon="⚠️", duration=2)

    st.markdown("Template")
    c1, c_edit, c2, c3 = st.columns([5, 1, 1, 1])

    with c1:
        names = list(st.session_state.prioritization_templates.keys())
        selected = st.selectbox(
            "Template",
            names,
            index=names.index(st.session_state.prioritization_current_template)
            if st.session_state.prioritization_current_template in names
            else 0,
            key="prioritization_template_select",
            label_visibility="collapsed",
        )
        st.session_state.prioritization_current_template = selected

    with c_edit:
        if st.button("✏️", key="prior_edit_template", use_container_width=True):
            st.session_state.prioritization_rename_mode = (
                not st.session_state.prioritization_rename_mode
            )

    if st.session_state.prioritization_rename_mode:
        new_name = st.text_input(
            "Rename Template",
            value=st.session_state.prioritization_current_template,
            key="prioritization_rename_input",
        )
        if (
            new_name
            and new_name != st.session_state.prioritization_current_template
            and new_name not in st.session_state.prioritization_templates
        ):
            st.session_state.prioritization_templates[new_name] = (
                st.session_state.prioritization_templates.pop(
                    st.session_state.prioritization_current_template
                )
            )
            st.session_state.prioritization_current_template = new_name
            st.session_state.prioritization_rename_mode = False
            save_prioritization_templates()
            st.rerun()

    with c2:
        if st.button("➕", key="prior_add_template", use_container_width=True):
            existing = set(st.session_state.prioritization_templates.keys())
            base = "New Template"
            candidate = base
            suffix = 1
            while candidate in existing:
                suffix += 1
                candidate = f"{base} {suffix}"
            st.session_state.prioritization_templates[candidate] = {
                "active": True,
                "prioritization_logic": "",
            }
            st.session_state.prioritization_current_template = candidate
            save_prioritization_templates()
            st.rerun()

    with c3:
        if st.button("🗑", key="prior_delete_template", use_container_width=True):
            if len(st.session_state.prioritization_templates) <= 1:
                st.warning("At least one template must exist.")
            else:
                del st.session_state.prioritization_templates[
                    st.session_state.prioritization_current_template
                ]
                st.session_state.prioritization_current_template = next(
                    iter(st.session_state.prioritization_templates.keys())
                )
                save_prioritization_templates()
                st.rerun()

    return st.session_state.prioritization_templates[
        st.session_state.prioritization_current_template
    ]


def render_prioritization_model_page(client) -> None:
    st.markdown(PRIORITIZATION_PAGE_STYLES, unsafe_allow_html=True)
    st.subheader("Prioritization Model")
    st.divider()

    start_card()
    template_data = render_prioritization_template_controls()

    active = st.checkbox(
        "Template Active",
        value=template_data.get("active", True),
        key="prior_template_active",
    )
    if active != template_data.get("active", True):
        template_data["active"] = active
        save_prioritization_templates()
    else:
        template_data["active"] = active

    current_logic = template_data.get("prioritization_logic", "")
    updated_logic = st.text_area(
        "Prioritization Logic",
        value=current_logic,
        key=f"prior_logic_{st.session_state.prioritization_current_template}",
        height=140,
    )
    if updated_logic != current_logic:
        template_data["prioritization_logic"] = updated_logic
        save_prioritization_templates()

    st.markdown(PARAMETER_DIVIDER, unsafe_allow_html=True)

    transcript = st.text_area(
        "Paste transcript here",
        key=st.session_state.prioritization_transcript_key,
    )

    col1, col2 = st.columns(2)
    run = col1.button("Run Prioritization", key="run_prioritization")
    reset = col2.button("Reset", key="reset_prioritization")

    end_card()

    if run:
        if transcript.strip() == "":
            st.error("Paste transcript first.")
            st.stop()

        active_templates = [
            (name, tdata)
            for name, tdata in st.session_state.prioritization_templates.items()
            if tdata.get("active", True)
        ]

        if not active_templates:
            st.warning("No active templates available.")
            st.stop()

        invalid_logic_templates = [
            name
            for name, tdata in active_templates
            if str(tdata.get("prioritization_logic", "")).strip() == ""
        ]

        if invalid_logic_templates:
            st.error(
                "Prioritization Logic cannot be empty for active templates: "
                + ", ".join(invalid_logic_templates)
            )
            st.stop()

        results_by_template = []
        try:
            with st.spinner("Running prioritization logic..."):
                for template_name, tdata in active_templates:
                    logic_text = str(tdata.get("prioritization_logic", "")).strip()
                    result = run_openai_lead_classifier(client, transcript, logic_text)
                    results_by_template.append((template_name, result))
        except AuditResponseParseError:
            st.error("AI response is invalid.")
            st.stop()
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            st.stop()

        for template_name, result in results_by_template:
            category = str(result.get("category", "")).upper().strip()
            st.markdown(f"**Template: {template_name}**")

            if category == "HOT":
                st.markdown("<p style='font-size:27px;font-weight:700;color:#d96a6e;'>🔥 HOT</p>", unsafe_allow_html=True)
            elif category == "WARM":
                st.markdown("<p style='font-size:27px;font-weight:700;color:#d6a15c;'>🟠 WARM</p>", unsafe_allow_html=True)
            elif category == "COLD":
                st.markdown("<p style='font-size:27px;font-weight:700;color:#7da4d4;'>❄️ COLD</p>", unsafe_allow_html=True)
            else:
                st.error(f"AI response is invalid for template: {template_name}")

    if reset:
        num = int(st.session_state.prioritization_transcript_key.split("_")[-1]) + 1
        st.session_state.prioritization_transcript_key = f"prioritization_transcript_{num}"
        st.rerun()


def run_app() -> None:
    st.set_page_config(layout="wide")
    initialize_session_state()
    initialize_prioritization_state()
    if "rule_engine_form_rev" not in st.session_state:
        st.session_state["rule_engine_form_rev"] = 0
    if "rule_upload_signature" not in st.session_state:
        st.session_state["rule_upload_signature"] = ""
    if "prior_upload_signature" not in st.session_state:
        st.session_state["prior_upload_signature"] = ""
    if "audit_result_export_rows" not in st.session_state:
        st.session_state["audit_result_export_rows"] = []
    render_flash_toast()

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    st.markdown(APP_STYLES, unsafe_allow_html=True)
    render_shared_header()
    if not render_app_access_gate():
        return

    page = render_workspace_selector()

    if page == "Audit":
        render_frontend_page(client)
    elif page == "Rule Engine":
        render_backend_page()
    else:
        render_prioritization_model_page(client)
