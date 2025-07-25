"""
JMP Tracker - Main Application
Journey Management Plan tracking system for personnel safety
"""

import streamlit as st
from config import PAGE_CONFIG, get_text
from database import get_spreadsheet, ensure_worksheets_exist
from ui import apply_custom_css, render_language_selector
from pages.dashboard import render_dashboard
from pages.departures import render_departures
from pages.arrivals import render_arrivals
from pages.management import render_management

# Page configuration
st.set_page_config(**PAGE_CONFIG)

# Apply custom CSS
apply_custom_css()

# Initialize session state
if 'language' not in st.session_state:
    st.session_state.language = 'en'

if "last_alert_time" not in st.session_state:
    from datetime import datetime, timedelta
    from config import LOCAL_TIMEZONE, ALERT_INTERVAL_MINUTES
    st.session_state.last_alert_time = datetime.now(LOCAL_TIMEZONE) - timedelta(minutes=ALERT_INTERVAL_MINUTES+1)

# Language selector
render_language_selector()

# Get current language
lang = st.session_state.get('language', 'en')

# Initialize spreadsheet and worksheets
try:
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        ensure_worksheets_exist(spreadsheet)
    else:
        st.error(get_text('error_connecting_sheets', lang))
        st.stop()
except Exception as e:
    st.error(f"{get_text('error', lang)}: {str(e)}")
    st.stop()

# Navigation
page_options = [
    get_text('dashboard', lang),
    get_text('departures', lang),
    get_text('arrivals', lang),
    get_text('management', lang)
]

# Check for URL parameters (for QR code navigation)
try:
    query_params = st.experimental_get_query_params()
    if 'page' in query_params:
        page_param = query_params['page'][0].lower()
        if page_param == 'departures':
            default_index = 1
        elif page_param == 'arrivals':
            default_index = 2
        elif page_param == 'management':
            default_index = 3
        else:
            default_index = 0
    else:
        default_index = 0
except:
    # Fallback for newer Streamlit versions
    default_index = 0

page = st.selectbox(
    "Navigation",
    page_options,
    index=default_index,
    label_visibility="collapsed"
)

# Render the selected page
if page == get_text('dashboard', lang):
    render_dashboard()
elif page == get_text('departures', lang):
    render_departures()
elif page == get_text('arrivals', lang):
    render_arrivals()
elif page == get_text('management', lang):
    render_management()
