"""
Database module for JMP Tracker
Handles all Google Sheets operations
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime, timedelta
import numpy as np
from config import (
    LOCAL_TIMEZONE, 
    PERSONNEL_CACHE_TTL, DEPARTURES_CACHE_TTL, GROUPS_CACHE_TTL,
    get_current_time
)

# Cache the Google Sheets client
@st.cache_resource
def get_google_sheets_client():
    """Initialize Google Sheets client with credentials from secrets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Get credentials from secrets
        creds_dict = st.secrets["connections"]["gsheets"]
        creds_dict = dict(creds_dict)
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        return client
    except Exception as e:
        st.error(f"Failed to initialize Google Sheets client: {str(e)}")
        return None

@st.cache_resource
def get_spreadsheet():
    """Get the Google Sheets spreadsheet"""
    try:
        client = get_google_sheets_client()
        if not client:
            return None
            
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet
    except Exception as e:
        st.error(f"Failed to open spreadsheet: {str(e)}")
        return None

def ensure_worksheets_exist(spreadsheet):
    """Ensure all required worksheets exist"""
    if not spreadsheet:
        return False
        
    try:
        worksheet_names = [ws.title for ws in spreadsheet.worksheets()]
        
        for sheet_name, headers in SHEET_HEADERS.items():
            if SHEET_NAMES[sheet_name] not in worksheet_names:
                worksheet = spreadsheet.add_worksheet(
                    title=SHEET_NAMES[sheet_name], 
                    rows=1000, 
                    cols=20
                )
                worksheet.update(values=[headers], range_name='A1')
        return True
    except Exception as e:
        st.error(f"Failed to ensure worksheets exist: {str(e)}")
        return False

def convert_to_json_serializable(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return ""
    else:
        return obj

def safe_dataframe_for_display(df):
    """Prepare DataFrame for display by converting problematic types"""
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    display_df = df.copy()
    
    # Convert phone numbers to strings
    if 'phone' in display_df.columns:
        display_df['phone'] = display_df['phone'].astype(str).replace('nan', '')
    
    if 'supervisor_phone' in display_df.columns:
        display_df['supervisor_phone'] = display_df['supervisor_phone'].astype(str).replace('nan', '')
    
    # Convert IDs to integers where possible, then to strings
    for col in ['id', 'departure_id', 'group_id', 'extensions_count']:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').fillna(0).astype(int).astype(str)
    
    return display_df

# Personnel operations
@st.cache_data(ttl=PERSONNEL_CACHE_TTL)
def get_personnel():
    """Get all personnel from manifest"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return pd.DataFrame(columns=SHEET_HEADERS['personnel'])
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['personnel'])
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=SHEET_HEADERS['personnel'])
        
        df = pd.DataFrame(data)
        df = df[df['name'] != '']  # Filter out empty rows
        
        return df
    except Exception as e:
        st.error(f"Failed to get personnel: {str(e)}")
        return pd.DataFrame(columns=SHEET_HEADERS['personnel'])

def add_personnel(name, phone=None, supervisor=None, supervisor_phone=None, company=None):
    """Add or update a person in the manifest"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['personnel'])
        personnel_df = get_personnel()
        
        now_local = get_current_time()
        
        # Convert all values to JSON serializable types
        row_data = [
            str(name),
            str(phone) if phone else '',
            str(supervisor) if supervisor else '',
            str(supervisor_phone) if supervisor_phone else '',
            str(company) if company else '',
            now_local.isoformat(),
            now_local.isoformat()
        ]
        
        if not personnel_df.empty and name in personnel_df['name'].values:
            # Update existing
            row_num = personnel_df[personnel_df['name'] == name].index[0] + 2
            row_data[5] = personnel_df[personnel_df['name'] == name]['created_at'].iloc[0]  # Keep original created_at
            worksheet.update(values=[row_data], range_name=f'A{row_num}:G{row_num}')
        else:
            # Add new
            worksheet.append_row(row_data)
        
        # Clear cache
        get_personnel.clear()
        return True
    except Exception as e:
        st.error(f"Failed to add personnel: {str(e)}")
        return False

# Departures operations
@st.cache_data(ttl=DEPARTURES_CACHE_TTL)
def get_all_departures():
    """Get all departures"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return pd.DataFrame(columns=SHEET_HEADERS['departures'])
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=SHEET_HEADERS['departures'])
        
        df = pd.DataFrame(data)
        
        # Convert numeric columns
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['extensions_count'] = pd.to_numeric(df['extensions_count'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Failed to get departures: {str(e)}")
        return pd.DataFrame(columns=SHEET_HEADERS['departures'])

@st.cache_data(ttl=DEPARTURES_CACHE_TTL)
def get_active_departures():
    """Get all active (not returned) departures"""
    try:
        df = get_all_departures()
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter active departures
        df = df[df['actual_return'] == '']
        
        if df.empty:
            return pd.DataFrame()
        
        # Parse timestamps with timezone awareness
        df['expected_return'] = pd.to_datetime(df['expected_return'])
        if df['expected_return'].dt.tz is None:
            df['expected_return'] = df['expected_return'].dt.tz_localize(LOCAL_TIMEZONE)
        
        now_local = get_current_time()
        df['is_overdue'] = df['expected_return'] < now_local
        
        # Calculate time remaining
        df['time_remaining'] = (df['expected_return'] - now_local).dt.total_seconds() / 3600
        
        return df.sort_values('time_remaining')
    except Exception as e:
        st.error(f"Failed to get active departures: {str(e)}")
        return pd.DataFrame()

def add_departure(person_name, destination, expected_return, phone=None, supervisor=None, 
                 company=None, group_id=None, initial_location=None):
    """Log a new departure"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        departures_df = get_all_departures()
        
        # Calculate new ID
        new_id = 1 if departures_df.empty else int(departures_df['id'].max()) + 1
        
        now_local = get_current_time()
        
        # Ensure expected_return is timezone aware
        if expected_return.tzinfo is None:
            expected_return = LOCAL_TIMEZONE.localize(expected_return)
        
        # Convert all values to JSON serializable types
        new_row = [
            int(new_id),
            str(person_name),
            str(destination),
            now_local.isoformat(),
            expected_return.isoformat(),
            '',  # actual_return
            str(phone) if phone else '',
            str(supervisor) if supervisor else '',
            str(company) if company else '',
            0,  # extensions_count
            False,  # is_overdue
            str(group_id) if group_id else '',
            json.dumps(initial_location) if initial_location else ''
        ]
        
        worksheet.append_row(new_row)
        
        # Clear caches
        get_all_departures.clear()
        get_active_departures.clear()
        
        return True
    except Exception as e:
        st.error(f"Failed to add departure: {str(e)}")
        return False

def mark_returned(departure_id):
    """Mark a departure as returned"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        departures_df = get_all_departures()
        
        row_index = departures_df[departures_df['id'] == int(departure_id)].index[0]
        row_num = row_index + 2
        
        now_local = get_current_time()
        worksheet.update(values=[[now_local.isoformat()]], range_name=f'F{row_num}')
        
        # Clear caches
        get_all_departures.clear()
        get_active_departures.clear()
        
        return True
    except Exception as e:
        st.error(f"Failed to mark as returned: {str(e)}")
        return False

def extend_departure(departure_id, hours, gps_location=None):
    """Extend a departure's expected return time"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
        
        # Update departures
        departures_worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        departures_df = get_all_departures()
        
        row_index = departures_df[departures_df['id'] == int(departure_id)].index[0]
        row_num = row_index + 2
        
        current_return = pd.to_datetime(departures_df.loc[row_index, 'expected_return'])
        if current_return.tzinfo is None:
            current_return = LOCAL_TIMEZONE.localize(current_return)
        
        new_return = current_return + timedelta(hours=hours)
        new_extensions_count = int(departures_df.loc[row_index, 'extensions_count']) + 1
        
        # Update expected return and extensions count
        departures_worksheet.update(values=[[new_return.isoformat()]], range_name=f'E{row_num}')
        departures_worksheet.update(values=[[int(new_extensions_count)]], range_name=f'J{row_num}')
        
        # Update last location if provided
        if gps_location:
            location_str = json.dumps(gps_location)
            departures_worksheet.update(values=[[location_str]], range_name=f'M{row_num}')
        
        # Add extension record
        extensions_worksheet = spreadsheet.worksheet(SHEET_NAMES['extensions'])
        
        try:
            extensions_data = extensions_worksheet.get_all_records()
            new_ext_id = len(extensions_data) + 1 if extensions_data else 1
        except:
            new_ext_id = 1
        
        now_local = get_current_time()
        new_extension = [
            int(new_ext_id),
            int(departure_id),
            int(hours),
            now_local.isoformat(),
            json.dumps(gps_location) if gps_location else ''
        ]
        
        extensions_worksheet.append_row(new_extension)
        
        # Clear caches
        get_all_departures.clear()
        get_active_departures.clear()
        
        return True
    except Exception as e:
        st.error(f"Failed to extend departure: {str(e)}")
        return False

def update_location(departure_id, location_data):
    """Update the last known location for a departure"""
    try:
        if not location_data or 'lat' not in location_data or 'lon' not in location_data:
            return False
            
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        departures_df = get_all_departures()
        
        row_index = departures_df[departures_df['id'] == int(departure_id)].index[0]
        row_num = row_index + 2
        
        now_local = get_current_time()
        location_str = json.dumps({
            'lat': float(location_data['lat']),
            'lon': float(location_data['lon']),
            'timestamp': now_local.isoformat()
        })
        
        worksheet.update(values=[[location_str]], range_name=f'M{row_num}')
        
        # Clear caches
        get_all_departures.clear()
        get_active_departures.clear()
        
        return True
    except Exception as e:
        st.error(f"Failed to update location: {str(e)}")
        return False

# Groups operations
@st.cache_data(ttl=GROUPS_CACHE_TTL)
def get_groups():
    """Get all groups"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return pd.DataFrame(columns=SHEET_HEADERS['groups'])
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['groups'])
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=SHEET_HEADERS['groups'])
        
        df = pd.DataFrame(data)
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Failed to get groups: {str(e)}")
        return pd.DataFrame(columns=SHEET_HEADERS['groups'])

def add_group(group_name, members, responsible_person):
    """Add a new group"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['groups'])
        groups_df = get_groups()
        
        new_id = 1 if groups_df.empty else int(groups_df['id'].max()) + 1
        
        now_local = get_current_time()
        new_row = [
            int(new_id),
            str(group_name),
            str(members),
            str(responsible_person),
            now_local.isoformat()
        ]
        
        worksheet.append_row(new_row)
        get_groups.clear()
        
        return new_id
    except Exception as e:
        st.error(f"Failed to add group: {str(e)}")
        return None

def update_group(group_id, members=None, responsible_person=None):
    """Update an existing group"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['groups'])
        groups_df = get_groups()
        
        row_index = groups_df[groups_df['id'] == int(group_id)].index[0]
        row_num = row_index + 2
        
        if members is not None:
            worksheet.update(values=[[str(members)]], range_name=f'C{row_num}')
        
        if responsible_person is not None:
            worksheet.update(values=[[str(responsible_person)]], range_name=f'D{row_num}')
        
        get_groups.clear()
        return True
    except Exception as e:
        st.error(f"Failed to update group: {str(e)}")
        return False

def mark_group_returned(group_id):
    """Mark all departures in a group as returned"""
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.worksheet(SHEET_NAMES['departures'])
        departures_df = get_all_departures()
        
        group_departures = departures_df[
            (departures_df['group_id'] == str(group_id)) & 
            (departures_df['actual_return'] == '')
        ]
        
        now_local = get_current_time()
        
        for _, dep in group_departures.iterrows():
            row_index = departures_df[departures_df['id'] == dep['id']].index[0]
            row_num = row_index + 2
            worksheet.update(values=[[now_local.isoformat()]], range_name=f'F{row_num}')
        
        # Clear caches
        get_all_departures.clear()
        get_active_departures.clear()
        
        return True
    except Exception as e:
        st.error(f"Failed to mark group as returned: {str(e)}")
        return False
