import json
import streamlit as st
import uuid

TEMPLATE_FILE = "templates.json"


def save_templates() -> None:
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.templates, f, indent=2)


def initialize_session_state() -> None:
    if "transcript_key" not in st.session_state:
        st.session_state["transcript_key"] = "transcript_0"

    if "has_run" not in st.session_state:
        st.session_state["has_run"] = False

    if "templates" not in st.session_state:
        try:
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                st.session_state.templates = json.load(f)
        except Exception:
            st.session_state.templates = {
                "Default Template": {
                    "active": True,
                    "parameters": [],
                }
            }

    if "current_template" not in st.session_state:
        st.session_state.current_template = (
            list(st.session_state.templates.keys())[0] if st.session_state.templates else None
        )

    if "rename_mode" not in st.session_state:
        st.session_state.rename_mode = False


def ensure_minimum_parameter(template_data: dict) -> None:
    if len(template_data["parameters"]) == 0:
        template_data["parameters"].append(
            {
                "id": str(uuid.uuid4()),
                "title": "Parameter",
                "type": "Regular",
                "fatal": False,
                "score": 0,
                "prompts": [""],
                "logic": [],
            }
        )
