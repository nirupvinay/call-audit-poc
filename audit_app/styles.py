APP_STYLES = """
<style>
:root {
    --bg-1: #4a1f2a;
    --bg-2: #6b2737;
    --bg-3: #8b454e;
    --bg-4: #5c2e3e;
    --text-primary: #f5ebe0;
    --text-secondary: #e3d7c8;
    --accent-gold: #d4a574;
    --input-bg: #efe8df;
    --input-text: #4e2431;
    --card-bg: rgba(28, 14, 19, 0.34);
    --card-border: rgba(212, 165, 116, 0.28);
    --card-shadow: 0 10px 24px rgba(20, 8, 13, 0.22);
}

.stApp {
    background: linear-gradient(135deg, var(--bg-1) 0%, var(--bg-2) 25%, var(--bg-3) 50%, var(--bg-2) 75%, var(--bg-4) 100%);
    background-attachment: fixed;
    color: var(--text-primary);
}

.block-container {
    max-width: none !important;
    padding: 16px 28px 24px !important;
}

html, body, .stApp {
    font-size: 14px !important;
    line-height: 1.45;
}

h1 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.2px;
    color: var(--text-primary) !important;
    margin-bottom: 8px !important;
}

h2, h3 {
    font-size: 1.2rem !important;
    font-weight: 650 !important;
    color: var(--text-primary) !important;
}

p, .stMarkdown, label, small {
    color: var(--text-secondary) !important;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox select,
.stNumberInput input,
div[data-baseweb="select"] > div {
    background-color: var(--input-bg) !important;
    border: 1px solid rgba(212, 165, 116, 0.5) !important;
    border-radius: 10px !important;
    color: var(--input-text) !important;
    font-size: 14px !important;
    min-height: 40px !important;
    transition: border-color 160ms ease, box-shadow 160ms ease, transform 140ms ease;
}

.stTextArea textarea {
    min-height: 84px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--accent-gold) !important;
    box-shadow: 0 0 0 2px rgba(212, 165, 116, 0.22) !important;
}

.stButton > button,
.stDownloadButton > button,
div[data-testid="column"] > div > div > button[kind="secondary"] {
    min-height: 40px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(212, 165, 116, 0.38) !important;
    background: linear-gradient(135deg, #874353 0%, #652a3b 100%) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.2px;
    box-shadow: 0 6px 14px rgba(39, 14, 23, 0.34) !important;
    transition: transform 140ms ease, box-shadow 160ms ease, background 160ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="column"] > div > div > button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #723648 0%, #562435 100%) !important;
    box-shadow: 0 8px 16px rgba(39, 14, 23, 0.42) !important;
    transform: translateY(-1px);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: translateY(0);
}

section[data-testid="stFileUploader"] > div {
    border: 1px dashed rgba(212, 165, 116, 0.45) !important;
    border-radius: 10px !important;
    background: rgba(20, 10, 15, 0.2) !important;
    padding: 3px 10px !important;
}

.ui-card {
    border: 1px solid var(--card-border);
    background: var(--card-bg);
    border-radius: 14px;
    box-shadow: var(--card-shadow);
    padding: 14px 14px 12px;
    margin-bottom: 12px;
    backdrop-filter: blur(1px);
}

.ui-card-tight {
    padding-top: 10px;
    padding-bottom: 8px;
}

.ui-golden-divider {
    height: 10px;
    margin-top: 16px;
    margin-bottom: 14px;
    background: linear-gradient(to right, transparent, rgba(212,165,116,0.52), transparent);
}

.stDataFrame {
    border: 1px solid rgba(212, 165, 116, 0.3) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 8px 20px rgba(21, 10, 15, 0.25) !important;
}

table {
    font-size: 12px !important;
}

thead tr th {
    text-align: center !important;
    background: rgba(96, 42, 57, 0.82) !important;
}

tbody tr:nth-child(even) {
    background: rgba(70, 30, 43, 0.34) !important;
}

tbody tr td:nth-child(1),
tbody tr td:nth-child(4) {
    text-align: left !important;
}

tbody tr td:nth-child(2),
tbody tr td:nth-child(3) {
    text-align: center !important;
}

div[data-testid="stCheckbox"] p {
    color: var(--text-primary) !important;
}

.element-container {
    margin-bottom: 0.6rem !important;
}

hr {
    border-color: rgba(245, 235, 224, 0.25) !important;
}


/* Toast text color */
div[data-testid="stToast"] * {
    color: #000000 !important;
}

div[data-testid="stSpinner"] > div {
    border-top-color: #d4a574 !important;
}

div[data-testid="stSpinner"] p {
    color: #f5ebe0 !important;
}

/* Ensure collapsed sidebar releases width */
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0 !important;
    max-width: 0 !important;
    width: 0 !important;
}

</style>
"""

LOGIC_DROPDOWN_STYLES = """
<style>
div[class*="st-key-logic_"] div[data-baseweb="select"],
div[class*="st-key-logic_"] div[data-baseweb="select"] > div {
    background-color: #1f1f1f !important;
    color: #f9f9f9 !important;
    text-align: center !important;
    min-width: 120px !important;
}

div[class*="st-key-logic_"] div[data-baseweb="select"] input {
    color: #f9f9f9 !important;
    text-align: center !important;
}

div[class*="st-key-logic_"] div[data-baseweb="select"] svg {
    fill: #f9f9f9 !important;
}
</style>
"""


SIDEBAR_NAV_STYLES = """
<style>
section[data-testid="stSidebar"] {
    min-width: 250px !important;
    max-width: 250px !important;
    background: linear-gradient(180deg, #5a2b3c 0%, #6a3042 70%, #5f2d3f 100%) !important;
    border-right: 1px solid rgba(212, 165, 116, 0.24);
}

section[data-testid="stSidebar"] * {
    color: #f5ebe0 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    border-radius: 10px !important;
    margin-bottom: 6px !important;
    padding: 8px 10px !important;
    border-left: 3px solid transparent !important;
    transition: background-color 150ms ease, border-color 150ms ease;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"][aria-checked="true"] {
    background: rgba(212, 165, 116, 0.16) !important;
    border-left-color: rgba(212, 165, 116, 0.95) !important;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
    background: rgba(245, 235, 224, 0.08) !important;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] label[data-baseweb="radio"] p {
    color: #f5ebe0 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
}
</style>
"""


PRIORITIZATION_PAGE_STYLES = """
<style>
.stApp {
    background: linear-gradient(135deg, #0b1f42 0%, #12346b 25%, #1b4f96 50%, #12346b 75%, #0f2f5f 100%) !important;
    background-attachment: fixed !important;
}

section[data-testid="stSidebar"] {
    min-width: 250px !important;
    max-width: 250px !important;
    background: linear-gradient(180deg, #0d2a57 0%, #102f63 100%) !important;
}

.stButton > button,
.stDownloadButton > button,
div[data-testid="column"] > div > div > button[kind="secondary"] {
    background: linear-gradient(135deg, #1c4e8f 0%, #143c73 100%) !important;
    color: #e8f0ff !important;
    border: 1px solid rgba(212, 165, 116, 0.34) !important;
    box-shadow: 0 6px 14px rgba(16, 40, 82, 0.44) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="column"] > div > div > button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #173f74 0%, #10325e 100%) !important;
}

.ui-card {
    background: rgba(11, 27, 59, 0.42) !important;
    border: 1px solid rgba(212, 165, 116, 0.24) !important;
    box-shadow: 0 10px 24px rgba(10, 23, 46, 0.36) !important;
}

div[data-testid="stSpinner"] > div {
    border-top-color: #d4a574 !important;
}

div[data-testid="stSpinner"] p {
    color: #e8f0ff !important;
}
</style>
"""


BACKEND_COMPACT_STYLES = """
<style>
div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-prompt_"]) {
    margin-bottom: 0.18rem !important;
}

div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-logic_"]) {
    margin-top: 0.02rem !important;
    margin-bottom: 0.02rem !important;
}

div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-add_prompt_"]) {
    margin-top: 0.08rem !important;
}
</style>
"""


PARAMETER_DIVIDER = """
<div class="ui-golden-divider"></div>
"""
