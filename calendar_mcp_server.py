# filename: calendar_mcp_server.py

import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Any, Optional, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "Google Calendar API libraries not installed. Please install with: "
        "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )

# -----------------------------
# CONFIGURATION
# -----------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Global Calendar service (initialized lazily)
_calendar_service: Any = None

# -----------------------------
# AUTHENTICATION
# -----------------------------
def get_calendar_service():
    """Get or create the Calendar service. Initializes lazily to ensure credentials are available."""
    global _calendar_service
    
    if _calendar_service is not None:
        return _calendar_service
    
    creds = None
    token_path = os.getenv("CALENDAR_TOKEN_PATH", "calendar_token.json")
    credentials_path = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials.json")
    
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token_path = os.getenv("CALENDAR_TOKEN_PATH", token_path)
        credentials_path = os.getenv("CALENDAR_CREDENTIALS_PATH", credentials_path)
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
                    f"Calendar credentials not found at {credentials_path}. "
                    "Please download credentials.json from Google Cloud Console and place it in the project directory. "
                    "Or set CALENDAR_CREDENTIALS_PATH environment variable to point to your credentials file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080, prompt='consent')
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    # Build the Calendar service
    try:
        _calendar_service = build('calendar', 'v3', credentials=creds)
        return _calendar_service
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Calendar service: {str(e)}. "
            "Please check your credentials and ensure Calendar API is enabled in Google Cloud Console."
        )

# -----------------------------
# MCP SERVER
# -----------------------------
app = Server("calendar-mcp-server")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def list_calendars() -> List[Dict[str, Any]]:
    """List all calendars for the user."""
    service = get_calendar_service()
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = []
        for calendar in calendar_list.get('items', []):
            calendars.append({
                'id': calendar['id'],
                'summary': calendar.get('summary', 'No Title'),
                'description': calendar.get('description', ''),
                'timeZone': calendar.get('timeZone', ''),
                'primary': calendar.get('primary', False),
                'accessRole': calendar.get('accessRole', '')
            })
        return calendars
    except HttpError as error:
        raise Exception(f"An error occurred while listing calendars: {error}")

def get_calendar_events(
    calendar_id: str = 'primary',
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    query: Optional[str] = None,
    single_events: bool = True,
    order_by: str = 'startTime'
) -> List[Dict[str, Any]]:
    """
    List events from a calendar.
    
    Args:
        calendar_id: Calendar ID (default: 'primary')
        time_min: Lower bound (exclusive) for an event's end time (ISO 8601 format)
        time_max: Upper bound (exclusive) for an event's start time (ISO 8601 format)
        max_results: Maximum number of events to return
        query: Free text search terms
        single_events: Whether to expand recurring events into instances
        order_by: Order of events ('startTime' or 'updated')
    
    Returns:
        List of event dictionaries
    """
    service = get_calendar_service()
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            q=query,
            singleEvents=single_events,
            orderBy=order_by
        ).execute()
        
        events = events_result.get('items', [])
        return events
    except HttpError as error:
        raise Exception(f"An error occurred while listing events: {error}")

def get_event(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Get a specific event by ID."""
    service = get_calendar_service()
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event
    except HttpError as error:
        raise Exception(f"An error occurred while getting event: {error}")

def create_event(
    summary: str,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    calendar_id: str = 'primary',
    timezone: str = 'UTC',
    all_day: bool = False
) -> Dict[str, Any]:
    """
    Create a new calendar event.
    
    Args:
        summary: Event title (required)
        description: Event description
        start_time: Start time in ISO 8601 format (e.g., '2025-01-15T10:00:00')
        end_time: End time in ISO 8601 format
        start_date: Start date for all-day events (YYYY-MM-DD format)
        end_date: End date for all-day events (YYYY-MM-DD format)
        location: Event location
        attendees: List of attendee email addresses
        calendar_id: Calendar ID (default: 'primary')
        timezone: Timezone (default: 'UTC')
        all_day: Whether this is an all-day event
    
    Returns:
        Created event dictionary
    """
    service = get_calendar_service()
    
    # Build event body
    event = {
        'summary': summary,
    }
    
    if description:
        event['description'] = description
    
    if location:
        event['location'] = location
    
    # Set start and end times
    if all_day:
        # All-day event
        if start_date:
            event['start'] = {'date': start_date}
        else:
            # Default to today
            today = datetime.now().date().isoformat()
            event['start'] = {'date': today}
        
        if end_date:
            event['end'] = {'date': end_date}
        else:
            # Default to same day (all-day events end date is exclusive, so add 1 day)
            start = event['start'].get('date', datetime.now().date().isoformat())
            end_date_obj = datetime.fromisoformat(start) + timedelta(days=1)
            event['end'] = {'date': end_date_obj.date().isoformat()}
    else:
        # Timed event
        if start_time:
            event['start'] = {
                'dateTime': start_time,
                'timeZone': timezone
            }
        else:
            # Default to now
            now = datetime.now(timezone.utc).isoformat()
            event['start'] = {
                'dateTime': now,
                'timeZone': timezone
            }
        
        if end_time:
            event['end'] = {
                'dateTime': end_time,
                'timeZone': timezone
            }
        else:
            # Default to 1 hour after start
            start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(hours=1)
            event['end'] = {
                'dateTime': end_dt.isoformat(),
                'timeZone': timezone
            }
    
    # Add attendees
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]
    
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return created_event
    except HttpError as error:
        raise Exception(f"An error occurred while creating event: {error}")

def update_event(
    calendar_id: str,
    event_id: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    timezone: str = 'UTC'
) -> Dict[str, Any]:
    """
    Update an existing calendar event.
    
    Args:
        calendar_id: Calendar ID
        event_id: Event ID to update
        summary: New event title
        description: New event description
        start_time: New start time (ISO 8601 format)
        end_time: New end time (ISO 8601 format)
        location: New location
        attendees: New list of attendee email addresses
        timezone: Timezone (default: 'UTC')
    
    Returns:
        Updated event dictionary
    """
    service = get_calendar_service()
    
    # Get the existing event
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as error:
        raise Exception(f"An error occurred while getting event: {error}")
    
    # Update fields
    if summary is not None:
        event['summary'] = summary
    
    if description is not None:
        event['description'] = description
    
    if location is not None:
        event['location'] = location
    
    if start_time is not None:
        if 'date' in event.get('start', {}):
            # Convert all-day to timed event
            event['start'] = {
                'dateTime': start_time,
                'timeZone': timezone
            }
        else:
            event['start']['dateTime'] = start_time
            event['start']['timeZone'] = timezone
    
    if end_time is not None:
        if 'date' in event.get('end', {}):
            # Convert all-day to timed event
            event['end'] = {
                'dateTime': end_time,
                'timeZone': timezone
            }
        else:
            event['end']['dateTime'] = end_time
            event['end']['timeZone'] = timezone
    
    if attendees is not None:
        event['attendees'] = [{'email': email} for email in attendees]
    
    try:
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        return updated_event
    except HttpError as error:
        raise Exception(f"An error occurred while updating event: {error}")

def delete_event(calendar_id: str, event_id: str) -> bool:
    """Delete a calendar event."""
    service = get_calendar_service()
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return True
    except HttpError as error:
        raise Exception(f"An error occurred while deleting event: {error}")

def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a calendar event into a readable format."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Handle all-day vs timed events
    if 'date' in start:
        start_time = start.get('date')
        end_time = end.get('date')
        is_all_day = True
    else:
        start_time = start.get('dateTime')
        end_time = end.get('dateTime')
        is_all_day = False
    
    # Parse attendees
    attendees = []
    for attendee in event.get('attendees', []):
        attendees.append({
            'email': attendee.get('email'),
            'responseStatus': attendee.get('responseStatus', 'needsAction')
        })
    
    return {
        'id': event.get('id'),
        'summary': event.get('summary', '(No Title)'),
        'description': event.get('description', ''),
        'location': event.get('location', ''),
        'start': start_time,
        'end': end_time,
        'is_all_day': is_all_day,
        'timezone': start.get('timeZone', ''),
        'attendees': attendees,
        'status': event.get('status', ''),
        'htmlLink': event.get('htmlLink', ''),
        'created': event.get('created', ''),
        'updated': event.get('updated', '')
    }

# -----------------------------
# MCP TOOLS
# -----------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="list_calendars",
            description="List all calendars accessible to the user",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_events",
            description="List events from a calendar with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default: 'primary')",
                        "default": "primary"
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Lower bound for event end time (ISO 8601 format, e.g., '2025-01-15T00:00:00Z')"
                    },
                    "time_max": {
                        "type": "string",
                        "description": "Upper bound for event start time (ISO 8601 format, e.g., '2025-01-20T23:59:59Z')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default: 10, max: 2500)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 2500
                    },
                    "query": {
                        "type": "string",
                        "description": "Free text search terms to match against event fields"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_event",
            description="Get detailed information about a specific calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default: 'primary')",
                        "default": "primary"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the event to retrieve"
                    }
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="create_event",
            description="Create a new calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title (required)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (e.g., '2025-01-15T10:00:00' or '2025-01-15T10:00:00-08:00')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format (e.g., '2025-01-15T11:00:00')"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for all-day events (YYYY-MM-DD format)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for all-day events (YYYY-MM-DD format)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of attendee email addresses"
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default: 'primary')",
                        "default": "primary"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (default: 'UTC', e.g., 'America/Los_Angeles', 'Europe/London')",
                        "default": "UTC"
                    },
                    "all_day": {
                        "type": "boolean",
                        "description": "Whether this is an all-day event (default: false)",
                        "default": False
                    }
                },
                "required": ["summary"]
            }
        ),
        Tool(
            name="update_event",
            description="Update an existing calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default: 'primary')",
                        "default": "primary"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the event to update"
                    },
                    "summary": {
                        "type": "string",
                        "description": "New event title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New event description"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time (ISO 8601 format)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time (ISO 8601 format)"
                    },
                    "location": {
                        "type": "string",
                        "description": "New location"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "New list of attendee email addresses"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (default: 'UTC')",
                        "default": "UTC"
                    }
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="delete_event",
            description="Delete a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (default: 'primary')",
                        "default": "primary"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the event to delete"
                    }
                },
                "required": ["event_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Optional[dict[str, Any]]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "list_calendars":
            try:
                calendars = list_calendars()
                
                if not calendars:
                    return [TextContent(
                        type="text",
                        text="No calendars found."
                    )]
                
                formatted = f"Found {len(calendars)} calendar(s):\n\n"
                for i, cal in enumerate(calendars, 1):
                    formatted += f"{i}. {cal['summary']}\n"
                    formatted += f"   ID: {cal['id']}\n"
                    formatted += f"   Primary: {'Yes' if cal['primary'] else 'No'}\n"
                    formatted += f"   Access: {cal['accessRole']}\n"
                    if cal['timeZone']:
                        formatted += f"   Timezone: {cal['timeZone']}\n"
                    formatted += "\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error listing calendars: {str(e)}"
                )]
        
        elif name == "list_events":
            calendar_id = arguments.get("calendar_id", "primary")
            time_min = arguments.get("time_min")
            time_max = arguments.get("time_max")
            max_results = arguments.get("max_results", 10)
            query = arguments.get("query")
            
            if not isinstance(max_results, int) or max_results < 1:
                max_results = 10
            if max_results > 2500:
                max_results = 2500
            
            try:
                events = get_calendar_events(
                    calendar_id=calendar_id,
                    time_min=time_min,
                    time_max=time_max,
                    max_results=max_results,
                    query=query
                )
                
                if not events:
                    return [TextContent(
                        type="text",
                        text=f"No events found in calendar '{calendar_id}'."
                    )]
                
                formatted = f"Found {len(events)} event(s) in calendar '{calendar_id}':\n\n"
                for i, event in enumerate(events, 1):
                    parsed = parse_event(event)
                    formatted += f"{i}. {parsed['summary']}\n"
                    formatted += f"   Event ID: {parsed['id']}\n"
                    formatted += f"   Start: {parsed['start']}\n"
                    formatted += f"   End: {parsed['end']}\n"
                    if parsed['location']:
                        formatted += f"   Location: {parsed['location']}\n"
                    if parsed['is_all_day']:
                        formatted += f"   Type: All-day event\n"
                    formatted += "\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error listing events: {str(e)}"
                )]
        
        elif name == "get_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            
            if not event_id:
                return [TextContent(
                    type="text",
                    text="Error: 'event_id' is required to get an event."
                )]
            
            try:
                event = get_event(calendar_id, event_id)
                parsed = parse_event(event)
                
                formatted = "Event Details:\n\n"
                formatted += f"Title: {parsed['summary']}\n"
                formatted += f"Event ID: {parsed['id']}\n"
                formatted += f"Start: {parsed['start']}\n"
                formatted += f"End: {parsed['end']}\n"
                formatted += f"All-day: {'Yes' if parsed['is_all_day'] else 'No'}\n"
                if parsed['timezone']:
                    formatted += f"Timezone: {parsed['timezone']}\n"
                if parsed['location']:
                    formatted += f"Location: {parsed['location']}\n"
                if parsed['description']:
                    formatted += f"Description: {parsed['description']}\n"
                if parsed['attendees']:
                    formatted += f"Attendees: {', '.join([a['email'] for a in parsed['attendees']])}\n"
                formatted += f"Status: {parsed['status']}\n"
                if parsed['htmlLink']:
                    formatted += f"Link: {parsed['htmlLink']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error retrieving event: {str(e)}"
                )]
        
        elif name == "create_event":
            summary = arguments.get("summary")
            if not summary:
                return [TextContent(
                    type="text",
                    text="Error: 'summary' is required to create an event."
                )]
            
            description = arguments.get("description")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            location = arguments.get("location")
            attendees = arguments.get("attendees")
            calendar_id = arguments.get("calendar_id", "primary")
            timezone = arguments.get("timezone", "UTC")
            all_day = arguments.get("all_day", False)
            
            try:
                event = create_event(
                    summary=summary,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    start_date=start_date,
                    end_date=end_date,
                    location=location,
                    attendees=attendees,
                    calendar_id=calendar_id,
                    timezone=timezone,
                    all_day=all_day
                )
                parsed = parse_event(event)
                
                formatted = "✅ Event created successfully!\n\n"
                formatted += f"Title: {parsed['summary']}\n"
                formatted += f"Event ID: {parsed['id']}\n"
                formatted += f"Start: {parsed['start']}\n"
                formatted += f"End: {parsed['end']}\n"
                if parsed['location']:
                    formatted += f"Location: {parsed['location']}\n"
                if parsed['attendees']:
                    formatted += f"Attendees: {', '.join([a['email'] for a in parsed['attendees']])}\n"
                if parsed['htmlLink']:
                    formatted += f"Link: {parsed['htmlLink']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error creating event: {str(e)}"
                )]
        
        elif name == "update_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            
            if not event_id:
                return [TextContent(
                    type="text",
                    text="Error: 'event_id' is required to update an event."
                )]
            
            summary = arguments.get("summary")
            description = arguments.get("description")
            start_time = arguments.get("start_time")
            end_time = arguments.get("end_time")
            location = arguments.get("location")
            attendees = arguments.get("attendees")
            timezone = arguments.get("timezone", "UTC")
            
            try:
                event = update_event(
                    calendar_id=calendar_id,
                    event_id=event_id,
                    summary=summary,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    attendees=attendees,
                    timezone=timezone
                )
                parsed = parse_event(event)
                
                formatted = "✅ Event updated successfully!\n\n"
                formatted += f"Title: {parsed['summary']}\n"
                formatted += f"Event ID: {parsed['id']}\n"
                formatted += f"Start: {parsed['start']}\n"
                formatted += f"End: {parsed['end']}\n"
                if parsed['location']:
                    formatted += f"Location: {parsed['location']}\n"
                if parsed['htmlLink']:
                    formatted += f"Link: {parsed['htmlLink']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error updating event: {str(e)}"
                )]
        
        elif name == "delete_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            
            if not event_id:
                return [TextContent(
                    type="text",
                    text="Error: 'event_id' is required to delete an event."
                )]
            
            try:
                delete_event(calendar_id, event_id)
                return [TextContent(
                    type="text",
                    text=f"✅ Event {event_id} deleted successfully from calendar '{calendar_id}'."
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error deleting event: {str(e)}"
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

