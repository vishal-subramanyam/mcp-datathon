# filename: gmail_mcp_server.py

import os
import asyncio
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from datetime import datetime, timedelta, timezone
from typing import List, Any, Optional, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "Gmail API libraries not installed. Please install with: "
        "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )

# -----------------------------
# CONFIGURATION
# -----------------------------
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Global Gmail service (initialized lazily)
_gmail_service: Any = None

# -----------------------------
# AUTHENTICATION
# -----------------------------
def get_gmail_service():
    """Get or create the Gmail service. Initializes lazily to ensure credentials are available."""
    global _gmail_service
    
    if _gmail_service is not None:
        return _gmail_service
    
    creds = None
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token_path = os.getenv("GMAIL_TOKEN_PATH", token_path)
        credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", credentials_path)
    except ImportError:
        pass
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise ValueError(
                    f"Gmail credentials not found at {credentials_path}. "
                    "Please download credentials.json from Google Cloud Console and place it in the project directory. "
                    "Or set GMAIL_CREDENTIALS_PATH environment variable to point to your credentials file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    # Build the Gmail service
    try:
        _gmail_service = build('gmail', 'v1', credentials=creds)
        return _gmail_service
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Gmail service: {str(e)}. "
            "Please check your credentials and ensure Gmail API is enabled in Google Cloud Console."
        )

# -----------------------------
# MCP SERVER
# -----------------------------
app = Server("gmail-mcp-server")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def list_messages(query: str = '', max_results: int = 10, user_id: str = 'me') -> List[Dict[str, Any]]:
    """
    List messages matching the query.
    
    Args:
        query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com', 'subject:test')
        max_results: Maximum number of messages to return
        user_id: User's email address or 'me' for authenticated user
    
    Returns:
        List of message dictionaries with id, threadId
    """
    service = get_gmail_service()
    try:
        response = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        return messages
    except HttpError as error:
        raise Exception(f"An error occurred while listing messages: {error}")

def get_message(message_id: str, user_id: str = 'me', format: str = 'full') -> Dict[str, Any]:
    """
    Get a message by ID.
    
    Args:
        message_id: The ID of the message
        user_id: User's email address or 'me' for authenticated user
        format: Format of the message ('full', 'metadata', 'minimal', 'raw')
    
    Returns:
        Message dictionary with full details
    """
    service = get_gmail_service()
    try:
        message = service.users().messages().get(
            userId=user_id,
            id=message_id,
            format=format
        ).execute()
        return message
    except HttpError as error:
        raise Exception(f"An error occurred while getting message: {error}")

def parse_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Gmail message into a readable format.
    
    Args:
        message: Message dictionary from Gmail API
    
    Returns:
        Parsed message with subject, from, to, date, body, etc.
    """
    payload = message.get('payload', {})
    headers = payload.get('headers', [])
    
    # Extract headers
    header_dict = {h['name']: h['value'] for h in headers}
    
    # Extract body
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                data = part['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        if payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    # Parse date
    date_str = header_dict.get('Date', '')
    try:
        parsed_date = email.utils.parsedate_to_datetime(date_str)
    except:
        parsed_date = None
    
    return {
        'id': message['id'],
        'threadId': message.get('threadId'),
        'subject': header_dict.get('Subject', '(No Subject)'),
        'from': header_dict.get('From', ''),
        'to': header_dict.get('To', ''),
        'date': parsed_date.isoformat() if parsed_date else date_str,
        'snippet': message.get('snippet', ''),
        'body': body,
        'labels': message.get('labelIds', []),
        'is_read': 'UNREAD' not in message.get('labelIds', []),
        'is_starred': 'STARRED' in message.get('labelIds', [])
    }

def send_message(
    to: str,
    subject: str,
    body: str,
    body_type: str = 'plain',
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    user_id: str = 'me'
) -> Dict[str, Any]:
    """
    Send an email message.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        body_type: 'plain' or 'html'
        cc: CC email address (optional)
        bcc: BCC email address (optional)
        user_id: User's email address or 'me' for authenticated user
    
    Returns:
        Dictionary with message ID and thread ID
    """
    service = get_gmail_service()
    try:
        message = MIMEText(body, body_type)
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send message
        sent_message = service.users().messages().send(
            userId=user_id,
            body={'raw': raw_message}
        ).execute()
        
        return {
            'id': sent_message['id'],
            'threadId': sent_message.get('threadId'),
            'labelIds': sent_message.get('labelIds', [])
        }
    except HttpError as error:
        raise Exception(f"An error occurred while sending message: {error}")

def mark_as_read(message_id: str, user_id: str = 'me') -> bool:
    """Mark a message as read."""
    service = get_gmail_service()
    try:
        service.users().messages().modify(
            userId=user_id,
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except HttpError as error:
        raise Exception(f"An error occurred while marking message as read: {error}")

def mark_as_unread(message_id: str, user_id: str = 'me') -> bool:
    """Mark a message as unread."""
    service = get_gmail_service()
    try:
        service.users().messages().modify(
            userId=user_id,
            id=message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        return True
    except HttpError as error:
        raise Exception(f"An error occurred while marking message as unread: {error}")

def delete_message(message_id: str, user_id: str = 'me') -> bool:
    """Delete a message."""
    service = get_gmail_service()
    try:
        service.users().messages().delete(userId=user_id, id=message_id).execute()
        return True
    except HttpError as error:
        raise Exception(f"An error occurred while deleting message: {error}")

# -----------------------------
# MCP TOOLS
# -----------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="list_emails",
            description="List emails from Gmail with optional filtering. Supports Gmail search queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'is:unread', 'from:example@gmail.com', 'subject:test', 'has:attachment'). Leave empty for all emails.",
                        "default": ""
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10, max: 500)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_email",
            description="Get detailed information about a specific email by message ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email message to retrieve"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="send_email",
            description="Send an email through Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "body_type": {
                        "type": "string",
                        "description": "Body type: 'plain' or 'html' (default: 'plain')",
                        "enum": ["plain", "html"],
                        "default": "plain"
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC email address (optional)"
                    },
                    "bcc": {
                        "type": "string",
                        "description": "BCC email address (optional)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="mark_email_read",
            description="Mark an email as read",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email message to mark as read"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="mark_email_unread",
            description="Mark an email as unread",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email message to mark as unread"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="delete_email",
            description="Delete an email from Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email message to delete"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails with advanced filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {
                        "type": "string",
                        "description": "Filter by sender email address"
                    },
                    "to": {
                        "type": "string",
                        "description": "Filter by recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Filter by subject (partial match)"
                    },
                    "has_attachment": {
                        "type": "boolean",
                        "description": "Filter by whether email has attachments"
                    },
                    "is_unread": {
                        "type": "boolean",
                        "description": "Filter by unread status"
                    },
                    "is_starred": {
                        "type": "boolean",
                        "description": "Filter by starred status"
                    },
                    "after_date": {
                        "type": "string",
                        "description": "Filter emails after this date (YYYY-MM-DD format)"
                    },
                    "before_date": {
                        "type": "string",
                        "description": "Filter emails before this date (YYYY-MM-DD format)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10, max: 500)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Optional[dict[str, Any]]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "list_emails":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 10)
            
            if not isinstance(max_results, int) or max_results < 1:
                max_results = 10
            if max_results > 500:
                max_results = 500
            
            messages = list_messages(query=query, max_results=max_results)
            
            if not messages:
                return [TextContent(
                    type="text",
                    text=f"No emails found matching query: '{query}'" if query else "No emails found."
                )]
            
            # Get details for each message
            email_list = []
            for msg in messages:
                try:
                    message_detail = get_message(msg['id'])
                    parsed = parse_message(message_detail)
                    email_list.append(parsed)
                except Exception as e:
                    continue
            
            # Format response
            formatted = f"Found {len(email_list)} email(s)"
            if query:
                formatted += f" matching query: '{query}'"
            formatted += "\n\n"
            
            for i, email_data in enumerate(email_list, 1):
                formatted += f"{i}. {email_data['subject']}\n"
                formatted += f"   From: {email_data['from']}\n"
                formatted += f"   To: {email_data['to']}\n"
                formatted += f"   Date: {email_data['date']}\n"
                formatted += f"   Message ID: {email_data['id']}\n"
                formatted += f"   Read: {'Yes' if email_data['is_read'] else 'No'}\n"
                formatted += f"   Starred: {'Yes' if email_data['is_starred'] else 'No'}\n"
                formatted += f"   Snippet: {email_data['snippet'][:100]}...\n" if len(email_data['snippet']) > 100 else f"   Snippet: {email_data['snippet']}\n"
                formatted += "\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_email":
            message_id = arguments.get("message_id")
            if not message_id:
                return [TextContent(
                    type="text",
                    text="Error: 'message_id' is required to get an email."
                )]
            
            try:
                message = get_message(message_id)
                parsed = parse_message(message)
                
                formatted = "Email Details:\n\n"
                formatted += f"Subject: {parsed['subject']}\n"
                formatted += f"From: {parsed['from']}\n"
                formatted += f"To: {parsed['to']}\n"
                formatted += f"Date: {parsed['date']}\n"
                formatted += f"Message ID: {parsed['id']}\n"
                formatted += f"Thread ID: {parsed['threadId']}\n"
                formatted += f"Read: {'Yes' if parsed['is_read'] else 'No'}\n"
                formatted += f"Starred: {'Yes' if parsed['is_starred'] else 'No'}\n"
                formatted += f"Labels: {', '.join(parsed['labels'])}\n"
                formatted += f"\nBody:\n{parsed['body']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error retrieving email: {str(e)}"
                )]
        
        elif name == "send_email":
            to = arguments.get("to")
            subject = arguments.get("subject")
            body = arguments.get("body")
            body_type = arguments.get("body_type", "plain")
            cc = arguments.get("cc")
            bcc = arguments.get("bcc")
            
            if not to:
                return [TextContent(
                    type="text",
                    text="Error: 'to' is required to send an email."
                )]
            if not subject:
                return [TextContent(
                    type="text",
                    text="Error: 'subject' is required to send an email."
                )]
            if not body:
                return [TextContent(
                    type="text",
                    text="Error: 'body' is required to send an email."
                )]
            
            try:
                result = send_message(
                    to=to,
                    subject=subject,
                    body=body,
                    body_type=body_type,
                    cc=cc,
                    bcc=bcc
                )
                
                formatted = "✅ Email sent successfully!\n\n"
                formatted += f"To: {to}\n"
                formatted += f"Subject: {subject}\n"
                formatted += f"Message ID: {result['id']}\n"
                formatted += f"Thread ID: {result.get('threadId', 'N/A')}\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error sending email: {str(e)}"
                )]
        
        elif name == "mark_email_read":
            message_id = arguments.get("message_id")
            if not message_id:
                return [TextContent(
                    type="text",
                    text="Error: 'message_id' is required to mark an email as read."
                )]
            
            try:
                mark_as_read(message_id)
                return [TextContent(
                    type="text",
                    text=f"✅ Email {message_id} marked as read."
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error marking email as read: {str(e)}"
                )]
        
        elif name == "mark_email_unread":
            message_id = arguments.get("message_id")
            if not message_id:
                return [TextContent(
                    type="text",
                    text="Error: 'message_id' is required to mark an email as unread."
                )]
            
            try:
                mark_as_unread(message_id)
                return [TextContent(
                    type="text",
                    text=f"✅ Email {message_id} marked as unread."
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error marking email as unread: {str(e)}"
                )]
        
        elif name == "delete_email":
            message_id = arguments.get("message_id")
            if not message_id:
                return [TextContent(
                    type="text",
                    text="Error: 'message_id' is required to delete an email."
                )]
            
            try:
                delete_message(message_id)
                return [TextContent(
                    type="text",
                    text=f"✅ Email {message_id} deleted successfully."
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error deleting email: {str(e)}"
                )]
        
        elif name == "search_emails":
            # Build Gmail query from arguments
            query_parts = []
            
            if arguments.get("from"):
                query_parts.append(f"from:{arguments['from']}")
            
            if arguments.get("to"):
                query_parts.append(f"to:{arguments['to']}")
            
            if arguments.get("subject"):
                query_parts.append(f"subject:{arguments['subject']}")
            
            if arguments.get("has_attachment"):
                query_parts.append("has:attachment")
            
            if arguments.get("is_unread"):
                query_parts.append("is:unread")
            
            if arguments.get("is_starred"):
                query_parts.append("is:starred")
            
            if arguments.get("after_date"):
                query_parts.append(f"after:{arguments['after_date']}")
            
            if arguments.get("before_date"):
                query_parts.append(f"before:{arguments['before_date']}")
            
            query = " ".join(query_parts)
            max_results = arguments.get("max_results", 10)
            
            if not isinstance(max_results, int) or max_results < 1:
                max_results = 10
            if max_results > 500:
                max_results = 500
            
            try:
                messages = list_messages(query=query, max_results=max_results)
                
                if not messages:
                    return [TextContent(
                        type="text",
                        text=f"No emails found matching the search criteria."
                    )]
                
                # Get details for each message
                email_list = []
                for msg in messages:
                    try:
                        message_detail = get_message(msg['id'])
                        parsed = parse_message(message_detail)
                        email_list.append(parsed)
                    except Exception as e:
                        continue
                
                # Format response
                formatted = f"Found {len(email_list)} email(s) matching search criteria\n\n"
                
                for i, email_data in enumerate(email_list, 1):
                    formatted += f"{i}. {email_data['subject']}\n"
                    formatted += f"   From: {email_data['from']}\n"
                    formatted += f"   Date: {email_data['date']}\n"
                    formatted += f"   Message ID: {email_data['id']}\n"
                    formatted += f"   Read: {'Yes' if email_data['is_read'] else 'No'}\n"
                    formatted += f"   Snippet: {email_data['snippet'][:80]}...\n" if len(email_data['snippet']) > 80 else f"   Snippet: {email_data['snippet']}\n"
                    formatted += "\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error searching emails: {str(e)}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"Configuration Error: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Unexpected Error: {str(e)}\n\nError type: {type(e).__name__}"
        )]

# -----------------------------
# MCP SERVER ENTRY POINT
# -----------------------------
async def main():
    """Run the MCP server using stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

