"""
UI module for JMP Tracker
Contains all UI styling and components
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import timedelta
import pandas as pd
from config import (
    get_text,
    format_time,
    LOGO_URL,
    QR_BASE_URL,
    APP_BASE_URL,
    ALERT_INTERVAL_MINUTES,
    get_current_time,
)


def apply_custom_css():
    """Apply custom CSS for the application"""
    st.markdown(
        """
    <style>
        /* Reset and base styles */
        .stApp {
            background-color: #f5f5f5;
            color: #333333;
        }
        
        /* Fixed layout styles */
        .main > div {
            padding-top: 70px;
        }
        
        /* Main content area adjustment */
        @media (min-width: 769px) {
            .main .block-container {
                padding-left: 220px !important;
                padding-right: 220px !important;
                max-width: none !important;
            }
        }
        
        /* Fixed header */
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #2c3e50;
            color: white;
            z-index: 999;
            padding: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .fixed-header h2 {
            color: white !important;
        }
        
        /* Fixed sidebars - Hidden on mobile */
        @media (min-width: 769px) {
            .fixed-left-sidebar {
                position: fixed;
                left: 0;
                top: 70px;
                bottom: 0;
                width: 200px;
                background-color: #34495e;
                color: white;
                padding: 20px;
                overflow-y: auto;
                border-right: 1px solid #2c3e50;
                z-index: 100;
            }
            
            .fixed-right-sidebar {
                position: fixed;
                right: 0;
                top: 70px;
                bottom: 0;
                width: 200px;
                background-color: #34495e;
                color: white;
                padding: 20px;
                overflow-y: auto;
                border-left: 1px solid #2c3e50;
                z-index: 100;
            }
            
            .fixed-left-sidebar h3, .fixed-right-sidebar h3 {
                color: white !important;
            }
            
            .main-content {
                margin-left: 200px;
                margin-right: 200px;
                padding: 20px;
                background-color: white;
                min-height: 100vh;
            }
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .fixed-left-sidebar, .fixed-right-sidebar {
                display: none !important;
            }
            .main-content {
                margin-left: 10px !important;
                margin-right: 10px !important;
                padding: 10px !important;
            }
            
            /* Larger buttons on mobile */
            .stButton > button {
                min-height: 50px;
                font-size: 16px !important;
            }
        }
        
        /* Metrics styling */
        [data-testid="metric-container"] {
            background-color: white;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Input fields styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            background-color: white !important;
            color: #333333 !important;
            border: 1px solid #ddd !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #45a049 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Departure cards */
        .departure-card-compact {
            background-color: white;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-left: 4px solid #2196F3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .departure-card-compact.overdue {
            border-left-color: #f44336;
            background-color: #ffebee;
        }
        
        .departure-card-compact.warning {
            border-left-color: #ff9800;
            background-color: #fff3e0;
        }
        
        .departure-card-compact.safe {
            border-left-color: #4caf50;
            background-color: #e8f5e9;
        }
        
        /* Headers styling */
        .main-header {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            color: #2c3e50;
        }
        
        .sub-header {
            font-size: 1.2em;
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        
        /* Alert boxes */
        .stAlert {
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #f8f9fa;
            border-radius: 8px 8px 0 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #333333 !important;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            color: #333333 !important;
        }
        
        /* Dataframe styling */
        .dataframe {
            background-color: white !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        /* Animation for overdue alerts */
        @keyframes pulse-red {
            0% { background-color: rgba(255, 0, 0, 0.1); }
            50% { background-color: rgba(255, 0, 0, 0.2); }
            100% { background-color: rgba(255, 0, 0, 0.1); }
        }
        
        .overdue-alert {
            animation: pulse-red 2s infinite;
        }
        
        /* Language selector */
        .language-selector {
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 1000;
        }
        
        /* Slider styling */
        .stSlider > div > div > div {
            background-color: #4CAF50 !important;
        }
        
        /* File uploader */
        .stFileUploader > div {
            background-color: #f8f9fa;
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 20px;
        }
        
        /* Make sure text is visible everywhere */
        h1, h2, h3, h4, h5, h6, p, span, div, label {
            color: #333333 !important;
        }
        
        /* Sidebar specific text */
        .fixed-left-sidebar p, .fixed-left-sidebar h3,
        .fixed-right-sidebar p, .fixed-right-sidebar h3 {
            color: white !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header(title, lang="en"):
    """Render the fixed header"""
    st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
    header_col1, header_col2, header_col3 = st.columns([1, 2, 1])

    with header_col1:
        st.image(LOGO_URL, width=40)

    with header_col2:
        st.markdown(
            f'<h2 style="text-align: center; margin: 0;">{title}</h2>',
            unsafe_allow_html=True,
        )

    with header_col3:
        if st.button(get_text("refresh", lang), key="main_refresh"):
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebars(lang="en"):
    """Render the fixed sidebars with QR codes"""
    departure_qr = f"{QR_BASE_URL}{APP_BASE_URL}/?page=departures"
    arrival_qr = f"{QR_BASE_URL}{APP_BASE_URL}/?page=arrivals"

    st.markdown(
        f"""
    <div class="fixed-left-sidebar" style="z-index: 100; background-color: #2d2d2d;">
        <div style="text-align: center;">
            <div style="font-size: 48px; margin-bottom: 10px;">⬆️</div>
            <h3>{get_text('departures', lang).replace('🚶 ', '')}</h3>
            <p>{get_text('scan_departure', lang)}</p>
            <img src="{departure_qr}" width="150">
        </div>
    </div>
    
    <div class="fixed-right-sidebar">
        <div style="text-align: center;">
            <div style="font-size: 48px; margin-bottom: 10px;">⬇️</div>
            <h3>{get_text('arrivals', lang).replace('🏃 ', '')}</h3>
            <p>{get_text('scan_arrival', lang)}</p>
            <img src="{arrival_qr}" width="150">
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_departure_card(dep, lang="en"):
    """Render a compact departure card"""
    # Determine card style
    if dep["is_overdue"]:
        card_class = "departure-card-compact overdue"
        status_icon = "🔴"
    elif dep["time_remaining"] < 0.5:
        card_class = "departure-card-compact warning"
        status_icon = "🟡"
    else:
        card_class = "departure-card-compact safe"
        status_icon = "🟢"

    # Time display
    if dep["is_overdue"]:
        hours_overdue = abs(int(dep["time_remaining"]))
        minutes_overdue = abs(int((dep["time_remaining"] % 1) * 60))
        time_text = get_text(
            "overdue_by", lang, hours=hours_overdue, minutes=minutes_overdue
        )
    else:
        hours = int(dep["time_remaining"])
        minutes = int((dep["time_remaining"] % 1) * 60)
        time_text = get_text("time_remaining", lang, hours=hours, minutes=minutes)

    # Location status
    has_location = False
    if "last_location" in dep and dep.get("last_location"):
        has_location = True
    location_icon = "📍" if has_location else ""

    departed_time = format_time(pd.to_datetime(dep["departed_at"]))

    st.markdown(
        f"""
    <div class="{card_class}">
        <div>
            {status_icon} <strong>{dep['person_name']}</strong> {location_icon}
            → {dep['destination']}
            <small style="color: #666; margin-left: 10px;">
                {get_text('departure_time', lang)}: {departed_time}
            </small>
        </div>
        <div>
            <strong style="color: {'red' if dep['is_overdue'] else 'inherit'};">{time_text}</strong>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def play_alert_sound():
    """Simple beep sound using Web Audio API"""
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
    components.html(sound_js, height=0)


def check_and_play_alerts(overdue_deps):
    """Check if we should play alert sound"""
    if not overdue_deps.empty:
        # Apply pulsing red background
        st.markdown(
            """
        <style>
            .main-content {
                animation: pulse-red 2s infinite;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Check if we should play alert sound (every 10 minutes)
        current_time = get_current_time()
        if "last_alert_time" not in st.session_state:
            st.session_state.last_alert_time = current_time - timedelta(
                minutes=ALERT_INTERVAL_MINUTES + 1
            )

        if (current_time - st.session_state.last_alert_time).total_seconds() > (
            ALERT_INTERVAL_MINUTES * 60
        ):
            play_alert_sound()
            st.session_state.last_alert_time = current_time


def add_pwa_install_button():
    """Add PWA install button functionality"""
    pwa_script = """
    <script>
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        const installButton = document.getElementById('install-button');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    if (outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                    }
                    deferredPrompt = null;
                }
            });
        }
    });
    
    // iOS Safari detection and instructions
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    if (isIOS) {
        const iosInstructions = document.getElementById('ios-instructions');
        if (iosInstructions) {
            iosInstructions.style.display = 'block';
        }
    }
    </script>
    
    <button id="install-button" class="install-button" style="display: none;">
        📱 Install App
    </button>
    
    <div id="ios-instructions" style="display: none; padding: 10px; background-color: #f0f0f0; border-radius: 5px; margin: 10px 0;">
        <p><strong>To install on iOS:</strong></p>
        <ol>
            <li>Tap the Share button <span style="font-size: 20px;">⎘</span></li>
            <li>Select "Add to Home Screen"</li>
            <li>Tap "Add"</li>
        </ol>
    </div>
    """
    components.html(pwa_script, height=100)


def render_language_selector():
    """Render language selector"""
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        lang_options = {"English": "en", "Français": "fr"}
        current_lang = st.session_state.get("language", "en")
        current_label = [k for k, v in lang_options.items() if v == current_lang][0]

        selected_lang = st.selectbox(
            "🌐",
            options=list(lang_options.keys()),
            index=list(lang_options.values()).index(current_lang),
            label_visibility="collapsed",
        )

        if lang_options[selected_lang] != current_lang:
            st.session_state.language = lang_options[selected_lang]
            st.rerun()
