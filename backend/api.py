"""
FastAPI backend that integrates OpenRouter with MCP servers.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
import httpx
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .service_layer import MCPService

app = FastAPI(title="Canvas MCP API")

# Get port from environment (Render provides this)
PORT = int(os.getenv("PORT", 8000))

# Get frontend URL from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

# CORS middleware - allow frontend and localhost for development
# Build allowed origins list
allowed_origins = [
    FRONTEND_URL,
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

# Add Streamlit Cloud URL if provided
STREAMLIT_URL = os.getenv("STREAMLIT_URL")
if STREAMLIT_URL:
    allowed_origins.append(STREAMLIT_URL)

# In production, be more specific with origins
# In development, allow all (for testing)
if os.getenv("ENVIRONMENT") != "production":
    allowed_origins = ["*"]  # Allow all in development

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet"  # You can change this to any model supported by OpenRouter


class ChatMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str
    conversation_history: Optional[List[ChatMessage]] = []


class QueryResponse(BaseModel):
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
    else:
        raise ValueError(f"Unknown function prefix: {function_name}")


async def execute_tool_call(function_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    server_name, tool_name = parse_tool_name(function_name)
    result = await MCPService.call_tool(server_name, tool_name, arguments)
    return result


@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """
    Process a user query through OpenRouter with MCP tool support.
    """
    try:
        # Build conversation messages
        messages = []
        
        # Add system message
        system_message = """You are a helpful assistant that can interact with Canvas (course management), 
Google Calendar, and Gmail. You have access to various tools to help users manage their courses, 
schedule events, and handle emails. Use the tools when needed to answer user queries."""
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current user query
        messages.append({"role": "user", "content": request.query})
        
        # Get available tools
        tools = MCPService.get_all_tools()
        
        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=60.0) as client:
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
                    "HTTP-Referer": base_url,  # Optional: for tracking
                    "X-Title": "Canvas MCP Frontend"  # Optional: for tracking
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
                    
                    # Execute tool
                    tool_result = await execute_tool_call(function_name, arguments)
                    
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


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Canvas MCP API",
        "version": "1.0.0"
    }


@app.get("/tools")
async def get_tools():
    """Get all available tools."""
    return {"tools": MCPService.get_all_tools()}

