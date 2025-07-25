import streamlit as st
from config import (
    SHEET_HEADERS, SHEET_NAMES,
    LOCAL_TIMEZONE, APP_BASE_URL, KMZ_URL,
    get_current_time, PAGE_CONFIG
)
from database import get_spreadsheet
import traceback

st.set_page_config(page_title="Debug Info", layout="wide")

st.title("🛠️ Debug Panel")
st.markdown("---")

# Section: Config Constants
st.header("Config Constants")

try:
    st.subheader("📑 SHEET_HEADERS")
    st.json(SHEET_HEADERS)

    st.subheader("📄 SHEET_NAMES")
    st.json(SHEET_NAMES)

    st.success("✅ Config constants loaded successfully.")
except Exception as e:
    st.error(f"❌ Failed to load SHEET_HEADERS or SHEET_NAMES:\n{str(e)}")
    st.code(traceback.format_exc())

# Section: Other Config
st.header("General Configuration")
st.write("Local Timezone:", LOCAL_TIMEZONE)
st.write("App Base URL:", APP_BASE_URL)
st.write("KMZ URL:", KMZ_URL)
st.write("Current Time:", get_current_time().isoformat())

# Section: Google Sheets
st.header("Google Sheets Connection Test")

try:
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        st.success("✅ Spreadsheet loaded successfully")
        st.write("Title:", spreadsheet.title)
        st.write("Worksheets:", [ws.title for ws in spreadsheet.worksheets()])
    else:
        st.error("❌ Spreadsheet returned as None.")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
    st.code(traceback.format_exc())

# Secrets test
st.header("Secrets Status")
try:
    creds = st.secrets["connections"]["gsheets"]
    st.success("✅ Google Sheets credentials found in st.secrets")
    st.write("Spreadsheet URL:", creds["spreadsheet"])
except Exception as e:
    st.error("❌ Missing or malformed Google Sheets secrets.")
    st.code(traceback.format_exc())
