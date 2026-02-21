import json
from pathlib import Path

import streamlit as st

TEMPLATE_FILE = "templates.json"
BACKUP_DIR = Path.home() / ".call-audit-poc"


def _candidate_paths(file_name: str) -> list[Path]:
    return [Path(file_name), BACKUP_DIR / file_name]


def save_json_with_backup(file_name: str, payload: dict) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for path in _candidate_paths(file_name):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


def load_json_with_backup(file_name: str) -> dict | None:
    valid_payloads: list[tuple[float, dict]] = []
    for path in _candidate_paths(file_name):
        try:
            with path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and loaded:
                valid_payloads.append((path.stat().st_mtime, loaded))
        except Exception:
            continue

    if not valid_payloads:
        return None

    valid_payloads.sort(key=lambda item: item[0], reverse=True)
    return valid_payloads[0][1]


def save_templates() -> None:
    save_json_with_backup(TEMPLATE_FILE, st.session_state.templates)


def initialize_session_state() -> None:
    if "transcript_key" not in st.session_state:
        st.session_state["transcript_key"] = "transcript_0"

    if "has_run" not in st.session_state:
        st.session_state["has_run"] = False

    if "templates" not in st.session_state:
        loaded_templates = load_json_with_backup(TEMPLATE_FILE)
        if loaded_templates:
            st.session_state.templates = loaded_templates
        else:
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
                "title": "Parameter",
                "type": "Regular",
                "fatal": False,
                "score": 0,
                "prompts": [""],
                "logic": [],
            }
        )
