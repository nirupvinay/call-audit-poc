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
/* Style only the Prompt Logic dropdown - black background, white text */
div[data-baseweb="select"]:has(input[aria-label="Prompt Logic"]) {
    background-color: #000000 !important;
}
div[data-baseweb="select"]:has(input[aria-label="Prompt Logic"]) > div {
    background-color: #000000 !important;
    color: #ffffff !important;
    text-align: center !important;
}
div[data-baseweb="select"]:has(input[aria-label="Prompt Logic"]) svg {
    fill: #ffffff !important;
}
div[data-baseweb="select"]:has(input[aria-label="Prompt Logic"]) input {
    background-color: #000000 !important;
    color: #ffffff !important;
    text-align: center !important;
}
</style>
"""



PROMPT_ROW_SCROLL_STYLES = """
<style>
/* Keep prompt widgets in one horizontal line and allow horizontal scroll instead of squeeze */
div[class*="st-key-prompt_row_"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    padding-bottom: 0.4rem;
}

div[class*="st-key-prompt_row_"] div[data-testid="column"] {
    min-width: 220px !important;
    flex: 0 0 auto !important;
}

div[class*="st-key-prompt_row_"] div[data-testid="column"]:nth-child(3n + 2) {
    min-width: 88px !important;
}

div[class*="st-key-prompt_row_"] div[data-testid="column"]:nth-child(3n) {
    min-width: 110px !important;
}
</style>
"""
PARAMETER_DIVIDER = """
<div style="
    height:5px;
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
