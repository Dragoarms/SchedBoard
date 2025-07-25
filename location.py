"""
Location module for JMP Tracker
Handles GPS tracking and map functionality
"""

import streamlit as st
import folium
import requests
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import json
import pandas as pd
from config import (
    KMZ_URL, DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM,
    get_text, get_current_time
)

@st.cache_data(ttl=3600)
def load_kmz_tracks():
    """Load KMZ file from GitHub and extract track data"""
    try:
        # Download KMZ file from GitHub
        response = requests.get(KMZ_URL)
        
        if response.status_code != 200:
            st.warning("Could not load map tracks from GitHub")
            return [], {'min_lat': DEFAULT_MAP_CENTER[0], 'max_lat': DEFAULT_MAP_CENTER[0], 
                       'min_lon': DEFAULT_MAP_CENTER[1], 'max_lon': DEFAULT_MAP_CENTER[1]}
        
        # KMZ is a zipped KML file
        tracks = []
        bounds = {'min_lat': 90, 'max_lat': -90, 'min_lon': 180, 'max_lon': -180}
        
        with tempfile.TemporaryFile() as tmp:
            tmp.write(response.content)
            tmp.seek(0)
            
            try:
                with zipfile.ZipFile(tmp, 'r') as kmz:
                    # Find the KML file inside
                    kml_filename = None
                    for name in kmz.namelist():
                        if name.endswith('.kml'):
                            kml_filename = name
                            break
                    
                    if kml_filename:
                        with kmz.open(kml_filename) as kml_file:
                            # Parse KML
                            tree = ET.parse(kml_file)
                            root = tree.getroot()
                            
                            # Define namespaces
                            ns = {'kml': 'http://www.opengis.net/kml/2.2',
                                  'gx': 'http://www.google.com/kml/ext/2.2'}
                            
                            # Extract placemarks (tracks, paths, etc.)
                            for placemark in root.findall('.//kml:Placemark', ns):
                                name_elem = placemark.find('kml:name', ns)
                                name = name_elem.text if name_elem is not None else "Track"
                                
                                # Look for LineString coordinates
                                for linestring in placemark.findall('.//kml:LineString/kml:coordinates', ns):
                                    if linestring.text:
                                        coords = []
                                        for coord in linestring.text.strip().split():
                                            parts = coord.split(',')
                                            if len(parts) >= 2:
                                                lon, lat = float(parts[0]), float(parts[1])
                                                coords.append([lat, lon])
                                                # Update bounds
                                                bounds['min_lat'] = min(bounds['min_lat'], lat)
                                                bounds['max_lat'] = max(bounds['max_lat'], lat)
                                                bounds['min_lon'] = min(bounds['min_lon'], lon)
                                                bounds['max_lon'] = max(bounds['max_lon'], lon)
                                        if coords:
                                            tracks.append({'name': name, 'coordinates': coords})
                                
                                # Look for Points
                                for point in placemark.findall('.//kml:Point/kml:coordinates', ns):
                                    if point.text:
                                        parts = point.text.strip().split(',')
                                        if len(parts) >= 2:
                                            lon, lat = float(parts[0]), float(parts[1])
                                            tracks.append({'name': name, 'type': 'point', 'coordinates': [lat, lon]})
                                            # Update bounds
                                            bounds['min_lat'] = min(bounds['min_lat'], lat)
                                            bounds['max_lat'] = max(bounds['max_lat'], lat)
                                            bounds['min_lon'] = min(bounds['min_lon'], lon)
                                            bounds['max_lon'] = max(bounds['max_lon'], lon)
            except Exception as e:
                st.warning(f"Error parsing KMZ file: {str(e)}")
                
        return tracks, bounds
    except Exception as e:
        st.warning(f"Error loading KMZ file: {str(e)}")
        return [], {'min_lat': DEFAULT_MAP_CENTER[0], 'max_lat': DEFAULT_MAP_CENTER[0], 
                   'min_lon': DEFAULT_MAP_CENTER[1], 'max_lon': DEFAULT_MAP_CENTER[1]}

def create_personnel_map(active_departures, lang='en'):
    """Create a Folium map with personnel locations and KMZ tracks"""
    tracks, bounds = load_kmz_tracks()
    
    # Calculate center and zoom based on KMZ bounds
    if bounds['min_lat'] != 90:  # If we have valid bounds
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
        center_lon = (bounds['min_lon'] + bounds['max_lon']) / 2
        
        # Calculate appropriate zoom level
        lat_range = bounds['max_lat'] - bounds['min_lat']
        lon_range = bounds['max_lon'] - bounds['min_lon']
        max_range = max(lat_range, lon_range)
        
        if max_range < 0.01:
            zoom_start = 15
        elif max_range < 0.05:
            zoom_start = 13
        elif max_range < 0.1:
            zoom_start = 12
        else:
            zoom_start = 11
    else:
        # Default to configured center
        center_lat, center_lon = DEFAULT_MAP_CENTER
        zoom_start = DEFAULT_MAP_ZOOM
    
    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    # Add KMZ tracks
    for track in tracks:
        if track.get('type') == 'point':
            # Add point markers
            folium.Marker(
                track['coordinates'],
                popup=track['name'],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        else:
            # Add polylines for tracks
            folium.PolyLine(
                track['coordinates'],
                color='blue',
                weight=3,
                opacity=0.8,
                popup=track['name']
            ).add_to(m)
    
    # Add personnel markers
    for _, dep in active_departures.iterrows():
        # Check if last_location column exists and has data
        if 'last_location' in dep and dep.get('last_location'):
            try:
                # Parse location data
                if isinstance(dep['last_location'], str) and dep['last_location'].strip():
                    location_data = json.loads(dep['last_location'])
                    
                    # Determine marker color based on status
                    if dep['is_overdue']:
                        color = 'red'
                        icon = 'exclamation-sign'
                    elif dep['time_remaining'] < 0.5:
                        color = 'orange'
                        icon = 'warning-sign'
                    else:
                        color = 'green'
                        icon = 'user'
                    
                    # Calculate time display
                    if dep['is_overdue']:
                        time_text = get_text('overdue', lang)
                    else:
                        hours = int(dep['time_remaining'])
                        minutes = int((dep['time_remaining'] % 1) * 60)
                        time_text = get_text('time_remaining', lang, hours=hours, minutes=minutes)
                    
                    # Create popup text
                    popup_text = f"""
                    <b>{dep['person_name']}</b><br>
                    📍 {dep['destination']}<br>
                    ⏱️ {time_text}<br>
                    📞 {dep['phone'] or 'N/A'}<br>
                    {get_text('last_update', lang)}: {location_data.get('timestamp', 'Unknown')}
                    """
                    
                    # Add marker
                    folium.Marker(
                        [location_data['lat'], location_data['lon']],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color=color, icon=icon),
                        tooltip=dep['person_name']
                    ).add_to(m)
                    
                    # Add circle to show approximate area
                    folium.Circle(
                        [location_data['lat'], location_data['lon']],
                        radius=100,  # 100 meters
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.2
                    ).add_to(m)
                    
            except Exception as e:
                pass  # Skip if location data is invalid
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: auto; 
                background-color: white; z-index: 1000; 
                border:2px solid grey; border-radius: 5px;
                padding: 10px; font-size: 14px;">
        <p style="margin: 0;"><b>{get_text('personnel_status', lang)}</b></p>
        <p style="margin: 5px 0;"><span style="color: green;">●</span> {get_text('on_time', lang)}</p>
        <p style="margin: 5px 0;"><span style="color: orange;">●</span> {get_text('due_soon', lang)}</p>
        <p style="margin: 5px 0;"><span style="color: red;">●</span> {get_text('overdue', lang)}</p>
        <p style="margin: 5px 0;"><span style="color: blue;">━</span> {get_text('roads_tracks', lang)}</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# Simple GPS button for basic use
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
                key=f"{key}_simple_lat"
            )
        
        with col2:
            lon = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                format="%.6f",
                key=f"{key}_simple_lon"
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

def get_gps_location_button():
    """
    Create a GPS location button that works across devices
    Uses Streamlit's built-in location capabilities
    """
    # For now, we'll use a simple approach
    # In production, you might want to use streamlit-geolocation or similar
    location_data = {}
    
    if st.button("📍 Get GPS Location", help="Click to share your current location"):
        # This is a placeholder - in production, you'd use JavaScript
        # or a proper geolocation library
        st.info("Please enable location services and allow this site to access your location.")
        
        # You could add JavaScript here to get actual location
        # For now, return empty dict
        location_data = {}
    
    return location_data

def validate_gps_data(gps_data):
    """Validate GPS data structure"""
    if not gps_data:
        return None
        
    if not isinstance(gps_data, dict):
        return None
        
    if 'lat' not in gps_data or 'lon' not in gps_data:
        return None
        
    try:
        lat = float(gps_data['lat'])
        lon = float(gps_data['lon'])
        
        # Basic validation of coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None
            
        return {
            'lat': lat,
            'lon': lon,
            'timestamp': get_current_time().isoformat()
        }
    except:
        return None

# Alternative GPS method using HTML5 geolocation
def get_location_html():
    """Generate HTML/JavaScript for location capture"""
    return """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    // Send position back to Streamlit
                    const coords = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    
                    // You would need to implement a way to pass this back to Python
                    // This could be done via st.experimental_set_query_params or similar
                    console.log('Location:', coords);
                    
                    // Display to user
                    document.getElementById('location-result').innerHTML = 
                        `Location captured: ${coords.lat.toFixed(6)}, ${coords.lon.toFixed(6)}`;
                },
                function(error) {
                    document.getElementById('location-result').innerHTML = 
                        'Error: ' + error.message;
                }
            );
        } else {
            document.getElementById('location-result').innerHTML = 
                'Geolocation is not supported by this browser.';
        }
    }
    </script>
    
    <button onclick="getLocation()" style="
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
    ">
        📍 Get Current Location
    </button>
    
    <div id="location-result" style="margin-top: 10px;"></div>
    """
