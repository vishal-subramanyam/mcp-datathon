"""
Service layer that provides programmatic access to MCP server tools.
This allows us to call MCP tools directly without going through stdio.
"""
import os
import sys
from typing import Dict, Any, List, Optional
import asyncio

# Add parent directory to path to import MCP servers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import helper functions from MCP servers
# Canvas
from mcp_server import (
    fetch_courses,
    fetch_upcoming_assignments,
    build_daily_briefing,
    create_assignment,
    delete_assignment,
    create_course
)

# Calendar
from calendar_mcp_server import (
    list_calendars,
    get_calendar_events,
    get_event,
    create_event,
    update_event,
    delete_event,
    parse_event
)

# Gmail
from gmail_mcp_server import (
    list_messages,
    get_message,
    parse_message,
    send_message,
    mark_as_read,
    mark_as_unread,
    delete_message
)


class MCPService:
    """Service layer for MCP tools."""
    
    @staticmethod
    async def call_tool(server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Call a tool from an MCP server.
        
        Args:
            server_name: Name of the MCP server ('canvas', 'calendar', 'gmail')
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response as a string
        """
        if arguments is None:
            arguments = {}
        
        try:
            if server_name == "canvas":
                return await MCPService._call_canvas_tool(tool_name, arguments)
            elif server_name == "calendar":
                return await MCPService._call_calendar_tool(tool_name, arguments)
            elif server_name == "gmail":
                return await MCPService._call_gmail_tool(tool_name, arguments)
            else:
                return f"Error: Unknown server '{server_name}'"
        except Exception as e:
            return f"Error calling tool: {str(e)}"
    
    @staticmethod
    async def _call_canvas_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a Canvas tool."""
        if tool_name == "get_courses":
            courses = fetch_courses()
            if not courses:
                return "No courses found for this Canvas account."
            formatted = "Canvas Courses:\n\n"
            for i, course in enumerate(courses, 1):
                formatted += f"{i}. {course['name']} (ID: {course['id']})\n"
            formatted += f"\nTotal: {len(courses)} course(s)"
            return formatted
        
        elif tool_name == "get_upcoming_assignments":
            days = arguments.get("days", 7)
            if not isinstance(days, int) or days < 1:
                days = 7
            assignments = fetch_upcoming_assignments(days)
            if not assignments:
                return f"No assignments due in the next {days} day(s)."
            formatted = f"Upcoming Assignments (next {days} days):\n\n"
            for i, a in enumerate(assignments, 1):
                formatted += f"{i}. {a['course']}: {a['title']}\n"
                formatted += f"   Due: {a['due_date']}\n"
                formatted += f"   Points: {a['points']}\n"
                formatted += f"   Priority Score: {a['priority_score']}\n"
                formatted += f"   URL: {a['url']}\n\n"
            formatted += f"Total: {len(assignments)} assignment(s)"
            return formatted
        
        elif tool_name == "get_daily_briefing":
            return build_daily_briefing()
        
        elif tool_name == "create_assignment":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return "Error: 'course_id' and 'name' are required."
            assignment = create_assignment(
                course_id=course_id,
                name=name,
                description=arguments.get("description"),
                due_at=arguments.get("due_at"),
                points_possible=arguments.get("points_possible"),
                submission_types=arguments.get("submission_types"),
                published=arguments.get("published", False)
            )
            formatted = "✅ Assignment created successfully!\n\n"
            formatted += f"Name: {assignment['name']}\n"
            formatted += f"Course ID: {assignment['course_id']}\n"
            formatted += f"Assignment ID: {assignment['id']}\n"
            if assignment['points_possible']:
                formatted += f"Points: {assignment['points_possible']}\n"
            if assignment['due_at']:
                formatted += f"Due Date: {assignment['due_at']}\n"
            formatted += f"URL: {assignment['html_url']}\n"
            return formatted
        
        elif tool_name == "delete_assignment":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return "Error: 'course_id' and 'assignment_id' are required."
            result = delete_assignment(course_id, assignment_id)
            formatted = "✅ Assignment deleted successfully!\n\n"
            formatted += f"Deleted Assignment: {result['deleted_assignment']['name']}\n"
            formatted += f"Course: {result['deleted_assignment']['course_name']}\n"
            return formatted
        
        elif tool_name == "create_course":
            name = arguments.get("name")
            if not name:
                return "Error: 'name' is required."
            course = create_course(
                name=name,
                course_code=arguments.get("course_code"),
                start_at=arguments.get("start_at"),
                end_at=arguments.get("end_at"),
                account_id=arguments.get("account_id")
            )
            formatted = "✅ Course created successfully!\n\n"
            formatted += f"Name: {course['name']}\n"
            formatted += f"Course ID: {course['id']}\n"
            formatted += f"URL: {course['html_url']}\n"
            return formatted
        
        else:
            return f"Error: Unknown Canvas tool '{tool_name}'"
    
    @staticmethod
    async def _call_calendar_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a Calendar tool."""
        if tool_name == "list_calendars":
            calendars = list_calendars()
            if not calendars:
                return "No calendars found."
            formatted = f"Found {len(calendars)} calendar(s):\n\n"
            for i, cal in enumerate(calendars, 1):
                formatted += f"{i}. {cal['summary']}\n"
                formatted += f"   ID: {cal['id']}\n"
                formatted += f"   Primary: {'Yes' if cal['primary'] else 'No'}\n\n"
            return formatted
        
        elif tool_name == "list_events":
            calendar_id = arguments.get("calendar_id", "primary")
            events = get_calendar_events(
                calendar_id=calendar_id,
                time_min=arguments.get("time_min"),
                time_max=arguments.get("time_max"),
                max_results=arguments.get("max_results", 10),
                query=arguments.get("query")
            )
            if not events:
                return f"No events found in calendar '{calendar_id}'."
            formatted = f"Found {len(events)} event(s):\n\n"
            for i, event in enumerate(events, 1):
                parsed = parse_event(event)
                formatted += f"{i}. {parsed['summary']}\n"
                formatted += f"   Start: {parsed['start']}\n"
                formatted += f"   End: {parsed['end']}\n\n"
            return formatted
        
        elif tool_name == "get_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            if not event_id:
                return "Error: 'event_id' is required."
            event = get_event(calendar_id, event_id)
            parsed = parse_event(event)
            formatted = "Event Details:\n\n"
            formatted += f"Title: {parsed['summary']}\n"
            formatted += f"Start: {parsed['start']}\n"
            formatted += f"End: {parsed['end']}\n"
            if parsed['location']:
                formatted += f"Location: {parsed['location']}\n"
            return formatted
        
        elif tool_name == "create_event":
            summary = arguments.get("summary")
            if not summary:
                return "Error: 'summary' is required."
            event = create_event(
                summary=summary,
                description=arguments.get("description"),
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                location=arguments.get("location"),
                attendees=arguments.get("attendees"),
                calendar_id=arguments.get("calendar_id", "primary"),
                timezone=arguments.get("timezone", "UTC"),
                all_day=arguments.get("all_day", False)
            )
            parsed = parse_event(event)
            formatted = "✅ Event created successfully!\n\n"
            formatted += f"Title: {parsed['summary']}\n"
            formatted += f"Event ID: {parsed['id']}\n"
            formatted += f"Start: {parsed['start']}\n"
            formatted += f"End: {parsed['end']}\n"
            return formatted
        
        elif tool_name == "update_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            if not event_id:
                return "Error: 'event_id' is required."
            event = update_event(
                calendar_id=calendar_id,
                event_id=event_id,
                summary=arguments.get("summary"),
                description=arguments.get("description"),
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                location=arguments.get("location"),
                attendees=arguments.get("attendees"),
                timezone=arguments.get("timezone", "UTC")
            )
            parsed = parse_event(event)
            formatted = "✅ Event updated successfully!\n\n"
            formatted += f"Title: {parsed['summary']}\n"
            formatted += f"Start: {parsed['start']}\n"
            formatted += f"End: {parsed['end']}\n"
            return formatted
        
        elif tool_name == "delete_event":
            calendar_id = arguments.get("calendar_id", "primary")
            event_id = arguments.get("event_id")
            if not event_id:
                return "Error: 'event_id' is required."
            delete_event(calendar_id, event_id)
            return f"✅ Event {event_id} deleted successfully."
        
        else:
            return f"Error: Unknown Calendar tool '{tool_name}'"
    
    @staticmethod
    async def _call_gmail_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a Gmail tool."""
        if tool_name == "list_emails":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 10)
            messages = list_messages(query=query, max_results=max_results)
            if not messages:
                return "No emails found."
            email_list = []
            for msg in messages:
                try:
                    message_detail = get_message(msg['id'])
                    parsed = parse_message(message_detail)
                    email_list.append(parsed)
                except Exception:
                    continue
            formatted = f"Found {len(email_list)} email(s):\n\n"
            for i, email_data in enumerate(email_list, 1):
                formatted += f"{i}. {email_data['subject']}\n"
                formatted += f"   From: {email_data['from']}\n"
                formatted += f"   Date: {email_data['date']}\n\n"
            return formatted
        
        elif tool_name == "get_email":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            message = get_message(message_id)
            parsed = parse_message(message)
            formatted = "Email Details:\n\n"
            formatted += f"Subject: {parsed['subject']}\n"
            formatted += f"From: {parsed['from']}\n"
            formatted += f"To: {parsed['to']}\n"
            formatted += f"Date: {parsed['date']}\n"
            formatted += f"\nBody:\n{parsed['body']}\n"
            return formatted
        
        elif tool_name == "send_email":
            to = arguments.get("to")
            subject = arguments.get("subject")
            body = arguments.get("body")
            if not to or not subject or not body:
                return "Error: 'to', 'subject', and 'body' are required."
            result = send_message(
                to=to,
                subject=subject,
                body=body,
                body_type=arguments.get("body_type", "plain"),
                cc=arguments.get("cc"),
                bcc=arguments.get("bcc")
            )
            formatted = "✅ Email sent successfully!\n\n"
            formatted += f"To: {to}\n"
            formatted += f"Subject: {subject}\n"
            formatted += f"Message ID: {result['id']}\n"
            return formatted
        
        elif tool_name == "mark_email_read":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            mark_as_read(message_id)
            return f"✅ Email {message_id} marked as read."
        
        elif tool_name == "mark_email_unread":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            mark_as_unread(message_id)
            return f"✅ Email {message_id} marked as unread."
        
        elif tool_name == "delete_email":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            delete_message(message_id)
            return f"✅ Email {message_id} deleted successfully."
        
        elif tool_name == "search_emails":
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
            query = " ".join(query_parts)
            max_results = arguments.get("max_results", 10)
            messages = list_messages(query=query, max_results=max_results)
            if not messages:
                return "No emails found matching the search criteria."
            email_list = []
            for msg in messages:
                try:
                    message_detail = get_message(msg['id'])
                    parsed = parse_message(message_detail)
                    email_list.append(parsed)
                except Exception:
                    continue
            formatted = f"Found {len(email_list)} email(s):\n\n"
            for i, email_data in enumerate(email_list, 1):
                formatted += f"{i}. {email_data['subject']}\n"
                formatted += f"   From: {email_data['from']}\n\n"
            return formatted
        
        else:
            return f"Error: Unknown Gmail tool '{tool_name}'"
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """Get all available tools from all MCP servers."""
        tools = []
        
        # Canvas tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_courses",
                    "description": "Get all Canvas courses for the authenticated user",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_upcoming_assignments",
                    "description": "Get assignments due in the next N days (default: 7). Assignments are sorted by priority score.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look ahead for assignments",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_daily_briefing",
                    "description": "Get a formatted daily briefing of upcoming assignments due in the next 7 days",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_assignment",
                    "description": "Create a new assignment in a Canvas course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "name": {"type": "string", "description": "The name/title of the assignment"},
                            "description": {"type": "string", "description": "Assignment description"},
                            "due_at": {"type": "string", "description": "Due date in ISO 8601 format"},
                            "points_possible": {"type": "number", "description": "Maximum points for the assignment"},
                            "published": {"type": "boolean", "description": "Whether to publish the assignment", "default": False}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_assignment",
                    "description": "Delete an assignment from a Canvas course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "assignment_id": {"type": "integer", "description": "The ID of the assignment to delete"}
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            }
        ])
        
        # Calendar tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "calendar_list_calendars",
                    "description": "List all calendars accessible to the user",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calendar_list_events",
                    "description": "List events from a calendar with optional filtering",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "calendar_id": {"type": "string", "description": "Calendar ID (default: 'primary')", "default": "primary"},
                            "time_min": {"type": "string", "description": "Lower bound for event end time (ISO 8601 format)"},
                            "time_max": {"type": "string", "description": "Upper bound for event start time (ISO 8601 format)"},
                            "max_results": {"type": "integer", "description": "Maximum number of events to return", "default": 10}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calendar_create_event",
                    "description": "Create a new calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string", "description": "Event title (required)"},
                            "description": {"type": "string", "description": "Event description"},
                            "start_time": {"type": "string", "description": "Start time in ISO 8601 format"},
                            "end_time": {"type": "string", "description": "End time in ISO 8601 format"},
                            "location": {"type": "string", "description": "Event location"},
                            "calendar_id": {"type": "string", "description": "Calendar ID", "default": "primary"},
                            "timezone": {"type": "string", "description": "Timezone", "default": "UTC"}
                        },
                        "required": ["summary"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calendar_delete_event",
                    "description": "Delete a calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "calendar_id": {"type": "string", "description": "Calendar ID", "default": "primary"},
                            "event_id": {"type": "string", "description": "The ID of the event to delete"}
                        },
                        "required": ["event_id"]
                    }
                }
            }
        ])
        
        # Gmail tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "gmail_list_emails",
                    "description": "List emails from Gmail with optional filtering",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')"},
                            "max_results": {"type": "integer", "description": "Maximum number of emails to return", "default": 10}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "gmail_get_email",
                    "description": "Get detailed information about a specific email by message ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_id": {"type": "string", "description": "The ID of the email message to retrieve"}
                        },
                        "required": ["message_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "gmail_send_email",
                    "description": "Send an email through Gmail",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "Recipient email address"},
                            "subject": {"type": "string", "description": "Email subject"},
                            "body": {"type": "string", "description": "Email body content"},
                            "body_type": {"type": "string", "description": "Body type: 'plain' or 'html'", "default": "plain"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            }
        ])
        
        return tools

