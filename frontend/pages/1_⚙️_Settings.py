"""
Settings page for managing user credentials.
"""
import streamlit as st
import os
from frontend.utils.api import store_credentials, get_credentials

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Settings - Canvas MPC",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Settings")
st.markdown("Manage your API credentials and settings")

# User ID input
st.header("User Identification")
user_id = st.text_input(
    "User ID",
    value=st.session_state.get("user_id", ""),
    help="Enter a unique identifier for your account"
)

if user_id:
    st.session_state.user_id = user_id
    st.success(f"Using user ID: {user_id}")
    
    # Canvas API Settings
    st.header("Canvas API")
    st.markdown("Configure your Canvas LMS API credentials")
    
    with st.expander("Canvas Settings", expanded=False):
        canvas_url = st.text_input(
            "Canvas API URL",
            placeholder="https://canvas.instructure.com",
            help="Your Canvas instance URL"
        )
        canvas_token = st.text_input(
            "Canvas API Token",
            type="password",
            help="Your Canvas API access token"
        )
        
        if st.button("Save Canvas Credentials"):
            if canvas_url and canvas_token:
                credentials = {
                    "api_url": canvas_url,
                    "api_key": canvas_token
                }
                if store_credentials(API_URL, user_id, "canvas", credentials):
                    st.success("✅ Canvas credentials saved successfully!")
                else:
                    st.error("❌ Failed to save Canvas credentials")
            else:
                st.warning("Please fill in all fields")
    
    # Google Calendar Settings
    st.header("Google Calendar")
    st.markdown("Configure your Google Calendar API credentials")
    
    with st.expander("Google Calendar Settings", expanded=False):
        st.info("""
        **Note:** Google Calendar requires OAuth 2.0 authentication.
        
        1. Download your OAuth credentials JSON from Google Cloud Console
        2. Use the authentication script: `python scripts/authenticate_calendar.py`
        3. The token will be stored securely in Supabase
        """)
        
        calendar_credentials = st.text_area(
            "Calendar Credentials JSON",
            height=200,
            help="Paste your calendar_token.json content here"
        )
        
        if st.button("Save Calendar Credentials"):
            if calendar_credentials:
                try:
                    import json
                    creds = json.loads(calendar_credentials)
                    if store_credentials(API_URL, user_id, "google_calendar", creds):
                        st.success("✅ Google Calendar credentials saved successfully!")
                    else:
                        st.error("❌ Failed to save Google Calendar credentials")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format")
            else:
                st.warning("Please paste your credentials JSON")
    
    # Gmail Settings
    st.header("Gmail")
    st.markdown("Configure your Gmail API credentials")
    
    with st.expander("Gmail Settings", expanded=False):
        st.info("""
        **Note:** Gmail requires OAuth 2.0 authentication.
        
        1. Download your OAuth credentials JSON from Google Cloud Console
        2. Use the authentication script: `python scripts/authenticate_gmail.py`
        3. The token will be stored securely in Supabase
        """)
        
        gmail_credentials = st.text_area(
            "Gmail Credentials JSON",
            height=200,
            help="Paste your token.json content here"
        )
        
        if st.button("Save Gmail Credentials"):
            if gmail_credentials:
                try:
                    import json
                    creds = json.loads(gmail_credentials)
                    if store_credentials(API_URL, user_id, "google_gmail", creds):
                        st.success("✅ Gmail credentials saved successfully!")
                    else:
                        st.error("❌ Failed to save Gmail credentials")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format")
            else:
                st.warning("Please paste your credentials JSON")
    
    # View stored credentials
    st.divider()
    st.header("Current Credentials")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Check Canvas"):
            creds = get_credentials(API_URL, user_id, "canvas")
            if creds:
                st.success("✅ Canvas credentials found")
            else:
                st.warning("❌ No Canvas credentials")
    
    with col2:
        if st.button("Check Calendar"):
            creds = get_credentials(API_URL, user_id, "google_calendar")
            if creds:
                st.success("✅ Calendar credentials found")
            else:
                st.warning("❌ No Calendar credentials")
    
    with col3:
        if st.button("Check Gmail"):
            creds = get_credentials(API_URL, user_id, "google_gmail")
            if creds:
                st.success("✅ Gmail credentials found")
            else:
                st.warning("❌ No Gmail credentials")

else:
    st.warning("Please enter a User ID to manage credentials")

