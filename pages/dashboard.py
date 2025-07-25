"""
Dashboard page for JMP Tracker
Main overview of all active personnel
"""

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from config import get_text, format_time
from database import get_active_departures, get_groups
from location import create_personnel_map
from ui import (
    render_header, render_sidebars, render_departure_card,
    check_and_play_alerts, add_pwa_install_button
)

def render_dashboard():
    """Render the dashboard page"""
    lang = st.session_state.get('language', 'en')
    
    # Header
    render_header(get_text('app_title', lang), lang)
    
    # Sidebars (desktop only)
    render_sidebars(lang)
    
    # Main content area
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Get active departures
    active_departures = get_active_departures()
    
    # Check for overdue and play sound if needed
    overdue_deps = active_departures[active_departures['is_overdue'] == True] if not active_departures.empty else pd.DataFrame()
    check_and_play_alerts(overdue_deps)
    
    # Map View Toggle
    if st.button(get_text('show_map', lang), type="primary", use_container_width=True):
        st.session_state.show_map = True
    
    if st.session_state.get('show_map', False):
        st.subheader(f"📍 {get_text('map_view_tab', lang)}")
        
        if active_departures.empty:
            st.info(get_text('no_data', lang))
        else:
            # Statistics
            if 'last_location' in active_departures.columns:
                with_locations = active_departures[
                    active_departures['last_location'].notna() & 
                    (active_departures['last_location'] != '')
                ]
            else:
                with_locations = pd.DataFrame()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(get_text('total_active', lang), len(active_departures))
            with col2:
                st.metric(get_text('with_gps', lang), len(with_locations))
            with col3:
                st.metric(get_text('no_gps', lang), len(active_departures) - len(with_locations))
            
            # Create and display map
            personnel_map = create_personnel_map(active_departures, lang)
            
            # Display the map
            map_data = st_folium(
                personnel_map,
                width=None,
                height=400,
                returned_objects=["last_object_clicked"],
                key="dashboard_map"
            )
            
            if st.button(get_text('hide_map', lang), key="hide_map"):
                st.session_state.show_map = False
                st.rerun()
    
    # Overdue alert container
    if not overdue_deps.empty:
        st.error(get_text('overdue_alert', lang, count=len(overdue_deps)))
        
        for _, dep in overdue_deps.iterrows():
            hours_overdue = abs(int(dep['time_remaining']))
            minutes_overdue = abs(int((dep['time_remaining'] % 1) * 60))
            st.markdown(f"""
            <div style="background-color: white; padding: 10px; margin: 5px 0; border-radius: 5px; border: 2px solid red;">
                <strong>{dep['person_name']}</strong> - {dep['destination']}
                • {get_text('overdue_by', lang, hours=hours_overdue, minutes=minutes_overdue)}
                • 📞 {dep['phone']} • {get_text('supervisor', lang)}: {dep['supervisor']}
            </div>
            """, unsafe_allow_html=True)
    
    # Active departures list
    st.subheader(get_text('active_departures', lang))
    
    if active_departures.empty:
        st.success(get_text('all_in_camp', lang))
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
        
        # Display compact departures
        for item in all_departures:
            if item['type'] == 'individual':
                render_departure_card(item['data'], lang)
            else:  # Group departure
                # Determine group status
                any_overdue = any(m['is_overdue'] for m in item['members'])
                min_time = item['time_remaining']
                
                if any_overdue:
                    card_class = "departure-card-compact overdue"
                    status_icon = "🔴"
                elif min_time < 0.5:
                    card_class = "departure-card-compact warning"
                    status_icon = "🟡"
                else:
                    card_class = "departure-card-compact safe"
                    status_icon = "🟢"
                
                # Time display for group
                if any_overdue:
                    time_text = get_text('overdue', lang)
                else:
                    hours = int(min_time)
                    minutes = int((min_time % 1) * 60)
                    time_text = get_text('time_remaining', lang, hours=hours, minutes=minutes)
                
                destination = item['members'][0]['destination']
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div>
                        {status_icon} <strong>👥 {item['group_name']}</strong>
                        ({len(item['members'])} {get_text('members', lang).lower()}) → {destination}
                    </div>
                    <div>
                        <strong style="color: {'red' if any_overdue else 'inherit'};">{time_text}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # PWA Install button
    st.markdown("---")
    add_pwa_install_button()
    
    st.markdown('</div>', unsafe_allow_html=True)
