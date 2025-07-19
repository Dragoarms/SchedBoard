"""
Camp Departure Tracker - Streamlit Version
Simple, remote-accessible, with pre-populated camp members
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import uuid
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Camp Tracker",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'departures' not in st.session_state:
    st.session_state.departures = []
if 'last_check' not in st.session_state:
    st.session_state.last_check = datetime.now()

# File paths
DATA_DIR = Path("camp_data")
DATA_DIR.mkdir(exist_ok=True)
DEPARTURES_FILE = DATA_DIR / "departures.json"
MEMBERS_FILE = DATA_DIR / "camp_members.csv"

# Load/Save functions
def load_departures():
    if DEPARTURES_FILE.exists():
        with open(DEPARTURES_FILE, 'r') as f:
            data = json.load(f)
            # Convert string dates back to datetime
            for d in data:
                d['departed_at'] = datetime.fromisoformat(d['departed_at'])
                d['expected_return'] = datetime.fromisoformat(d['expected_return'])
                if d.get('returned_at'):
                    d['returned_at'] = datetime.fromisoformat(d['returned_at'])
            return data
    return []

def save_departures(departures):
    # Convert datetime to string for JSON
    data = []
    for d in departures.copy():
        d_copy = d.copy()
        d_copy['departed_at'] = d['departed_at'].isoformat()
        d_copy['expected_return'] = d['expected_return'].isoformat()
        if d.get('returned_at'):
            d_copy['returned_at'] = d['returned_at'].isoformat()
        data.append(d_copy)
    
    with open(DEPARTURES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_camp_members():
    """Load camp members from CSV or create sample data"""
    if MEMBERS_FILE.exists():
        return pd.read_csv(MEMBERS_FILE)
    else:
        # Create sample data
        sample_data = {
            'name': ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown', 'Charlie Davis'],
            'phone': ['+1-555-0101', '+1-555-0102', '+1-555-0103', '+1-555-0104', '+1-555-0105'],
            'supervisor': ['Mike Johnson', 'Mike Johnson', 'Sarah Lee', 'Sarah Lee', 'Mike Johnson'],
            'supervisor_phone': ['+1-555-0001', '+1-555-0001', '+1-555-0002', '+1-555-0002', '+1-555-0001'],
            'cabin': ['A', 'A', 'B', 'B', 'C']
        }
        df = pd.DataFrame(sample_data)
        df.to_csv(MEMBERS_FILE, index=False)
        return df

def generate_update_code():
    """Generate a simple 6-character code"""
    return str(uuid.uuid4())[:6].upper()

# Load data
st.session_state.departures = load_departures()
camp_members = load_camp_members()

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .overdue-alert {
        background-color: #fee2e2;
        border: 2px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    .departure-card {
        border: 1px solid #e5e7eb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        background-color: #f9fafb;
    }
    .overdue-card {
        background-color: #fee2e2;
        border-color: #ef4444;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏕️ Camp Departure Tracker")

# Check for overdue
active_departures = [d for d in st.session_state.departures if not d.get('returned_at')]
overdue = []
now = datetime.now()

for d in active_departures:
    if d['expected_return'] < now:
        overdue.append(d)

# Alert banner for overdue
if overdue:
    st.markdown(f"""
    <div class="overdue-alert">
        <h2>⚠️ {len(overdue)} PEOPLE OVERDUE!</h2>
        <p>{'<br>'.join([f"• {d['name']} - Expected back {d['expected_return'].strftime('%I:%M %p')}" for d in overdue])}</p>
    </div>
    """, unsafe_allow_html=True)

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Currently Out", len(active_departures))
with col2:
    st.metric("Overdue", len(overdue))
with col3:
    today_returns = len([d for d in st.session_state.departures 
                        if d.get('returned_at') and d['returned_at'].date() == datetime.now().date()])
    st.metric("Returned Today", today_returns)
with col4:
    st.metric("Total in Camp", len(camp_members) - len(active_departures))

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🚶 New Departure", "📍 Currently Out", "👥 Camp Members", "📱 Update Return Time"])

# Tab 1: New Departure
with tab1:
    st.header("Log New Departure")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Quick select from camp members
        st.subheader("Quick Select Member")
        
        # Search box
        search = st.text_input("🔍 Search by name", placeholder="Start typing...")
        
        # Filter members
        if search:
            filtered_members = camp_members[camp_members['name'].str.contains(search, case=False)]
        else:
            filtered_members = camp_members
        
        # Show members not currently out
        current_out_names = [d['name'] for d in active_departures]
        available_members = filtered_members[~filtered_members['name'].isin(current_out_names)]
        
        if len(available_members) > 0:
            # Create selection buttons
            st.write("**Available Members:**")
            
            # Create columns for member buttons
            cols = st.columns(3)
            for idx, member in available_members.iterrows():
                col_idx = idx % 3
                with cols[col_idx]:
                    if st.button(f"🚶 {member['name']}", key=f"select_{idx}"):
                        st.session_state.selected_member = member
        else:
            st.info("All members matching search are currently out")
    
    with col2:
        st.subheader("Departure Details")
        
        # Get selected member info
        if 'selected_member' in st.session_state:
            member = st.session_state.selected_member
            name = member['name']
            phone = member['phone']
            supervisor = member['supervisor']
            supervisor_phone = member['supervisor_phone']
            
            st.success(f"Selected: **{name}**")
            st.caption(f"Phone: {phone}")
            st.caption(f"Supervisor: {supervisor} ({supervisor_phone})")
        else:
            st.info("Select a member or enter manually")
            name = st.text_input("Name (manual entry)")
            phone = st.text_input("Phone (optional)")
            supervisor = ""
            supervisor_phone = ""
        
        destination = st.text_input("Destination", placeholder="Town, hiking trail, etc.")
        
        # Duration selection
        duration_options = {
            "1 hour": 1, "2 hours": 2, "3 hours": 3, "4 hours": 4,
            "5 hours": 5, "6 hours": 6, "8 hours": 8, "12 hours": 12,
            "24 hours": 24
        }
        duration = st.selectbox("Expected Duration", options=list(duration_options.keys()), index=2)
        
        if st.button("✅ Log Departure", type="primary", disabled=not (name and destination)):
            # Create departure record
            departure = {
                'id': str(uuid.uuid4()),
                'name': name,
                'phone': phone,
                'supervisor': supervisor,
                'supervisor_phone': supervisor_phone,
                'destination': destination,
                'departed_at': datetime.now(),
                'expected_return': datetime.now() + timedelta(hours=duration_options[duration]),
                'returned_at': None,
                'update_code': generate_update_code(),
                'extensions': []
            }
            
            st.session_state.departures.append(departure)
            save_departures(st.session_state.departures)
            
            # Clear selection
            if 'selected_member' in st.session_state:
                del st.session_state.selected_member
            
            # Show success with update code
            st.success(f"""
            ✅ **{name}** logged as departed to **{destination}**
            
            📱 **Update Code: `{departure['update_code']}`**
            
            Share this code with {name} to update their return time:
            `{st.secrets.get('app_url', 'http://your-app-url.com')}/update/{departure['update_code']}`
            """)
            st.balloons()

# Tab 2: Currently Out
with tab2:
    st.header("Currently Out")
    
    if active_departures:
        # Sort by expected return time
        active_departures.sort(key=lambda x: x['expected_return'])
        
        for departure in active_departures:
            is_overdue = departure['expected_return'] < now
            time_diff = abs(departure['expected_return'] - now)
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            
            # Card style based on status
            card_class = "overdue-card" if is_overdue else "departure-card"
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.markdown(f"### 🚶 {departure['name']}")
                    st.caption(f"📍 {departure['destination']}")
                    st.caption(f"🕐 Left: {departure['departed_at'].strftime('%I:%M %p')}")
                    if departure.get('phone'):
                        st.caption(f"📱 {departure['phone']}")
                    if departure.get('extensions'):
                        st.caption(f"🔄 Extended {len(departure['extensions'])} times")
                
                with col2:
                    if is_overdue:
                        st.error(f"⚠️ OVERDUE by {hours}h {minutes}m")
                    else:
                        st.success(f"⏰ {hours}h {minutes}m remaining")
                    
                    st.caption(f"Expected: {departure['expected_return'].strftime('%I:%M %p')}")
                    st.caption(f"Update code: `{departure['update_code']}`")
                
                with col3:
                    # Action buttons
                    if st.button(f"✅ Returned", key=f"return_{departure['id']}"):
                        departure['returned_at'] = datetime.now()
                        save_departures(st.session_state.departures)
                        st.rerun()
                    
                    # Quick extend buttons
                    col_ext1, col_ext2, col_ext3 = st.columns(3)
                    with col_ext1:
                        if st.button("+1h", key=f"ext1_{departure['id']}"):
                            departure['expected_return'] += timedelta(hours=1)
                            departure['extensions'].append({'time': datetime.now(), 'hours': 1})
                            save_departures(st.session_state.departures)
                            st.rerun()
                    with col_ext2:
                        if st.button("+2h", key=f"ext2_{departure['id']}"):
                            departure['expected_return'] += timedelta(hours=2)
                            departure['extensions'].append({'time': datetime.now(), 'hours': 2})
                            save_departures(st.session_state.departures)
                            st.rerun()
                    with col_ext3:
                        if st.button("+3h", key=f"ext3_{departure['id']}"):
                            departure['expected_return'] += timedelta(hours=3)
                            departure['extensions'].append({'time': datetime.now(), 'hours': 3})
                            save_departures(st.session_state.departures)
                            st.rerun()
                
                st.divider()
    else:
        st.success("✅ Everyone is currently in camp!")

# Tab 3: Camp Members Management
with tab3:
    st.header("Camp Members")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show current members
        st.subheader("Current Members")
        
        # Add status column
        members_display = camp_members.copy()
        members_display['Status'] = members_display['name'].apply(
            lambda x: '🚶 Out' if x in [d['name'] for d in active_departures] else '✅ In Camp'
        )
        
        # Display as table
        st.dataframe(
            members_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Name",
                "phone": "Phone",
                "supervisor": "Supervisor",
                "supervisor_phone": "Supervisor Phone",
                "cabin": "Cabin/Group",
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )
    
    with col2:
        st.subheader("Add New Member")
        
        with st.form("add_member"):
            new_name = st.text_input("Name")
            new_phone = st.text_input("Phone")
            new_supervisor = st.text_input("Supervisor")
            new_supervisor_phone = st.text_input("Supervisor Phone")
            new_cabin = st.text_input("Cabin/Group")
            
            if st.form_submit_button("Add Member"):
                if new_name:
                    new_member = pd.DataFrame([{
                        'name': new_name,
                        'phone': new_phone,
                        'supervisor': new_supervisor,
                        'supervisor_phone': new_supervisor_phone,
                        'cabin': new_cabin
                    }])
                    
                    global camp_members
                    camp_members = pd.concat([camp_members, new_member], ignore_index=True)
                    camp_members.to_csv(MEMBERS_FILE, index=False)
                    st.success(f"Added {new_name} to camp members!")
                    st.rerun()
    
    # Download/Upload section
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Download Members CSV",
            data=camp_members.to_csv(index=False),
            file_name=f"camp_members_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        uploaded_file = st.file_uploader("📤 Upload Members CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                camp_members = pd.read_csv(uploaded_file)
                camp_members.to_csv(MEMBERS_FILE, index=False)
                st.success("Members list updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")

# Tab 4: Update Return Time (for mobile users)
with tab4:
    st.header("📱 Update Your Return Time")
    
    update_code = st.text_input("Enter your update code:", placeholder="ABC123")
    
    if update_code:
        # Find departure by code
        departure = None
        for d in active_departures:
            if d.get('update_code', '').upper() == update_code.upper():
                departure = d
                break
        
        if departure:
            st.success(f"Found departure for **{departure['name']}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                📍 **Destination:** {departure['destination']}  
                🕐 **Left at:** {departure['departed_at'].strftime('%I:%M %p')}  
                ⏰ **Expected back:** {departure['expected_return'].strftime('%I:%M %p')}
                """)
            
            with col2:
                st.subheader("Need more time?")
                
                # Quick extend buttons
                col_ext1, col_ext2, col_ext3 = st.columns(3)
                with col_ext1:
                    if st.button("+1 Hour", key="mob_ext1"):
                        departure['expected_return'] += timedelta(hours=1)
                        departure['extensions'].append({'time': datetime.now(), 'hours': 1})
                        save_departures(st.session_state.departures)
                        st.success("Extended by 1 hour!")
                        st.rerun()
                
                with col_ext2:
                    if st.button("+2 Hours", key="mob_ext2"):
                        departure['expected_return'] += timedelta(hours=2)
                        departure['extensions'].append({'time': datetime.now(), 'hours': 2})
                        save_departures(st.session_state.departures)
                        st.success("Extended by 2 hours!")
                        st.rerun()
                
                with col_ext3:
                    if st.button("+3 Hours", key="mob_ext3"):
                        departure['expected_return'] += timedelta(hours=3)
                        departure['extensions'].append({'time': datetime.now(), 'hours': 3})
                        save_departures(st.session_state.departures)
                        st.success("Extended by 3 hours!")
                        st.rerun()
                
                # Custom time
                st.divider()
                new_time = st.time_input("Or set specific return time:", 
                                        value=departure['expected_return'].time())
                if st.button("Update Time"):
                    new_datetime = datetime.combine(departure['expected_return'].date(), new_time)
                    if new_datetime > datetime.now():
                        departure['expected_return'] = new_datetime
                        save_departures(st.session_state.departures)
                        st.success(f"Updated return time to {new_time.strftime('%I:%M %p')}!")
                        st.rerun()
                    else:
                        st.error("Please select a future time")
        else:
            st.error("Invalid update code. Please check and try again.")
    else:
        st.info("Enter the 6-character code you received when departing")

# Auto-refresh
if st.button("🔄 Refresh"):
    st.rerun()

# Add auto-refresh every 30 seconds
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload(1);
}, 30000);
</script>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    if st.button("📥 Export Departures"):
        departures_json = json.dumps([{
            'name': d['name'],
            'destination': d['destination'],
            'departed_at': d['departed_at'].isoformat(),
            'expected_return': d['expected_return'].isoformat(),
            'returned_at': d.get('returned_at').isoformat() if d.get('returned_at') else None,
            'extensions': d.get('extensions', [])
        } for d in st.session_state.departures], indent=2)
        
        st.download_button(
            label="Download JSON",
            data=departures_json,
            file_name=f"departures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    if st.button("🗑️ Clear Old Records"):
        # Remove departures older than 30 days
        cutoff = datetime.now() - timedelta(days=30)
        st.session_state.departures = [d for d in st.session_state.departures 
                                      if d['departed_at'] > cutoff]
        save_departures(st.session_state.departures)
        st.success("Cleared records older than 30 days")

# Footer
st.divider()
st.caption("🏕️ Camp Departure Tracker - Auto-refreshes every 30 seconds")