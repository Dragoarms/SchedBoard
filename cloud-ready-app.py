import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# Page config
st.set_page_config(
    page_title="Camp Tracker",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Sheets setup
@st.cache_resource
def get_google_sheets_client():
    """Initialize Google Sheets client with credentials from secrets"""
    # Define the scope
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # Get credentials from Streamlit secrets
    creds_dict = st.secrets["connections"]["gsheets"]
    creds_dict = dict(creds_dict)  # Convert from AttrDict to regular dict
    
    # Create credentials object
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    # Authorize the client
    client = gspread.authorize(creds)
    
    return client

@st.cache_resource
def get_spreadsheet():
    """Get the Google Sheets spreadsheet"""
    client = get_google_sheets_client()
    
    # Get spreadsheet URL from secrets
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Open the spreadsheet
    spreadsheet = client.open_by_url(spreadsheet_url)
    
    return spreadsheet

def ensure_worksheets_exist(spreadsheet):
    """Ensure all required worksheets exist"""
    worksheet_names = [ws.title for ws in spreadsheet.worksheets()]
    
    # Define required worksheets with headers
    required_worksheets = {
        "Personnel": ["name", "phone", "supervisor", "supervisor_phone", "company", "created_at", "updated_at"],
        "Departures": ["id", "person_name", "destination", "departed_at", "expected_return", "actual_return", "phone", "supervisor", "company", "extensions_count", "is_overdue"],
        "Extensions": ["id", "departure_id", "hours_extended", "extended_at"]
    }
    
    for sheet_name, headers in required_worksheets.items():
        if sheet_name not in worksheet_names:
            # Create new worksheet
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            # Add headers
            worksheet.update(values=[headers], range_name='A1')

@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_personnel():
    """Get all personnel from manifest"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Personnel")
    
    # Get all values
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=['name', 'phone', 'supervisor', 'supervisor_phone', 'company', 'created_at', 'updated_at'])
    
    return df[df['name'] != '']  # Filter out empty rows

def add_personnel(name, phone=None, supervisor=None, supervisor_phone=None, company=None):
    """Add or update a person in the manifest"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Personnel")
    
    # Get existing data
    personnel_df = get_personnel()
    
    # Check if person exists
    if not personnel_df.empty and name in personnel_df['name'].values:
        # Update existing - find row number
        row_num = personnel_df[personnel_df['name'] == name].index[0] + 2  # +2 for header and 0-index
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
        # Add new person
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
    
    # Clear cache after modification
    get_all_departures.clear()
    get_active_departures.clear()
    
    # Clear cache after modification
    get_personnel.clear()

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_all_departures():
    """Get all departures"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if df.empty:
        return pd.DataFrame(columns=["id", "person_name", "destination", "departed_at", "expected_return", "actual_return", "phone", "supervisor", "company", "extensions_count", "is_overdue"])
    
    # Convert string columns to appropriate types
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['extensions_count'] = pd.to_numeric(df['extensions_count'], errors='coerce').fillna(0)
    
    return df

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_active_departures():
    """Get all active (not returned) departures"""
    df = get_all_departures()
    
    if df.empty:
        return pd.DataFrame()
    
    # Filter active departures (where actual_return is empty)
    df = df[df['actual_return'] == '']
    
    if df.empty:
        return pd.DataFrame()
    
    # Check if overdue
    df['expected_return'] = pd.to_datetime(df['expected_return'])
    df['is_overdue'] = df['expected_return'] < datetime.now()
    
    return df.sort_values('expected_return')

def add_departure(person_name, destination, expected_return, phone=None, supervisor=None, company=None):
    """Log a new departure"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    # Get current departures to generate ID
    departures_df = get_all_departures()
    new_id = 1 if departures_df.empty else int(departures_df['id'].max()) + 1
    
    # Add new departure
    new_row = [
        new_id,
        person_name,
        destination,
        datetime.now().isoformat(),
        expected_return.isoformat(),
        '',  # actual_return (empty)
        phone or '',
        supervisor or '',
        company or '',
        0,  # extensions_count
        False  # is_overdue
    ]
    
    worksheet.append_row(new_row)

def mark_returned(departure_id):
    """Mark a departure as returned"""
    spreadsheet = get_spreadsheet()
    worksheet = spreadsheet.worksheet("Departures")
    
    # Get all departures
    departures_df = get_all_departures()
    
    # Find the row to update
    row_index = departures_df[departures_df['id'] == departure_id].index[0]
    row_num = row_index + 2  # +2 for header and 0-index
    
    # Update actual_return column (column F, index 6)
    worksheet.update(values=[[datetime.now().isoformat()]], range_name=f'F{row_num}')
    
    # Clear cache after modification
    get_all_departures.clear()
    get_active_departures.clear()

def extend_departure(departure_id, hours):
    """Extend a departure's expected return time"""
    spreadsheet = get_spreadsheet()
    dep_worksheet = spreadsheet.worksheet("Departures")
    ext_worksheet = spreadsheet.worksheet("Extensions")
    
    # Get departure info
    departures_df = get_all_departures()
    dep_row = departures_df[departures_df['id'] == departure_id]
    
    if dep_row.empty:
        return
    
    row_index = dep_row.index[0]
    row_num = row_index + 2  # +2 for header and 0-index
    
    # Calculate new return time
    current_return = pd.to_datetime(dep_row['expected_return'].iloc[0])
    new_return = current_return + timedelta(hours=hours)
    
    # Update expected return and extension count
    current_extensions = int(dep_row['extensions_count'].iloc[0])
    dep_worksheet.update(values=[[new_return.isoformat()]], range_name=f'E{row_num}')  # Column E for expected_return
    dep_worksheet.update(values=[[current_extensions + 1]], range_name=f'J{row_num}')  # Column J for extensions_count
    
    # Add extension record
    extensions_data = ext_worksheet.get_all_records()
    ext_df = pd.DataFrame(extensions_data)
    new_ext_id = 1 if ext_df.empty else int(ext_df['id'].max()) + 1
    
    ext_worksheet.append_row([
        new_ext_id,
        departure_id,
        hours,
        datetime.now().isoformat()
    ])
    
    # Clear cache after modification
    get_all_departures.clear()
    get_active_departures.clear()

# Initialize spreadsheet and worksheets
try:
    spreadsheet = get_spreadsheet()
    ensure_worksheets_exist(spreadsheet)
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {str(e)}")
    st.stop()

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["📝 Departure Form", "📊 Tracker & Management"])

if page == "📝 Departure Form":
    st.title("🏕️ Camp Departure Form")
    
    # Get personnel list
    personnel_df = get_personnel()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create form
        with st.form("departure_form", clear_on_submit=True):
            # Name selection
            if not personnel_df.empty:
                name_options = ["-- Add New Person --"] + personnel_df['name'].tolist()
                selected_name = st.selectbox("Name", name_options)
                
                if selected_name == "-- Add New Person --":
                    new_name = st.text_input("Enter Name", key="new_name")
                    new_phone = st.text_input("Phone Number (optional)", key="new_phone")
                    new_supervisor = st.text_input("Supervisor (optional)", key="new_supervisor")
                    new_company = st.text_input("Company (optional)", key="new_company")
                else:
                    # Get person's details from manifest
                    person = personnel_df[personnel_df['name'] == selected_name].iloc[0]
                    new_name = None
            else:
                st.info("No personnel in manifest. Add new person below.")
                selected_name = None
                new_name = st.text_input("Name", key="new_name")
                new_phone = st.text_input("Phone Number (optional)", key="new_phone")
                new_supervisor = st.text_input("Supervisor (optional)", key="new_supervisor")
                new_company = st.text_input("Company (optional)", key="new_company")
            
            # Destination
            destination = st.text_input("Destination", key="destination")
            
            # Expected duration
            col_date, col_time = st.columns(2)
            with col_date:
                duration_hours = st.selectbox(
                    "Expected Duration",
                    options=[1, 2, 3, 4, 5, 6, 8, 12, 24],
                    index=2,  # Default to 3 hours
                    format_func=lambda x: f"{x} hour{'s' if x > 1 else ''}"
                )
            
            with col_time:
                departure_time = st.time_input("Departure Time", value=datetime.now().time())
            
            # Calculate expected return
            departure_datetime = datetime.combine(datetime.now().date(), departure_time)
            expected_return = departure_datetime + timedelta(hours=duration_hours)
            
            st.info(f"Expected return: {expected_return.strftime('%I:%M %p')}")
            
            # Submit button
            submitted = st.form_submit_button("Log Departure", use_container_width=True, type="primary")
            
            if submitted:
                if new_name:  # New person
                    if new_name.strip():
                        add_personnel(new_name, new_phone, new_supervisor, None, new_company)
                        add_departure(new_name, destination, expected_return, new_phone, new_supervisor, new_company)
                        st.success(f"✅ {new_name} logged as departed to {destination}")
                        st.rerun()
                    else:
                        st.error("Please enter a name")
                elif selected_name and selected_name != "-- Add New Person --":  # Existing person
                    person = personnel_df[personnel_df['name'] == selected_name].iloc[0]
                    add_departure(
                        selected_name, 
                        destination, 
                        expected_return,
                        person.get('phone'),
                        person.get('supervisor'),
                        person.get('company')
                    )
                    st.success(f"✅ {selected_name} logged as departed to {destination}")
                    st.rerun()
                else:
                    st.error("Please select or enter a name")
    
    with col2:
        # Quick stats
        st.markdown("### 📊 Current Status")
        active_departures = get_active_departures()
        
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Currently Out", len(active_departures))
        with metric_col2:
            overdue_count = len(active_departures[active_departures['is_overdue'] == True]) if not active_departures.empty else 0
            st.metric("Overdue", overdue_count, delta_color="inverse")
        
        if overdue_count > 0:
            st.error(f"⚠️ {overdue_count} people are overdue!")

elif page == "📊 Tracker & Management":
    st.title("🏕️ Camp Tracker & Management")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📍 Active Departures", "📋 Personnel Manifest", "📈 Statistics"])
    
    with tab1:
        active_departures = get_active_departures()
        
        if active_departures.empty:
            st.success("✅ Everyone is in camp!")
        else:
            # Display active departures
            for _, dep in active_departures.iterrows():
                # Calculate time remaining
                expected_return = pd.to_datetime(dep['expected_return'])
                time_remaining = expected_return - datetime.now()
                hours_remaining = time_remaining.total_seconds() / 3600
                
                # Determine status
                if dep['is_overdue']:
                    status_color = "🔴"
                    status_text = f"OVERDUE by {abs(int(hours_remaining))}h {abs(int((hours_remaining % 1) * 60))}m"
                elif hours_remaining < 0.5:
                    status_color = "🟡"
                    status_text = f"{int(hours_remaining * 60)}m remaining"
                else:
                    status_color = "🟢"
                    status_text = f"{int(hours_remaining)}h {int((hours_remaining % 1) * 60)}m remaining"
                
                # Create card
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {status_color} {dep['person_name']}")
                        st.caption(f"📍 {dep['destination']} • 🏢 {dep['company'] or 'N/A'}")
                        st.caption(f"🕐 Departed: {pd.to_datetime(dep['departed_at']).strftime('%I:%M %p')}")
                        if dep['extensions_count'] > 0:
                            st.caption(f"🔄 Extended {int(dep['extensions_count'])} time(s)")
                    
                    with col2:
                        st.markdown(f"**{status_text}**")
                        
                        # Quick extend buttons
                        col_ext1, col_ext2, col_ext3 = st.columns(3)
                        with col_ext1:
                            if st.button("+1h", key=f"ext1_{dep['id']}"):
                                extend_departure(dep['id'], 1)
                                st.rerun()
                        with col_ext2:
                            if st.button("+2h", key=f"ext2_{dep['id']}"):
                                extend_departure(dep['id'], 2)
                                st.rerun()
                        with col_ext3:
                            if st.button("+3h", key=f"ext3_{dep['id']}"):
                                extend_departure(dep['id'], 3)
                                st.rerun()
                    
                    with col3:
                        if st.button("✅ Mark Returned", key=f"return_{dep['id']}", type="primary"):
                            mark_returned(dep['id'])
                            st.success(f"{dep['person_name']} marked as returned")
                            st.rerun()
                    
                    st.divider()
    
    with tab2:
        st.subheader("Personnel Manifest Upload")
        
        # File uploader
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
                    # Process each row
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
        
        # Display current manifest
        st.subheader("Current Personnel Manifest")
        personnel_df = get_personnel()
        
        if not personnel_df.empty:
            # Add search/filter
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
            
            # Download manifest
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
        st.subheader("Statistics")
        
        # Get all departures
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
            
            # Most frequent destinations
            st.subheader("Top Destinations")
            top_destinations = all_departures['destination'].value_counts().head(10)
            if not top_destinations.empty:
                st.bar_chart(top_destinations)
        else:
            st.info("No departure data available yet.")

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)
