"""
Streamlit frontend for Canvas MCP.
"""
import streamlit as st
import requests
import os
from typing import List, Dict, Any

# Backend API URL - use 127.0.0.1 instead of localhost for better Windows compatibility
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


def check_backend_connection() -> bool:
    """Check if backend is accessible."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def send_message(query: str) -> str:
    """Send a message to the backend API."""
    try:
        # Prepare conversation history
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.conversation_history
        ]
        
        payload = {
            "query": query,
            "conversation_history": conversation_history
        }
        
        response = requests.post(f"{API_URL}/chat", json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response received")
    
    except requests.exceptions.ConnectionError:
        return f"❌ **Connection Error**: Cannot connect to backend at `{API_URL}`\n\n**Please make sure:**\n1. The backend is running: `uvicorn backend.api:app --reload --port 8000`\n2. Try using `127.0.0.1:8000` instead of `localhost:8000`\n3. Check if Windows Firewall is blocking the connection"
    except requests.exceptions.Timeout:
        return f"⏱️ **Timeout Error**: Request took too long. The backend might be overloaded or there's a network issue."
    except requests.exceptions.RequestException as e:
        return f"❌ **Error**: {str(e)}"


def main():
    st.set_page_config(
        page_title="Canvas MCP Assistant",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 Canvas MCP Assistant")
    st.markdown("Ask me anything about your courses, calendar, or emails!")
    
    # Check backend connection
    if "backend_checked" not in st.session_state:
        st.session_state.backend_checked = False
    
    if not st.session_state.backend_checked:
        with st.spinner("Checking backend connection..."):
            if check_backend_connection():
                st.success(f"✅ Connected to backend at {API_URL}")
                st.session_state.backend_checked = True
            else:
                st.error(f"❌ Cannot connect to backend at {API_URL}")
                st.info("""
                **To start the backend:**
                1. Open a new terminal
                2. Run: `uvicorn backend.api:app --reload --port 8000`
                3. Wait for "Application startup complete"
                4. Refresh this page
                
                **If you're on Windows and having connection issues:**
                - Try: `uvicorn backend.api:app --reload --port 8000 --host 127.0.0.1`
                - Check Windows Firewall settings
                - Make sure no proxy is interfering with localhost
                """)
                st.session_state.backend_checked = True
                st.stop()
    
    # Sidebar with info
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This assistant can help you with:
        - **Canvas**: View courses, assignments, and create new ones
        - **Calendar**: View and create calendar events
        - **Gmail**: Read and send emails
        
        Just ask in natural language!
        """)
        
        st.markdown(f"**Backend URL:** `{API_URL}`")
        
        if st.button("Test Backend Connection"):
            if check_backend_connection():
                st.success("✅ Backend is accessible!")
            else:
                st.error("❌ Cannot reach backend")
        
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
                response = send_message(prompt)
                st.markdown(response)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.conversation_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()

