"""
API utilities for communicating with the backend.
"""
import requests
from typing import List, Dict, Any, Optional


def check_backend_connection(api_url: str) -> bool:
    """
    Check if backend is accessible.
    
    Args:
        api_url: URL of the backend API
    
    Returns:
        True if backend is accessible, False otherwise
    """
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def send_message(
    api_url: str,
    query: str,
    conversation_history: List[Dict[str, str]],
    user_id: Optional[str] = None
) -> str:
    """
    Send a message to the backend API.
    
    Args:
        api_url: URL of the backend API
        query: User's query
        conversation_history: List of previous messages
        user_id: Optional user ID for per-user credentials
    
    Returns:
        Response text from the backend
    """
    try:
        # Prepare conversation history
        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        
        payload = {
            "query": query,
            "conversation_history": history
        }
        
        if user_id:
            payload["user_id"] = user_id
        
        response = requests.post(f"{api_url}/chat", json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "No response received")
    
    except requests.exceptions.ConnectionError:
        return f"❌ **Connection Error**: Cannot connect to backend at `{api_url}`\n\n**Please make sure:**\n1. The backend is running: `uvicorn backend.main:app --reload --port 8000`\n2. Try using `127.0.0.1:8000` instead of `localhost:8000`\n3. Check if Windows Firewall is blocking the connection"
    except requests.exceptions.Timeout:
        return f"⏱️ **Timeout Error**: Request took too long. The backend might be overloaded or there's a network issue."
    except requests.exceptions.RequestException as e:
        return f"❌ **Error**: {str(e)}"


def store_credentials(
    api_url: str,
    user_id: str,
    service: str,
    credentials: Dict[str, Any]
) -> bool:
    """
    Store user credentials for a service.
    
    Args:
        api_url: URL of the backend API
        user_id: User's unique identifier
        service: Service name (canvas, google_calendar, google_gmail)
        credentials: Credentials to store
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            f"{api_url}/auth/credentials",
            json={
                "user_id": user_id,
                "service": service,
                "credentials": credentials
            },
            timeout=10
        )
        return response.status_code == 200
    except:
        return False


def get_credentials(
    api_url: str,
    user_id: str,
    service: str
) -> Optional[Dict[str, Any]]:
    """
    Get user credentials for a service.
    
    Args:
        api_url: URL of the backend API
        user_id: User's unique identifier
        service: Service name
    
    Returns:
        Credentials dictionary or None
    """
    try:
        response = requests.get(
            f"{api_url}/auth/credentials/{user_id}/{service}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("credentials")
        return None
    except:
        return None

