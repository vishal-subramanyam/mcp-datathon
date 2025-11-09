"""
API routes for Canvas MPC.
Handles chat requests, tool execution, and authentication.
"""
import os
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
import httpx
import json
import secrets

from backend.services.mcp_service import MCPService
from backend.services.auth_service import AuthService

router = APIRouter()

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Combined scopes for Gmail + Calendar
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

# Store OAuth state temporarily (in production, use Redis or database)
# Format: {state: {"user_id": str, "timestamp": float}}
oauth_states: Dict[str, Dict[str, Any]] = {}

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not set. Chat functionality will not work.")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


class ChatMessage(BaseModel):
    """Message in a conversation."""
    role: str
    content: str


class QueryRequest(BaseModel):
    """Request for chat endpoint."""
    query: str
    conversation_history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = None  # Optional user ID for per-user credentials


class QueryResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    tool_calls: Optional[List[Dict[str, Any]]] = []


def parse_tool_name(function_name: str) -> Tuple[str, str]:
    """
    Parse function name to extract server and tool name.
    Format: {server}_{tool_name}
    Example: canvas_get_courses -> ("canvas", "get_courses")
    """
    if function_name.startswith("canvas_"):
        return ("canvas", function_name[7:])
    elif function_name.startswith("calendar_"):
        return ("calendar", function_name[9:])
    elif function_name.startswith("gmail_"):
        return ("gmail", function_name[6:])
    elif function_name.startswith("flashcard_"):
        return ("flashcard", function_name[10:])
    else:
        raise ValueError(f"Unknown function prefix: {function_name}")


async def execute_tool_call(
    function_name: str, 
    arguments: Dict[str, Any],
    user_id: Optional[str] = None
) -> str:
    """
    Execute a tool call and return the result.
    
    Args:
        function_name: Name of the function to call
        arguments: Arguments to pass to the function
        user_id: Optional user ID for per-user credentials
    
    Returns:
        Result of the tool call as a string
    """
    server_name, tool_name = parse_tool_name(function_name)
    
    # Get user credentials if user_id is provided
    credentials = None
    if user_id:
        # Map server name to service name
        service_map = {
            "canvas": "canvas",
            "calendar": "google_calendar",
            "gmail": "google_gmail"
        }
        service = service_map.get(server_name)
        if service:
            credentials = await AuthService.get_user_credentials(user_id, service)
    
    result = await MCPService.call_tool(server_name, tool_name, arguments, credentials)
    return result


@router.post("/chat", response_model=QueryResponse)
async def chat(
    request: QueryRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Process a user query through OpenRouter with MCP tool support.
    
    Args:
        request: Query request with user message and history
        authorization: Optional Bearer token for user authentication
    
    Returns:
        Query response with assistant's reply
    """
    try:
        if not OPENROUTER_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenRouter API key not configured"
            )
        
        # Extract user_id from authorization header or request
        user_id = request.user_id
        if authorization and authorization.startswith("Bearer "):
            # Verify session token and get user_id
            session_token = authorization[7:]
            session = await AuthService.get_session(session_token)
            if session:
                user_id = session['user_id']
        
        # Build conversation messages
        messages = []
        
        # Add system message
        system_message = """You are a helpful assistant that can interact with Canvas (course management), 
Google Calendar, Gmail, and Flashcards. You have access to various tools to help users manage their courses, 
schedule events, handle emails, and create study flashcards. 

For flashcard creation (KEEP IT SIMPLE AND FAST):
1. Get course: Use canvas_get_courses to find the course
2. Get content: Use canvas_get_page_content for 1-2 key pages OR canvas_get_assignment_details for assignment info. DON'T fetch too much content.
3. Create set: Use flashcard_create_set with course_id and course_name. Save the set_id.
4. Generate: Use flashcard_generate with course_context (limit to key content, max 2-3 pages). Default generates 5 flashcards quickly.
5. Add: Use flashcard_add_flashcards with the set_id and generated flashcards.

IMPORTANT: Keep course_context short (1-2 pages max). Too much content causes timeouts. Prefer assignment descriptions over full page content when possible.

Use the tools when needed to answer user queries."""
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current user query
        messages.append({"role": "user", "content": request.query})
        
        # Get available tools
        tools = MCPService.get_all_tools()
        
        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=90.0) as client:
            max_iterations = 10  # Limit tool call iterations
            iteration = 0
            
            while iteration < max_iterations:
                payload = {
                    "model": MODEL,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                }
                
                # Get base URL from environment or use default
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": base_url,
                    "X-Title": "Canvas MPC"
                }
                
                response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                
                # Extract assistant message
                assistant_message = response_data["choices"][0]["message"]
                messages.append(assistant_message)
                
                # Check if tool calls are needed
                tool_calls = assistant_message.get("tool_calls", [])
                
                if not tool_calls:
                    # No more tool calls, return the final response
                    final_response = assistant_message.get("content", "")
                    return QueryResponse(
                        response=final_response,
                        tool_calls=None
                    )
                
                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Execute tool with user credentials
                    tool_result = await execute_tool_call(function_name, arguments, user_id)
                    
                    # Add tool result to messages
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })
                
                # Add tool results to messages
                messages.extend(tool_results)
                
                iteration += 1
            
            # If we've exceeded max iterations, return the last response
            final_response = messages[-1].get("content", "Maximum iterations reached.")
            return QueryResponse(
                response=final_response,
                tool_calls=None
            )
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"OpenRouter API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/tools")
async def get_tools():
    """Get all available MCP tools."""
    return {"tools": MCPService.get_all_tools()}


@router.post("/auth/credentials")
async def store_credentials(
    user_id: str,
    service: str,
    credentials: Dict[str, Any]
):
    """
    Store user credentials for a specific service.
    
    Args:
        user_id: User's unique identifier
        service: Service name (canvas, google_calendar, google_gmail)
        credentials: Credentials to store
    """
    success = await AuthService.store_user_credentials(user_id, service, credentials)
    if success:
        return {"message": "Credentials stored successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store credentials")


@router.get("/auth/credentials/{user_id}/{service}")
async def get_credentials(user_id: str, service: str):
    """
    Get user credentials for a specific service.
    
    Args:
        user_id: User's unique identifier
        service: Service name
    """
    credentials = await AuthService.get_user_credentials(user_id, service)
    if credentials:
        return {"credentials": credentials}
    else:
        raise HTTPException(status_code=404, detail="Credentials not found")


@router.delete("/auth/credentials/{user_id}/{service}")
async def delete_credentials(user_id: str, service: str):
    """
    Delete user credentials for a specific service.
    
    Args:
        user_id: User's unique identifier
        service: Service name
    """
    success = await AuthService.delete_user_credentials(user_id, service)
    if success:
        return {"message": "Credentials deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete credentials")


@router.get("/auth/google/authorize")
async def google_authorize(user_id: str):
    """
    Initiate Google OAuth flow.
    Redirects user to Google consent screen.
    
    Args:
        user_id: User's unique identifier
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    if not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_REDIRECT_URI not configured. Please set it in environment variables."
        )
    
    try:
        from google_auth_oauthlib.flow import Flow
        import time
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {
            "user_id": user_id,
            "timestamp": time.time()
        }
        
        # Clean up old states (older than 10 minutes)
        current_time = time.time()
        oauth_states.clear()  # Simple cleanup - in production use TTL-based storage
        oauth_states[state] = {
            "user_id": user_id,
            "timestamp": current_time
        }
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Generate authorization URL
        # Use 'select_account' for better UX (user chooses account)
        # Use 'consent' to force consent screen (useful for testing or re-auth)
        # For production, 'select_account' provides better user experience
        prompt_type = os.getenv("GOOGLE_OAUTH_PROMPT", "select_account")
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt=prompt_type,  # 'select_account' or 'consent'
            state=state
        )
        
        return RedirectResponse(url=authorization_url)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth libraries not installed. Please install google-auth-oauthlib."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate OAuth flow: {str(e)}"
        )


@router.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for tokens and stores them.
    
    Args:
        code: Authorization code from Google
        state: State parameter for CSRF protection
    """
    import time
    
    # Validate state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    
    state_data = oauth_states.pop(state)
    user_id = state_data.get("user_id")
    
    # Check if state is too old (more than 10 minutes)
    if time.time() - state_data.get("timestamp", 0) > 600:
        raise HTTPException(status_code=400, detail="OAuth state expired")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )
    
    if not GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_REDIRECT_URI not configured"
        )
    
    try:
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user email from Google
        try:
            oauth2_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            user_email = user_info.get('email')
            
            # Use email as user_id if not provided
            if not user_id and user_email:
                user_id = user_email
        except Exception as e:
            print(f"Warning: Could not fetch user email: {e}")
            # Continue without email
        
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID is required. Please provide user_id in the authorization request."
            )
        
        # Convert credentials to dict for storage
        creds_dict = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else GOOGLE_SCOPES
        }
        
        # Store credentials for both Gmail and Calendar
        # (Same credentials work for both since we requested both scopes)
        gmail_success = await AuthService.store_user_credentials(
            user_id, "google_gmail", creds_dict
        )
        calendar_success = await AuthService.store_user_credentials(
            user_id, "google_calendar", creds_dict
        )
        
        if gmail_success and calendar_success:
            # Redirect back to frontend with success
            frontend_url = os.getenv("FRONTEND_URL", os.getenv("STREAMLIT_URL", "http://localhost:8501"))
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&user_id={user_id}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to store credentials"
            )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth libraries not installed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback error: {str(e)}"
        )

