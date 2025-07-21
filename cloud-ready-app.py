import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import time
import base64
from streamlit_gps_location import gps_location_button

# Page config with custom icon
st.set_page_config(
    page_title="JMP Tracker",
    page_icon="Icons/logo.ico",
    layout="wide",
    initial_sidebar_state="collapsed"  # We'll use custom sidebars
)

# Custom CSS for dashboard styling and animations
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Pulsing red animation for overdue alerts */
    @keyframes pulse-red {
        0% { background-color: rgba(255, 0, 0, 0.1); }
        50% { background-color: rgba(255, 0, 0, 0.3); }
        100% { background-color: rgba(255, 0, 0, 0.1); }
    }
    
    .overdue-alert {
        animation: pulse-red 2s infinite;
        border: 2px solid red;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .overdue-container {
        background-color: #ffebee;
        border: 2px solid #f44336;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    /* Dashboard card styling */
    .departure-card {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #2196F3;
    }
    
    .departure-card.overdue {
        border-left-color: #f44336;
        background-color: #ffebee;
    }
    
    .departure-card.warning {
        border-left-color: #ff9800;
        background-color: #fff3e0;
    }
    
    .departure-card.safe {
        border-left-color: #4caf50;
        background-color: #e8f5e9;
    }
    
    /* Sidebar styling */
    .custom-sidebar {
        background-color: #f0f0f0;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    
    .sidebar-icon {
        font-size: 48px;
        margin-bottom: 10px;
    }
    
    /* Center logo */
    .center-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for sound alerts
def play_alert_sound():
    # Simple beep sound using Web Audio API
    sound_js = """
    <script>
    var audioContext = new (window.AudioContext || window.webkitAudioContext)();
    function playBeep() {
        var oscillator = audioContext.createOscillator();
        var gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
    
    // Play 3 beeps
    playBeep();
    setTimeout(playBeep, 600);
    setTimeout(playBeep, 1200);
    </script>
    """
    st.components.v1.html(sound_js, height=0)

# Authentication check (only for management page)
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "6218":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# Google Sheets setup functions (same as before)
@st.cache_resource
def get_google_sheets_client():
    """Initialize Google Sheets client with credentials from secrets"""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds_dict = st.secrets["connections"]["gsheets"]
    creds_dict = dict(creds_dict)
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    return client

@st.cache_resource
def get_spreadsheet():
    """Get the Google Sheets spreadsheet"""
    client = get_google_sheets_client()
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    spreadsheet = client.open_by_url(spreadsheet_url)
    return spreadsheet

def ensure_worksheets_exist(spreadsheet):
    """Ensure all required worksheets exist"""
    worksheet_names = [ws.title for ws in spreadsheet.worksheets()]
    
    required_worksheets = {
        "Personnel": ["name", "phone", "supervisor", "supervisor_phone", "company", "created_at", "updated_at"],
        "Departures": ["id", "person_name", "destination", "departed_at", "expected_return", "actual_return", 
                      "phone", "supervisor", "company", "extensions_count", "is_overdue", "group_id", "last_location"],
        "Extensions": ["id", "departure_id", "hours_extended", "extended_at", "gps_location"],
        "Groups": ["id", "group_name", "members", "responsible_person", "created_at"]
    }
    
    for sheet_name, headers in required_worksheets.items():
        if sheet_name not in worksheet_names:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            worksheet.update(values=[headers], range_name='A1')

# Data access functions (keeping the same as before, with minor additions for GPS)
@st.cache_data(ttl=60)
def get_personnel():
    """Get all personnel from manifest"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Personnel")
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=['name', 'phone', 'supervisor', 'supervisor_phone', 'company', 'created_at', 'updated_at'])
    
    return df[df['name'] != '']

@st.cache_data(ttl=30)
def get_groups():
    """Get all groups"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Groups")
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=['id', 'group_name', 'members', 'responsible_person', 'created_at'])
    
    return df

def add_personnel(name, phone=None, supervisor=None, supervisor_phone=None, company=None):
    """Add or update a person in the manifest"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Personnel")
    
    personnel_df = get_personnel()
    
    if not personnel_df.empty and name in personnel_df['name'].values:
        row_num = personnel_df[personnel_df['name'] == name].index[0] + 2
        worksheet.update(values=[[
            name,
            phone or '',
            supervisor or '',
            supervisor_phone or '',
            company or '',
            personnel_df[personnel_df['name'] == name]['created_at'].iloc[0],
            datetime.now().isoformat()
        ]], range_name=f'A{row_num}:G{row_num}')
    else:
        new_row = [
            name,
            phone or '',
            supervisor or '',
            supervisor_phone or '',
            company or '',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ]
        worksheet.append_row(new_row)
    
    get_personnel.clear()

@st.cache_data(ttl=30)
def get_all_departures():
    """Get all departures"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=["id", "person_name", "destination", "departed_at", "expected_return", 
                                   "actual_return", "phone", "supervisor", "company", "extensions_count", 
                                   "is_overdue", "group_id", "last_location"])
    
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['extensions_count'] = pd.to_numeric(df['extensions_count'], errors='coerce').fillna(0)
    
    return df

@st.cache_data(ttl=30)
def get_active_departures():
    """Get all active (not returned) departures"""
    df = get_all_departures()
    
    if df.empty:
        return pd.DataFrame()
    
    df = df[df['actual_return'] == '']
    
    if df.empty:
        return pd.DataFrame()
    
    df['expected_return'] = pd.to_datetime(df['expected_return'])
    df['is_overdue'] = df['expected_return'] < datetime.now()
    
    # Calculate time remaining
    df['time_remaining'] = (df['expected_return'] - datetime.now()).dt.total_seconds() / 3600
    
    return df.sort_values('time_remaining')

def add_departure(person_name, destination, expected_return, phone=None, supervisor=None, company=None, group_id=None):
    """Log a new departure"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    departures_df = get_all_departures()
    new_id = 1 if departures_df.empty else int(departures_df['id'].max()) + 1
    
    new_row = [
        new_id,
        person_name,
        destination,
        datetime.now().isoformat(),
        expected_return.isoformat(),
        '',
        phone or '',
        supervisor or '',
        company or '',
        0,
        False,
        group_id or '',
        ''  # last_location
    ]
    
    worksheet.append_row(new_row)
    
    get_all_departures.clear()
    get_active_departures.clear()

def mark_returned(departure_id):
    """Mark a departure as returned"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    departures_df = get_all_departures()
    
    row_index = departures_df[departures_df['id'] == departure_id].index[0]
    row_num = row_index + 2
    
    worksheet.update(values=[[datetime.now().isoformat()]], range_name=f'F{row_num}')
    
    get_all_departures.clear()
    get_active_departures.clear()

def extend_departure(departure_id, hours, gps_location=None):
    """Extend a departure's expected return time"""
    spreadsheet = get_spreadsheet()
    
    # Update departures
    departures_worksheet = spreadsheet.worksheet("Departures")
    departures_df = get_all_departures()
    
    row_index = departures_df[departures_df['id'] == departure_id].index[0]
    row_num = row_index + 2
    
    current_return = pd.to_datetime(departures_df.loc[row_index, 'expected_return'])
    new_return = current_return + timedelta(hours=hours)
    new_extensions_count = int(departures_df.loc[row_index, 'extensions_count']) + 1
    
    # Update expected return and extensions count
    departures_worksheet.update(values=[[new_return.isoformat()]], range_name=f'E{row_num}')
    departures_worksheet.update(values=[[new_extensions_count]], range_name=f'J{row_num}')
    
    # Update last location if provided
    if gps_location:
        departures_worksheet.update(values=[[str(gps_location)]], range_name=f'M{row_num}')
    
    # Add extension record
    extensions_worksheet = spreadsheet.worksheet("Extensions")
    extensions_df = pd.read_sql_query("SELECT * FROM Extensions", spreadsheet) if False else pd.DataFrame()
    new_ext_id = 1 if extensions_df.empty else len(extensions_df) + 1
    
    new_extension = [
        new_ext_id,
        departure_id,
        hours,
        datetime.now().isoformat(),
        str(gps_location) if gps_location else ''
    ]
    
    extensions_worksheet.append_row(new_extension)
    
    get_all_departures.clear()
    get_active_departures.clear()

def mark_group_returned(group_id):
    """Mark all departures in a group as returned"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    departures_df = get_all_departures()
    group_departures = departures_df[(departures_df['group_id'] == str(group_id)) & (departures_df['actual_return'] == '')]
    
    for _, dep in group_departures.iterrows():
        row_index = departures_df[departures_df['id'] == dep['id']].index[0]
        row_num = row_index + 2
        worksheet.update(values=[[datetime.now().isoformat()]], range_name=f'F{row_num}')
    
    get_all_departures.clear()
    get_active_departures.clear()

def add_group(group_name, members, responsible_person):
    """Add a new group"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Groups")
    
    groups_df = get_groups()
    new_id = 1 if groups_df.empty else int(groups_df['id'].max()) + 1
    
    new_row = [
        new_id,
        group_name,
        members,
        responsible_person,
        datetime.now().isoformat()
    ]
    
    worksheet.append_row(new_row)
    get_groups.clear()
    
    return new_id

# Initialize spreadsheet and worksheets
try:
    spreadsheet = get_spreadsheet()
    ensure_worksheets_exist(spreadsheet)
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {str(e)}")
    st.stop()

# Navigation
page = st.selectbox(
    "Navigation",
    ["🏠 Dashboard", "🚶 Departures", "🏃 Arrivals", "📊 Management"],
    label_visibility="collapsed"
)

# Alert sound management
if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = datetime.now() - timedelta(minutes=11)

# Dashboard Page
if page == "🏠 Dashboard":
    # Center logo at top
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.image("https://raw.githubusercontent.com/Dragoarms/SchedBoard/main/Icons/logo.ico", width=150)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">JMP Tracker Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time Personnel Tracking</p>', unsafe_allow_html=True)
    
    # Get active departures
    active_departures = get_active_departures()
    
    # Check for overdue and play sound if needed
    overdue_deps = active_departures[active_departures['is_overdue'] == True] if not active_departures.empty else pd.DataFrame()
    
    if not overdue_deps.empty:
        # Apply pulsing red background
        st.markdown("""
        <style>
            .stApp {
                animation: pulse-red 2s infinite;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Check if we should play alert sound (every 10 minutes)
        current_time = datetime.now()
        if (current_time - st.session_state.last_alert_time).total_seconds() > 600:
            play_alert_sound()
            st.session_state.last_alert_time = current_time
    
    # Main content area with custom sidebars
    left_col, main_col, right_col = st.columns([1, 3, 1])
    
    # Left sidebar - Departures
    with left_col:
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-icon">⬆️</div>', unsafe_allow_html=True)
        st.markdown("### Departures")
        st.markdown("Scan to log departure:")
        # Generate QR code for departures page (you'll need to replace with actual URL)
        departures_url = "https://jmpboard.streamlit.app/?page=departures"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={departures_url}", width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content - Active departures
    with main_col:
        # Overdue alert container
        if not overdue_deps.empty:
            st.markdown('<div class="overdue-container">', unsafe_allow_html=True)
            st.error(f"⚠️ **ALERT: {len(overdue_deps)} OVERDUE PERSONNEL**")
            
            for _, dep in overdue_deps.iterrows():
                hours_overdue = abs(dep['time_remaining'])
                st.markdown(f"""
                <div style="background-color: white; padding: 10px; margin: 5px 0; border-radius: 5px;">
                    <strong>{dep['person_name']}</strong> - {dep['destination']}<br>
                    Overdue by: {int(hours_overdue)}h {int((hours_overdue % 1) * 60)}m<br>
                    📞 {dep['phone']} | Supervisor: {dep['supervisor']}
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Active departures list
        st.subheader("Active Departures")
        
        if active_departures.empty:
            st.success("✅ All personnel are in camp!")
        else:
            # Group departures by group_id
            groups_dict = {}
            individual_deps = []
            
            for _, dep in active_departures.iterrows():
                if dep['group_id'] and dep['group_id'] != '':
                    if dep['group_id'] not in groups_dict:
                        groups_dict[dep['group_id']] = []
                    groups_dict[dep['group_id']].append(dep)
                else:
                    individual_deps.append(dep)
            
            # Combine and sort all departures
            all_departures = []
            
            # Add individual departures
            for dep in individual_deps:
                all_departures.append({
                    'type': 'individual',
                    'data': dep,
                    'time_remaining': dep['time_remaining']
                })
            
            # Add group departures
            groups_df = get_groups()
            for group_id, group_deps in groups_dict.items():
                # Get minimum time remaining for the group
                min_time = min([d['time_remaining'] for d in group_deps])
                group_info = groups_df[groups_df['id'] == int(group_id)].iloc[0] if not groups_df.empty else None
                
                all_departures.append({
                    'type': 'group',
                    'group_id': group_id,
                    'group_name': group_info['group_name'] if group_info is not None else f"Group {group_id}",
                    'members': group_deps,
                    'time_remaining': min_time
                })
            
            # Sort by time remaining
            all_departures.sort(key=lambda x: x['time_remaining'])
            
            # Display departures
            for item in all_departures:
                if item['type'] == 'individual':
                    dep = item['data']
                    
                    # Determine card style
                    if dep['is_overdue']:
                        card_class = "departure-card overdue"
                        status_icon = "🔴"
                    elif dep['time_remaining'] < 0.5:
                        card_class = "departure-card warning"
                        status_icon = "🟡"
                    else:
                        card_class = "departure-card safe"
                        status_icon = "🟢"
                    
                    # Time display
                    if dep['is_overdue']:
                        time_text = f"Overdue by {abs(int(dep['time_remaining']))}h {abs(int((dep['time_remaining'] % 1) * 60))}m"
                    else:
                        time_text = f"{int(dep['time_remaining'])}h {int((dep['time_remaining'] % 1) * 60)}m remaining"
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0;">{status_icon} {dep['person_name']}</h4>
                                <p style="margin: 5px 0;">📍 {dep['destination']}</p>
                                <p style="margin: 5px 0; color: #666;">
                                    Departed: {pd.to_datetime(dep['departed_at']).strftime('%I:%M %p')} | 
                                    Expected: {pd.to_datetime(dep['expected_return']).strftime('%I:%M %p')}
                                </p>
                                <p style="margin: 5px 0;">🏢 {dep['company'] or 'N/A'} | 📞 {dep['phone'] or 'N/A'}</p>
                            </div>
                            <div style="text-align: right;">
                                <h3 style="margin: 0; color: {'red' if dep['is_overdue'] else 'inherit'};">{time_text}</h3>
                                {f'<p style="margin: 5px 0;">🔄 Extended {int(dep["extensions_count"])} times</p>' if dep['extensions_count'] > 0 else ''}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                else:  # Group departure
                    # Determine group status
                    any_overdue = any(m['is_overdue'] for m in item['members'])
                    min_time = item['time_remaining']
                    
                    if any_overdue:
                        card_class = "departure-card overdue"
                        status_icon = "🔴"
                    elif min_time < 0.5:
                        card_class = "departure-card warning"
                        status_icon = "🟡"
                    else:
                        card_class = "departure-card safe"
                        status_icon = "🟢"
                    
                    # Time display for group
                    if any_overdue:
                        time_text = f"Overdue members!"
                    else:
                        time_text = f"Earliest return in {int(min_time)}h {int((min_time % 1) * 60)}m"
                    
                    members_list = ", ".join([m['person_name'] for m in item['members']])
                    destination = item['members'][0]['destination']  # Assuming same destination
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0;">{status_icon} 👥 {item['group_name']}</h4>
                                <p style="margin: 5px 0;">📍 {destination}</p>
                                <p style="margin: 5px 0; color: #666;">Members: {members_list}</p>
                                <p style="margin: 5px 0;">{len(item['members'])} people in group</p>
                            </div>
                            <div style="text-align: right;">
                                <h3 style="margin: 0; color: {'red' if any_overdue else 'inherit'};">{time_text}</h3>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Right sidebar - Arrivals
    with right_col:
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-icon">⬇️</div>', unsafe_allow_html=True)
        st.markdown("### Arrivals")
        st.markdown("Scan to check in:")
        # Generate QR code for arrivals page
        arrivals_url = "https://jmpboard.streamlit.app/?page=arrivals"
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={arrivals_url}", width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh every 30 seconds
    time.sleep(30)
    st.rerun()

# Departures Page
elif page == "🚶 Departures":
    col1, col2 = st.columns([0.5, 11.5])
    with col1:
        st.image("https://raw.githubusercontent.com/Dragoarms/SchedBoard/main/Icons/logo.ico", width=50)
    with col2:
        st.markdown('<p class="main-header">JMP - Departures</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="sub-header">Log personnel departures</p>', unsafe_allow_html=True)
    
    # Get personnel list
    personnel_df = get_personnel()
    groups_df = get_groups()
    
    # Departure type selection
    dep_type = st.radio("Departure Type", ["Individual", "Group"], horizontal=True)
    
    if dep_type == "Individual":
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Searchable dropdown for names
            all_names = ["➕ Add New Person"] + personnel_df['name'].tolist() if not personnel_df.empty else ["➕ Add New Person"]
            
            selected_name = st.selectbox(
                "Name",
                options=all_names,
                index=0,
                help="Start typing to filter names"
            )
            
            if selected_name == "➕ Add New Person":
                new_name = st.text_input("Enter Name")
                person_data = None
            else:
                new_name = None
                person_data = personnel_df[personnel_df['name'] == selected_name].iloc[0] if not personnel_df.empty else None
            
            # Always show these fields
            destination = st.text_input("Destination", key="destination")
            
            col_date, col_time = st.columns(2)
            with col_date:
                arrival_date = st.date_input("Expected Arrival Date", value=datetime.now().date())
            with col_time:
                arrival_time = st.time_input("Expected Arrival Time", value=(datetime.now() + timedelta(hours=3)).time())
            
            expected_arrival = datetime.combine(arrival_date, arrival_time)
            
            # Show departure time and calculated duration
            departure_time = datetime.now()
            duration = expected_arrival - departure_time
            hours = duration.total_seconds() / 3600
            
            st.info(f"📅 Departure: {departure_time.strftime('%I:%M %p')} | ⏱️ Duration: {int(hours)}h {int((hours % 1) * 60)}m")
            
            # Only show additional fields if they're missing from records
            if selected_name == "➕ Add New Person" or (person_data is not None and not person_data.get('phone')):
                phone = st.text_input("Phone Number")
            else:
                phone = person_data.get('phone') if person_data is not None else None
            
            if selected_name == "➕ Add New Person" or (person_data is not None and not person_data.get('supervisor')):
                supervisor = st.text_input("Supervisor")
            else:
                supervisor = person_data.get('supervisor') if person_data is not None else None
            
            if selected_name == "➕ Add New Person" or (person_data is not None and not person_data.get('company')):
                company = st.text_input("Company")
            else:
                company = person_data.get('company') if person_data is not None else None
            
            # Submit button
            if st.button("Log Departure", type="primary", use_container_width=True):
                if new_name:  # New person
                    if new_name.strip() and destination.strip():
                        add_personnel(new_name, phone, supervisor, None, company)
                        add_departure(new_name, destination, expected_arrival, phone, supervisor, company)
                        st.success(f"✅ {new_name} logged as departed to {destination}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Please enter name and destination")
                elif selected_name != "➕ Add New Person":  # Existing person
                    if destination.strip():
                        add_departure(selected_name, destination, expected_arrival,
                                    phone or person_data.get('phone'),
                                    supervisor or person_data.get('supervisor'),
                                    company or person_data.get('company'))
                        st.success(f"✅ {selected_name} logged as departed to {destination}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Please enter destination")
                else:
                    st.error("Please select or enter a name")
        
        with col2:
            # Quick stats
            st.markdown("### 📊 Current Status")
            active_departures = get_active_departures()
            
            total_out = len(active_departures)
            overdue_count = len(active_departures[active_departures['is_overdue'] == True]) if not active_departures.empty else 0
            
            st.metric("Currently Out", total_out)
            st.metric("Overdue", overdue_count, delta_color="inverse")
            
            if overdue_count > 0:
                st.error(f"⚠️ {overdue_count} people are overdue!")
    
    else:  # Group departure
        st.subheader("Group Departure")
        
        # Option to select existing group or create new
        group_option = st.radio("Group Option", ["Select Existing Group", "Create New Group"], horizontal=True)
        
        if group_option == "Select Existing Group" and not groups_df.empty:
            selected_group = st.selectbox("Select Group", groups_df['group_name'].tolist())
            group_data = groups_df[groups_df['group_name'] == selected_group].iloc[0]
            members = group_data['members'].split(',')
            responsible_person = group_data['responsible_person']
            
            st.info(f"**Members:** {', '.join(members)}")
            st.info(f"**Responsible Person:** {responsible_person}")
            
            destination = st.text_input("Destination for entire group")
            
            col_date, col_time = st.columns(2)
            with col_date:
                arrival_date = st.date_input("Expected Arrival Date", value=datetime.now().date(), key="group_date")
            with col_time:
                arrival_time = st.time_input("Expected Arrival Time", value=(datetime.now() + timedelta(hours=3)).time(), key="group_time")
            
            expected_arrival = datetime.combine(arrival_date, arrival_time)
            
            if st.button("Log Group Departure", type="primary"):
                if destination.strip():
                    group_id = group_data['id']
                    # Log departure for each member
                    for member in members:
                        member = member.strip()
                        add_departure(member, destination, expected_arrival, group_id=group_id)
                    st.success(f"✅ Group '{selected_group}' logged as departed to {destination}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please enter destination")
        
        else:  # Create new group
            group_name = st.text_input("Group Name (e.g., 'Night Shift Team')")
            members_input = st.text_area("Members (one per line)", height=150)
            responsible_person = st.text_input("Responsible Person")
            
            if st.button("Create Group", type="secondary"):
                if group_name and members_input and responsible_person:
                    members = [m.strip() for m in members_input.split('\n') if m.strip()]
                    members_str = ','.join(members)
                    
                    # Add all members to personnel if they don't exist
                    for member in members:
                        personnel_df = get_personnel()
                        if member not in personnel_df['name'].values:
                            add_personnel(member)
                    
                    group_id = add_group(group_name, members_str, responsible_person)
                    st.success(f"✅ Group '{group_name}' created with {len(members)} members")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please fill in all fields")

# Arrivals Page
elif page == "🏃 Arrivals":
    st.markdown('<p class="main-header">JMP - Arrivals</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Mark personnel as returned</p>', unsafe_allow_html=True)
    
    active_departures = get_active_departures()
    
    if active_departures.empty:
        st.success("✅ Everyone is in camp!")
    else:
        # Tab view for individual vs group returns
        tab1, tab2, tab3 = st.tabs(["Individual Returns", "Group Returns", "Extend Time"])
        
        with tab1:
            # Group by overdue status
            overdue = active_departures[active_departures['is_overdue'] == True]
            on_time = active_departures[active_departures['is_overdue'] == False]
            
            if not overdue.empty:
                st.error(f"### 🔴 Overdue ({len(overdue)})")
                for _, dep in overdue.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{dep['person_name']}** → {dep['destination']}")
                        st.caption(f"Overdue by {abs(int(dep['time_remaining']))}h {abs(int((dep['time_remaining'] % 1) * 60))}m")
                    
                    with col2:
                        st.caption(f"Expected: {pd.to_datetime(dep['expected_return']).strftime('%I:%M %p')}")
                        st.caption(f"Departed: {pd.to_datetime(dep['departed_at']).strftime('%I:%M %p')}")
                    
                    with col3:
                        if st.button("✅ Returned", key=f"return_{dep['id']}", type="primary"):
                            mark_returned(dep['id'])
                            st.success(f"{dep['person_name']} marked as returned")
                            time.sleep(1)
                            st.rerun()
                
                st.divider()
            
            if not on_time.empty:
                st.success(f"### 🟢 On Time ({len(on_time)})")
                for _, dep in on_time.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{dep['person_name']}** → {dep['destination']}")
                        if dep['time_remaining'] > 0:
                            st.caption(f"{int(dep['time_remaining'])}h {int((dep['time_remaining'] % 1) * 60)}m remaining")
                        else:
                            st.caption("Due now")
                    
                    with col2:
                        st.caption(f"Expected: {pd.to_datetime(dep['expected_return']).strftime('%I:%M %p')}")
                        st.caption(f"Departed: {pd.to_datetime(dep['departed_at']).strftime('%I:%M %p')}")
                    
                    with col3:
                        if st.button("✅ Returned", key=f"return_{dep['id']}", type="primary"):
                            mark_returned(dep['id'])
                            st.success(f"{dep['person_name']} marked as returned")
                            time.sleep(1)
                            st.rerun()
        
        with tab2:
            # Show active group departures
            groups_out = active_departures[active_departures['group_id'] != ''].groupby('group_id')
            
            if len(groups_out) > 0:
                st.info(f"### 👥 Active Group Departures ({len(groups_out)})")
                
                for group_id, group_deps in groups_out:
                    groups_df = get_groups()
                    if not groups_df.empty:
                        group_info = groups_df[groups_df['id'] == int(group_id)]
                        if not group_info.empty:
                            group_name = group_info.iloc[0]['group_name']
                            st.markdown(f"**{group_name}** ({len(group_deps)} members out)")
                            
                            # Show group members
                            members_list = ", ".join(group_deps['person_name'].tolist())
                            st.caption(f"Members: {members_list}")
                            
                            # Check if any are overdue
                            any_overdue = any(group_deps['is_overdue'])
                            if any_overdue:
                                st.error("⚠️ Some members are overdue!")
                            
                            if st.button(f"✅ Mark Entire Group as Returned", key=f"group_return_{group_id}", type="primary"):
                                mark_group_returned(group_id)
                                st.success(f"All members of '{group_name}' marked as returned")
                                time.sleep(1)
                                st.rerun()
                            
                            st.divider()
            else:
                st.info("No active group departures")
        
        with tab3:
            st.subheader("Extend Time")
            st.info("Select a person to extend their expected return time")
            
            # Select person to extend
            person_names = active_departures['person_name'].tolist()
            selected_person = st.selectbox("Select Person", person_names)
            
            if selected_person:
                person_data = active_departures[active_departures['person_name'] == selected_person].iloc[0]
                
                st.write(f"**Current Expected Return:** {pd.to_datetime(person_data['expected_return']).strftime('%I:%M %p')}")
                
                # Extension options
                col1, col2 = st.columns(2)
                with col1:
                    hours_to_extend = st.number_input("Hours to Extend", min_value=1, max_value=24, value=1)
                
                with col2:
                    # GPS location button
                    st.write("Optional: Share current location")
                    gps_data = gps_location_button(
                        buttonText="📍 Get GPS Location",
                        key=f"gps_{person_data['id']}"
                    )
                
                if st.button("Extend Time", type="primary"):
                    extend_departure(person_data['id'], hours_to_extend, gps_data)
                    st.success(f"✅ Extended {selected_person}'s return time by {hours_to_extend} hours")
                    if gps_data:
                        st.info(f"📍 Location recorded: {gps_data.get('lat', 'N/A')}, {gps_data.get('lon', 'N/A')}")
                    time.sleep(1)
                    st.rerun()

# Management Page (Password Protected)
elif page == "📊 Management":
    # Password protection
    if not check_password():
        st.stop()
    
    st.markdown('<p class="main-header">JMP - Management</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Monitor and manage all personnel</p>', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Active Departures", "📋 Personnel Manifest", "👥 Groups", "📈 Statistics"])
    
    with tab1:
        active_departures = get_active_departures()
        
        if active_departures.empty:
            st.success("✅ Everyone is in camp!")
        else:
            # Add refresh button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Refresh Data"):
                    get_personnel.clear()
                    get_all_departures.clear()
                    get_active_departures.clear()
                    st.rerun()
            
            # Display active departures with management options
            for _, dep in active_departures.iterrows():
                if dep['is_overdue']:
                    status_color = "🔴"
                    status_text = f"OVERDUE by {abs(int(dep['time_remaining']))}h {abs(int((dep['time_remaining'] % 1) * 60))}m"
                elif dep['time_remaining'] < 0.5:
                    status_color = "🟡"
                    status_text = f"{int(dep['time_remaining'] * 60)}m remaining"
                else:
                    status_color = "🟢"
                    status_text = f"{int(dep['time_remaining'])}h {int((dep['time_remaining'] % 1) * 60)}m remaining"
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {status_color} {dep['person_name']}")
                        st.caption(f"📍 {dep['destination']} • 🏢 {dep['company'] or 'N/A'}")
                        st.caption(f"🕐 Departed: {pd.to_datetime(dep['departed_at']).strftime('%I:%M %p')}")
                        if dep['extensions_count'] > 0:
                            st.caption(f"🔄 Extended {int(dep['extensions_count'])} time(s)")
                        if dep.get('last_location'):
                            st.caption(f"📍 Last Location: {dep['last_location']}")
                    
                    with col2:
                        st.markdown(f"**{status_text}**")
                        st.caption(f"Expected: {pd.to_datetime(dep['expected_return']).strftime('%I:%M %p')}")
                        
                        # Quick extension buttons
                        col_ext1, col_ext2 = st.columns(2)
                        with col_ext1:
                            if st.button("+1h", key=f"ext1_{dep['id']}"):
                                extend_departure(dep['id'], 1)
                                st.rerun()
                        with col_ext2:
                            if st.button("+2h", key=f"ext2_{dep['id']}"):
                                extend_departure(dep['id'], 2)
                                st.rerun()
                    
                    with col3:
                        if st.button("✅ Mark Returned", key=f"mgmt_return_{dep['id']}", type="primary"):
                            mark_returned(dep['id'])
                            st.success(f"{dep['person_name']} marked as returned")
                            time.sleep(1)
                            st.rerun()
                        
                        # Contact info
                        if dep['phone']:
                            st.caption(f"📞 {dep['phone']}")
                        if dep['supervisor']:
                            st.caption(f"👤 {dep['supervisor']}")
                    
                    st.divider()
    
    with tab2:
        st.subheader("Personnel Manifest Upload")
        
        uploaded_file = st.file_uploader(
            "Upload CSV file", 
            type=['csv'],
            help="CSV should contain: Name, Phone, Supervisor, SupervisorPhone, Company"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Upload to Manifest", type="primary"):
                    for _, row in df.iterrows():
                        if pd.notna(row.get('name', row.get('Name', row.get('full name')))):
                            name = row.get('name', row.get('Name', row.get('full name')))
                            phone = row.get('phone', row.get('Phone', row.get('mobile')))
                            supervisor = row.get('supervisor', row.get('Supervisor', row.get('manager')))
                            supervisor_phone = row.get('supervisor_phone', row.get('SupervisorPhone'))
                            company = row.get('company', row.get('Company', row.get('organization')))
                            
                            add_personnel(str(name), str(phone) if pd.notna(phone) else None, 
                                        str(supervisor) if pd.notna(supervisor) else None, 
                                        str(supervisor_phone) if pd.notna(supervisor_phone) else None, 
                                        str(company) if pd.notna(company) else None)
                    
                    st.success(f"✅ Uploaded {len(df)} records to manifest")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
        
        st.subheader("Current Personnel Manifest")
        personnel_df = get_personnel()
        
        if not personnel_df.empty:
            search = st.text_input("Search personnel", placeholder="Type to search...")
            if search:
                mask = personnel_df['name'].str.contains(search, case=False, na=False)
                filtered_df = personnel_df[mask]
            else:
                filtered_df = personnel_df
            
            st.dataframe(
                filtered_df[['name', 'phone', 'supervisor', 'company']], 
                use_container_width=True,
                hide_index=True
            )
            
            csv = personnel_df.to_csv(index=False)
            st.download_button(
                label="Download Manifest as CSV",
                data=csv,
                file_name=f"personnel_manifest_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No personnel in manifest yet. Upload a CSV to get started.")
    
    with tab3:
        st.subheader("Group Management")
        
        groups_df = get_groups()
        
        if not groups_df.empty:
            for _, group in groups_df.iterrows():
                with st.expander(f"**{group['group_name']}** - {group['responsible_person']}"):
                    members = group['members'].split(',')
                    st.write(f"**Members ({len(members)}):**")
                    for member in members:
                        st.write(f"- {member.strip()}")
                    st.caption(f"Created: {group['created_at']}")
        else:
            st.info("No groups created yet.")
    
    with tab4:
        st.subheader("Statistics")
        
        all_departures = get_all_departures()
        
        if not all_departures.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_out = len(get_active_departures())
                st.metric("Currently Out", total_out)
            
            with col2:
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if 'actual_return' in all_departures.columns:
                    all_departures['actual_return_dt'] = pd.to_datetime(all_departures['actual_return'], errors='coerce')
                    today_returns = len(all_departures[
                        (all_departures['actual_return_dt'] >= today_start) & 
                        (all_departures['actual_return_dt'].notna())
                    ])
                else:
                    today_returns = 0
                st.metric("Returned Today", today_returns)
            
            with col3:
                all_departures['departed_at'] = pd.to_datetime(all_departures['departed_at'])
                total_departures_today = len(all_departures[
                    all_departures['departed_at'] >= today_start
                ])
                st.metric("Departures Today", total_departures_today)
            
            with col4:
                completed = all_departures[all_departures['actual_return'] != ''].copy()
                if not completed.empty:
                    completed['actual_return_dt'] = pd.to_datetime(completed['actual_return'])
                    completed['departed_at_dt'] = pd.to_datetime(completed['departed_at'])
                    completed['duration'] = (completed['actual_return_dt'] - completed['departed_at_dt']).dt.total_seconds() / 3600
                    avg_duration = completed['duration'].mean()
                    st.metric("Avg Duration", f"{avg_duration:.1f}h")
                else:
                    st.metric("Avg Duration", "N/A")
            
            st.subheader("Top Destinations")
            top_destinations = all_departures['destination'].value_counts().head(10)
            if not top_destinations.empty:
                st.bar_chart(top_destinations)
