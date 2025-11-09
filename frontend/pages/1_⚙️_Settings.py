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

# User ID input (optional for Google OAuth)
st.header("User Identification")
user_id = st.text_input(
    "User ID (Optional)",
    value=st.session_state.get("user_id", ""),
    help="Enter a unique identifier for your account. If connecting Google, you can leave this blank and your Google email will be used automatically."
)

# Google Account Linking (Available even without User ID)
st.header("🔗 Google Account")
st.markdown("Link your Google account to enable Gmail and Calendar integration")

# If user_id is provided, check if already linked
if user_id:
    st.session_state.user_id = user_id
    st.info(f"Using user ID: `{user_id}`. If you connect Google without a User ID, your Google email will be used as the User ID.")

# Check if already linked (only if user_id is provided)
gmail_creds = None
calendar_creds = None
if user_id:
    gmail_creds = get_credentials(API_URL, user_id, "google_gmail")
    calendar_creds = get_credentials(API_URL, user_id, "google_calendar")

if user_id and gmail_creds and calendar_creds:
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
    st.info("🔗 Connect your Google account to enable Gmail and Calendar features")
    
    # Button to start OAuth flow - user_id is optional
    import urllib.parse
    if user_id:
        auth_url = f"{API_URL}/auth/google/authorize?user_id={urllib.parse.quote(user_id)}"
        st.markdown(f"**Note:** Connecting with User ID: `{user_id}`")
    else:
        auth_url = f"{API_URL}/auth/google/authorize"
        st.markdown("**Note:** No User ID provided. Your Google email will be used as the User ID automatically.")
    
    # Create a prominent button using Streamlit
    st.markdown("### 👆 Click the button below to connect:")
    
    # Display the button prominently
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # Create a clickable link styled as a button
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{auth_url}" target="_self" style="text-decoration: none;">
                <button style="
                    background-color: #4285F4;
                    color: white;
                    padding: 15px 40px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 18px;
                    font-weight: bold;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    transition: background-color 0.3s;
                    width: 100%;
                " onmouseover="this.style.backgroundColor='#357ae8'" onmouseout="this.style.backgroundColor='#4285F4'">
                    🔗 Connect Google Account
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # Also provide a Streamlit button as backup
        if st.button("🔗 Connect Google Account (Alternative)", use_container_width=True, help="Click this if the button above doesn't work"):
            st.markdown(f'<script>window.location.href = "{auth_url}";</script>', unsafe_allow_html=True)
            st.info("Redirecting to Google... If you're not redirected, click the link above.")
            st.stop()
    
    st.markdown("---")
    
    with st.expander("ℹ️ What happens when I click?", expanded=True):
        st.markdown("""
        **Step-by-step process:**
        1. **Click "Connect Google Account"** → You'll be redirected to Google's secure login page
        2. **Sign in** → Enter your Google account email and password
        3. **Grant permissions** → Google will ask you to allow access to:
           - Gmail (to read and send emails)
           - Google Calendar (to view and create events)
        4. **Automatic redirect** → You'll be brought back to this page
        5. **Success!** → You'll see a green success message
        6. **User ID** → If you didn't provide one, your Google email will be used automatically
        7. **Ready to use** → You can now use Gmail and Calendar features in the chat!
        
        **Security:**
        - Your credentials are stored securely in Supabase
        - Only you can access your data
        - You can unlink your account anytime
        - No manual token copying needed!
        """)

# Canvas API Settings (only if user_id is provided)
if user_id:
    st.divider()
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

# Database Verification Section
st.divider()
st.header("📊 Database Verification")
st.markdown("Verify that your User IDs and credentials are stored in Supabase")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 List All Users in Database", use_container_width=True):
        import requests
        try:
            response = requests.get(f"{API_URL}/auth/users", timeout=10)
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                count = data.get("count", 0)
                
                if count > 0:
                    st.success(f"✅ Found {count} user(s) in database:")
                    for user in users:
                        with st.expander(f"User: {user['user_id']}", expanded=False):
                            st.write(f"**Services:** {', '.join(user['services'])}")
                            st.write(f"**Created:** {user.get('created_at', 'N/A')}")
                            st.write(f"**Updated:** {user.get('updated_at', 'N/A')}")
                else:
                    st.info("📭 No users found in database yet.")
            else:
                st.error(f"❌ Failed to fetch users: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

with col2:
    if st.button("🔍 Check My Credentials", use_container_width=True, disabled=not user_id):
        if not user_id:
            st.warning("Please enter a User ID first")
        else:
            import requests
            try:
                response = requests.get(f"{API_URL}/auth/users/{urllib.parse.quote(user_id)}/credentials", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    credentials = data.get("credentials", {})
                    services = data.get("services", [])
                    
                    if services:
                        st.success(f"✅ Found credentials for: {', '.join(services)}")
                        for service in services:
                            cred_info = credentials.get(service, {})
                            st.write(f"**{service}:**")
                            st.write(f"  - Created: {cred_info.get('created_at', 'N/A')}")
                            st.write(f"  - Updated: {cred_info.get('updated_at', 'N/A')}")
                    else:
                        st.info(f"📭 No credentials found for User ID: {user_id}")
                else:
                    st.error(f"❌ Failed to fetch credentials: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# View stored credentials (only if user_id is provided)
if user_id:
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
    st.info("💡 **Tip:** Enter a User ID above to check specific credentials, or connect Google account to auto-create a User ID from your email.")

