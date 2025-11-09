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

# Flashcard storage
from flashcard_storage import FlashcardStorage

# Flashcard generation
from flashcard_generator import generate_flashcards_from_context

# Canvas additional functions
from mcp_server import (
    get_assignment_details,
    get_course_modules,
    get_course_files,
    get_course_pages,
    get_page_content
)


class MCPService:
    """Service layer for MCP tools."""
    
    @staticmethod
    async def call_tool(server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Call a tool from an MCP server.
        
        Args:
            server_name: Name of the MCP server ('canvas', 'calendar', 'gmail', 'flashcard')
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
            elif server_name == "flashcard":
                return await MCPService._call_flashcard_tool(tool_name, arguments)
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
        
        elif tool_name == "get_assignment_details":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return "Error: 'course_id' and 'assignment_id' are required."
            details = get_assignment_details(course_id, assignment_id)
            formatted = "Assignment Details:\n\n"
            formatted += f"Name: {details['name']}\n"
            formatted += f"Course: {details['course_name']}\n"
            formatted += f"Due Date: {details['due_at']}\n"
            if details.get('description'):
                formatted += f"\nDescription:\n{details['description'][:500]}...\n" if len(details['description']) > 500 else f"\nDescription:\n{details['description']}\n"
            return formatted
        
        elif tool_name == "get_course_modules":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            modules = get_course_modules(course_id)
            if not modules:
                return f"No modules found for course {course_id}."
            formatted = f"Course Modules ({len(modules)}):\n\n"
            for module in modules:
                formatted += f"Module: {module['name']}\n"
                formatted += f"  Items: {len(module['items'])}\n"
            return formatted
        
        elif tool_name == "get_course_files":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            files = get_course_files(course_id)
            if not files:
                return f"No files found for course {course_id}."
            formatted = f"Course Files ({len(files)}):\n\n"
            for file in files[:10]:
                formatted += f"• {file['display_name']}\n"
            return formatted
        
        elif tool_name == "get_course_pages":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            pages = get_course_pages(course_id)
            if not pages:
                return f"No pages found for course {course_id}."
            formatted = f"Course Pages ({len(pages)}):\n\n"
            for page in pages:
                formatted += f"• {page['title']}\n"
            return formatted
        
        elif tool_name == "get_page_content":
            course_id = arguments.get("course_id")
            page_url = arguments.get("page_url")
            if not course_id or not page_url:
                return "Error: 'course_id' and 'page_url' are required."
            page_content = get_page_content(course_id, page_url)
            formatted = f"Page: {page_content['title']}\n\n"
            formatted += f"Content:\n{page_content['body']}"
            return formatted
        
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
    async def _call_flashcard_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a Flashcard tool.
        
        Note: tool_name has the 'flashcard_' prefix removed by parse_tool_name.
        So 'flashcard_create_set' becomes 'create_set'.
        """
        if tool_name == "create_set":
            course_id = arguments.get("course_id")
            course_name = arguments.get("course_name")
            assignment_id = arguments.get("assignment_id")
            assignment_name = arguments.get("assignment_name")
            notes = arguments.get("notes")
            
            if not course_id or not course_name:
                return "Error: 'course_id' and 'course_name' are required."
            
            set_id = FlashcardStorage.create_flashcard_set(
                course_id=course_id,
                course_name=course_name,
                assignment_id=assignment_id,
                assignment_name=assignment_name,
                notes=notes
            )
            
            formatted = "✅ Flashcard set created successfully!\n\n"
            formatted += f"Set ID: {set_id}\n"
            formatted += f"Course: {course_name}\n"
            if assignment_name:
                formatted += f"Assignment: {assignment_name}\n"
            return formatted
        
        elif tool_name == "add_flashcards":
            set_id = arguments.get("set_id")
            flashcards = arguments.get("flashcards", [])
            
            if not set_id or not flashcards:
                return "Error: 'set_id' and 'flashcards' are required."
            
            FlashcardStorage.add_flashcards_to_set(set_id, flashcards)
            return f"✅ Added {len(flashcards)} flashcard(s) to set {set_id}!"
        
        elif tool_name == "generate":
            # This tool generates flashcards using Claude from course context
            course_context = arguments.get("course_context", "")
            student_notes = arguments.get("student_notes")
            assignment_context = arguments.get("assignment_context")
            num_flashcards = arguments.get("num_flashcards", 5)  # Default to 5 for speed
            
            if not course_context:
                return "Error: 'course_context' is required to generate flashcards."
            
            # Limit num_flashcards to prevent timeouts
            if num_flashcards > 10:
                num_flashcards = 10
            
            try:
                flashcards = await generate_flashcards_from_context(
                    course_context=course_context,
                    student_notes=student_notes,
                    assignment_context=assignment_context,
                    num_flashcards=num_flashcards
                )
                
                # Return flashcards in a format Claude can use
                import json
                flashcards_json = json.dumps(flashcards, indent=2)
                return f"✅ Generated {len(flashcards)} flashcards:\n\n{flashcards_json}\n\nUse flashcard_add_flashcards with set_id to add these to a flashcard set."
            except Exception as e:
                return f"Error generating flashcards: {str(e)}"
        
        elif tool_name == "get_set":
            set_id = arguments.get("set_id")
            if not set_id:
                return "Error: 'set_id' is required."
            
            flashcard_set = FlashcardStorage.get_flashcard_set(set_id)
            if not flashcard_set:
                return f"Error: Flashcard set {set_id} not found."
            
            formatted = f"Flashcard Set: {flashcard_set['course_name']}\n\n"
            formatted += f"Flashcards: {len(flashcard_set.get('flashcards', []))}\n"
            if flashcard_set.get('assignment_name'):
                formatted += f"Assignment: {flashcard_set['assignment_name']}\n"
            return formatted
        
        elif tool_name == "get_sets_by_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            
            sets = FlashcardStorage.get_flashcard_sets_by_course(course_id)
            if not sets:
                return f"No flashcard sets found for course {course_id}."
            
            formatted = f"Flashcard Sets ({len(sets)}):\n\n"
            for s in sets:
                formatted += f"• Set ID: {s['id']}\n"
                formatted += f"  Flashcards: {len(s.get('flashcards', []))}\n"
            return formatted
        
        elif tool_name == "get_needing_review":
            set_id = arguments.get("set_id")
            limit = arguments.get("limit")
            
            if not set_id:
                return "Error: 'set_id' is required."
            
            flashcards = FlashcardStorage.get_flashcards_needing_review(set_id, limit)
            if not flashcards:
                return f"No flashcards needing review in set {set_id}."
            
            formatted = f"Flashcards Needing Review ({len(flashcards)}):\n\n"
            for i, card in enumerate(flashcards, 1):
                formatted += f"{i}. Q: {card.get('question', 'N/A')}\n"
                formatted += f"   A: {card.get('answer', 'N/A')}\n\n"
            return formatted
        
        elif tool_name == "record_review":
            set_id = arguments.get("set_id")
            flashcard_id = arguments.get("flashcard_id")
            correct = arguments.get("correct")
            
            if not set_id or not flashcard_id or correct is None:
                return "Error: 'set_id', 'flashcard_id', and 'correct' are required."
            
            FlashcardStorage.record_flashcard_review(set_id, flashcard_id, correct)
            status = "correct" if correct else "incorrect"
            return f"✅ Recorded flashcard review: {status}"
        
        elif tool_name == "get_progress":
            set_id = arguments.get("set_id")
            if not set_id:
                return "Error: 'set_id' is required."
            
            progress = FlashcardStorage.get_flashcard_progress(set_id)
            formatted = f"Flashcard Progress:\n\n"
            formatted += f"Total Reviews: {progress.get('total_reviews', 0)}\n"
            formatted += f"Mastered: {progress.get('mastered_count', 0)}\n"
            formatted += f"Needs Review: {progress.get('needs_review_count', 0)}\n"
            return formatted
        
        elif tool_name == "get_all_sets":
            sets = FlashcardStorage.get_all_sets()
            if not sets:
                return "No flashcard sets found."
            
            formatted = f"All Flashcard Sets ({len(sets)}):\n\n"
            for s in sets:
                formatted += f"• {s['course_name']} - Set ID: {s['id']}\n"
            return formatted
        
        elif tool_name == "delete_set":
            set_id = arguments.get("set_id")
            if not set_id:
                return "Error: 'set_id' is required."
            
            FlashcardStorage.delete_flashcard_set(set_id)
            return f"✅ Flashcard set {set_id} deleted successfully."
        
        else:
            return f"Error: Unknown Flashcard tool '{tool_name}'"
    
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
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_assignment_details",
                    "description": "Get detailed information about a specific assignment including description and rubric",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "assignment_id": {"type": "integer", "description": "The ID of the assignment"}
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_course_modules",
                    "description": "Get all modules and module items for a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_course_files",
                    "description": "Get all files for a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_course_pages",
                    "description": "Get all pages for a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_page_content",
                    "description": "Get the HTML/text content of a Canvas page. Use this to get content from pages for flashcard generation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "page_url": {"type": "string", "description": "The URL slug of the page (e.g., 'syllabus')"}
                        },
                        "required": ["course_id", "page_url"]
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
        
        # Flashcard tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "flashcard_create_set",
                    "description": "Create a new flashcard set for a course, optionally linked to an assignment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "course_name": {"type": "string", "description": "The name of the course"},
                            "assignment_id": {"type": "integer", "description": "Optional: The ID of the assignment"},
                            "assignment_name": {"type": "string", "description": "Optional: The name of the assignment"},
                            "notes": {"type": "string", "description": "Optional: Student notes to include"}
                        },
                        "required": ["course_id", "course_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_add_flashcards",
                    "description": "Add flashcards to an existing flashcard set. Provide flashcards as a list with 'question' and 'answer' fields.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "set_id": {"type": "string", "description": "The ID of the flashcard set"},
                            "flashcards": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string", "description": "The question/front of the flashcard"},
                                        "answer": {"type": "string", "description": "The answer/back of the flashcard"},
                                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
                                    },
                                    "required": ["question", "answer"]
                                },
                                "description": "List of flashcards to add"
                            }
                        },
                        "required": ["set_id", "flashcards"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_get_set",
                    "description": "Get a flashcard set by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "set_id": {"type": "string", "description": "The ID of the flashcard set"}
                        },
                        "required": ["set_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_get_sets_by_course",
                    "description": "Get all flashcard sets for a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_get_needing_review",
                    "description": "Get flashcards that need review (not mastered)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "set_id": {"type": "string", "description": "The ID of the flashcard set"},
                            "limit": {"type": "integer", "description": "Maximum number of flashcards to return"}
                        },
                        "required": ["set_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_record_review",
                    "description": "Record a flashcard review (correct or incorrect)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "set_id": {"type": "string", "description": "The ID of the flashcard set"},
                            "flashcard_id": {"type": "string", "description": "The ID of the flashcard"},
                            "correct": {"type": "boolean", "description": "Whether the student got it correct"}
                        },
                        "required": ["set_id", "flashcard_id", "correct"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_get_progress",
                    "description": "Get progress statistics for a flashcard set",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "set_id": {"type": "string", "description": "The ID of the flashcard set"}
                        },
                        "required": ["set_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "flashcard_get_all_sets",
                    "description": "Get all flashcard sets",
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
                    "name": "flashcard_generate",
                    "description": "Generate flashcards using AI from course context and student notes. Returns a list of flashcards that can be added to a set.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_context": {
                                "type": "string",
                                "description": "Course materials, assignment details, modules, pages, etc. to generate flashcards from"
                            },
                            "student_notes": {
                                "type": "string",
                                "description": "Optional student notes to include in flashcard generation"
                            },
                            "assignment_context": {
                                "type": "string",
                                "description": "Optional assignment-specific context (rubric, requirements, etc.)"
                            },
                            "num_flashcards": {
                                "type": "integer",
                                "description": "Number of flashcards to generate (default: 5, max: 10 for speed)",
                                "default": 5
                            }
                        },
                        "required": ["course_context"]
                    }
                }
            }
        ])
        
        return tools

