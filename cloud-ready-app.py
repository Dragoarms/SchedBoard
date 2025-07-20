import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Page config
st.set_page_config(
    page_title="Camp Tracker",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Google Sheets connection
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# Sheet names
PERSONNEL_SHEET = "Personnel"
DEPARTURES_SHEET = "Departures"
EXTENSIONS_SHEET = "Extensions"

def init_sheets(conn):
    """Initialize sheets if they don't exist"""
    try:
        # Try to read existing sheets
        conn.read(worksheet=PERSONNEL_SHEET)
        conn.read(worksheet=DEPARTURES_SHEET)
        conn.read(worksheet=EXTENSIONS_SHEET)
    except:
        # Create initial empty dataframes
        personnel_df = pd.DataFrame(columns=['name', 'phone', 'supervisor', 'supervisor_phone', 'company', 'created_at', 'updated_at'])
        departures_df = pd.DataFrame(columns=['id', 'person_name', 'destination', 'departed_at', 'expected_return', 'actual_return', 'phone', 'supervisor', 'company', 'extensions_count', 'is_overdue'])
        extensions_df = pd.DataFrame(columns=['id', 'departure_id', 'hours_extended', 'extended_at'])
        
        # Create sheets
        conn.create(worksheet=PERSONNEL_SHEET, data=personnel_df)
        conn.create(worksheet=DEPARTURES_SHEET, data=departures_df)
        conn.create(worksheet=EXTENSIONS_SHEET, data=extensions_df)

def get_personnel(conn):
    """Get all personnel from manifest"""
    df = conn.read(worksheet=PERSONNEL_SHEET, usecols=list(range(7)))
    return df.dropna(subset=['name'])

def add_personnel(conn, name, phone=None, supervisor=None, supervisor_phone=None, company=None):
    """Add or update a person in the manifest"""
    personnel_df = get_personnel(conn)
    
    # Check if person exists
    if name in personnel_df['name'].values:
        # Update existing
        idx = personnel_df[personnel_df['name'] == name].index[0]
        personnel_df.loc[idx] = {
            'name': name,
            'phone': phone,
            'supervisor': supervisor,
            'supervisor_phone': supervisor_phone,
            'company': company,
            'created_at': personnel_df.loc[idx, 'created_at'],
            'updated_at': datetime.now().isoformat()
        }
    else:
        # Add new
        new_person = pd.DataFrame([{
            'name': name,
            'phone': phone,
            'supervisor': supervisor,
            'supervisor_phone': supervisor_phone,
            'company': company,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }])
        personnel_df = pd.concat([personnel_df, new_person], ignore_index=True)
    
    # Update sheet
    conn.update(worksheet=PERSONNEL_SHEET, data=personnel_df)

def get_active_departures(conn):
    """Get all active (not returned) departures"""
    df = conn.read(worksheet=DEPARTURES_SHEET, usecols=list(range(11)))
    
    if df.empty:
        return pd.DataFrame()
    
    # Filter active departures
    df = df[df['actual_return'].isna()]
    
    # Check if overdue
    df['expected_return'] = pd.to_datetime(df['expected_return'])
    df['is_overdue'] = df['expected_return'] < datetime.now()
    
    return df.sort_values('expected_return')

def add_departure(conn, person_name, destination, expected_return, phone=None, supervisor=None, company=None):
    """Log a new departure"""
    departures_df = conn.read(worksheet=DEPARTURES_SHEET, usecols=list(range(11)))
    
    # Generate new ID
    new_id = len(departures_df) + 1
    
    # Add new departure
    new_departure = pd.DataFrame([{
        'id': new_id,
        'person_name': person_name,
        'destination': destination,
        'departed_at': datetime.now().isoformat(),
        'expected_return': expected_return.isoformat(),
        'actual_return': None,
        'phone': phone,
        'supervisor': supervisor,
        'company': company,
        'extensions_count': 0,
        'is_overdue': False
    }])
    
    departures_df = pd.concat([departures_df, new_departure], ignore_index=True)
    conn.update(worksheet=DEPARTURES_SHEET, data=departures_df)

def mark_returned(conn, departure_id):
    """Mark a departure as returned"""
    departures_df = conn.read(worksheet=DEPARTURES_SHEET, usecols=list(range(11)))
    
    # Update the departure
    idx = departures_df[departures_df['id'] == departure_id].index[0]
    departures_df.loc[idx, 'actual_return'] = datetime.now().isoformat()
    
    conn.update(worksheet=DEPARTURES_SHEET, data=departures_df)

def extend_departure(conn, departure_id, hours):
    """Extend a departure's expected return time"""
    # Update departures
    departures_df = conn.read(worksheet=DEPARTURES_SHEET, usecols=list(range(11)))
    idx = departures_df[departures_df['id'] == departure_id].index[0]
    
    current_return = pd.to_datetime(departures_df.loc[idx, 'expected_return'])
    new_return = current_return + timedelta(hours=hours)
    
    departures_df.loc[idx, 'expected_return'] = new_return.isoformat()
    departures_df.loc[idx, 'extensions_count'] += 1
    
    conn.update(worksheet=DEPARTURES_SHEET, data=departures_df)
    
    # Add extension record
    extensions_df = conn.read(worksheet=EXTENSIONS_SHEET, usecols=list(range(4)))
    new_extension = pd.DataFrame([{
        'id': len(extensions_df) + 1,
        'departure_id': departure_id,
        'hours_extended': hours,
        'extended_at': datetime.now().isoformat()
    }])
    
    extensions_df = pd.concat([extensions_df, new_extension], ignore_index=True)
    conn.update(worksheet=EXTENSIONS_SHEET, data=extensions_df)

# Main app
conn = get_connection()

# Initialize sheets on first run
if 'initialized' not in st.session_state:
    init_sheets(conn)
    st.session_state.initialized = True

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["📝 Departure Form", "📊 Tracker & Management"])

if page == "📝 Departure Form":
    st.title("🏕️ Camp Departure Form")
    
    # Get personnel list
    personnel_df = get_personnel(conn)
    
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
                        add_personnel(conn, new_name, new_phone, new_supervisor, None, new_company)
                        add_departure(conn, new_name, destination, expected_return, new_phone, new_supervisor, new_company)
                        st.success(f"✅ {new_name} logged as departed to {destination}")
                        st.rerun()
                    else:
                        st.error("Please enter a name")
                elif selected_name and selected_name != "-- Add New Person --":  # Existing person
                    person = personnel_df[personnel_df['name'] == selected_name].iloc[0]
                    add_departure(
                        conn,
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
        active_departures = get_active_departures(conn)
        
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
        active_departures = get_active_departures(conn)
        
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
                                extend_departure(conn, dep['id'], 1)
                                st.rerun()
                        with col_ext2:
                            if st.button("+2h", key=f"ext2_{dep['id']}"):
                                extend_departure(conn, dep['id'], 2)
                                st.rerun()
                        with col_ext3:
                            if st.button("+3h", key=f"ext3_{dep['id']}"):
                                extend_departure(conn, dep['id'], 3)
                                st.rerun()
                    
                    with col3:
                        if st.button("✅ Mark Returned", key=f"return_{dep['id']}", type="primary"):
                            mark_returned(conn, dep['id'])
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
                            
                            add_personnel(conn, name, phone, supervisor, supervisor_phone, company)
                    
                    st.success(f"✅ Uploaded {len(df)} records to manifest")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
        
        # Display current manifest
        st.subheader("Current Personnel Manifest")
        personnel_df = get_personnel(conn)
        
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
        all_departures = conn.read(worksheet=DEPARTURES_SHEET, usecols=list(range(11)))
        
        if not all_departures.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_out = len(get_active_departures(conn))
                st.metric("Currently Out", total_out)
            
            with col2:
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                all_departures['actual_return'] = pd.to_datetime(all_departures['actual_return'])
                today_returns = len(all_departures[
                    (all_departures['actual_return'] >= today_start) & 
                    (all_departures['actual_return'].notna())
                ])
                st.metric("Returned Today", today_returns)
            
            with col3:
                all_departures['departed_at'] = pd.to_datetime(all_departures['departed_at'])
                total_departures_today = len(all_departures[
                    all_departures['departed_at'] >= today_start
                ])
                st.metric("Departures Today", total_departures_today)
            
            with col4:
                completed = all_departures[all_departures['actual_return'].notna()].copy()
                if not completed.empty:
                    completed['duration'] = (completed['actual_return'] - completed['departed_at']).dt.total_seconds() / 3600
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