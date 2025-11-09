"""
Settings page for managing user credentials.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path to fix imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.utils.api import store_credentials, get_credentials

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Check for OAuth success redirect
query_params = st.query_params
if query_params.get("oauth_success") == "true":
    user_id_from_oauth = query_params.get("user_id", "")
    if user_id_from_oauth:
        st.session_state.user_id = user_id_from_oauth
        st.success(f"✅ Google account linked successfully! User ID: {user_id_from_oauth}")
        # Clear query params
        st.query_params.clear()

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
    
    # Google Account Linking (Combined Gmail + Calendar)
    st.header("🔗 Google Account")
    st.markdown("Link your Google account to enable Gmail and Calendar integration")
    
    # Check if already linked
    gmail_creds = get_credentials(API_URL, user_id, "google_gmail")
    calendar_creds = get_credentials(API_URL, user_id, "google_calendar")
    
    if gmail_creds and calendar_creds:
        st.success("✅ Google account linked! Gmail and Calendar are ready to use.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Re-link Google Account"):
                # Initiate OAuth flow
                import urllib.parse
                auth_url = f"{API_URL}/auth/google/authorize?user_id={urllib.parse.quote(user_id)}"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                st.info("Redirecting to Google...")
        
        with col2:
            if st.button("❌ Unlink Google Account"):
                # Delete credentials
                import requests
                try:
                    requests.delete(f"{API_URL}/auth/credentials/{urllib.parse.quote(user_id)}/google_gmail", timeout=10)
                    requests.delete(f"{API_URL}/auth/credentials/{urllib.parse.quote(user_id)}/google_calendar", timeout=10)
                    st.success("✅ Google account unlinked")
                    st.rerun()
                except:
                    st.error("❌ Failed to unlink account")
    else:
        st.info("🔗 Link your Google account to enable Gmail and Calendar features")
        
        # Button to start OAuth flow
        import urllib.parse
        auth_url = f"{API_URL}/auth/google/authorize?user_id={urllib.parse.quote(user_id)}"
        
        st.markdown(f"""
        <a href="{auth_url}" target="_self">
            <button style="background-color: #4285F4; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;">
                🔗 Connect Google Account
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **What this does:**
        - Opens Google's secure login page
        - Requests access to Gmail and Calendar
        - Stores your credentials securely in Supabase
        - No manual token copying needed!
        
        **Note:** You'll be redirected back to this page after authentication.
        """)
        
        # Manual fallback option
        with st.expander("⚠️ Manual Setup (Advanced)", expanded=False):
            st.warning("""
            **Only use this if OAuth doesn't work.**
            
            For manual setup:
            1. Download your OAuth credentials JSON from Google Cloud Console
            2. Use the authentication script: `python backend/services/authenticate_gmail.py`
            3. Paste the token.json content below
            """)
            
            gmail_credentials = st.text_area(
                "Gmail Token JSON",
                height=150,
                help="Paste your token.json content here"
            )
            
            if st.button("Save Manual Gmail Token"):
                if gmail_credentials:
                    try:
                        import json
                        creds = json.loads(gmail_credentials)
                        if store_credentials(API_URL, user_id, "google_gmail", creds):
                            st.success("✅ Gmail credentials saved!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save credentials")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format")
                else:
                    st.warning("Please paste your token JSON")
    
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

