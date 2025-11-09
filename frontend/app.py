"""
Streamlit frontend for Canvas MPC.
Main application entry point.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path to fix imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import using relative import (works in Streamlit Cloud)
from utils.api import check_backend_connection, send_message

# Configure page
st.set_page_config(
    page_title="Canvas MPC Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API URL from environment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Check for OAuth success redirect
query_params = st.query_params
if query_params.get("oauth_success") == "true":
    user_id_from_oauth = query_params.get("user_id", "")
    if user_id_from_oauth:
        st.session_state.user_id = user_id_from_oauth
        st.success(f"✅ Google account linked successfully!")
        # Clear query params
        st.query_params.clear()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "backend_checked" not in st.session_state:
    st.session_state.backend_checked = False


def main():
    """Main application function."""
    st.title("🎓 Canvas MPC Assistant")
    st.markdown("Ask me anything about your courses, calendar, or emails!")
    
    # Check backend connection
    if not st.session_state.backend_checked:
        with st.spinner("Checking backend connection..."):
            if check_backend_connection(API_URL):
                st.success(f"✅ Connected to backend at {API_URL}")
                st.session_state.backend_checked = True
            else:
                st.error(f"❌ Cannot connect to backend at {API_URL}")
                st.info("""
                **To start the backend:**
                1. Open a new terminal
                2. Run: `uvicorn backend.main:app --reload --port 8000`
                3. Wait for "Application startup complete"
                4. Refresh this page
                
                **If you're on Windows and having connection issues:**
                - Try: `uvicorn backend.main:app --reload --port 8000 --host 127.0.0.1`
                - Check Windows Firewall settings
                - Make sure no proxy is interfering with localhost
                """)
                st.session_state.backend_checked = True
                st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This assistant can help you with:
        - **Canvas**: View courses, assignments, and create new ones
        - **Calendar**: View and create calendar events
        - **Gmail**: Read and send emails
        - **Flashcards**: Create and study flashcards from course content
        
        Just ask in natural language!
        """)
        
        st.divider()
        
        st.markdown(f"**Backend URL:** `{API_URL}`")
        
        # User ID input (optional)
        st.subheader("User Settings")
        user_id = st.text_input(
            "User ID (optional)",
            value=st.session_state.user_id or "",
            help="Enter your user ID to use per-user credentials"
        )
        if user_id:
            st.session_state.user_id = user_id
            st.success(f"Using user ID: {user_id}")
        
        st.divider()
        
        # Connection test button
        if st.button("Test Backend Connection"):
            if check_backend_connection(API_URL):
                st.success("✅ Backend is accessible!")
            else:
                st.error("❌ Cannot reach backend")
        
        # Clear conversation button
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_message(
                    API_URL,
                    prompt,
                    st.session_state.conversation_history,
                    st.session_state.user_id
                )
                st.markdown(response)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.conversation_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()

