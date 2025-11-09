"""
Tool Registry
Registers and executes all MCP tools for use with OpenRouter API.
"""

import os
import sys
from typing import Dict, Any, List, Optional
import asyncio

# Import MCP server modules
try:
    # Canvas tools - import the helper functions directly
    import mcp_server
    CANVAS_AVAILABLE = True
except ImportError:
    CANVAS_AVAILABLE = False
    mcp_server = None

try:
    # Gmail tools - import the helper functions directly
    import gmail_mcp_server
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    gmail_mcp_server = None

try:
    # Calendar tools - import the helper functions directly
    import calendar_mcp_server
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    calendar_mcp_server = None


class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self):
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools."""
        if CANVAS_AVAILABLE:
            self._register_canvas_tools()
        if GMAIL_AVAILABLE:
            self._register_gmail_tools()
        if CALENDAR_AVAILABLE:
            self._register_calendar_tools()
    
    def _register_canvas_tools(self):
        """Register Canvas tools."""
        self.tools["get_courses"] = {
            "function": self._execute_get_courses,
            "description": "Get all Canvas courses for the authenticated user",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_courses",
                    "description": "Get all Canvas courses for the authenticated user",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        }
        
        self.tools["get_upcoming_assignments"] = {
            "function": self._execute_get_upcoming_assignments,
            "description": "Get assignments due in the next N days (default: 7). Assignments are sorted by priority score.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_upcoming_assignments",
                    "description": "Get assignments due in the next N days (default: 7). Assignments are sorted by priority score (higher priority = due sooner).",
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
            }
        }
        
        self.tools["get_daily_briefing"] = {
            "function": self._execute_get_daily_briefing,
            "description": "Get a formatted daily briefing of upcoming assignments due in the next 7 days",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_daily_briefing",
                    "description": "Get a formatted daily briefing of upcoming assignments due in the next 7 days",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        }
        
        self.tools["create_assignment"] = {
            "function": self._execute_create_assignment,
            "description": "Create a new assignment in a Canvas course",
            "schema": {
                "type": "function",
                "function": {
                    "name": "create_assignment",
                    "description": "Create a new assignment in a Canvas course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {
                                "type": "integer",
                                "description": "The ID of the course where the assignment will be created"
                            },
                            "name": {
                                "type": "string",
                                "description": "The name/title of the assignment"
                            },
                            "description": {
                                "type": "string",
                                "description": "Assignment description (supports HTML)"
                            },
                            "due_at": {
                                "type": "string",
                                "description": "Due date in ISO 8601 format (e.g., '2025-12-31T23:59:00Z')"
                            },
                            "points_possible": {
                                "type": "number",
                                "description": "Maximum points for the assignment"
                            },
                            "submission_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of submission types. Common options: 'online_upload', 'online_text_entry', 'online_url', 'on_paper', 'none'"
                            },
                            "published": {
                                "type": "boolean",
                                "description": "Whether to publish the assignment immediately (default: false)",
                                "default": False
                            }
                        },
                        "required": ["course_id", "name"]
                    }
                }
            }
        }
        
        self.tools["delete_assignment"] = {
            "function": self._execute_delete_assignment,
            "description": "Delete an assignment from a Canvas course",
            "schema": {
                "type": "function",
                "function": {
                    "name": "delete_assignment",
                    "description": "Delete an assignment from a Canvas course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {
                                "type": "integer",
                                "description": "The ID of the course containing the assignment"
                            },
                            "assignment_id": {
                                "type": "integer",
                                "description": "The ID of the assignment to delete"
                            }
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            }
        }
        
        self.tools["create_course"] = {
            "function": self._execute_create_course,
            "description": "Create a new Canvas course. Note: Requires appropriate permissions (typically admin or account admin).",
            "schema": {
                "type": "function",
                "function": {
                    "name": "create_course",
                    "description": "Create a new Canvas course. Note: Requires appropriate permissions (typically admin or account admin).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Course name (required)"
                            },
                            "course_code": {
                                "type": "string",
                                "description": "Course code (optional)"
                            },
                            "start_at": {
                                "type": "string",
                                "description": "Course start date in ISO 8601 format (e.g., '2025-01-01T00:00:00Z')"
                            },
                            "end_at": {
                                "type": "string",
                                "description": "Course end date in ISO 8601 format (e.g., '2025-12-31T23:59:59Z')"
                            },
                            "account_id": {
                                "type": "integer",
                                "description": "Account ID to create the course in (optional, defaults to user's account)"
                            }
                        },
                        "required": ["name"]
                    }
                }
            }
        }
    
    def _register_gmail_tools(self):
        """Register Gmail tools."""
        self.tools["list_emails"] = {
            "function": self._execute_list_emails,
            "description": "List emails from Gmail with optional filtering. Supports Gmail search queries.",
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_emails",
                    "description": "List emails from Gmail with optional filtering. Supports Gmail search queries.",
                    "parameters": {
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
                }
            }
        }
        
        self.tools["get_email"] = {
            "function": self._execute_get_email,
            "description": "Get detailed information about a specific email by message ID",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_email",
                    "description": "Get detailed information about a specific email by message ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "The ID of the email message to retrieve"
                            }
                        },
                        "required": ["message_id"]
                    }
                }
            }
        }
        
        self.tools["send_email"] = {
            "function": self._execute_send_email,
            "description": "Send an email through Gmail",
            "schema": {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email through Gmail",
                    "parameters": {
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
                }
            }
        }
        
        self.tools["search_emails"] = {
            "function": self._execute_search_emails,
            "description": "Search emails with advanced filtering options",
            "schema": {
                "type": "function",
                "function": {
                    "name": "search_emails",
                    "description": "Search emails with advanced filtering options",
                    "parameters": {
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
                }
            }
        }
    
    def _register_calendar_tools(self):
        """Register Calendar tools."""
        self.tools["list_calendars"] = {
            "function": self._execute_list_calendars,
            "description": "List all calendars accessible to the user",
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_calendars",
                    "description": "List all calendars accessible to the user",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        }
        
        self.tools["list_events"] = {
            "function": self._execute_list_events,
            "description": "List events from a calendar with optional filtering",
            "schema": {
                "type": "function",
                "function": {
                    "name": "list_events",
                    "description": "List events from a calendar with optional filtering",
                    "parameters": {
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
                }
            }
        }
        
        self.tools["get_event"] = {
            "function": self._execute_get_event,
            "description": "Get detailed information about a specific calendar event",
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_event",
                    "description": "Get detailed information about a specific calendar event",
                    "parameters": {
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
                }
            }
        }
        
        self.tools["create_event"] = {
            "function": self._execute_create_event,
            "description": "Create a new calendar event",
            "schema": {
                "type": "function",
                "function": {
                    "name": "create_event",
                    "description": "Create a new calendar event",
                    "parameters": {
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
                                "description": "Start time in ISO 8601 format (e.g., '2025-01-15T10:00:00')"
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
                                "items": {"type": "string"},
                                "description": "List of attendee email addresses"
                            },
                            "calendar_id": {
                                "type": "string",
                                "description": "Calendar ID (default: 'primary')",
                                "default": "primary"
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone (default: 'UTC')",
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
                }
            }
        }
        
        self.tools["update_event"] = {
            "function": self._execute_update_event,
            "description": "Update an existing calendar event",
            "schema": {
                "type": "function",
                "function": {
                    "name": "update_event",
                    "description": "Update an existing calendar event",
                    "parameters": {
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
                                "items": {"type": "string"},
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
                }
            }
        }
        
        self.tools["delete_event"] = {
            "function": self._execute_delete_event,
            "description": "Delete a calendar event",
            "schema": {
                "type": "function",
                "function": {
                    "name": "delete_event",
                    "description": "Delete a calendar event",
                    "parameters": {
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
                }
            }
        }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions in OpenRouter format."""
        return [tool["schema"]["function"] for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result as a string."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."
        
        try:
            result = self.tools[tool_name]["function"](arguments)
            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    # Canvas tool executions
    def _execute_get_courses(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        courses = mcp_server.fetch_courses()
        if not courses:
            return "No courses found for this Canvas account."
        
        formatted = "Canvas Courses:\n\n"
        for i, course in enumerate(courses, 1):
            formatted += f"{i}. {course['name']} (ID: {course['id']})\n"
        formatted += f"\nTotal: {len(courses)} course(s)"
        return formatted
    
    def _execute_get_upcoming_assignments(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        days = arguments.get("days", 7)
        if not isinstance(days, int) or days < 1:
            days = 7
        
        assignments = mcp_server.fetch_upcoming_assignments(days)
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
    
    def _execute_get_daily_briefing(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        return mcp_server.build_daily_briefing()
    
    def _execute_create_assignment(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        course_id = arguments.get("course_id")
        name = arguments.get("name")
        
        if not course_id or not name:
            return "Error: 'course_id' and 'name' are required."
        
        assignment = mcp_server.create_assignment(
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
        if assignment.get('points_possible'):
            formatted += f"Points: {assignment['points_possible']}\n"
        if assignment.get('due_at'):
            formatted += f"Due Date: {assignment['due_at']}\n"
        formatted += f"URL: {assignment.get('html_url', 'N/A')}\n"
        return formatted
    
    def _execute_delete_assignment(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        course_id = arguments.get("course_id")
        assignment_id = arguments.get("assignment_id")
        
        if not course_id or not assignment_id:
            return "Error: 'course_id' and 'assignment_id' are required."
        
        result = mcp_server.delete_assignment(course_id, assignment_id)
        return f"✅ Assignment '{result['deleted_assignment']['name']}' deleted successfully from course '{result['deleted_assignment']['course_name']}'."
    
    def _execute_create_course(self, arguments: Dict[str, Any]) -> str:
        if not CANVAS_AVAILABLE:
            return "Error: Canvas tools are not available."
        name = arguments.get("name")
        if not name:
            return "Error: 'name' is required."
        
        course = mcp_server.create_course(
            name=name,
            course_code=arguments.get("course_code"),
            start_at=arguments.get("start_at"),
            end_at=arguments.get("end_at"),
            account_id=arguments.get("account_id")
        )
        
        formatted = "✅ Course created successfully!\n\n"
        formatted += f"Name: {course['name']}\n"
        formatted += f"Course ID: {course['id']}\n"
        if course.get('course_code'):
            formatted += f"Course Code: {course['course_code']}\n"
        formatted += f"URL: {course.get('html_url', 'N/A')}\n"
        return formatted
    
    # Gmail tool executions
    def _execute_list_emails(self, arguments: Dict[str, Any]) -> str:
        if not GMAIL_AVAILABLE:
            return "Error: Gmail tools are not available."
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        
        messages = gmail_mcp_server.list_messages(query=query, max_results=max_results)
        if not messages:
            return f"No emails found matching query: '{query}'" if query else "No emails found."
        
        email_list = []
        for msg in messages:
            try:
                message_detail = gmail_mcp_server.get_message(msg['id'])
                parsed = gmail_mcp_server.parse_message(message_detail)
                email_list.append(parsed)
            except Exception:
                continue
        
        formatted = f"Found {len(email_list)} email(s)"
        if query:
            formatted += f" matching query: '{query}'"
        formatted += "\n\n"
        
        for i, email_data in enumerate(email_list, 1):
            formatted += f"{i}. {email_data['subject']}\n"
            formatted += f"   From: {email_data['from']}\n"
            formatted += f"   Date: {email_data['date']}\n"
            formatted += f"   Message ID: {email_data['id']}\n"
            formatted += f"   Read: {'Yes' if email_data['is_read'] else 'No'}\n"
            formatted += f"   Snippet: {email_data['snippet'][:100]}...\n" if len(email_data['snippet']) > 100 else f"   Snippet: {email_data['snippet']}\n"
            formatted += "\n"
        
        return formatted
    
    def _execute_get_email(self, arguments: Dict[str, Any]) -> str:
        if not GMAIL_AVAILABLE:
            return "Error: Gmail tools are not available."
        message_id = arguments.get("message_id")
        if not message_id:
            return "Error: 'message_id' is required."
        
        message = gmail_mcp_server.get_message(message_id)
        parsed = gmail_mcp_server.parse_message(message)
        
        formatted = "Email Details:\n\n"
        formatted += f"Subject: {parsed['subject']}\n"
        formatted += f"From: {parsed['from']}\n"
        formatted += f"To: {parsed['to']}\n"
        formatted += f"Date: {parsed['date']}\n"
        formatted += f"Message ID: {parsed['id']}\n"
        formatted += f"\nBody:\n{parsed['body']}\n"
        return formatted
    
    def _execute_send_email(self, arguments: Dict[str, Any]) -> str:
        if not GMAIL_AVAILABLE:
            return "Error: Gmail tools are not available."
        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        
        if not to or not subject or not body:
            return "Error: 'to', 'subject', and 'body' are required."
        
        result = gmail_mcp_server.send_message(
            to=to,
            subject=subject,
            body=body,
            body_type=arguments.get("body_type", "plain"),
            cc=arguments.get("cc"),
            bcc=arguments.get("bcc")
        )
        
        return f"✅ Email sent successfully!\n\nTo: {to}\nSubject: {subject}\nMessage ID: {result['id']}"
    
    def _execute_search_emails(self, arguments: Dict[str, Any]) -> str:
        if not GMAIL_AVAILABLE:
            return "Error: Gmail tools are not available."
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
        
        messages = gmail_mcp_server.list_messages(query=query, max_results=max_results)
        if not messages:
            return "No emails found matching the search criteria."
        
        email_list = []
        for msg in messages:
            try:
                message_detail = gmail_mcp_server.get_message(msg['id'])
                parsed = gmail_mcp_server.parse_message(message_detail)
                email_list.append(parsed)
            except Exception:
                continue
        
        formatted = f"Found {len(email_list)} email(s) matching search criteria\n\n"
        for i, email_data in enumerate(email_list, 1):
            formatted += f"{i}. {email_data['subject']}\n"
            formatted += f"   From: {email_data['from']}\n"
            formatted += f"   Date: {email_data['date']}\n"
            formatted += f"   Message ID: {email_data['id']}\n\n"
        
        return formatted
    
    # Calendar tool executions
    def _execute_list_calendars(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
        calendars = calendar_mcp_server.list_calendars()
        
        if not calendars:
            return "No calendars found."
        
        formatted = f"Found {len(calendars)} calendar(s):\n\n"
        for i, cal in enumerate(calendars, 1):
            formatted += f"{i}. {cal['summary']}\n"
            formatted += f"   ID: {cal['id']}\n"
            formatted += f"   Primary: {'Yes' if cal['primary'] else 'No'}\n"
            formatted += "\n"
        
        return formatted
    
    def _execute_list_events(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
        calendar_id = arguments.get("calendar_id", "primary")
        time_min = arguments.get("time_min")
        time_max = arguments.get("time_max")
        max_results = arguments.get("max_results", 10)
        query = arguments.get("query")
        
        events = calendar_mcp_server.get_calendar_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            query=query
        )
        
        if not events:
            return f"No events found in calendar '{calendar_id}'."
        
        formatted = f"Found {len(events)} event(s) in calendar '{calendar_id}':\n\n"
        for i, event in enumerate(events, 1):
            parsed = calendar_mcp_server.parse_event(event)
            formatted += f"{i}. {parsed['summary']}\n"
            formatted += f"   Event ID: {parsed['id']}\n"
            formatted += f"   Start: {parsed['start']}\n"
            formatted += f"   End: {parsed['end']}\n"
            if parsed.get('location'):
                formatted += f"   Location: {parsed['location']}\n"
            formatted += "\n"
        
        return formatted
    
    def _execute_get_event(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
        calendar_id = arguments.get("calendar_id", "primary")
        event_id = arguments.get("event_id")
        
        if not event_id:
            return "Error: 'event_id' is required."
        
        event = calendar_mcp_server.get_event(calendar_id, event_id)
        parsed = calendar_mcp_server.parse_event(event)
        
        formatted = "Event Details:\n\n"
        formatted += f"Title: {parsed['summary']}\n"
        formatted += f"Event ID: {parsed['id']}\n"
        formatted += f"Start: {parsed['start']}\n"
        formatted += f"End: {parsed['end']}\n"
        if parsed.get('location'):
            formatted += f"Location: {parsed['location']}\n"
        if parsed.get('description'):
            formatted += f"Description: {parsed['description']}\n"
        return formatted
    
    def _execute_create_event(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
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
        if parsed.get('htmlLink'):
            formatted += f"Link: {parsed['htmlLink']}\n"
        return formatted
    
    def _execute_update_event(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
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
        
        return f"✅ Event updated successfully!\n\nTitle: {parsed['summary']}\nEvent ID: {parsed['id']}"
    
    def _execute_delete_event(self, arguments: Dict[str, Any]) -> str:
        if not CALENDAR_AVAILABLE:
            return "Error: Calendar tools are not available."
        calendar_id = arguments.get("calendar_id", "primary")
        event_id = arguments.get("event_id")
        
        if not event_id:
            return "Error: 'event_id' is required."
        
        delete_event(calendar_id, event_id)
        return f"✅ Event {event_id} deleted successfully from calendar '{calendar_id}'."

