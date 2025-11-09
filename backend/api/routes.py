"""
API routes for Canvas MPC.
Handles chat requests, tool execution, and authentication.
"""
import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
import httpx
import json

from backend.services.mcp_service import MCPService
from backend.services.auth_service import AuthService

router = APIRouter()

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

