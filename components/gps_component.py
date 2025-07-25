"""
GPS Component for JMP Tracker
Provides reliable GPS location capture across devices
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
from config import get_text

def create_gps_component(key_prefix="gps"):
    """
    Create a GPS location capture component
    Returns location data or None
    """
    lang = st.session_state.get('language', 'en')
    
    # Create unique keys for this instance
    lat_key = f"{key_prefix}_lat"
    lon_key = f"{key_prefix}_lon"
    status_key = f"{key_prefix}_status"
    
    # Initialize session state
    if lat_key not in st.session_state:
        st.session_state[lat_key] = None
    if lon_key not in st.session_state:
        st.session_state[lon_key] = None
    if status_key not in st.session_state:
        st.session_state[status_key] = "ready"
    
    # JavaScript for GPS capture with better error handling
    gps_javascript = f"""
    <div id="gps-container-{key_prefix}">
        <button onclick="getLocation_{key_prefix}()" style="
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        ">
            <span>📍</span>
            <span>{get_text('get_current_location', lang)}</span>
        </button>
        
        <div id="gps-status-{key_prefix}" style="
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        "></div>
        
        <div id="gps-result-{key_prefix}" style="
            margin-top: 10px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
            display: none;
        "></div>
    </div>
    
    <script>
    function getLocation_{key_prefix}() {{
        const statusDiv = document.getElementById('gps-status-{key_prefix}');
        const resultDiv = document.getElementById('gps-result-{key_prefix}');
        
        // Show loading status
        statusDiv.style.display = 'block';
        statusDiv.style.background = '#e3f2fd';
        statusDiv.innerHTML = '⏳ {get_text("getting_location", lang) if lang == "en" else "Obtention de la position..."}';
        
        if (!navigator.geolocation) {{
            statusDiv.style.background = '#ffebee';
            statusDiv.innerHTML = '❌ {get_text("geolocation_not_supported", lang) if lang == "en" else "Géolocalisation non supportée"}';
            return;
        }}
        
        // Get location with timeout
        navigator.geolocation.getCurrentPosition(
            function(position) {{
                // Success
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                
                statusDiv.style.background = '#e8f5e9';
                statusDiv.innerHTML = '✅ {get_text("location_captured", lang)}';
                
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <strong>📍 Location:</strong><br>
                    Latitude: ${{lat.toFixed(6)}}<br>
                    Longitude: ${{lon.toFixed(6)}}<br>
                    Accuracy: ±${{accuracy.toFixed(0)}}m
                `;
                
                // Store in hidden inputs for Streamlit to read
                const form = document.createElement('form');
                form.innerHTML = `
                    <input type="hidden" id="lat-{key_prefix}" value="${{lat}}">
                    <input type="hidden" id="lon-{key_prefix}" value="${{lon}}">
                `;
                document.body.appendChild(form);
                
                // Try to communicate with Streamlit
                try {{
                    // This is a workaround - we'll use manual input as backup
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        key: '{key_prefix}',
                        value: {{ lat: lat, lon: lon }}
                    }}, '*');
                }} catch (e) {{
                    console.log('Streamlit communication failed, use manual input');
                }}
            }},
            function(error) {{
                // Error
                statusDiv.style.background = '#ffebee';
                let errorMsg = '❌ ';
                
                switch(error.code) {{
                    case error.PERMISSION_DENIED:
                        errorMsg += '{get_text("location_permission_denied", lang) if lang == "en" else "Permission refusée"}';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMsg += '{get_text("location_unavailable", lang) if lang == "en" else "Position non disponible"}';
                        break;
                    case error.TIMEOUT:
                        errorMsg += '{get_text("location_timeout", lang) if lang == "en" else "Délai dépassé"}';
                        break;
                    default:
                        errorMsg += error.message;
                }}
                
                statusDiv.innerHTML = errorMsg;
            }},
            {{
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }}
        );
    }}
    </script>
    """
    
    # Display the GPS component
    components.html(gps_javascript, height=200)
    
    # Manual input section
    st.write("---")
    manual_section = st.expander(
        get_text('manual_gps_entry', lang) if lang == 'en' else 'Entrée GPS manuelle'
    )
    
    with manual_section:
        st.info(
            get_text('manual_gps_info', lang) if lang == 'en' 
            else "Si la géolocalisation automatique ne fonctionne pas, entrez les coordonnées manuellement"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            manual_lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=float(st.session_state[lat_key]) if st.session_state[lat_key] else 0.0,
                format="%.6f",
                key=f"{key_prefix}_manual_lat",
                help="-90 to +90"
            )
        
        with col2:
            manual_lon = st.number_input(
                "Longitude", 
                min_value=-180.0,
                max_value=180.0,
                value=float(st.session_state[lon_key]) if st.session_state[lon_key] else 0.0,
                format="%.6f",
                key=f"{key_prefix}_manual_lon",
                help="-180 to +180"
            )
        
        if st.button(
            get_text('use_these_coordinates', lang) if lang == 'en' else 'Utiliser ces coordonnées',
            key=f"{key_prefix}_manual_confirm"
        ):
            if manual_lat != 0.0 and manual_lon != 0.0:
                st.session_state[lat_key] = manual_lat
                st.session_state[lon_key] = manual_lon
                st.session_state[status_key] = "captured"
                st.success(get_text('location_captured', lang))
                return {"lat": manual_lat, "lon": manual_lon}
    
    # Return captured location if available
    if st.session_state[lat_key] and st.session_state[lon_key]:
        return {
            "lat": st.session_state[lat_key],
            "lon": st.session_state[lon_key]
        }
    
    return None

def clear_gps_data(key_prefix="gps"):
    """Clear GPS data from session state"""
    keys_to_clear = [
        f"{key_prefix}_lat",
        f"{key_prefix}_lon", 
        f"{key_prefix}_status",
        f"{key_prefix}_manual_lat",
        f"{key_prefix}_manual_lon"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Alternative: Simple GPS button for basic use
def simple_gps_button(label=None, key="gps"):
    """
    Simplified GPS button that returns coordinates or None
    Uses only manual input for reliability
    """
    lang = st.session_state.get('language', 'en')
    
    if label is None:
        label = get_text('get_current_location', lang)
    
    with st.container():
        st.write(f"📍 **{label}**")
        
        # Instructions based on device
        with st.expander(get_text('how_to_share_location', lang) if lang == 'en' else 'Comment partager votre position'):
            st.markdown(f"""
            **{get_text('on_phone', lang) if lang == 'en' else 'Sur téléphone'}:**
            1. {get_text('open_maps_app', lang) if lang == 'en' else 'Ouvrez Google Maps ou Apple Maps'}
            2. {get_text('long_press_location', lang) if lang == 'en' else 'Appuyez longuement sur votre position'}
            3. {get_text('copy_coordinates', lang) if lang == 'en' else 'Copiez les coordonnées'}
            4. {get_text('paste_below', lang) if lang == 'en' else 'Collez ci-dessous'}
            
            **{get_text('on_computer', lang) if lang == 'en' else 'Sur ordinateur'}:**
            1. {get_text('open_google_maps', lang) if lang == 'en' else 'Ouvrez Google Maps'}
            2. {get_text('right_click_location', lang) if lang == 'en' else 'Clic droit sur votre position'}
            3. {get_text('click_coordinates', lang) if lang == 'en' else 'Cliquez sur les coordonnées affichées'}
            4. {get_text('paste_below', lang) if lang == 'en' else 'Collez ci-dessous'}
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=0.0,
                format="%.6f",
                key=f"{key}_simple_lat",
                placeholder="-6.792400"
            )
        
        with col2:
            lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                format="%.6f",
                key=f"{key}_simple_lon",
                placeholder="39.208300"
            )
        
        # Paste field for coordinates
        coord_input = st.text_input(
            get_text('or_paste_coordinates', lang) if lang == 'en' else 'Ou collez les coordonnées',
            key=f"{key}_paste",
            placeholder="-6.792400, 39.208300",
            help=get_text('paste_from_maps', lang) if lang == 'en' else 'Collez depuis Google Maps'
        )
        
        # Parse pasted coordinates
        if coord_input:
            try:
                # Handle various formats
                coord_input = coord_input.strip()
                # Remove common separators and labels
                coord_input = coord_input.replace('°', '').replace('N', '').replace('S', '')
                coord_input = coord_input.replace('E', '').replace('W', '').replace(',', ' ')
                
                parts = coord_input.split()
                if len(parts) >= 2:
                    parsed_lat = float(parts[0])
                    parsed_lon = float(parts[1])
                    
                    if -90 <= parsed_lat <= 90 and -180 <= parsed_lon <= 180:
                        return {"lat": parsed_lat, "lon": parsed_lon}
            except:
                st.error(get_text('invalid_coordinates', lang) if lang == 'en' else 'Coordonnées invalides')
        
        # Return manual input if valid
        if lat != 0.0 and lon != 0.0:
            return {"lat": lat, "lon": lon}
        
        return None
