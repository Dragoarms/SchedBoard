"""
Authentication module for JMP Tracker
Handles password protection for sensitive areas
"""

import streamlit as st
import hashlib
from config import get_text

def hash_password(password):
    """Hash a password for secure comparison"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(required_page='management'):
    """
    Returns True if the user has the correct password.
    Password is stored in st.secrets for security.
    """
    
    # Initialize session state
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if "password_attempts" not in st.session_state:
        st.session_state.password_attempts = 0
    
    # Get language
    lang = st.session_state.get('language', 'en')
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        entered_password = st.session_state.get("password_input", "")
        
        try:
            # Get password from secrets
            correct_password = st.secrets.get("app_password", "")
            
            if not correct_password:
                st.error("Password not configured in secrets!")
                return
            
            if entered_password == correct_password:
                st.session_state.password_correct = True
                st.session_state.password_attempts = 0
                # Clear the password from session state
                if "password_input" in st.session_state:
                    del st.session_state["password_input"]
            else:
                st.session_state.password_correct = False
                st.session_state.password_attempts += 1
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            st.session_state.password_correct = False

    # If already authenticated, return True
    if st.session_state.password_correct:
        return True
    
    # Show password input
    with st.container():
        st.text_input(
            get_text('password', lang),
            type="password",
            on_change=password_entered,
            key="password_input"
        )
        
        # Show error if password was incorrect
        if st.session_state.password_attempts > 0:
            st.error(get_text('password_incorrect', lang))
            
            # Lock out after too many attempts
            if st.session_state.password_attempts >= 5:
                st.error("Too many failed attempts. Please refresh the page.")
                st.stop()
    
    return False

def logout():
    """Clear authentication state"""
    st.session_state.password_correct = False
    st.session_state.password_attempts = 0
    if "password_input" in st.session_state:
        del st.session_state["password_input"]

def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        if check_password():
            return func(*args, **kwargs)
        else:
            st.warning("Authentication required")
            return None
    return wrapper
