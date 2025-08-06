# gps_utils.py

"""
GPS utilities for JMP Tracker
Provides automatic GPS capture functionality
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from config import get_text, get_current_time


def get_gps_location_button(key="gps", auto_capture=True):
    """
    Create a GPS location capture that works across devices
    """
    lang = st.session_state.get("language", "en")

    # Unique key for this GPS instance
    location_key = f"location_{key}"

    # JavaScript for automatic GPS capture
    gps_script = f"""
    <script>
    // Auto-capture GPS on load
    (function() {{
        if ({str(auto_capture).lower()} && navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                function(position) {{
                    // Store in parent window
                    window.parent.streamlitLocation = {{
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: new Date().toISOString()
                    }};
                    
                    // Update display
                    const statusEl = document.getElementById('gps-status-{key}');
                    if (statusEl) {{
                        statusEl.innerHTML = '✅ Location captured: ' + 
                            position.coords.latitude.toFixed(6) + ', ' + 
                            position.coords.longitude.toFixed(6);
                        statusEl.style.color = '#4CAF50';
                    }}
                }},
                function(error) {{
                    console.log('GPS auto-capture failed:', error);
                }},
                {{enableHighAccuracy: true, timeout: 5000, maximumAge: 0}}
            );
        }}
    }})();
    
    function captureGPS_{key}() {{
        const statusEl = document.getElementById('gps-status-{key}');
        statusEl.innerHTML = '⏳ Getting location...';
        statusEl.style.color = '#ff9800';
        
        if (!navigator.geolocation) {{
            statusEl.innerHTML = '❌ Geolocation not supported';
            statusEl.style.color = '#f44336';
            return;
        }}
        
        navigator.geolocation.getCurrentPosition(
            function(position) {{
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                
                // Store in parent window
                window.parent.streamlitLocation = {{
                    lat: lat,
                    lon: lon,
                    accuracy: accuracy,
                    timestamp: new Date().toISOString()
                }};
                
                // Update display
                statusEl.innerHTML = '✅ Location captured: ' + 
                    lat.toFixed(6) + ', ' + lon.toFixed(6) + 
                    ' (±' + accuracy.toFixed(0) + 'm)';
                statusEl.style.color = '#4CAF50';
                
                // Update hidden inputs
                document.getElementById('gps-lat-{key}').value = lat;
                document.getElementById('gps-lon-{key}').value = lon;
            }},
            function(error) {{
                let msg = '❌ ';
                switch(error.code) {{
                    case error.PERMISSION_DENIED:
                        msg += 'Permission denied';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        msg += 'Position unavailable';
                        break;
                    case error.TIMEOUT:
                        msg += 'Request timed out';
                        break;
                    default:
                        msg += 'Unknown error';
                }}
                statusEl.innerHTML = msg;
                statusEl.style.color = '#f44336';
            }},
            {{
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }}
        );
    }}
    </script>
    
    <div style="margin: 10px 0;">
        <button onclick="captureGPS_{key}()" style="
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
            transition: all 0.3s ease;
        " onmouseover="this.style.backgroundColor='#45a049'" 
           onmouseout="this.style.backgroundColor='#4CAF50'">
            <span>📍</span>
            <span>{get_text('get_current_location', lang)}</span>
        </button>
        
        <div id="gps-status-{key}" style="
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: 500;
        "></div>
        
        <input type="hidden" id="gps-lat-{key}" value="">
        <input type="hidden" id="gps-lon-{key}" value="">
    </div>
    """

    # Display the GPS capture component
    components.html(gps_script, height=120)

    # Fallback manual input
    with st.expander("📍 Manual GPS Entry", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            lat = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                format="%.6f",
                key=f"{key}_manual_lat",
                help="e.g., -6.792400",
            )

        with col2:
            lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                format="%.6f",
                key=f"{key}_manual_lon",
                help="e.g., 39.208300",
            )

        if st.button("Use Manual Coordinates", key=f"{key}_use_manual"):
            if lat != 0.0 and lon != 0.0:
                return {
                    "lat": lat,
                    "lon": lon,
                    "timestamp": get_current_time().isoformat(),
                }

    # Check session state for captured location
    if (
        f"{location_key}_lat" in st.session_state
        and f"{location_key}_lon" in st.session_state
    ):
        return {
            "lat": st.session_state[f"{location_key}_lat"],
            "lon": st.session_state[f"{location_key}_lon"],
            "timestamp": st.session_state.get(
                f"{location_key}_timestamp", get_current_time().isoformat()
            ),
        }

    return None


def capture_gps_silently():
    """
    Capture GPS location silently in the background
    """
    silent_script = """
    <script>
    (function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    window.parent.postMessage({
                        type: 'gps_location',
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    }, '*');
                },
                function(error) {
                    console.log('Silent GPS capture failed:', error);
                },
                {enableHighAccuracy: true, timeout: 5000, maximumAge: 0}
            );
        }
    })();
    </script>
    """

    components.html(silent_script, height=0)
