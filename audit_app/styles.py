APP_STYLES = """
<style>
/* Rich burgundy gradient background - more pronounced */
.stApp {
    background: linear-gradient(135deg, #4a1f2a 0%, #6b2737 25%, #8b454e 50%, #6b2737 75%, #5c2e3e 100%);
    background-attachment: fixed;
}

.block-container {
    max-width: none !important;
    padding-left: 2rem;
    padding-right: 2rem;
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
    background-color: #e6e6e6 !important;
    border: 2px solid #d4a574 !important;
    border-radius: 6px !important;
    color: #6b2737 !important;
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

/* Style secondary buttons */
div[data-testid="column"] > div > div > button[kind="secondary"] {
    background: linear-gradient(135deg, #6b2737 0%, #8b454e 100%) !important;
    color: #f5ebe0 !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 5px 10px !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(107, 39, 55, 0.4) !important;
}

div[data-testid="column"] > div > div > button:hover {
    background: linear-gradient(135deg, #5c2e3e 0%, #6b2737 100%) !important;
    box-shadow: 0 3px 8px rgba(107, 39, 55, 0.5) !important;
}

/* Save Templates button */
.stButton > button:first-child {
    background: linear-gradient(135deg, #8b454e 0%, #6b2737 100%) !important;
    color: #f5ebe0 !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    padding: 5px 10px !important;
    box-shadow: 0 2px 6px rgba(139, 69, 78, 0.4) !important;
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

/* Number input styling */
.stNumberInput input {
    background-color: #e6e6e6 !important;
    border: 2px solid #d4a574 !important;
    border-radius: 6px !important;
    color: #6b2737 !important;
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

/* Force beige color for checkbox side text */
div[data-testid="stCheckbox"] p {
    color: #f5ebe0 !important;
}

/* Make table text beige */
table, th, td {
    color: #f5ebe0 !important;
}

/* Center all column headers */
thead tr th {
    text-align: center !important;
}

/* Column alignments */
tbody tr td:nth-child(1) {
    text-align: left !important;
}

tbody tr td:nth-child(2),
tbody tr td:nth-child(3) {
    text-align: center !important;
}

tbody tr td:nth-child(5) {
    text-align: left !important;
}

/* Download button styling */
.stDownloadButton > button {
    background: linear-gradient(135deg, #8b454e 0%, #6b2737 100%) !important;
    color: #f5ebe0 !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    padding: 5px 10px !important;
    box-shadow: 0 2px 6px rgba(139, 69, 78, 0.4) !important;
    width: 200px !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #6b2737 0%, #5c2e3e 100%) !important;
    box-shadow: 0 3px 8px rgba(139, 69, 78, 0.5) !important;
}

/* File uploader styling */
section[data-testid="stFileUploader"] > div {
    padding: 2px 8px !important;
    height: 32px !important;
    font-size: 12px !important;
}
</style>
"""

LOGIC_DROPDOWN_STYLES = """
<style>
/* Style only logic dropdown widgets by stable widget key prefix */
div[class*="st-key-logic_"] div[data-baseweb="select"],
div[class*="st-key-logic_"] div[data-baseweb="select"] > div {
    background-color: #000000 !important;
    color: #ffffff !important;
    text-align: center !important;
}

div[class*="st-key-logic_"] div[data-baseweb="select"] input {
    color: #ffffff !important;
    text-align: center !important;
}

div[class*="st-key-logic_"] div[data-baseweb="select"] svg {
    fill: #ffffff !important;
}
</style>
"""


SIDEBAR_NAV_STYLES = """
<style>
/* Icon-like vertical workspace switcher */
section[data-testid="stSidebar"] {
    width: 78px !important;
    min-width: 78px !important;
}

section[data-testid="stSidebar"] div[data-baseweb="radio"] > div {
    flex-direction: column;
    gap: 12px;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    justify-content: center;
    padding: 8px 0 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] p {
    font-size: 20px !important;
}
</style>
"""


BACKEND_COMPACT_STYLES = """
<style>
/* Reduce extra vertical gaps in Rule Engine page */
div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-prompt_"]) {
    margin-bottom: 0.2rem !important;
}

div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-logic_"]) {
    margin-top: 0.05rem !important;
    margin-bottom: 0.05rem !important;
}

div[data-testid="stVerticalBlock"] > div:has(div[class*="st-key-add_prompt_"]) {
    margin-top: 0.1rem !important;
}
</style>
"""



PARAMETER_DIVIDER = """
<div style="
    height:10px;
    background: linear-gradient(
        to right,
        transparent,
        rgba(212,165,116,0.35),
        transparent
    );
    margin-top:10px;
    margin-bottom:6px;
"></div>
"""
