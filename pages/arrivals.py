"""
Arrivals page for JMP Tracker
Mark personnel as returned and handle extensions
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
from config import get_text, format_time, get_current_time, SHEET_NAMES, SHEET_HEADERS
from database import (
    get_active_departures, get_groups, mark_returned, 
    mark_group_returned, extend_departure
)
from location import simple_gps_button

def render_arrivals():
    """Render the arrivals page"""
    lang = st.session_state.get('language', 'en')
    
    st.markdown(f'<p class="main-header">{get_text("app_title", lang)} - {get_text("arrivals", lang)}</p>', 
               unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{get_text("mark_returned", lang)}</p>', 
               unsafe_allow_html=True)
    
    active_departures = get_active_departures()
    
    if active_departures.empty:
        st.success(get_text('everyone_in_camp', lang))
    else:
        # Tab view for individual vs group returns
        tab1, tab2, tab3 = st.tabs([
            get_text('individual_returns', lang), 
            get_text('group_returns', lang), 
            get_text('extend_time', lang)
        ])
        
        with tab1:
            render_individual_returns(active_departures, lang)
        
        with tab2:
            render_group_returns(active_departures, lang)
        
        with tab3:
            render_extensions(active_departures, lang)

def render_individual_returns(active_departures, lang):
    """Render individual returns tab"""
    # Group by overdue status
    overdue = active_departures[active_departures['is_overdue'] == True]
    on_time = active_departures[active_departures['is_overdue'] == False]
    
    if not overdue.empty:
        st.error(f"### 🔴 {get_text('overdue', lang)} ({len(overdue)})")
        for _, dep in overdue.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{dep['person_name']}** → {dep['destination']}")
                hours = abs(int(dep['time_remaining']))
                minutes = abs(int((dep['time_remaining'] % 1) * 60))
                st.caption(get_text('overdue_by', lang, hours=hours, minutes=minutes))
            
            with col2:
                st.caption(get_text('expected_at', lang, time=format_time(pd.to_datetime(dep['expected_return']))))
                st.caption(get_text('departed_at', lang, time=format_time(pd.to_datetime(dep['departed_at']))))
            
            with col3:
                if st.button(get_text('mark_returned', lang), key=f"return_{dep['id']}", type="primary"):
                    if mark_returned(dep['id']):
                        st.success(f"{dep['person_name']} {get_text('marked_returned', lang)}")
                        time.sleep(1)
                        st.rerun()
        
        st.divider()
    
    if not on_time.empty:
        st.success(f"### 🟢 {get_text('on_time', lang)} ({len(on_time)})")
        for _, dep in on_time.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{dep['person_name']}** → {dep['destination']}")
                if dep['time_remaining'] > 0:
                    hours = int(dep['time_remaining'])
                    minutes = int((dep['time_remaining'] % 1) * 60)
                    st.caption(get_text('time_remaining', lang, hours=hours, minutes=minutes))
                else:
                    st.caption(get_text('due_now', lang))
            
            with col2:
                st.caption(get_text('expected_at', lang, time=format_time(pd.to_datetime(dep['expected_return']))))
                st.caption(get_text('departed_at', lang, time=format_time(pd.to_datetime(dep['departed_at']))))
            
            with col3:
                if st.button(get_text('mark_returned', lang), key=f"return_{dep['id']}", type="primary"):
                    if mark_returned(dep['id']):
                        st.success(f"{dep['person_name']} {get_text('marked_returned', lang)}")
                        time.sleep(1)
                        st.rerun()

def render_group_returns(active_departures, lang):
    """Render group returns tab"""
    # Show active group departures
    groups_out = active_departures[active_departures['group_id'] != ''].groupby('group_id')
    
    if len(groups_out) > 0:
        st.info(f"### 👥 {get_text('active_groups', lang)} ({len(groups_out)})")
        
        groups_df = get_groups()
        
        for group_id, group_deps in groups_out:
            if not groups_df.empty:
                group_info = groups_df[groups_df['id'] == int(group_id)]
                if not group_info.empty:
                    group_name = group_info.iloc[0]['group_name']
                    st.markdown(f"**{group_name}** ({get_text('members_out', lang, count=len(group_deps))})")
                    
                    # Show group members
                    members_list = ", ".join(group_deps['person_name'].tolist())
                    st.caption(f"{get_text('members', lang)}: {members_list}")
                    
                    # Check if any are overdue
                    any_overdue = any(group_deps['is_overdue'])
                    if any_overdue:
                        st.error(get_text('some_overdue', lang))
                    
                    if st.button(get_text('mark_group_returned', lang), 
                               key=f"group_return_{group_id}", type="primary"):
                        if mark_group_returned(group_id):
                            st.success(get_text('group_returned_success', lang, name=group_name))
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider()
    else:
        st.info(get_text('no_active_groups', lang))

def render_extensions(active_departures, lang):
    """Render time extensions tab"""
    st.subheader(get_text('extend_time', lang))
    st.info(get_text('select_person_extend', lang))
    
    # Select person to extend
    person_names = active_departures['person_name'].tolist()
    selected_person = st.selectbox(get_text('select_person', lang), person_names)
    
    if selected_person:
        person_data = active_departures[active_departures['person_name'] == selected_person].iloc[0]
        
        st.write(f"**{get_text('current_expected_return', lang)}:** {format_time(pd.to_datetime(person_data['expected_return']))}")
        
        # Extension options
        col1, col2 = st.columns(2)
        with col1:
            hours_to_extend = st.number_input(
                get_text('hours_to_extend', lang), 
                min_value=1, 
                max_value=24, 
                value=1
            )
        
        with col2:
            # GPS location section
            st.write(get_text('share_location', lang))
            
            # Use the simple GPS button
            gps_data = simple_gps_button(key="extension")
        
        if st.button(get_text('extend_time', lang), type="primary"):
            # Store GPS data properly
            location_to_store = None
            if gps_data:
                location_to_store = {
                    'lat': gps_data['lat'],
                    'lon': gps_data['lon'],
                    'timestamp': get_current_time().isoformat()
                }
            
            if extend_departure(person_data['id'], hours_to_extend, location_to_store):
                st.success(get_text('extended_success', lang, name=selected_person, hours=hours_to_extend))
                if location_to_store:
                    st.info(get_text('location_recorded', lang, lat=location_to_store['lat'], lon=location_to_store['lon']))
                
                time.sleep(1)
                st.rerun()
