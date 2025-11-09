# filename: mcp_server.py

import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException
from datetime import datetime, timedelta, timezone
from typing import List, Any, Optional

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = "https://canvas.instructure.com"

# Global canvas client (initialized lazily)
_canvas_client: Optional[Canvas] = None

def get_canvas_client() -> Canvas:
    """Get or create the Canvas client. Initializes lazily to ensure env vars are available."""
    global _canvas_client
    
    if _canvas_client is not None:
        return _canvas_client
    
    # Try to get API key from environment
    API_KEY = os.getenv("CANVAS_API_KEY")
    
    # If not found, try loading from .env file
    if not API_KEY:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            API_KEY = os.getenv("CANVAS_API_KEY")
        except ImportError:
            pass
    
    # Validate API key
    if not API_KEY:
        raise ValueError(
            "CANVAS_API_KEY not found. Please set it as an environment variable or in a .env file. "
            "When using Claude Desktop, ensure the API key is set in the config file's 'env' section."
        )
    
    if not API_KEY.strip():
        raise ValueError("CANVAS_API_KEY is set but empty. Please provide a valid API key.")
    
    # Initialize and cache the client
    try:
        _canvas_client = Canvas(API_URL, API_KEY.strip())
        return _canvas_client
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Canvas client: {str(e)}. "
            f"Please check that your API_URL ({API_URL}) and API_KEY are correct."
        )

# -----------------------------
# MCP SERVER
# -----------------------------
app = Server("canvas-mcp-server")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def fetch_courses() -> List[dict]:
    """Fetch all courses."""
    canvas = get_canvas_client()
    courses_list = []
    for course in canvas.get_courses():
        courses_list.append({"id": course.id, "name": course.name})
    return courses_list

def fetch_upcoming_assignments(days: int = 7) -> List[dict]:
    """Fetch assignments due in the next X days, with priority scoring."""
    canvas = get_canvas_client()
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days)
    assignments = []
    courses = fetch_courses()

    for course in courses:
        try:
            course_obj = canvas.get_course(course["id"])
            for a in course_obj.get_assignments():
                if a.due_at:
                    due = datetime.fromisoformat(a.due_at.replace("Z", "+00:00"))
                    if now <= due <= end_date:
                        priority_score = 1 / ((due - now).total_seconds() / 3600 + 1)
                        assignments.append({
                            "course": course["name"],
                            "title": a.name,
                            "due_date": a.due_at,
                            "points": a.points_possible,
                            "priority_score": round(priority_score, 2),
                            "url": a.html_url
                        })
        except CanvasException:
            continue

    assignments.sort(key=lambda x: x["priority_score"], reverse=True)
    return assignments

def build_daily_briefing() -> str:
    """Generate a daily briefing summary."""
    assignments = fetch_upcoming_assignments()
    if not assignments:
        return "You have no assignments due in the next 7 days."
    
    briefing = "📅 Your upcoming Canvas assignments:\n\n"
    for a in assignments:
        briefing += f"• {a['course']}: {a['title']} (Due: {a['due_date']}, Points: {a['points']})\n"
    return briefing

def create_assignment(
    course_id: int,
    name: str,
    description: Optional[str] = None,
    due_at: Optional[str] = None,
    points_possible: Optional[float] = None,
    submission_types: Optional[List[str]] = None,
    published: bool = False
) -> dict:
    """
    Create an assignment in a Canvas course.
    
    Args:
        course_id: The ID of the course
        name: Assignment name (required)
        description: Assignment description (optional)
        due_at: Due date in ISO 8601 format, e.g., '2025-12-31T23:59:00Z' (optional)
        points_possible: Maximum points for the assignment (optional)
        submission_types: List of submission types, e.g., ['online_upload', 'online_text_entry'] (optional)
        published: Whether to publish the assignment immediately (default: False)
    
    Returns:
        Dictionary with assignment details
    """
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    # Build assignment parameters
    assignment_params = {
        "name": name,
        "published": published
    }
    
    if description:
        assignment_params["description"] = description
    
    if due_at:
        assignment_params["due_at"] = due_at
    
    if points_possible is not None:
        assignment_params["points_possible"] = points_possible
    
    if submission_types:
        assignment_params["submission_types"] = submission_types
    
    # Create the assignment
    assignment = course.create_assignment(assignment=assignment_params)
    
    return {
        "id": assignment.id,
        "name": assignment.name,
        "course_id": course_id,
        "description": assignment.description,
        "due_at": assignment.due_at,
        "points_possible": assignment.points_possible,
        "submission_types": assignment.submission_types,
        "published": assignment.published,
        "html_url": assignment.html_url
    }

def delete_assignment(course_id: int, assignment_id: int) -> dict:
    """
    Delete an assignment from a Canvas course.
    
    Args:
        course_id: The ID of the course containing the assignment
        assignment_id: The ID of the assignment to delete
    
    Returns:
        Dictionary with deletion confirmation
    """
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    
    # Store assignment info before deletion
    assignment_info = {
        "id": assignment.id,
        "name": assignment.name,
        "course_id": course_id,
        "course_name": course.name
    }
    
    # Delete the assignment
    assignment.delete()
    
    return {
        "success": True,
        "deleted_assignment": assignment_info
    }

def create_course(
    name: str,
    course_code: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    license: Optional[str] = None,
    is_public: bool = False,
    is_public_to_auth_users: bool = False,
    public_syllabus: bool = False,
    public_syllabus_to_auth: bool = False,
    public_description: Optional[str] = None,
    allow_student_wiki_edits: bool = False,
    allow_wiki_comments: bool = False,
    allow_student_forum_attachments: bool = False,
    open_enrollment: bool = False,
    self_enrollment: bool = False,
    restrict_enrollments_to_course_dates: bool = False,
    course_format: Optional[str] = None,
    apply_assignment_group_weights: bool = False,
    account_id: Optional[int] = None
) -> dict:
    """
    Create a new Canvas course.
    
    Args:
        name: Course name (required)
        course_code: Course code (optional)
        start_at: Course start date in ISO 8601 format (optional)
        end_at: Course end date in ISO 8601 format (optional)
        license: Course license (optional)
        is_public: Whether the course is public (default: False)
        is_public_to_auth_users: Whether the course is public to authenticated users (default: False)
        public_syllabus: Whether the syllabus is public (default: False)
        public_syllabus_to_auth: Whether the syllabus is public to authenticated users (default: False)
        public_description: Public course description (optional)
        allow_student_wiki_edits: Whether students can edit wikis (default: False)
        allow_wiki_comments: Whether wiki comments are allowed (default: False)
        allow_student_forum_attachments: Whether students can attach files to forum posts (default: False)
        open_enrollment: Whether enrollment is open (default: False)
        self_enrollment: Whether self-enrollment is enabled (default: False)
        restrict_enrollments_to_course_dates: Whether to restrict enrollments to course dates (default: False)
        course_format: Course format (optional)
        apply_assignment_group_weights: Whether to apply assignment group weights (default: False)
        account_id: Account ID to create the course in (optional, defaults to user's account)
    
    Returns:
        Dictionary with course details
    """
    canvas = get_canvas_client()
    
    # Build course parameters
    course_params = {
        "name": name,
        "is_public": is_public,
        "is_public_to_auth_users": is_public_to_auth_users,
        "public_syllabus": public_syllabus,
        "public_syllabus_to_auth": public_syllabus_to_auth,
        "allow_student_wiki_edits": allow_student_wiki_edits,
        "allow_wiki_comments": allow_wiki_comments,
        "allow_student_forum_attachments": allow_student_forum_attachments,
        "open_enrollment": open_enrollment,
        "self_enrollment": self_enrollment,
        "restrict_enrollments_to_course_dates": restrict_enrollments_to_course_dates,
        "apply_assignment_group_weights": apply_assignment_group_weights
    }
    
    if course_code:
        course_params["course_code"] = course_code
    
    if start_at:
        course_params["start_at"] = start_at
    
    if end_at:
        course_params["end_at"] = end_at
    
    if license:
        course_params["license"] = license
    
    if public_description:
        course_params["public_description"] = public_description
    
    if course_format:
        course_params["course_format"] = course_format
    
    # Create the course
    # If account_id is provided, create in that account, otherwise try to find a suitable account
    if account_id:
        account = canvas.get_account(account_id)
        course = account.create_course(course=course_params)
    else:
        # Try to get accounts that the user has access to
        # Typically, users with course creation permissions can access at least one account
        try:
            accounts = list(canvas.get_accounts())
            if accounts:
                # Use the first account (typically the root account or user's account)
                account = accounts[0]
                course = account.create_course(course=course_params)
            else:
                raise CanvasException(
                    "No accounts found. Please provide an 'account_id' parameter. "
                    "Course creation requires access to an account with appropriate permissions."
                )
        except CanvasException:
            # Re-raise Canvas exceptions (will be handled by caller)
            raise
        except Exception as e:
            # For other exceptions, wrap in a more informative error
            raise CanvasException(
                f"Failed to access accounts for course creation: {str(e)}. "
                "Please provide an 'account_id' parameter or ensure your API key has appropriate permissions."
            )
    
    return {
        "id": course.id,
        "name": course.name,
        "course_code": course.course_code,
        "start_at": course.start_at,
        "end_at": course.end_at,
        "workflow_state": course.workflow_state,
        "html_url": course.html_url
    }

# -----------------------------
# MCP TOOLS
# -----------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="get_courses",
            description="Get all Canvas courses for the authenticated user",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_upcoming_assignments",
            description="Get assignments due in the next N days (default: 7). Assignments are sorted by priority score (higher priority = due sooner).",
            inputSchema={
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
        ),
        Tool(
            name="get_daily_briefing",
            description="Get a formatted daily briefing of upcoming assignments due in the next 7 days",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_assignment",
            description="Create a new assignment in a Canvas course",
            inputSchema={
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
                        "items": {
                            "type": "string"
                        },
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
        ),
        Tool(
            name="delete_assignment",
            description="Delete an assignment from a Canvas course",
            inputSchema={
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
        ),
        Tool(
            name="create_course",
            description="Create a new Canvas course. Note: Requires appropriate permissions (typically admin or account admin).",
            inputSchema={
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
                    "license": {
                        "type": "string",
                        "description": "Course license (optional)"
                    },
                    "is_public": {
                        "type": "boolean",
                        "description": "Whether the course is public (default: false)",
                        "default": False
                    },
                    "is_public_to_auth_users": {
                        "type": "boolean",
                        "description": "Whether the course is public to authenticated users (default: false)",
                        "default": False
                    },
                    "public_syllabus": {
                        "type": "boolean",
                        "description": "Whether the syllabus is public (default: false)",
                        "default": False
                    },
                    "public_syllabus_to_auth": {
                        "type": "boolean",
                        "description": "Whether the syllabus is public to authenticated users (default: false)",
                        "default": False
                    },
                    "public_description": {
                        "type": "string",
                        "description": "Public course description (optional)"
                    },
                    "account_id": {
                        "type": "integer",
                        "description": "Account ID to create the course in (optional, defaults to user's account)"
                    }
                },
                "required": ["name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Optional[dict[str, Any]]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "get_courses":
            courses = fetch_courses()
            if not courses:
                return [TextContent(
                    type="text",
                    text="No courses found for this Canvas account."
                )]
            
            # Format courses as a readable list
            formatted = "Canvas Courses:\n\n"
            for i, course in enumerate(courses, 1):
                formatted += f"{i}. {course['name']} (ID: {course['id']})\n"
            formatted += f"\nTotal: {len(courses)} course(s)"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_upcoming_assignments":
            days = arguments.get("days", 7)
            if not isinstance(days, int) or days < 1:
                days = 7
            
            assignments = fetch_upcoming_assignments(days)
            if not assignments:
                return [TextContent(
                    type="text",
                    text=f"No assignments due in the next {days} day(s)."
                )]
            
            # Format assignments with priority information
            formatted = f"Upcoming Assignments (next {days} days):\n\n"
            for i, a in enumerate(assignments, 1):
                formatted += f"{i}. {a['course']}: {a['title']}\n"
                formatted += f"   Due: {a['due_date']}\n"
                formatted += f"   Points: {a['points']}\n"
                formatted += f"   Priority Score: {a['priority_score']}\n"
                formatted += f"   URL: {a['url']}\n\n"
            formatted += f"Total: {len(assignments)} assignment(s)"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_daily_briefing":
            briefing = build_daily_briefing()
            return [TextContent(type="text", text=briefing)]
        
        elif name == "create_assignment":
            # Validate required parameters
            if "course_id" not in arguments:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required to create an assignment."
                )]
            if "name" not in arguments:
                return [TextContent(
                    type="text",
                    text="Error: 'name' is required to create an assignment."
                )]
            
            course_id = arguments.get("course_id")
            if not isinstance(course_id, int):
                try:
                    course_id = int(course_id)
                except (ValueError, TypeError):
                    return [TextContent(
                        type="text",
                        text=f"Error: 'course_id' must be an integer, got {type(course_id).__name__}"
                    )]
            
            name = arguments.get("name")
            description = arguments.get("description")
            due_at = arguments.get("due_at")
            points_possible = arguments.get("points_possible")
            submission_types = arguments.get("submission_types")
            published = arguments.get("published", False)
            
            # Validate course_id exists and user has access
            try:
                canvas = get_canvas_client()
                course = canvas.get_course(course_id)
                # Try to access course name to verify access
                _ = course.name
            except CanvasException as e:
                error_msg = str(e)
                if "404" in error_msg or "Not Found" in error_msg:
                    return [TextContent(
                        type="text",
                        text=f"Error: Course with ID {course_id} not found. Please verify the course ID is correct."
                    )]
                elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg or "Forbidden" in error_msg:
                    return [TextContent(
                        type="text",
                        text=f"Error: You don't have permission to access course {course_id}. {error_msg}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error accessing course {course_id}: {error_msg}"
                    )]
            
            # Create the assignment
            assignment = create_assignment(
                course_id=course_id,
                name=name,
                description=description,
                due_at=due_at,
                points_possible=points_possible,
                submission_types=submission_types,
                published=published
            )
            
            # Format response
            formatted = "✅ Assignment created successfully!\n\n"
            formatted += f"Name: {assignment['name']}\n"
            formatted += f"Course ID: {assignment['course_id']}\n"
            formatted += f"Assignment ID: {assignment['id']}\n"
            
            if assignment['points_possible']:
                formatted += f"Points: {assignment['points_possible']}\n"
            
            if assignment['due_at']:
                formatted += f"Due Date: {assignment['due_at']}\n"
            
            if assignment['submission_types']:
                formatted += f"Submission Types: {', '.join(assignment['submission_types'])}\n"
            
            formatted += f"Published: {assignment['published']}\n"
            formatted += f"URL: {assignment['html_url']}\n"
            
            if assignment['description']:
                formatted += f"\nDescription: {assignment['description'][:200]}...\n" if len(assignment['description']) > 200 else f"\nDescription: {assignment['description']}\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "delete_assignment":
            # Validate required parameters
            if "course_id" not in arguments:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required to delete an assignment."
                )]
            if "assignment_id" not in arguments:
                return [TextContent(
                    type="text",
                    text="Error: 'assignment_id' is required to delete an assignment."
                )]
            
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            
            # Validate types
            if not isinstance(course_id, int):
                try:
                    course_id = int(course_id)
                except (ValueError, TypeError):
                    return [TextContent(
                        type="text",
                        text=f"Error: 'course_id' must be an integer, got {type(course_id).__name__}"
                    )]
            
            if not isinstance(assignment_id, int):
                try:
                    assignment_id = int(assignment_id)
                except (ValueError, TypeError):
                    return [TextContent(
                        type="text",
                        text=f"Error: 'assignment_id' must be an integer, got {type(assignment_id).__name__}"
                    )]
            
            # Validate course_id and assignment_id exist and user has access
            try:
                canvas = get_canvas_client()
                course = canvas.get_course(course_id)
                assignment = course.get_assignment(assignment_id)
                # Try to access course and assignment names to verify access
                _ = course.name
                _ = assignment.name
            except CanvasException as e:
                error_msg = str(e)
                if "404" in error_msg or "Not Found" in error_msg:
                    return [TextContent(
                        type="text",
                        text=f"Error: Course with ID {course_id} or assignment with ID {assignment_id} not found. Please verify the IDs are correct."
                    )]
                elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg or "Forbidden" in error_msg:
                    return [TextContent(
                        type="text",
                        text=f"Error: You don't have permission to delete assignment {assignment_id} from course {course_id}. {error_msg}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error accessing course {course_id} or assignment {assignment_id}: {error_msg}"
                    )]
            
            # Delete the assignment
            try:
                result = delete_assignment(course_id=course_id, assignment_id=assignment_id)
                
                # Format response
                formatted = "✅ Assignment deleted successfully!\n\n"
                formatted += f"Deleted Assignment: {result['deleted_assignment']['name']}\n"
                formatted += f"Assignment ID: {result['deleted_assignment']['id']}\n"
                formatted += f"Course: {result['deleted_assignment']['course_name']}\n"
                formatted += f"Course ID: {result['deleted_assignment']['course_id']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except CanvasException as e:
                error_msg = str(e)
                return [TextContent(
                    type="text",
                    text=f"Error deleting assignment: {error_msg}"
                )]
        
        elif name == "create_course":
            # Validate required parameters
            if "name" not in arguments:
                return [TextContent(
                    type="text",
                    text="Error: 'name' is required to create a course."
                )]
            
            name = arguments.get("name")
            course_code = arguments.get("course_code")
            start_at = arguments.get("start_at")
            end_at = arguments.get("end_at")
            license = arguments.get("license")
            is_public = arguments.get("is_public", False)
            is_public_to_auth_users = arguments.get("is_public_to_auth_users", False)
            public_syllabus = arguments.get("public_syllabus", False)
            public_syllabus_to_auth = arguments.get("public_syllabus_to_auth", False)
            public_description = arguments.get("public_description")
            account_id = arguments.get("account_id")
            
            # Validate account_id if provided
            if account_id is not None:
                if not isinstance(account_id, int):
                    try:
                        account_id = int(account_id)
                    except (ValueError, TypeError):
                        return [TextContent(
                            type="text",
                            text=f"Error: 'account_id' must be an integer, got {type(account_id).__name__}"
                        )]
            
            # Create the course
            try:
                course = create_course(
                    name=name,
                    course_code=course_code,
                    start_at=start_at,
                    end_at=end_at,
                    license=license,
                    is_public=is_public,
                    is_public_to_auth_users=is_public_to_auth_users,
                    public_syllabus=public_syllabus,
                    public_syllabus_to_auth=public_syllabus_to_auth,
                    public_description=public_description,
                    account_id=account_id
                )
                
                # Format response
                formatted = "✅ Course created successfully!\n\n"
                formatted += f"Name: {course['name']}\n"
                formatted += f"Course ID: {course['id']}\n"
                
                if course['course_code']:
                    formatted += f"Course Code: {course['course_code']}\n"
                
                if course['start_at']:
                    formatted += f"Start Date: {course['start_at']}\n"
                
                if course['end_at']:
                    formatted += f"End Date: {course['end_at']}\n"
                
                formatted += f"Workflow State: {course['workflow_state']}\n"
                formatted += f"URL: {course['html_url']}\n"
                
                return [TextContent(type="text", text=formatted)]
            except CanvasException as e:
                error_msg = str(e)
                if "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg or "Forbidden" in error_msg:
                    return [TextContent(
                        type="text",
                        text=f"Error: You don't have permission to create courses. {error_msg}\n\n"
                             "Note: Course creation typically requires admin or account admin permissions."
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error creating course: {error_msg}"
                    )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except CanvasException as e:
        error_msg = str(e)
        # Check for common authentication errors
        if "401" in error_msg or "Unauthorized" in error_msg or "authentication" in error_msg.lower():
            return [TextContent(
                type="text",
                text=f"Canvas Authentication Error: {error_msg}\n\n"
                     "Possible solutions:\n"
                     "1. Verify your Canvas API key is correct in your Claude Desktop config\n"
                     "2. Check that the API key hasn't expired or been revoked\n"
                     "3. Ensure the API key is properly set in the 'env' section of your config file\n"
                     "4. Try regenerating your API key from Canvas Settings → Approved Integrations"
            )]
        return [TextContent(
            type="text",
            text=f"Canvas API Error: {error_msg}"
        )]
    except ValueError as e:
        # Handle configuration errors (missing API key, etc.)
        return [TextContent(
            type="text",
            text=f"Configuration Error: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Unexpected Error: {str(e)}\n\n"
                 f"Error type: {type(e).__name__}"
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