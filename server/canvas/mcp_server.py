# filename: mcp_server.py
# Canvas MCP Server using FastMCP

from fastmcp import FastMCP
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from functools import wraps
from zoneinfo import ZoneInfo
from .config import API_URL, get_api_key, USER_TIMEZONE

# -----------------------------
# CONFIGURATION
# -----------------------------

# Global canvas client (initialized lazily)
_canvas_client: Optional[Canvas] = None

def get_canvas_client() -> Canvas:
    """Get or create the Canvas client. Initializes lazily to ensure env vars are available."""
    global _canvas_client
    
    if _canvas_client is not None:
        return _canvas_client
    
    # Get API key from config
    API_KEY = get_api_key()
    
    # Initialize and cache the client
    try:
        _canvas_client = Canvas(API_URL, API_KEY)
        return _canvas_client
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Canvas client: {str(e)}. "
            f"Please check that your API_URL ({API_URL}) and API_KEY are correct."
        )

# -----------------------------
# FASTMCP SERVER
# -----------------------------
mcp = FastMCP("canvas-mcp-server")

# -----------------------------
# ERROR HANDLING HELPER
# -----------------------------
def handle_canvas_errors(func):
    """Decorator to handle Canvas API errors consistently."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CanvasException as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg or "authentication" in error_msg.lower():
                return (
                    f"Canvas Authentication Error: {error_msg}\n\n"
                    "Possible solutions:\n"
                    "1. Verify your Canvas API key is correct in your Claude Desktop config\n"
                    "2. Check that the API key hasn't expired or been revoked\n"
                    "3. Ensure the API key is properly set in the 'env' section of your config file\n"
                    "4. Try regenerating your API key from Canvas Settings → Approved Integrations"
                )
            return f"Canvas API Error: {error_msg}"
        except ValueError as e:
            return f"Configuration Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}\n\nError type: {type(e).__name__}"
    return wrapper

# -----------------------------
# TIMEZONE HELPER FUNCTIONS
# -----------------------------

def get_user_timezone():
    """Get the user's configured timezone."""
    return USER_TIMEZONE

def convert_utc_to_local(utc_datetime_str: Optional[str]) -> Optional[datetime]:
    """Convert UTC datetime string from Canvas to local timezone."""
    if not utc_datetime_str:
        return None
    
    try:
        # Parse UTC datetime
        utc_dt = datetime.fromisoformat(utc_datetime_str.replace("Z", "+00:00"))
        
        # Convert to local timezone
        local_tz = get_user_timezone()
        return utc_dt.astimezone(local_tz)
    except (ValueError, AttributeError):
        return None

def format_datetime_local(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime in local timezone for display."""
    if not dt:
        return None
    
    try:
        local_tz = get_user_timezone()
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                # Assume UTC if no timezone info
                dt = dt.replace(tzinfo=timezone.utc)
            local_dt = dt.astimezone(local_tz)
            return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        return str(dt)
    except (ValueError, AttributeError):
        return str(dt) if dt else None

def get_local_now() -> datetime:
    """Get current datetime in user's timezone."""
    local_tz = get_user_timezone()
    return datetime.now(local_tz)

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
    now = get_local_now()
    end_date = now + timedelta(days=days)
    assignments = []
    courses = fetch_courses()

    for course in courses:
        try:
            course_obj = canvas.get_course(course["id"])
            for a in course_obj.get_assignments():
                if a.due_at:
                    # Convert Canvas UTC datetime to local timezone
                    due_utc = datetime.fromisoformat(a.due_at.replace("Z", "+00:00"))
                    due_local = due_utc.astimezone(get_user_timezone())
                    
                    if now <= due_local <= end_date:
                        priority_score = 1 / ((due_local - now).total_seconds() / 3600 + 1)
                        assignments.append({
                            "course": course["name"],
                            "title": a.name,
                            "due_date": format_datetime_local(due_local),
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

def create_assignment_helper(
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

def delete_assignment_helper(course_id: int, assignment_id: int) -> dict:
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

def create_course_helper(
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
# MCP TOOLS (FastMCP Decorators)
# -----------------------------
@handle_canvas_errors
@mcp.tool()
def get_courses() -> str:
    """Get all Canvas courses for the authenticated user"""
    courses = fetch_courses()
    if not courses:
        return "No courses found for this Canvas account."
    
    # Format courses as a readable list
    formatted = "Canvas Courses:\n\n"
    for i, course in enumerate(courses, 1):
        formatted += f"{i}. {course['name']} (ID: {course['id']})\n"
    formatted += f"\nTotal: {len(courses)} course(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_upcoming_assignments(days: int = 7) -> str:
    """Get assignments due in the next N days (default: 7). Assignments are sorted by priority score (higher priority = due sooner).
    
    Args:
        days: Number of days to look ahead for assignments (default: 7)
    """
    if days < 1:
        days = 7
    
    assignments = fetch_upcoming_assignments(days)
    if not assignments:
        return f"No assignments due in the next {days} day(s)."
    
    # Format assignments with priority information
    formatted = f"Upcoming Assignments (next {days} days):\n\n"
    for i, a in enumerate(assignments, 1):
        formatted += f"{i}. {a['course']}: {a['title']}\n"
        formatted += f"   Due: {a['due_date']}\n"
        formatted += f"   Points: {a['points']}\n"
        formatted += f"   Priority Score: {a['priority_score']}\n"
        formatted += f"   URL: {a['url']}\n\n"
    formatted += f"Total: {len(assignments)} assignment(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_daily_briefing() -> str:
    """Get a formatted daily briefing of upcoming assignments due in the next 7 days"""
    return build_daily_briefing()

@handle_canvas_errors
@mcp.tool()
def create_assignment(
    course_id: int,
    name: str,
    description: Optional[str] = None,
    due_at: Optional[str] = None,
    points_possible: Optional[float] = None,
    submission_types: Optional[List[str]] = None,
    published: bool = False
) -> str:
    """Create a new assignment in a Canvas course.
    
    Args:
        course_id: The ID of the course where the assignment will be created
        name: The name/title of the assignment
        description: Assignment description (supports HTML)
        due_at: Due date in ISO 8601 format (e.g., '2025-12-31T23:59:00Z')
        points_possible: Maximum points for the assignment
        submission_types: List of submission types. Common options: 'online_upload', 'online_text_entry', 'online_url', 'on_paper', 'none'
        published: Whether to publish the assignment immediately (default: false)
    """
    # Validate course_id exists and user has access
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        # Try to access course name to verify access
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            return f"Error: Course with ID {course_id} not found. Please verify the course ID is correct."
        elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg or "Forbidden" in error_msg:
            return f"Error: You don't have permission to access course {course_id}. {error_msg}"
        else:
            return f"Error accessing course {course_id}: {error_msg}"
    
    # Create the assignment
    assignment = create_assignment_helper(
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
        due_local = convert_utc_to_local(assignment['due_at'])
        formatted += f"Due Date: {format_datetime_local(due_local)}\n"
    
    if assignment['submission_types']:
        formatted += f"Submission Types: {', '.join(assignment['submission_types'])}\n"
    
    formatted += f"Published: {assignment['published']}\n"
    formatted += f"URL: {assignment['html_url']}\n"
    
    if assignment['description']:
        desc_preview = assignment['description'][:200] + "..." if len(assignment['description']) > 200 else assignment['description']
        formatted += f"\nDescription: {desc_preview}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_assignment(course_id: int, assignment_id: int) -> str:
    """Delete an assignment from a Canvas course.
    
    Args:
        course_id: The ID of the course containing the assignment
        assignment_id: The ID of the assignment to delete
    """
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
            return f"Error: Course with ID {course_id} or assignment with ID {assignment_id} not found. Please verify the IDs are correct."
        elif "401" in error_msg or "403" in error_msg or "Unauthorized" in error_msg or "Forbidden" in error_msg:
            return f"Error: You don't have permission to delete assignment {assignment_id} from course {course_id}. {error_msg}"
        else:
            return f"Error accessing course {course_id} or assignment {assignment_id}: {error_msg}"
    
    # Delete the assignment
    result = delete_assignment_helper(course_id=course_id, assignment_id=assignment_id)
    
    # Format response
    formatted = "✅ Assignment deleted successfully!\n\n"
    formatted += f"Deleted Assignment: {result['deleted_assignment']['name']}\n"
    formatted += f"Assignment ID: {result['deleted_assignment']['id']}\n"
    formatted += f"Course: {result['deleted_assignment']['course_name']}\n"
    formatted += f"Course ID: {result['deleted_assignment']['course_id']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
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
    account_id: Optional[int] = None
) -> str:
    """Create a new Canvas course. Note: Requires appropriate permissions (typically admin or account admin).
    
    Args:
        name: Course name (required)
        course_code: Course code (optional)
        start_at: Course start date in ISO 8601 format (e.g., '2025-01-01T00:00:00Z')
        end_at: Course end date in ISO 8601 format (e.g., '2025-12-31T23:59:59Z')
        license: Course license (optional)
        is_public: Whether the course is public (default: false)
        is_public_to_auth_users: Whether the course is public to authenticated users (default: false)
        public_syllabus: Whether the syllabus is public (default: false)
        public_syllabus_to_auth: Whether the syllabus is public to authenticated users (default: false)
        public_description: Public course description (optional)
        account_id: Account ID to create the course in (optional, defaults to user's account)
    """
    # Create the course
    course = create_course_helper(
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
        start_local = convert_utc_to_local(course['start_at'])
        formatted += f"Start Date: {format_datetime_local(start_local)}\n"
    
    if course['end_at']:
        end_local = convert_utc_to_local(course['end_at'])
        formatted += f"End Date: {format_datetime_local(end_local)}\n"
    
    formatted += f"Workflow State: {course['workflow_state']}\n"
    formatted += f"URL: {course['html_url']}\n"
    
    return formatted

# ============================================================================
# PHASE 1: CORE ACADEMIC RESOURCES
# ============================================================================

# -----------------------------
# SUBMISSIONS - Helper Functions
# -----------------------------

def create_submission_helper(
    course_id: int,
    assignment_id: int,
    submission_type: str,
    body: Optional[str] = None,
    url: Optional[str] = None,
    file_ids: Optional[List[int]] = None,
    comment: Optional[str] = None
) -> dict:
    """Create a submission for an assignment."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    
    submission_params = {
        "submission_type": submission_type
    }
    
    if body:
        submission_params["body"] = body
    if url:
        submission_params["url"] = url
    if file_ids:
        submission_params["file_ids"] = file_ids
    if comment:
        submission_params["comment"] = comment
    
    submission = assignment.submit(submission=submission_params)
    
    return {
        "id": submission.id,
        "assignment_id": assignment_id,
        "user_id": submission.user_id,
        "submission_type": submission.submission_type,
        "workflow_state": submission.workflow_state,
        "submitted_at": submission.submitted_at,
        "score": submission.score,
        "grade": submission.grade
    }

def fetch_submission(course_id: int, assignment_id: int, user_id: int) -> dict:
    """Fetch a specific submission."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submission = assignment.get_submission(user_id)
    
    return {
        "id": submission.id,
        "assignment_id": assignment_id,
        "user_id": submission.user_id,
        "submission_type": submission.submission_type,
        "workflow_state": submission.workflow_state,
        "submitted_at": submission.submitted_at,
        "score": submission.score,
        "grade": submission.grade,
        "body": getattr(submission, 'body', None),
        "url": getattr(submission, 'url', None),
        "preview_url": getattr(submission, 'preview_url', None),
        "attachments": [{"id": a.id, "filename": a.filename, "url": a.url} for a in getattr(submission, 'attachments', [])]
    }

def fetch_submissions(course_id: int, assignment_id: int) -> List[dict]:
    """Fetch all submissions for an assignment."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    
    submissions = []
    for submission in assignment.get_submissions():
        submissions.append({
            "id": submission.id,
            "user_id": submission.user_id,
            "submission_type": submission.submission_type,
            "workflow_state": submission.workflow_state,
            "submitted_at": submission.submitted_at,
            "score": submission.score,
            "grade": submission.grade
        })
    
    return submissions

def update_submission_helper(
    course_id: int,
    assignment_id: int,
    user_id: int,
    grade: Optional[str] = None,
    comment: Optional[str] = None,
    excused: Optional[bool] = None,
    submission_type: Optional[str] = None,
    body: Optional[str] = None,
    url: Optional[str] = None
) -> dict:
    """Update a submission (for grading or resubmission)."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submission = assignment.get_submission(user_id)
    
    submission_params = {}
    if grade is not None:
        submission_params["grade_data[posted_grade]"] = grade
    if comment:
        submission_params["comment[text_comment]"] = comment
    if excused is not None:
        submission_params["submission[excuse]"] = excused
    if submission_type:
        submission_params["submission[submission_type]"] = submission_type
    if body:
        submission_params["submission[body]"] = body
    if url:
        submission_params["submission[url]"] = url
    
    updated_submission = submission.edit(submission=submission_params)
    
    return {
        "id": updated_submission.id,
        "assignment_id": assignment_id,
        "user_id": updated_submission.user_id,
        "workflow_state": updated_submission.workflow_state,
        "score": updated_submission.score,
        "grade": updated_submission.grade
    }

def delete_submission_helper(course_id: int, assignment_id: int, user_id: int) -> dict:
    """Delete a submission."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    submission = assignment.get_submission(user_id)
    
    submission_info = {
        "id": submission.id,
        "user_id": submission.user_id,
        "assignment_id": assignment_id
    }
    
    submission.delete()
    
    return {
        "success": True,
        "deleted_submission": submission_info
    }

# -----------------------------
# SUBMISSIONS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_submission(
    course_id: int,
    assignment_id: int,
    submission_type: str,
    body: Optional[str] = None,
    url: Optional[str] = None,
    file_ids: Optional[List[int]] = None,
    comment: Optional[str] = None
) -> str:
    """Create a submission for an assignment.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
        submission_type: Type of submission ('online_text_entry', 'online_upload', 'online_url', 'media_recording', 'student_annotation')
        body: Text content for text submissions
        url: URL for URL submissions
        file_ids: List of file IDs for file uploads
        comment: Comment to include with submission
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        _ = assignment.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or assignment not found. {error_msg}"
        return f"Error: {error_msg}"
    
    submission = create_submission_helper(
        course_id=course_id,
        assignment_id=assignment_id,
        submission_type=submission_type,
        body=body,
        url=url,
        file_ids=file_ids,
        comment=comment
    )
    
    formatted = "✅ Submission created successfully!\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Assignment ID: {submission['assignment_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    formatted += f"Type: {submission['submission_type']}\n"
    formatted += f"State: {submission['workflow_state']}\n"
    if submission.get('submitted_at'):
        submitted_local = convert_utc_to_local(submission['submitted_at'])
        formatted += f"Submitted At: {format_datetime_local(submitted_local)}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_submission(course_id: int, assignment_id: int, user_id: int) -> str:
    """Get a specific submission for an assignment.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
        user_id: The ID of the user whose submission to retrieve
    """
    submission = fetch_submission(course_id, assignment_id, user_id)
    
    formatted = f"Submission Details:\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Assignment ID: {submission['assignment_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    formatted += f"Type: {submission['submission_type']}\n"
    formatted += f"State: {submission['workflow_state']}\n"
    
    if submission.get('submitted_at'):
        submitted_local = convert_utc_to_local(submission['submitted_at'])
        formatted += f"Submitted At: {format_datetime_local(submitted_local)}\n"
    
    if submission.get('score') is not None:
        formatted += f"Score: {submission['score']}\n"
    
    if submission.get('grade'):
        formatted += f"Grade: {submission['grade']}\n"
    
    if submission.get('body'):
        formatted += f"\nBody: {submission['body'][:200]}...\n" if len(submission.get('body', '')) > 200 else f"\nBody: {submission['body']}\n"
    
    if submission.get('url'):
        formatted += f"URL: {submission['url']}\n"
    
    if submission.get('attachments'):
        formatted += f"\nAttachments: {len(submission['attachments'])} file(s)\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_submissions(course_id: int, assignment_id: int) -> str:
    """List all submissions for an assignment.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
    """
    submissions = fetch_submissions(course_id, assignment_id)
    
    if not submissions:
        return f"No submissions found for assignment {assignment_id}."
    
    formatted = f"Submissions for Assignment {assignment_id}:\n\n"
    for i, sub in enumerate(submissions, 1):
        formatted += f"{i}. User ID: {sub['user_id']}\n"
        formatted += f"   Submission ID: {sub['id']}\n"
        formatted += f"   Type: {sub['submission_type']}\n"
        formatted += f"   State: {sub['workflow_state']}\n"
        if sub.get('submitted_at'):
            submitted_local = convert_utc_to_local(sub['submitted_at'])
            formatted += f"   Submitted: {format_datetime_local(submitted_local)}\n"
        if sub.get('grade'):
            formatted += f"   Grade: {sub['grade']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(submissions)} submission(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_submission(
    course_id: int,
    assignment_id: int,
    user_id: int,
    grade: Optional[str] = None,
    comment: Optional[str] = None,
    excused: Optional[bool] = None
) -> str:
    """Update a submission (grade, comment, or resubmit).
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
        user_id: The ID of the user whose submission to update
        grade: Grade to assign (e.g., 'A', '95', 'pass')
        comment: Comment/feedback to add
        excused: Whether to excuse the submission
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        _ = assignment.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, assignment, or submission not found. {error_msg}"
        return f"Error: {error_msg}"
    
    submission = update_submission_helper(
        course_id=course_id,
        assignment_id=assignment_id,
        user_id=user_id,
        grade=grade,
        comment=comment,
        excused=excused
    )
    
    formatted = "✅ Submission updated successfully!\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Assignment ID: {submission['assignment_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    formatted += f"State: {submission['workflow_state']}\n"
    
    if submission.get('grade'):
        formatted += f"Grade: {submission['grade']}\n"
    
    if submission.get('score') is not None:
        formatted += f"Score: {submission['score']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_submission(course_id: int, assignment_id: int, user_id: int) -> str:
    """Delete a submission.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
        user_id: The ID of the user whose submission to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        _ = assignment.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, assignment, or submission not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_submission_helper(course_id, assignment_id, user_id)
    
    formatted = "✅ Submission deleted successfully!\n\n"
    formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
    formatted += f"Assignment ID: {result['deleted_submission']['assignment_id']}\n"
    formatted += f"User ID: {result['deleted_submission']['user_id']}\n"
    
    return formatted

# -----------------------------
# QUIZZES - Helper Functions
# -----------------------------

def create_quiz_helper(
    course_id: int,
    title: str,
    description: Optional[str] = None,
    quiz_type: str = "assignment",
    time_limit: Optional[int] = None,
    allowed_attempts: Optional[int] = None,
    scoring_policy: Optional[str] = None,
    shuffle_answers: bool = False,
    show_correct_answers: bool = True,
    show_correct_answers_last_attempt: bool = False,
    show_correct_answers_at: Optional[str] = None,
    hide_correct_answers_at: Optional[str] = None,
    one_question_at_a_time: bool = False,
    cant_go_back: bool = False,
    access_code: Optional[str] = None,
    ip_filter: Optional[str] = None,
    due_at: Optional[str] = None,
    lock_at: Optional[str] = None,
    unlock_at: Optional[str] = None,
    published: bool = False,
    one_time_results: bool = False,
    only_visible_to_overrides: bool = False
) -> dict:
    """Create a quiz in a Canvas course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    quiz_params = {
        "title": title,
        "quiz_type": quiz_type,
        "shuffle_answers": shuffle_answers,
        "show_correct_answers": show_correct_answers,
        "show_correct_answers_last_attempt": show_correct_answers_last_attempt,
        "one_question_at_a_time": one_question_at_a_time,
        "cant_go_back": cant_go_back,
        "published": published,
        "one_time_results": one_time_results,
        "only_visible_to_overrides": only_visible_to_overrides
    }
    
    if description:
        quiz_params["description"] = description
    if time_limit is not None:
        quiz_params["time_limit"] = time_limit
    if allowed_attempts is not None:
        quiz_params["allowed_attempts"] = allowed_attempts
    if scoring_policy:
        quiz_params["scoring_policy"] = scoring_policy
    if show_correct_answers_at:
        quiz_params["show_correct_answers_at"] = show_correct_answers_at
    if hide_correct_answers_at:
        quiz_params["hide_correct_answers_at"] = hide_correct_answers_at
    if access_code:
        quiz_params["access_code"] = access_code
    if ip_filter:
        quiz_params["ip_filter"] = ip_filter
    if due_at:
        quiz_params["due_at"] = due_at
    if lock_at:
        quiz_params["lock_at"] = lock_at
    if unlock_at:
        quiz_params["unlock_at"] = unlock_at
    
    quiz = course.create_quiz(quiz=quiz_params)
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "course_id": course_id,
        "description": quiz.description,
        "quiz_type": quiz.quiz_type,
        "time_limit": quiz.time_limit,
        "allowed_attempts": quiz.allowed_attempts,
        "scoring_policy": quiz.scoring_policy,
        "due_at": quiz.due_at,
        "lock_at": quiz.lock_at,
        "unlock_at": quiz.unlock_at,
        "published": quiz.published,
        "html_url": quiz.html_url
    }

def fetch_quiz(course_id: int, quiz_id: int) -> dict:
    """Fetch a specific quiz."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "course_id": course_id,
        "description": quiz.description,
        "quiz_type": quiz.quiz_type,
        "time_limit": quiz.time_limit,
        "allowed_attempts": quiz.allowed_attempts,
        "scoring_policy": quiz.scoring_policy,
        "shuffle_answers": quiz.shuffle_answers,
        "show_correct_answers": quiz.show_correct_answers,
        "due_at": quiz.due_at,
        "lock_at": quiz.lock_at,
        "unlock_at": quiz.unlock_at,
        "published": quiz.published,
        "html_url": quiz.html_url,
        "question_count": getattr(quiz, 'question_count', None)
    }

def fetch_quizzes(course_id: int) -> List[dict]:
    """Fetch all quizzes for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    quizzes = []
    for quiz in course.get_quizzes():
        quizzes.append({
            "id": quiz.id,
            "title": quiz.title,
            "quiz_type": quiz.quiz_type,
            "due_at": quiz.due_at,
            "published": quiz.published,
            "question_count": getattr(quiz, 'question_count', None)
        })
    
    return quizzes

def fetch_quiz_questions(course_id: int, quiz_id: int) -> List[dict]:
    """Fetch questions for a quiz."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    questions = []
    for question in quiz.get_questions():
        questions.append({
            "id": question.id,
            "question_name": getattr(question, 'question_name', None),
            "question_type": question.question_type,
            "question_text": getattr(question, 'question_text', None),
            "points_possible": getattr(question, 'points_possible', None),
            "answers": [{"id": a.get('id'), "text": a.get('text'), "weight": a.get('weight')} for a in getattr(question, 'answers', [])]
        })
    
    return questions

def update_quiz_helper(
    course_id: int,
    quiz_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    quiz_type: Optional[str] = None,
    time_limit: Optional[int] = None,
    allowed_attempts: Optional[int] = None,
    scoring_policy: Optional[str] = None,
    shuffle_answers: Optional[bool] = None,
    show_correct_answers: Optional[bool] = None,
    due_at: Optional[str] = None,
    lock_at: Optional[str] = None,
    unlock_at: Optional[str] = None,
    published: Optional[bool] = None
) -> dict:
    """Update a quiz."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    quiz_params = {}
    if title:
        quiz_params["title"] = title
    if description is not None:
        quiz_params["description"] = description
    if quiz_type:
        quiz_params["quiz_type"] = quiz_type
    if time_limit is not None:
        quiz_params["time_limit"] = time_limit
    if allowed_attempts is not None:
        quiz_params["allowed_attempts"] = allowed_attempts
    if scoring_policy:
        quiz_params["scoring_policy"] = scoring_policy
    if shuffle_answers is not None:
        quiz_params["shuffle_answers"] = shuffle_answers
    if show_correct_answers is not None:
        quiz_params["show_correct_answers"] = show_correct_answers
    if due_at:
        quiz_params["due_at"] = due_at
    if lock_at:
        quiz_params["lock_at"] = lock_at
    if unlock_at:
        quiz_params["unlock_at"] = unlock_at
    if published is not None:
        quiz_params["published"] = published
    
    updated_quiz = quiz.edit(quiz=quiz_params)
    
    return {
        "id": updated_quiz.id,
        "title": updated_quiz.title,
        "course_id": course_id,
        "quiz_type": updated_quiz.quiz_type,
        "published": updated_quiz.published,
        "html_url": updated_quiz.html_url
    }

def delete_quiz_helper(course_id: int, quiz_id: int) -> dict:
    """Delete a quiz."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    quiz_info = {
        "id": quiz.id,
        "title": quiz.title,
        "course_id": course_id
    }
    
    quiz.delete()
    
    return {
        "success": True,
        "deleted_quiz": quiz_info
    }

# -----------------------------
# QUIZZES - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_quiz(
    course_id: int,
    title: str,
    description: Optional[str] = None,
    quiz_type: str = "assignment",
    time_limit: Optional[int] = None,
    allowed_attempts: Optional[int] = None,
    due_at: Optional[str] = None,
    published: bool = False
) -> str:
    """Create a new quiz in a Canvas course.
    
    Args:
        course_id: The ID of the course
        title: Quiz title (required)
        description: Quiz description
        quiz_type: Type of quiz ('practice_quiz', 'assignment', 'graded_survey', 'survey')
        time_limit: Time limit in minutes
        allowed_attempts: Number of allowed attempts
        due_at: Due date in ISO 8601 format
        published: Whether to publish immediately
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    quiz = create_quiz_helper(
        course_id=course_id,
        title=title,
        description=description,
        quiz_type=quiz_type,
        time_limit=time_limit,
        allowed_attempts=allowed_attempts,
        due_at=due_at,
        published=published
    )
    
    formatted = "✅ Quiz created successfully!\n\n"
    formatted += f"Title: {quiz['title']}\n"
    formatted += f"Quiz ID: {quiz['id']}\n"
    formatted += f"Course ID: {quiz['course_id']}\n"
    formatted += f"Type: {quiz['quiz_type']}\n"
    formatted += f"Published: {quiz['published']}\n"
    formatted += f"URL: {quiz['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_quiz(course_id: int, quiz_id: int) -> str:
    """Get a specific quiz.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
    """
    quiz = fetch_quiz(course_id, quiz_id)
    
    formatted = f"Quiz Details:\n\n"
    formatted += f"Title: {quiz['title']}\n"
    formatted += f"Quiz ID: {quiz['id']}\n"
    formatted += f"Course ID: {quiz['course_id']}\n"
    formatted += f"Type: {quiz['quiz_type']}\n"
    
    if quiz.get('description'):
        formatted += f"\nDescription: {quiz['description'][:200]}...\n" if len(quiz.get('description', '')) > 200 else f"\nDescription: {quiz['description']}\n"
    
    if quiz.get('time_limit'):
        formatted += f"Time Limit: {quiz['time_limit']} minutes\n"
    
    if quiz.get('allowed_attempts'):
        formatted += f"Allowed Attempts: {quiz['allowed_attempts']}\n"
    
    if quiz.get('due_at'):
        due_local = convert_utc_to_local(quiz['due_at'])
        formatted += f"Due Date: {format_datetime_local(due_local)}\n"
    
    formatted += f"Published: {quiz['published']}\n"
    formatted += f"URL: {quiz['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_quizzes(course_id: int) -> str:
    """List all quizzes for a course.
    
    Args:
        course_id: The ID of the course
    """
    quizzes = fetch_quizzes(course_id)
    
    if not quizzes:
        return f"No quizzes found for course {course_id}."
    
    formatted = f"Quizzes for Course {course_id}:\n\n"
    for i, quiz in enumerate(quizzes, 1):
        formatted += f"{i}. {quiz['title']}\n"
        formatted += f"   Quiz ID: {quiz['id']}\n"
        formatted += f"   Type: {quiz['quiz_type']}\n"
        if quiz.get('due_at'):
            due_local = convert_utc_to_local(quiz['due_at'])
            formatted += f"   Due: {format_datetime_local(due_local)}\n"
        formatted += f"   Published: {quiz['published']}\n\n"
    
    formatted += f"Total: {len(quizzes)} quiz(zes)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_quiz_questions(course_id: int, quiz_id: int) -> str:
    """Get all questions for a quiz.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
    """
    questions = fetch_quiz_questions(course_id, quiz_id)
    
    if not questions:
        return f"No questions found for quiz {quiz_id}."
    
    formatted = f"Questions for Quiz {quiz_id}:\n\n"
    for i, q in enumerate(questions, 1):
        formatted += f"{i}. {q.get('question_name', 'Question ' + str(i))}\n"
        formatted += f"   Type: {q['question_type']}\n"
        if q.get('points_possible'):
            formatted += f"   Points: {q['points_possible']}\n"
        if q.get('question_text'):
            text = q['question_text'][:100] + "..." if len(q.get('question_text', '')) > 100 else q['question_text']
            formatted += f"   Text: {text}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(questions)} question(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_quiz(
    course_id: int,
    quiz_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    time_limit: Optional[int] = None,
    allowed_attempts: Optional[int] = None,
    due_at: Optional[str] = None,
    published: Optional[bool] = None
) -> str:
    """Update a quiz.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
        title: New quiz title
        description: New quiz description
        time_limit: New time limit in minutes
        allowed_attempts: New number of allowed attempts
        due_at: New due date in ISO 8601 format
        published: Whether to publish/unpublish
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        quiz = course.get_quiz(quiz_id)
        _ = quiz.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or quiz not found. {error_msg}"
        return f"Error: {error_msg}"
    
    quiz = update_quiz_helper(
        course_id=course_id,
        quiz_id=quiz_id,
        title=title,
        description=description,
        time_limit=time_limit,
        allowed_attempts=allowed_attempts,
        due_at=due_at,
        published=published
    )
    
    formatted = "✅ Quiz updated successfully!\n\n"
    formatted += f"Quiz ID: {quiz['id']}\n"
    formatted += f"Title: {quiz['title']}\n"
    formatted += f"Published: {quiz['published']}\n"
    formatted += f"URL: {quiz['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_quiz(course_id: int, quiz_id: int) -> str:
    """Delete a quiz.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        quiz = course.get_quiz(quiz_id)
        _ = quiz.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or quiz not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_quiz_helper(course_id, quiz_id)
    
    formatted = "✅ Quiz deleted successfully!\n\n"
    formatted += f"Deleted Quiz: {result['deleted_quiz']['title']}\n"
    formatted += f"Quiz ID: {result['deleted_quiz']['id']}\n"
    formatted += f"Course ID: {result['deleted_quiz']['course_id']}\n"
    
    return formatted

# -----------------------------
# QUIZ SUBMISSIONS - Helper Functions
# -----------------------------

def create_quiz_submission_helper(
    course_id: int,
    quiz_id: int,
    access_code: Optional[str] = None
) -> dict:
    """Create a quiz submission (start quiz attempt)."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    submission_params = {}
    if access_code:
        submission_params["access_code"] = access_code
    
    submission = quiz.create_submission(quiz_submission=submission_params)
    
    return {
        "id": submission.id,
        "quiz_id": quiz_id,
        "user_id": submission.user_id,
        "attempt": submission.attempt,
        "started_at": submission.started_at,
        "finished_at": submission.finished_at,
        "workflow_state": submission.workflow_state,
        "validation_token": getattr(submission, 'validation_token', None)
    }

def fetch_quiz_submission(course_id: int, quiz_id: int, submission_id: int) -> dict:
    """Fetch a specific quiz submission."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    submission = quiz.get_submission(submission_id)
    
    return {
        "id": submission.id,
        "quiz_id": quiz_id,
        "user_id": submission.user_id,
        "attempt": submission.attempt,
        "started_at": submission.started_at,
        "finished_at": submission.finished_at,
        "workflow_state": submission.workflow_state,
        "score": submission.score,
        "kept_score": getattr(submission, 'kept_score', None),
        "fudge_points": getattr(submission, 'fudge_points', None),
        "quiz_points_possible": getattr(submission, 'quiz_points_possible', None)
    }

def fetch_quiz_submissions(course_id: int, quiz_id: int) -> List[dict]:
    """Fetch all quiz submissions."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    
    submissions = []
    for submission in quiz.get_submissions():
        submissions.append({
            "id": submission.id,
            "user_id": submission.user_id,
            "attempt": submission.attempt,
            "started_at": submission.started_at,
            "finished_at": submission.finished_at,
            "workflow_state": submission.workflow_state,
            "score": submission.score
        })
    
    return submissions

def update_quiz_submission_helper(
    course_id: int,
    quiz_id: int,
    submission_id: int,
    fudge_points: Optional[float] = None,
    question_scores: Optional[Dict[int, float]] = None,
    comment: Optional[str] = None
) -> dict:
    """Update quiz submission score."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    submission = quiz.get_submission(submission_id)
    
    params = {}
    if fudge_points is not None:
        params["fudge_points"] = fudge_points
    if question_scores:
        for q_id, score in question_scores.items():
            params[f"questions[{q_id}][score]"] = score
    if comment:
        params["comment"] = comment
    
    updated_submission = submission.update_score_and_comments(**params)
    
    return {
        "id": updated_submission.id,
        "quiz_id": quiz_id,
        "user_id": updated_submission.user_id,
        "score": updated_submission.score,
        "fudge_points": getattr(updated_submission, 'fudge_points', None)
    }

def delete_quiz_submission_helper(course_id: int, quiz_id: int, submission_id: int) -> dict:
    """Delete a quiz submission."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    quiz = course.get_quiz(quiz_id)
    submission = quiz.get_submission(submission_id)
    
    submission_info = {
        "id": submission.id,
        "user_id": submission.user_id,
        "quiz_id": quiz_id,
        "attempt": submission.attempt
    }
    
    submission.delete()
    
    return {
        "success": True,
        "deleted_submission": submission_info
    }

# -----------------------------
# QUIZ SUBMISSIONS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_quiz_submission(
    course_id: int,
    quiz_id: int,
    access_code: Optional[str] = None
) -> str:
    """Create a quiz submission (start quiz attempt).
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
        access_code: Access code if required
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        quiz = course.get_quiz(quiz_id)
        _ = quiz.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or quiz not found. {error_msg}"
        return f"Error: {error_msg}"
    
    submission = create_quiz_submission_helper(course_id, quiz_id, access_code)
    
    formatted = "✅ Quiz submission created successfully!\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Quiz ID: {submission['quiz_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    formatted += f"Attempt: {submission['attempt']}\n"
    formatted += f"State: {submission['workflow_state']}\n"
    if submission.get('started_at'):
        started_local = convert_utc_to_local(submission['started_at'])
        formatted += f"Started At: {format_datetime_local(started_local)}\n"
    if submission.get('validation_token'):
        formatted += f"Validation Token: {submission['validation_token']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_quiz_submission(course_id: int, quiz_id: int, submission_id: int) -> str:
    """Get a specific quiz submission.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
        submission_id: The ID of the submission
    """
    submission = fetch_quiz_submission(course_id, quiz_id, submission_id)
    
    formatted = f"Quiz Submission Details:\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Quiz ID: {submission['quiz_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    formatted += f"Attempt: {submission['attempt']}\n"
    formatted += f"State: {submission['workflow_state']}\n"
    
    if submission.get('started_at'):
        started_local = convert_utc_to_local(submission['started_at'])
        formatted += f"Started At: {format_datetime_local(started_local)}\n"
    
    if submission.get('finished_at'):
        finished_local = convert_utc_to_local(submission['finished_at'])
        formatted += f"Finished At: {format_datetime_local(finished_local)}\n"
    
    if submission.get('score') is not None:
        formatted += f"Score: {submission['score']}\n"
    
    if submission.get('fudge_points'):
        formatted += f"Fudge Points: {submission['fudge_points']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_quiz_submissions(course_id: int, quiz_id: int) -> str:
    """List all quiz submissions.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
    """
    submissions = fetch_quiz_submissions(course_id, quiz_id)
    
    if not submissions:
        return f"No submissions found for quiz {quiz_id}."
    
    formatted = f"Quiz Submissions for Quiz {quiz_id}:\n\n"
    for i, sub in enumerate(submissions, 1):
        formatted += f"{i}. User ID: {sub['user_id']}\n"
        formatted += f"   Submission ID: {sub['id']}\n"
        formatted += f"   Attempt: {sub['attempt']}\n"
        formatted += f"   State: {sub['workflow_state']}\n"
        if sub.get('started_at'):
            started_local = convert_utc_to_local(sub['started_at'])
            formatted += f"   Started: {format_datetime_local(started_local)}\n"
        if sub.get('score') is not None:
            formatted += f"   Score: {sub['score']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(submissions)} submission(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_quiz_submission_score(
    course_id: int,
    quiz_id: int,
    submission_id: int,
    fudge_points: Optional[float] = None,
    question_scores: Optional[Dict[int, float]] = None,
    comment: Optional[str] = None
) -> str:
    """Update quiz submission score (manual grading).
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
        submission_id: The ID of the submission
        fudge_points: Points to add/subtract from score
        question_scores: Dictionary mapping question IDs to scores
        comment: Comment to add
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        quiz = course.get_quiz(quiz_id)
        _ = quiz.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, quiz, or submission not found. {error_msg}"
        return f"Error: {error_msg}"
    
    submission = update_quiz_submission_helper(
        course_id, quiz_id, submission_id, fudge_points, question_scores, comment
    )
    
    formatted = "✅ Quiz submission updated successfully!\n\n"
    formatted += f"Submission ID: {submission['id']}\n"
    formatted += f"Quiz ID: {submission['quiz_id']}\n"
    formatted += f"User ID: {submission['user_id']}\n"
    if submission.get('score') is not None:
        formatted += f"Score: {submission['score']}\n"
    if submission.get('fudge_points'):
        formatted += f"Fudge Points: {submission['fudge_points']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_quiz_submission(course_id: int, quiz_id: int, submission_id: int) -> str:
    """Delete a quiz submission.
    
    Args:
        course_id: The ID of the course
        quiz_id: The ID of the quiz
        submission_id: The ID of the submission to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        quiz = course.get_quiz(quiz_id)
        _ = quiz.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, quiz, or submission not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_quiz_submission_helper(course_id, quiz_id, submission_id)
    
    formatted = "✅ Quiz submission deleted successfully!\n\n"
    formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
    formatted += f"Quiz ID: {result['deleted_submission']['quiz_id']}\n"
    formatted += f"User ID: {result['deleted_submission']['user_id']}\n"
    formatted += f"Attempt: {result['deleted_submission']['attempt']}\n"
    
    return formatted

# ============================================================================
# PHASE 2: COMMUNICATION RESOURCES
# ============================================================================

# -----------------------------
# DISCUSSIONS - Helper Functions
# -----------------------------

def create_discussion_helper(
    course_id: int,
    title: str,
    message: str,
    pinned: bool = False,
    locked: bool = False,
    require_initial_post: bool = False,
    allow_rating: bool = False,
    only_graders_can_rate: bool = False,
    sort_by_rating: bool = False,
    delayed_post_at: Optional[str] = None,
    is_announcement: bool = False
) -> dict:
    """Create a discussion topic."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    topic_params = {
        "title": title,
        "message": message,
        "pinned": pinned,
        "locked": locked,
        "require_initial_post": require_initial_post,
        "allow_rating": allow_rating,
        "only_graders_can_rate": only_graders_can_rate,
        "sort_by_rating": sort_by_rating,
        "is_announcement": is_announcement
    }
    
    if delayed_post_at:
        topic_params["delayed_post_at"] = delayed_post_at
    
    discussion = course.create_discussion_topic(topic=topic_params)
    
    return {
        "id": discussion.id,
        "title": discussion.title,
        "course_id": course_id,
        "message": discussion.message,
        "pinned": discussion.pinned,
        "locked": discussion.locked,
        "posted_at": discussion.posted_at,
        "html_url": discussion.html_url
    }

def fetch_discussion(course_id: int, topic_id: int) -> dict:
    """Fetch a specific discussion."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    discussion = course.get_discussion_topic(topic_id)
    
    return {
        "id": discussion.id,
        "title": discussion.title,
        "course_id": course_id,
        "message": discussion.message,
        "pinned": discussion.pinned,
        "locked": discussion.locked,
        "posted_at": discussion.posted_at,
        "last_reply_at": getattr(discussion, 'last_reply_at', None),
        "html_url": discussion.html_url
    }

def fetch_discussions(course_id: int) -> List[dict]:
    """Fetch all discussions for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    discussions = []
    for discussion in course.get_discussion_topics():
        discussions.append({
            "id": discussion.id,
            "title": discussion.title,
            "pinned": discussion.pinned,
            "locked": discussion.locked,
            "posted_at": discussion.posted_at
        })
    
    return discussions

def fetch_discussion_entries(course_id: int, topic_id: int) -> List[dict]:
    """Fetch entries (posts/replies) for a discussion."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    discussion = course.get_discussion_topic(topic_id)
    
    entries = []
    for entry in discussion.get_entries():
        entries.append({
            "id": entry.id,
            "user_id": entry.user_id,
            "message": entry.message,
            "created_at": entry.created_at,
            "updated_at": getattr(entry, 'updated_at', None),
            "parent_id": getattr(entry, 'parent_id', None)
        })
    
    return entries

def update_discussion_helper(
    course_id: int,
    topic_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None,
    pinned: Optional[bool] = None,
    locked: Optional[bool] = None
) -> dict:
    """Update a discussion topic."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    discussion = course.get_discussion_topic(topic_id)
    
    topic_params = {}
    if title:
        topic_params["title"] = title
    if message:
        topic_params["message"] = message
    if pinned is not None:
        topic_params["pinned"] = pinned
    if locked is not None:
        topic_params["locked"] = locked
    
    updated_discussion = discussion.edit(topic=topic_params)
    
    return {
        "id": updated_discussion.id,
        "title": updated_discussion.title,
        "course_id": course_id,
        "pinned": updated_discussion.pinned,
        "locked": updated_discussion.locked
    }

def delete_discussion_helper(course_id: int, topic_id: int) -> dict:
    """Delete a discussion topic."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    discussion = course.get_discussion_topic(topic_id)
    
    discussion_info = {
        "id": discussion.id,
        "title": discussion.title,
        "course_id": course_id
    }
    
    discussion.delete()
    
    return {
        "success": True,
        "deleted_discussion": discussion_info
    }

# -----------------------------
# DISCUSSIONS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_discussion(
    course_id: int,
    title: str,
    message: str,
    pinned: bool = False,
    locked: bool = False,
    require_initial_post: bool = False
) -> str:
    """Create a new discussion topic in a Canvas course.
    
    Args:
        course_id: The ID of the course
        title: Discussion title (required)
        message: Discussion message/content (required)
        pinned: Whether to pin the discussion
        locked: Whether to lock the discussion
        require_initial_post: Whether students must post before seeing replies
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    discussion = create_discussion_helper(
        course_id=course_id,
        title=title,
        message=message,
        pinned=pinned,
        locked=locked,
        require_initial_post=require_initial_post
    )
    
    formatted = "✅ Discussion created successfully!\n\n"
    formatted += f"Title: {discussion['title']}\n"
    formatted += f"Discussion ID: {discussion['id']}\n"
    formatted += f"Course ID: {discussion['course_id']}\n"
    formatted += f"Pinned: {discussion['pinned']}\n"
    formatted += f"Locked: {discussion['locked']}\n"
    formatted += f"URL: {discussion['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_discussion(course_id: int, topic_id: int) -> str:
    """Get a specific discussion topic.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the discussion topic
    """
    discussion = fetch_discussion(course_id, topic_id)
    
    formatted = f"Discussion Details:\n\n"
    formatted += f"Title: {discussion['title']}\n"
    formatted += f"Discussion ID: {discussion['id']}\n"
    formatted += f"Course ID: {discussion['course_id']}\n"
    formatted += f"Pinned: {discussion['pinned']}\n"
    formatted += f"Locked: {discussion['locked']}\n"
    
    if discussion.get('posted_at'):
        posted_local = convert_utc_to_local(discussion['posted_at'])
        formatted += f"Posted At: {format_datetime_local(posted_local)}\n"
    
    if discussion.get('message'):
        msg = discussion['message'][:200] + "..." if len(discussion.get('message', '')) > 200 else discussion['message']
        formatted += f"\nMessage: {msg}\n"
    
    formatted += f"URL: {discussion['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_discussions(course_id: int) -> str:
    """List all discussions for a course.
    
    Args:
        course_id: The ID of the course
    """
    discussions = fetch_discussions(course_id)
    
    if not discussions:
        return f"No discussions found for course {course_id}."
    
    formatted = f"Discussions for Course {course_id}:\n\n"
    for i, disc in enumerate(discussions, 1):
        formatted += f"{i}. {disc['title']}\n"
        formatted += f"   Discussion ID: {disc['id']}\n"
        formatted += f"   Pinned: {disc['pinned']}\n"
        formatted += f"   Locked: {disc['locked']}\n"
        if disc.get('posted_at'):
            posted_local = convert_utc_to_local(disc['posted_at'])
            formatted += f"   Posted: {format_datetime_local(posted_local)}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(discussions)} discussion(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_discussion_entries(course_id: int, topic_id: int) -> str:
    """Get all entries (posts/replies) for a discussion.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the discussion topic
    """
    entries = fetch_discussion_entries(course_id, topic_id)
    
    if not entries:
        return f"No entries found for discussion {topic_id}."
    
    formatted = f"Discussion Entries for Topic {topic_id}:\n\n"
    for i, entry in enumerate(entries, 1):
        formatted += f"{i}. Entry ID: {entry['id']}\n"
        formatted += f"   User ID: {entry['user_id']}\n"
        if entry.get('parent_id'):
            formatted += f"   Reply to: {entry['parent_id']}\n"
        if entry.get('created_at'):
            created_local = convert_utc_to_local(entry['created_at'])
            formatted += f"   Created: {format_datetime_local(created_local)}\n"
        if entry.get('message'):
            msg = entry['message'][:100] + "..." if len(entry.get('message', '')) > 100 else entry['message']
            formatted += f"   Message: {msg}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(entries)} entry/entries"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_discussion(
    course_id: int,
    topic_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None,
    pinned: Optional[bool] = None,
    locked: Optional[bool] = None
) -> str:
    """Update a discussion topic.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the discussion topic
        title: New discussion title
        message: New discussion message
        pinned: Whether to pin/unpin
        locked: Whether to lock/unlock
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        discussion = course.get_discussion_topic(topic_id)
        _ = discussion.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or discussion not found. {error_msg}"
        return f"Error: {error_msg}"
    
    discussion = update_discussion_helper(
        course_id=course_id,
        topic_id=topic_id,
        title=title,
        message=message,
        pinned=pinned,
        locked=locked
    )
    
    formatted = "✅ Discussion updated successfully!\n\n"
    formatted += f"Discussion ID: {discussion['id']}\n"
    formatted += f"Title: {discussion['title']}\n"
    formatted += f"Pinned: {discussion['pinned']}\n"
    formatted += f"Locked: {discussion['locked']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_discussion(course_id: int, topic_id: int) -> str:
    """Delete a discussion topic.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the discussion topic to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        discussion = course.get_discussion_topic(topic_id)
        _ = discussion.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or discussion not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_discussion_helper(course_id, topic_id)
    
    formatted = "✅ Discussion deleted successfully!\n\n"
    formatted += f"Deleted Discussion: {result['deleted_discussion']['title']}\n"
    formatted += f"Discussion ID: {result['deleted_discussion']['id']}\n"
    formatted += f"Course ID: {result['deleted_discussion']['course_id']}\n"
    
    return formatted

# -----------------------------
# ANNOUNCEMENTS - Helper Functions
# -----------------------------

def create_announcement_helper(
    course_id: int,
    title: str,
    message: str,
    delayed_post_at: Optional[str] = None,
    allow_rating: bool = False
) -> dict:
    """Create an announcement (uses discussion API with is_announcement=True)."""
    return create_discussion_helper(
        course_id=course_id,
        title=title,
        message=message,
        is_announcement=True,
        delayed_post_at=delayed_post_at,
        allow_rating=allow_rating
    )

def fetch_announcement(course_id: int, topic_id: int) -> dict:
    """Fetch a specific announcement."""
    return fetch_discussion(course_id, topic_id)

def fetch_announcements(course_id: int) -> List[dict]:
    """Fetch all announcements for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    announcements = []
    for topic in course.get_discussion_topics(only_announcements=True):
        announcements.append({
            "id": topic.id,
            "title": topic.title,
            "posted_at": topic.posted_at,
            "delayed_post_at": getattr(topic, 'delayed_post_at', None)
        })
    
    return announcements

def update_announcement_helper(
    course_id: int,
    topic_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None
) -> dict:
    """Update an announcement."""
    return update_discussion_helper(course_id, topic_id, title, message)

def delete_announcement_helper(course_id: int, topic_id: int) -> dict:
    """Delete an announcement."""
    return delete_discussion_helper(course_id, topic_id)

# -----------------------------
# ANNOUNCEMENTS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_announcement(
    course_id: int,
    title: str,
    message: str,
    delayed_post_at: Optional[str] = None
) -> str:
    """Create a new announcement in a Canvas course.
    
    Args:
        course_id: The ID of the course
        title: Announcement title (required)
        message: Announcement message/content (required)
        delayed_post_at: Delayed post date in ISO 8601 format
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    announcement = create_announcement_helper(
        course_id=course_id,
        title=title,
        message=message,
        delayed_post_at=delayed_post_at
    )
    
    formatted = "✅ Announcement created successfully!\n\n"
    formatted += f"Title: {announcement['title']}\n"
    formatted += f"Announcement ID: {announcement['id']}\n"
    formatted += f"Course ID: {announcement['course_id']}\n"
    if announcement.get('posted_at'):
        posted_local = convert_utc_to_local(announcement['posted_at'])
        formatted += f"Posted At: {format_datetime_local(posted_local)}\n"
    formatted += f"URL: {announcement['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_announcement(course_id: int, topic_id: int) -> str:
    """Get a specific announcement.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the announcement topic
    """
    announcement = fetch_announcement(course_id, topic_id)
    
    formatted = f"Announcement Details:\n\n"
    formatted += f"Title: {announcement['title']}\n"
    formatted += f"Announcement ID: {announcement['id']}\n"
    formatted += f"Course ID: {announcement['course_id']}\n"
    
    if announcement.get('posted_at'):
        posted_local = convert_utc_to_local(announcement['posted_at'])
        formatted += f"Posted At: {format_datetime_local(posted_local)}\n"
    
    if announcement.get('message'):
        msg = announcement['message'][:200] + "..." if len(announcement.get('message', '')) > 200 else announcement['message']
        formatted += f"\nMessage: {msg}\n"
    
    formatted += f"URL: {announcement['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_announcements(course_id: int) -> str:
    """List all announcements for a course.
    
    Args:
        course_id: The ID of the course
    """
    announcements = fetch_announcements(course_id)
    
    if not announcements:
        return f"No announcements found for course {course_id}."
    
    formatted = f"Announcements for Course {course_id}:\n\n"
    for i, ann in enumerate(announcements, 1):
        formatted += f"{i}. {ann['title']}\n"
        formatted += f"   Announcement ID: {ann['id']}\n"
        if ann.get('posted_at'):
            formatted += f"   Posted: {ann['posted_at']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(announcements)} announcement(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_announcement(
    course_id: int,
    topic_id: int,
    title: Optional[str] = None,
    message: Optional[str] = None
) -> str:
    """Update an announcement.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the announcement topic
        title: New announcement title
        message: New announcement message
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        discussion = course.get_discussion_topic(topic_id)
        _ = discussion.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or announcement not found. {error_msg}"
        return f"Error: {error_msg}"
    
    announcement = update_announcement_helper(course_id, topic_id, title, message)
    
    formatted = "✅ Announcement updated successfully!\n\n"
    formatted += f"Announcement ID: {announcement['id']}\n"
    formatted += f"Title: {announcement['title']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_announcement(course_id: int, topic_id: int) -> str:
    """Delete an announcement.
    
    Args:
        course_id: The ID of the course
        topic_id: The ID of the announcement topic to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        discussion = course.get_discussion_topic(topic_id)
        _ = discussion.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or announcement not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_announcement_helper(course_id, topic_id)
    
    formatted = "✅ Announcement deleted successfully!\n\n"
    formatted += f"Deleted Announcement: {result['deleted_discussion']['title']}\n"
    formatted += f"Announcement ID: {result['deleted_discussion']['id']}\n"
    
    return formatted

# -----------------------------
# CONVERSATIONS/MESSAGES - Helper Functions
# -----------------------------

def create_conversation_helper(
    recipient_ids: List[int],
    body: str,
    subject: Optional[str] = None,
    group_conversation: bool = True,
    attachment_ids: Optional[List[int]] = None,
    media_comment_id: Optional[str] = None,
    media_comment_type: Optional[str] = None
) -> dict:
    """Create a conversation (send message)."""
    canvas = get_canvas_client()
    user = canvas.get_current_user()
    
    conversation_params = {
        "recipients": recipient_ids,
        "body": body,
        "group_conversation": group_conversation
    }
    
    if subject:
        conversation_params["subject"] = subject
    if attachment_ids:
        conversation_params["attachment_ids"] = attachment_ids
    if media_comment_id:
        conversation_params["media_comment_id"] = media_comment_id
    if media_comment_type:
        conversation_params["media_comment_type"] = media_comment_type
    
    conversation = user.create_conversation(conversation=conversation_params)
    
    return {
        "id": conversation.id,
        "subject": conversation.subject,
        "workflow_state": conversation.workflow_state,
        "last_message_at": getattr(conversation, 'last_message_at', None)
    }

def fetch_conversation(conversation_id: int) -> dict:
    """Fetch a specific conversation."""
    canvas = get_canvas_client()
    user = canvas.get_current_user()
    conversation = user.get_conversation(conversation_id)
    
    return {
        "id": conversation.id,
        "subject": conversation.subject,
        "workflow_state": conversation.workflow_state,
        "last_message_at": getattr(conversation, 'last_message_at', None),
        "participants": [{"id": p.id, "name": p.name} for p in getattr(conversation, 'participants', [])],
        "messages": [{"id": m.id, "created_at": m.created_at, "body": m.body} for m in getattr(conversation, 'messages', [])]
    }

def fetch_conversations() -> List[dict]:
    """Fetch all conversations for current user."""
    canvas = get_canvas_client()
    user = canvas.get_current_user()
    
    conversations = []
    for conversation in user.get_conversations():
        conversations.append({
            "id": conversation.id,
            "subject": conversation.subject,
            "workflow_state": conversation.workflow_state,
            "last_message_at": getattr(conversation, 'last_message_at', None)
        })
    
    return conversations

def update_conversation_helper(
    conversation_id: int,
    workflow_state: Optional[str] = None,
    starred: Optional[bool] = None
) -> dict:
    """Update a conversation (mark read/unread, archive, star)."""
    canvas = get_canvas_client()
    user = canvas.get_current_user()
    conversation = user.get_conversation(conversation_id)
    
    conversation_params = {}
    if workflow_state:
        conversation_params["conversation[workflow_state]"] = workflow_state
    if starred is not None:
        conversation_params["conversation[starred]"] = starred
    
    updated_conversation = conversation.edit(conversation=conversation_params)
    
    return {
        "id": updated_conversation.id,
        "workflow_state": updated_conversation.workflow_state,
        "starred": getattr(updated_conversation, 'starred', None)
    }

def delete_conversation_helper(conversation_id: int) -> dict:
    """Delete a conversation."""
    canvas = get_canvas_client()
    user = canvas.get_current_user()
    conversation = user.get_conversation(conversation_id)
    
    conversation_info = {
        "id": conversation.id,
        "subject": conversation.subject
    }
    
    conversation.delete()
    
    return {
        "success": True,
        "deleted_conversation": conversation_info
    }

# -----------------------------
# CONVERSATIONS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def send_message(
    recipient_ids: List[int],
    body: str,
    subject: Optional[str] = None,
    group_conversation: bool = True
) -> str:
    """Send a message to users.
    
    Args:
        recipient_ids: List of user IDs to send message to (required)
        body: Message body/content (required)
        subject: Message subject
        group_conversation: Whether this is a group conversation
    """
    conversation = create_conversation_helper(
        recipient_ids=recipient_ids,
        body=body,
        subject=subject,
        group_conversation=group_conversation
    )
    
    formatted = "✅ Message sent successfully!\n\n"
    formatted += f"Conversation ID: {conversation['id']}\n"
    if conversation.get('subject'):
        formatted += f"Subject: {conversation['subject']}\n"
    formatted += f"State: {conversation['workflow_state']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_conversation(conversation_id: int) -> str:
    """Get a specific conversation.
    
    Args:
        conversation_id: The ID of the conversation
    """
    conversation = fetch_conversation(conversation_id)
    
    formatted = f"Conversation Details:\n\n"
    formatted += f"Conversation ID: {conversation['id']}\n"
    if conversation.get('subject'):
        formatted += f"Subject: {conversation['subject']}\n"
    formatted += f"State: {conversation['workflow_state']}\n"
    
    if conversation.get('last_message_at'):
        last_msg_local = convert_utc_to_local(conversation['last_message_at'])
        formatted += f"Last Message: {format_datetime_local(last_msg_local)}\n"
    
    if conversation.get('participants'):
        formatted += f"\nParticipants: {len(conversation['participants'])} user(s)\n"
    
    if conversation.get('messages'):
        formatted += f"Messages: {len(conversation['messages'])} message(s)\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_conversations() -> str:
    """List all conversations for the current user."""
    conversations = fetch_conversations()
    
    if not conversations:
        return "No conversations found."
    
    formatted = f"Conversations:\n\n"
    for i, conv in enumerate(conversations, 1):
        formatted += f"{i}. "
        if conv.get('subject'):
            formatted += f"{conv['subject']}\n"
        else:
            formatted += f"Conversation {conv['id']}\n"
        formatted += f"   Conversation ID: {conv['id']}\n"
        formatted += f"   State: {conv['workflow_state']}\n"
        if conv.get('last_message_at'):
            last_msg_local = convert_utc_to_local(conv['last_message_at'])
            formatted += f"   Last Message: {format_datetime_local(last_msg_local)}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(conversations)} conversation(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_conversation(
    conversation_id: int,
    workflow_state: Optional[str] = None,
    starred: Optional[bool] = None
) -> str:
    """Update a conversation (mark read/unread, archive, star).
    
    Args:
        conversation_id: The ID of the conversation
        workflow_state: New workflow state ('read', 'unread', 'archived')
        starred: Whether to star/unstar the conversation
    """
    conversation = update_conversation_helper(
        conversation_id=conversation_id,
        workflow_state=workflow_state,
        starred=starred
    )
    
    formatted = "✅ Conversation updated successfully!\n\n"
    formatted += f"Conversation ID: {conversation['id']}\n"
    formatted += f"State: {conversation['workflow_state']}\n"
    if conversation.get('starred') is not None:
        formatted += f"Starred: {conversation['starred']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_conversation(conversation_id: int) -> str:
    """Delete a conversation.
    
    Args:
        conversation_id: The ID of the conversation to delete
    """
    result = delete_conversation_helper(conversation_id)
    
    formatted = "✅ Conversation deleted successfully!\n\n"
    formatted += f"Deleted Conversation ID: {result['deleted_conversation']['id']}\n"
    if result['deleted_conversation'].get('subject'):
        formatted += f"Subject: {result['deleted_conversation']['subject']}\n"
    
    return formatted

# ============================================================================
# PHASE 3: CONTENT ORGANIZATION
# ============================================================================

# -----------------------------
# MODULES - Helper Functions
# -----------------------------

def create_module_helper(
    course_id: int,
    name: str,
    position: Optional[int] = None,
    unlock_at: Optional[str] = None,
    require_sequential_progress: bool = False,
    prerequisite_module_ids: Optional[List[int]] = None,
    publish_final_grade: bool = False
) -> dict:
    """Create a module in a Canvas course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    module_params = {
        "name": name,
        "require_sequential_progress": require_sequential_progress,
        "publish_final_grade": publish_final_grade
    }
    
    if position is not None:
        module_params["position"] = position
    if unlock_at:
        module_params["unlock_at"] = unlock_at
    if prerequisite_module_ids:
        module_params["prerequisite_module_ids"] = prerequisite_module_ids
    
    module = course.create_module(course_module=module_params)
    
    return {
        "id": module.id,
        "name": module.name,
        "course_id": course_id,
        "position": module.position,
        "unlock_at": module.unlock_at,
        "require_sequential_progress": module.require_sequential_progress,
        "items_count": getattr(module, 'items_count', 0)
    }

def fetch_module(course_id: int, module_id: int) -> dict:
    """Fetch a specific module."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    
    return {
        "id": module.id,
        "name": module.name,
        "course_id": course_id,
        "position": module.position,
        "unlock_at": module.unlock_at,
        "require_sequential_progress": module.require_sequential_progress,
        "items_count": getattr(module, 'items_count', 0),
        "items_url": getattr(module, 'items_url', None)
    }

def fetch_modules(course_id: int) -> List[dict]:
    """Fetch all modules for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    modules = []
    for module in course.get_modules():
        modules.append({
            "id": module.id,
            "name": module.name,
            "position": module.position,
            "unlock_at": module.unlock_at,
            "items_count": getattr(module, 'items_count', 0)
        })
    
    return modules

def fetch_module_items(course_id: int, module_id: int) -> List[dict]:
    """Fetch items in a module."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    
    items = []
    for item in module.get_module_items():
        items.append({
            "id": item.id,
            "title": item.title,
            "type": item.type,
            "content_id": getattr(item, 'content_id', None),
            "position": item.position,
            "indent": getattr(item, 'indent', 0),
            "url": getattr(item, 'url', None)
        })
    
    return items

def update_module_helper(
    course_id: int,
    module_id: int,
    name: Optional[str] = None,
    position: Optional[int] = None,
    unlock_at: Optional[str] = None,
    require_sequential_progress: Optional[bool] = None
) -> dict:
    """Update a module."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    
    module_params = {}
    if name:
        module_params["name"] = name
    if position is not None:
        module_params["position"] = position
    if unlock_at:
        module_params["unlock_at"] = unlock_at
    if require_sequential_progress is not None:
        module_params["require_sequential_progress"] = require_sequential_progress
    
    updated_module = module.edit(course_module=module_params)
    
    return {
        "id": updated_module.id,
        "name": updated_module.name,
        "course_id": course_id,
        "position": updated_module.position
    }

def delete_module_helper(course_id: int, module_id: int) -> dict:
    """Delete a module."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    
    module_info = {
        "id": module.id,
        "name": module.name,
        "course_id": course_id
    }
    
    module.delete()
    
    return {
        "success": True,
        "deleted_module": module_info
    }

# -----------------------------
# MODULES - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_module(
    course_id: int,
    name: str,
    position: Optional[int] = None,
    unlock_at: Optional[str] = None,
    require_sequential_progress: bool = False
) -> str:
    """Create a new module in a Canvas course.
    
    Args:
        course_id: The ID of the course
        name: Module name (required)
        position: Module position/order
        unlock_at: Unlock date in ISO 8601 format
        require_sequential_progress: Whether students must complete items in order
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    module = create_module_helper(
        course_id=course_id,
        name=name,
        position=position,
        unlock_at=unlock_at,
        require_sequential_progress=require_sequential_progress
    )
    
    formatted = "✅ Module created successfully!\n\n"
    formatted += f"Name: {module['name']}\n"
    formatted += f"Module ID: {module['id']}\n"
    formatted += f"Course ID: {module['course_id']}\n"
    formatted += f"Position: {module['position']}\n"
    formatted += f"Items Count: {module['items_count']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_module(course_id: int, module_id: int) -> str:
    """Get a specific module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
    """
    module = fetch_module(course_id, module_id)
    
    formatted = f"Module Details:\n\n"
    formatted += f"Name: {module['name']}\n"
    formatted += f"Module ID: {module['id']}\n"
    formatted += f"Course ID: {module['course_id']}\n"
    formatted += f"Position: {module['position']}\n"
    formatted += f"Items Count: {module['items_count']}\n"
    
    if module.get('unlock_at'):
        unlock_local = convert_utc_to_local(module['unlock_at'])
        formatted += f"Unlock At: {format_datetime_local(unlock_local)}\n"
    
    formatted += f"Sequential Progress: {module['require_sequential_progress']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_modules(course_id: int) -> str:
    """List all modules for a course.
    
    Args:
        course_id: The ID of the course
    """
    modules = fetch_modules(course_id)
    
    if not modules:
        return f"No modules found for course {course_id}."
    
    formatted = f"Modules for Course {course_id}:\n\n"
    for i, mod in enumerate(modules, 1):
        formatted += f"{i}. {mod['name']}\n"
        formatted += f"   Module ID: {mod['id']}\n"
        formatted += f"   Position: {mod['position']}\n"
        formatted += f"   Items: {mod['items_count']}\n"
        if mod.get('unlock_at'):
            unlock_local = convert_utc_to_local(mod['unlock_at'])
            formatted += f"   Unlock: {format_datetime_local(unlock_local)}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(modules)} module(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_module_items(course_id: int, module_id: int) -> str:
    """Get all items in a module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
    """
    items = fetch_module_items(course_id, module_id)
    
    if not items:
        return f"No items found in module {module_id}."
    
    formatted = f"Items in Module {module_id}:\n\n"
    for i, item in enumerate(items, 1):
        formatted += f"{i}. {item['title']}\n"
        formatted += f"   Item ID: {item['id']}\n"
        formatted += f"   Type: {item['type']}\n"
        formatted += f"   Position: {item['position']}\n"
        if item.get('content_id'):
            formatted += f"   Content ID: {item['content_id']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(items)} item(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_module(
    course_id: int,
    module_id: int,
    name: Optional[str] = None,
    position: Optional[int] = None,
    unlock_at: Optional[str] = None,
    require_sequential_progress: Optional[bool] = None
) -> str:
    """Update a module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
        name: New module name
        position: New position
        unlock_at: New unlock date
        require_sequential_progress: Whether to require sequential progress
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        _ = module.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or module not found. {error_msg}"
        return f"Error: {error_msg}"
    
    module = update_module_helper(
        course_id=course_id,
        module_id=module_id,
        name=name,
        position=position,
        unlock_at=unlock_at,
        require_sequential_progress=require_sequential_progress
    )
    
    formatted = "✅ Module updated successfully!\n\n"
    formatted += f"Module ID: {module['id']}\n"
    formatted += f"Name: {module['name']}\n"
    formatted += f"Position: {module['position']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_module(course_id: int, module_id: int) -> str:
    """Delete a module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        _ = module.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or module not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_module_helper(course_id, module_id)
    
    formatted = "✅ Module deleted successfully!\n\n"
    formatted += f"Deleted Module: {result['deleted_module']['name']}\n"
    formatted += f"Module ID: {result['deleted_module']['id']}\n"
    formatted += f"Course ID: {result['deleted_module']['course_id']}\n"
    
    return formatted

# -----------------------------
# MODULE ITEMS - Helper Functions
# -----------------------------

def create_module_item_helper(
    course_id: int,
    module_id: int,
    type: str,
    content_id: Optional[int] = None,
    title: Optional[str] = None,
    position: Optional[int] = None,
    indent: int = 0,
    page_url: Optional[str] = None,
    external_url: Optional[str] = None,
    new_tab: bool = False
) -> dict:
    """Create a module item."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    
    item_params = {
        "type": type,
        "indent": indent,
        "new_tab": new_tab
    }
    
    if content_id:
        item_params["content_id"] = content_id
    if title:
        item_params["title"] = title
    if position is not None:
        item_params["position"] = position
    if page_url:
        item_params["page_url"] = page_url
    if external_url:
        item_params["external_url"] = external_url
    
    item = module.create_module_item(module_item=item_params)
    
    return {
        "id": item.id,
        "title": item.title,
        "type": item.type,
        "module_id": module_id,
        "content_id": getattr(item, 'content_id', None),
        "position": item.position,
        "indent": item.indent
    }

def fetch_module_item(course_id: int, module_id: int, item_id: int) -> dict:
    """Fetch a specific module item."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    item = module.get_module_item(item_id)
    
    return {
        "id": item.id,
        "title": item.title,
        "type": item.type,
        "module_id": module_id,
        "content_id": getattr(item, 'content_id', None),
        "position": item.position,
        "indent": item.indent,
        "url": getattr(item, 'url', None)
    }

def update_module_item_helper(
    course_id: int,
    module_id: int,
    item_id: int,
    title: Optional[str] = None,
    position: Optional[int] = None,
    indent: Optional[int] = None
) -> dict:
    """Update a module item."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    item = module.get_module_item(item_id)
    
    item_params = {}
    if title:
        item_params["title"] = title
    if position is not None:
        item_params["position"] = position
    if indent is not None:
        item_params["indent"] = indent
    
    updated_item = item.edit(module_item=item_params)
    
    return {
        "id": updated_item.id,
        "title": updated_item.title,
        "type": updated_item.type,
        "module_id": module_id,
        "position": updated_item.position
    }

def delete_module_item_helper(course_id: int, module_id: int, item_id: int) -> dict:
    """Delete a module item."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    module = course.get_module(module_id)
    item = module.get_module_item(item_id)
    
    item_info = {
        "id": item.id,
        "title": item.title,
        "module_id": module_id
    }
    
    item.delete()
    
    return {
        "success": True,
        "deleted_item": item_info
    }

# -----------------------------
# MODULE ITEMS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_module_item(
    course_id: int,
    module_id: int,
    type: str,
    content_id: Optional[int] = None,
    title: Optional[str] = None,
    position: Optional[int] = None,
    indent: int = 0
) -> str:
    """Create a new item in a module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
        type: Item type ('Assignment', 'File', 'Page', 'Discussion', 'Quiz', 'ExternalUrl', 'ExternalTool')
        content_id: ID of the content (assignment, file, etc.)
        title: Item title
        position: Item position in module
        indent: Indentation level (0-3)
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        _ = module.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or module not found. {error_msg}"
        return f"Error: {error_msg}"
    
    item = create_module_item_helper(
        course_id=course_id,
        module_id=module_id,
        type=type,
        content_id=content_id,
        title=title,
        position=position,
        indent=indent
    )
    
    formatted = "✅ Module item created successfully!\n\n"
    formatted += f"Title: {item['title']}\n"
    formatted += f"Item ID: {item['id']}\n"
    formatted += f"Module ID: {item['module_id']}\n"
    formatted += f"Type: {item['type']}\n"
    formatted += f"Position: {item['position']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_module_item(course_id: int, module_id: int, item_id: int) -> str:
    """Get a specific module item.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
        item_id: The ID of the module item
    """
    item = fetch_module_item(course_id, module_id, item_id)
    
    formatted = f"Module Item Details:\n\n"
    formatted += f"Title: {item['title']}\n"
    formatted += f"Item ID: {item['id']}\n"
    formatted += f"Module ID: {item['module_id']}\n"
    formatted += f"Type: {item['type']}\n"
    formatted += f"Position: {item['position']}\n"
    formatted += f"Indent: {item['indent']}\n"
    
    if item.get('content_id'):
        formatted += f"Content ID: {item['content_id']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_module_items(course_id: int, module_id: int) -> str:
    """List all items in a module.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
    """
    items = fetch_module_items(course_id, module_id)
    
    if not items:
        return f"No items found in module {module_id}."
    
    formatted = f"Items in Module {module_id}:\n\n"
    for i, item in enumerate(items, 1):
        formatted += f"{i}. {item['title']}\n"
        formatted += f"   Item ID: {item['id']}\n"
        formatted += f"   Type: {item['type']}\n"
        formatted += f"   Position: {item['position']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(items)} item(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_module_item(
    course_id: int,
    module_id: int,
    item_id: int,
    title: Optional[str] = None,
    position: Optional[int] = None,
    indent: Optional[int] = None
) -> str:
    """Update a module item.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
        item_id: The ID of the module item
        title: New item title
        position: New position
        indent: New indentation level
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        item = module.get_module_item(item_id)
        _ = item.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, module, or item not found. {error_msg}"
        return f"Error: {error_msg}"
    
    item = update_module_item_helper(
        course_id=course_id,
        module_id=module_id,
        item_id=item_id,
        title=title,
        position=position,
        indent=indent
    )
    
    formatted = "✅ Module item updated successfully!\n\n"
    formatted += f"Item ID: {item['id']}\n"
    formatted += f"Title: {item['title']}\n"
    formatted += f"Position: {item['position']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_module_item(course_id: int, module_id: int, item_id: int) -> str:
    """Delete a module item.
    
    Args:
        course_id: The ID of the course
        module_id: The ID of the module
        item_id: The ID of the module item to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        item = module.get_module_item(item_id)
        _ = item.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course, module, or item not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_module_item_helper(course_id, module_id, item_id)
    
    formatted = "✅ Module item deleted successfully!\n\n"
    formatted += f"Deleted Item: {result['deleted_item']['title']}\n"
    formatted += f"Item ID: {result['deleted_item']['id']}\n"
    formatted += f"Module ID: {result['deleted_item']['module_id']}\n"
    
    return formatted

# -----------------------------
# PAGES/WIKI PAGES - Helper Functions
# -----------------------------

def create_page_helper(
    course_id: int,
    title: str,
    body: str,
    editing_roles: Optional[str] = None,
    published: bool = False,
    front_page: bool = False
) -> dict:
    """Create a wiki page."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    page_params = {
        "title": title,
        "body": body,
        "published": published,
        "front_page": front_page
    }
    
    if editing_roles:
        page_params["editing_roles"] = editing_roles
    
    page = course.create_page(wiki_page=page_params)
    
    return {
        "id": page.page_id,
        "title": page.title,
        "url": page.url,
        "course_id": course_id,
        "body": page.body,
        "published": page.published,
        "front_page": page.front_page,
        "html_url": page.html_url
    }

def fetch_page(course_id: int, url: str) -> dict:
    """Fetch a specific page by URL."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    page = course.get_page(url)
    
    return {
        "id": page.page_id,
        "title": page.title,
        "url": page.url,
        "course_id": course_id,
        "body": page.body,
        "published": page.published,
        "front_page": page.front_page,
        "html_url": page.html_url,
        "updated_at": getattr(page, 'updated_at', None)
    }

def fetch_pages(course_id: int) -> List[dict]:
    """Fetch all pages for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    pages = []
    for page in course.get_pages():
        pages.append({
            "id": page.page_id,
            "title": page.title,
            "url": page.url,
            "published": page.published,
            "front_page": page.front_page
        })
    
    return pages

def update_page_helper(
    course_id: int,
    url: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    published: Optional[bool] = None,
    front_page: Optional[bool] = None
) -> dict:
    """Update a page."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    page = course.get_page(url)
    
    page_params = {}
    if title:
        page_params["title"] = title
    if body:
        page_params["body"] = body
    if published is not None:
        page_params["published"] = published
    if front_page is not None:
        page_params["front_page"] = front_page
    
    updated_page = page.edit(wiki_page=page_params)
    
    return {
        "id": updated_page.page_id,
        "title": updated_page.title,
        "url": updated_page.url,
        "course_id": course_id,
        "published": updated_page.published
    }

def delete_page_helper(course_id: int, url: str) -> dict:
    """Delete a page."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    page = course.get_page(url)
    
    page_info = {
        "id": page.page_id,
        "title": page.title,
        "url": page.url,
        "course_id": course_id
    }
    
    page.delete()
    
    return {
        "success": True,
        "deleted_page": page_info
    }

# -----------------------------
# PAGES - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_page(
    course_id: int,
    title: str,
    body: str,
    editing_roles: Optional[str] = None,
    published: bool = False,
    front_page: bool = False
) -> str:
    """Create a new wiki page in a Canvas course.
    
    Args:
        course_id: The ID of the course
        title: Page title (required)
        body: Page body/content in HTML (required)
        editing_roles: Who can edit ('teachers', 'students', 'members', 'public')
        published: Whether to publish immediately
        front_page: Whether to set as front page
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    page = create_page_helper(
        course_id=course_id,
        title=title,
        body=body,
        editing_roles=editing_roles,
        published=published,
        front_page=front_page
    )
    
    formatted = "✅ Page created successfully!\n\n"
    formatted += f"Title: {page['title']}\n"
    formatted += f"Page ID: {page['id']}\n"
    formatted += f"URL: {page['url']}\n"
    formatted += f"Course ID: {page['course_id']}\n"
    formatted += f"Published: {page['published']}\n"
    formatted += f"Front Page: {page['front_page']}\n"
    formatted += f"Page URL: {page['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_page(course_id: int, url: str) -> str:
    """Get a specific page by URL.
    
    Args:
        course_id: The ID of the course
        url: The URL/slug of the page
    """
    page = fetch_page(course_id, url)
    
    formatted = f"Page Details:\n\n"
    formatted += f"Title: {page['title']}\n"
    formatted += f"Page ID: {page['id']}\n"
    formatted += f"URL: {page['url']}\n"
    formatted += f"Course ID: {page['course_id']}\n"
    formatted += f"Published: {page['published']}\n"
    formatted += f"Front Page: {page['front_page']}\n"
    
    if page.get('body'):
        body_preview = page['body'][:200] + "..." if len(page.get('body', '')) > 200 else page['body']
        formatted += f"\nBody: {body_preview}\n"
    
    formatted += f"Page URL: {page['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_pages(course_id: int) -> str:
    """List all pages for a course.
    
    Args:
        course_id: The ID of the course
    """
    pages = fetch_pages(course_id)
    
    if not pages:
        return f"No pages found for course {course_id}."
    
    formatted = f"Pages for Course {course_id}:\n\n"
    for i, page in enumerate(pages, 1):
        formatted += f"{i}. {page['title']}\n"
        formatted += f"   Page ID: {page['id']}\n"
        formatted += f"   URL: {page['url']}\n"
        formatted += f"   Published: {page['published']}\n"
        if page.get('front_page'):
            formatted += f"   Front Page: Yes\n"
        formatted += "\n"
    
    formatted += f"Total: {len(pages)} page(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_page(
    course_id: int,
    url: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    published: Optional[bool] = None,
    front_page: Optional[bool] = None
) -> str:
    """Update a page.
    
    Args:
        course_id: The ID of the course
        url: The URL/slug of the page
        title: New page title
        body: New page body/content
        published: Whether to publish/unpublish
        front_page: Whether to set as front page
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        page = course.get_page(url)
        _ = page.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or page not found. {error_msg}"
        return f"Error: {error_msg}"
    
    page = update_page_helper(
        course_id=course_id,
        url=url,
        title=title,
        body=body,
        published=published,
        front_page=front_page
    )
    
    formatted = "✅ Page updated successfully!\n\n"
    formatted += f"Page ID: {page['id']}\n"
    formatted += f"Title: {page['title']}\n"
    formatted += f"URL: {page['url']}\n"
    formatted += f"Published: {page['published']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_page(course_id: int, url: str) -> str:
    """Delete a page.
    
    Args:
        course_id: The ID of the course
        url: The URL/slug of the page to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        page = course.get_page(url)
        _ = page.title
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or page not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_page_helper(course_id, url)
    
    formatted = "✅ Page deleted successfully!\n\n"
    formatted += f"Deleted Page: {result['deleted_page']['title']}\n"
    formatted += f"Page ID: {result['deleted_page']['id']}\n"
    formatted += f"URL: {result['deleted_page']['url']}\n"
    
    return formatted

# ============================================================================
# PHASE 4: FILE MANAGEMENT
# ============================================================================

# -----------------------------
# FILES - Helper Functions
# -----------------------------

def upload_file_helper(
    course_id: int,
    file_path: str,
    folder_id: Optional[int] = None,
    on_duplicate: str = "rename",
    parent_folder_path: Optional[str] = None
) -> dict:
    """Upload a file to Canvas."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    if folder_id:
        folder = course.get_folder(folder_id)
        file_obj = folder.upload(file_path, on_duplicate=on_duplicate)
    elif parent_folder_path:
        folder = course.get_folder_by_path(parent_folder_path)
        file_obj = folder.upload(file_path, on_duplicate=on_duplicate)
    else:
        file_obj = course.upload(file_path, on_duplicate=on_duplicate)
    
    return {
        "id": file_obj.id,
        "filename": file_obj.filename,
        "display_name": file_obj.display_name,
        "content_type": file_obj.content_type,
        "size": file_obj.size,
        "url": file_obj.url,
        "course_id": course_id
    }

def fetch_file(course_id: int, file_id: int) -> dict:
    """Fetch a specific file."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    file_obj = course.get_file(file_id)
    
    return {
        "id": file_obj.id,
        "filename": file_obj.filename,
        "display_name": file_obj.display_name,
        "content_type": file_obj.content_type,
        "size": file_obj.size,
        "url": file_obj.url,
        "locked": file_obj.locked,
        "hidden": file_obj.hidden,
        "locked_for_user": getattr(file_obj, 'locked_for_user', False),
        "course_id": course_id
    }

def fetch_files(course_id: int, folder_id: Optional[int] = None, search_term: Optional[str] = None) -> List[dict]:
    """Fetch files for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    if folder_id:
        folder = course.get_folder(folder_id)
        files_iter = folder.get_files()
    else:
        files_iter = course.get_files()
    
    files = []
    for file_obj in files_iter:
        if search_term and search_term.lower() not in file_obj.filename.lower():
            continue
        files.append({
            "id": file_obj.id,
            "filename": file_obj.filename,
            "display_name": file_obj.display_name,
            "content_type": file_obj.content_type,
            "size": file_obj.size,
            "url": file_obj.url
        })
    
    return files

def update_file_helper(
    course_id: int,
    file_id: int,
    name: Optional[str] = None,
    locked: Optional[bool] = None,
    hidden: Optional[bool] = None
) -> dict:
    """Update a file."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    file_obj = course.get_file(file_id)
    
    file_params = {}
    if name:
        file_params["name"] = name
    if locked is not None:
        file_params["locked"] = locked
    if hidden is not None:
        file_params["hidden"] = hidden
    
    updated_file = file_obj.edit(file=file_params)
    
    return {
        "id": updated_file.id,
        "filename": updated_file.filename,
        "display_name": updated_file.display_name,
        "locked": updated_file.locked,
        "hidden": updated_file.hidden
    }

def delete_file_helper(course_id: int, file_id: int) -> dict:
    """Delete a file."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    file_obj = course.get_file(file_id)
    
    file_info = {
        "id": file_obj.id,
        "filename": file_obj.filename,
        "course_id": course_id
    }
    
    file_obj.delete()
    
    return {
        "success": True,
        "deleted_file": file_info
    }

# -----------------------------
# FILES - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def upload_file(
    course_id: int,
    file_path: str,
    folder_id: Optional[int] = None,
    on_duplicate: str = "rename"
) -> str:
    """Upload a file to a Canvas course.
    
    Args:
        course_id: The ID of the course
        file_path: Local path to the file to upload (required)
        folder_id: ID of the folder to upload to
        on_duplicate: What to do if file exists ('rename' or 'overwrite')
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    file_obj = upload_file_helper(
        course_id=course_id,
        file_path=file_path,
        folder_id=folder_id,
        on_duplicate=on_duplicate
    )
    
    formatted = "✅ File uploaded successfully!\n\n"
    formatted += f"Filename: {file_obj['filename']}\n"
    formatted += f"File ID: {file_obj['id']}\n"
    formatted += f"Course ID: {file_obj['course_id']}\n"
    formatted += f"Size: {file_obj['size']} bytes\n"
    formatted += f"Content Type: {file_obj['content_type']}\n"
    formatted += f"URL: {file_obj['url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_file(course_id: int, file_id: int) -> str:
    """Get a specific file.
    
    Args:
        course_id: The ID of the course
        file_id: The ID of the file
    """
    file_obj = fetch_file(course_id, file_id)
    
    formatted = f"File Details:\n\n"
    formatted += f"Filename: {file_obj['filename']}\n"
    formatted += f"File ID: {file_obj['id']}\n"
    formatted += f"Display Name: {file_obj['display_name']}\n"
    formatted += f"Size: {file_obj['size']} bytes\n"
    formatted += f"Content Type: {file_obj['content_type']}\n"
    formatted += f"Locked: {file_obj['locked']}\n"
    formatted += f"Hidden: {file_obj['hidden']}\n"
    formatted += f"URL: {file_obj['url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_files(course_id: int, folder_id: Optional[int] = None, search_term: Optional[str] = None) -> str:
    """List files for a course.
    
    Args:
        course_id: The ID of the course
        folder_id: Optional folder ID to list files from
        search_term: Optional search term to filter files
    """
    files = fetch_files(course_id, folder_id, search_term)
    
    if not files:
        return f"No files found for course {course_id}."
    
    formatted = f"Files for Course {course_id}:\n\n"
    for i, file_obj in enumerate(files, 1):
        formatted += f"{i}. {file_obj['filename']}\n"
        formatted += f"   File ID: {file_obj['id']}\n"
        formatted += f"   Size: {file_obj['size']} bytes\n"
        formatted += f"   Type: {file_obj['content_type']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(files)} file(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_file(
    course_id: int,
    file_id: int,
    name: Optional[str] = None,
    locked: Optional[bool] = None,
    hidden: Optional[bool] = None
) -> str:
    """Update a file (rename, lock, hide).
    
    Args:
        course_id: The ID of the course
        file_id: The ID of the file
        name: New filename
        locked: Whether to lock/unlock
        hidden: Whether to hide/show
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        file_obj = course.get_file(file_id)
        _ = file_obj.filename
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or file not found. {error_msg}"
        return f"Error: {error_msg}"
    
    file_obj = update_file_helper(
        course_id=course_id,
        file_id=file_id,
        name=name,
        locked=locked,
        hidden=hidden
    )
    
    formatted = "✅ File updated successfully!\n\n"
    formatted += f"File ID: {file_obj['id']}\n"
    formatted += f"Filename: {file_obj['filename']}\n"
    formatted += f"Locked: {file_obj['locked']}\n"
    formatted += f"Hidden: {file_obj['hidden']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_file(course_id: int, file_id: int) -> str:
    """Delete a file.
    
    Args:
        course_id: The ID of the course
        file_id: The ID of the file to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        file_obj = course.get_file(file_id)
        _ = file_obj.filename
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or file not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_file_helper(course_id, file_id)
    
    formatted = "✅ File deleted successfully!\n\n"
    formatted += f"Deleted File: {result['deleted_file']['filename']}\n"
    formatted += f"File ID: {result['deleted_file']['id']}\n"
    formatted += f"Course ID: {result['deleted_file']['course_id']}\n"
    
    return formatted

# -----------------------------
# FOLDERS - Helper Functions
# -----------------------------

def create_folder_helper(
    course_id: int,
    name: str,
    parent_folder_id: Optional[int] = None,
    locked: bool = False,
    hidden: bool = False
) -> dict:
    """Create a folder."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    if parent_folder_id:
        parent_folder = course.get_folder(parent_folder_id)
        folder = parent_folder.create_folder(name=name, locked=locked, hidden=hidden)
    else:
        folder = course.create_folder(name=name, locked=locked, hidden=hidden)
    
    return {
        "id": folder.id,
        "name": folder.name,
        "full_name": folder.full_name,
        "course_id": course_id,
        "parent_folder_id": getattr(folder, 'parent_folder_id', None),
        "locked": folder.locked,
        "hidden": folder.hidden,
        "files_count": getattr(folder, 'files_count', 0),
        "folders_count": getattr(folder, 'folders_count', 0)
    }

def fetch_folder(course_id: int, folder_id: int) -> dict:
    """Fetch a specific folder."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    folder = course.get_folder(folder_id)
    
    return {
        "id": folder.id,
        "name": folder.name,
        "full_name": folder.full_name,
        "course_id": course_id,
        "parent_folder_id": getattr(folder, 'parent_folder_id', None),
        "locked": folder.locked,
        "hidden": folder.hidden,
        "files_count": getattr(folder, 'files_count', 0),
        "folders_count": getattr(folder, 'folders_count', 0)
    }

def fetch_folders(course_id: int, folder_id: Optional[int] = None) -> List[dict]:
    """Fetch folders for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    if folder_id:
        parent_folder = course.get_folder(folder_id)
        folders_iter = parent_folder.get_folders()
    else:
        folders_iter = course.get_folders()
    
    folders = []
    for folder in folders_iter:
        folders.append({
            "id": folder.id,
            "name": folder.name,
            "full_name": folder.full_name,
            "parent_folder_id": getattr(folder, 'parent_folder_id', None),
            "files_count": getattr(folder, 'files_count', 0),
            "folders_count": getattr(folder, 'folders_count', 0)
        })
    
    return folders

def update_folder_helper(
    course_id: int,
    folder_id: int,
    name: Optional[str] = None,
    locked: Optional[bool] = None,
    hidden: Optional[bool] = None
) -> dict:
    """Update a folder."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    folder = course.get_folder(folder_id)
    
    folder_params = {}
    if name:
        folder_params["name"] = name
    if locked is not None:
        folder_params["locked"] = locked
    if hidden is not None:
        folder_params["hidden"] = hidden
    
    updated_folder = folder.edit(folder=folder_params)
    
    return {
        "id": updated_folder.id,
        "name": updated_folder.name,
        "full_name": updated_folder.full_name,
        "course_id": course_id
    }

def delete_folder_helper(course_id: int, folder_id: int) -> dict:
    """Delete a folder."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    folder = course.get_folder(folder_id)
    
    folder_info = {
        "id": folder.id,
        "name": folder.name,
        "course_id": course_id
    }
    
    folder.delete()
    
    return {
        "success": True,
        "deleted_folder": folder_info
    }

# -----------------------------
# FOLDERS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_folder(
    course_id: int,
    name: str,
    parent_folder_id: Optional[int] = None,
    locked: bool = False,
    hidden: bool = False
) -> str:
    """Create a new folder in a Canvas course.
    
    Args:
        course_id: The ID of the course
        name: Folder name (required)
        parent_folder_id: ID of parent folder (optional)
        locked: Whether to lock the folder
        hidden: Whether to hide the folder
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    folder = create_folder_helper(
        course_id=course_id,
        name=name,
        parent_folder_id=parent_folder_id,
        locked=locked,
        hidden=hidden
    )
    
    formatted = "✅ Folder created successfully!\n\n"
    formatted += f"Name: {folder['name']}\n"
    formatted += f"Folder ID: {folder['id']}\n"
    formatted += f"Full Name: {folder['full_name']}\n"
    formatted += f"Course ID: {folder['course_id']}\n"
    formatted += f"Files: {folder['files_count']}\n"
    formatted += f"Subfolders: {folder['folders_count']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_folder(course_id: int, folder_id: int) -> str:
    """Get a specific folder.
    
    Args:
        course_id: The ID of the course
        folder_id: The ID of the folder
    """
    folder = fetch_folder(course_id, folder_id)
    
    formatted = f"Folder Details:\n\n"
    formatted += f"Name: {folder['name']}\n"
    formatted += f"Folder ID: {folder['id']}\n"
    formatted += f"Full Name: {folder['full_name']}\n"
    formatted += f"Course ID: {folder['course_id']}\n"
    formatted += f"Locked: {folder['locked']}\n"
    formatted += f"Hidden: {folder['hidden']}\n"
    formatted += f"Files: {folder['files_count']}\n"
    formatted += f"Subfolders: {folder['folders_count']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_folders(course_id: int, folder_id: Optional[int] = None) -> str:
    """List folders for a course.
    
    Args:
        course_id: The ID of the course
        folder_id: Optional parent folder ID to list subfolders
    """
    folders = fetch_folders(course_id, folder_id)
    
    if not folders:
        return f"No folders found for course {course_id}."
    
    formatted = f"Folders for Course {course_id}:\n\n"
    for i, folder in enumerate(folders, 1):
        formatted += f"{i}. {folder['name']}\n"
        formatted += f"   Folder ID: {folder['id']}\n"
        formatted += f"   Full Name: {folder['full_name']}\n"
        formatted += f"   Files: {folder['files_count']}\n"
        formatted += f"   Subfolders: {folder['folders_count']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(folders)} folder(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_folder(
    course_id: int,
    folder_id: int,
    name: Optional[str] = None,
    locked: Optional[bool] = None,
    hidden: Optional[bool] = None
) -> str:
    """Update a folder.
    
    Args:
        course_id: The ID of the course
        folder_id: The ID of the folder
        name: New folder name
        locked: Whether to lock/unlock
        hidden: Whether to hide/show
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        folder = course.get_folder(folder_id)
        _ = folder.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or folder not found. {error_msg}"
        return f"Error: {error_msg}"
    
    folder = update_folder_helper(
        course_id=course_id,
        folder_id=folder_id,
        name=name,
        locked=locked,
        hidden=hidden
    )
    
    formatted = "✅ Folder updated successfully!\n\n"
    formatted += f"Folder ID: {folder['id']}\n"
    formatted += f"Name: {folder['name']}\n"
    formatted += f"Full Name: {folder['full_name']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_folder(course_id: int, folder_id: int) -> str:
    """Delete a folder (must be empty).
    
    Args:
        course_id: The ID of the course
        folder_id: The ID of the folder to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        folder = course.get_folder(folder_id)
        _ = folder.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or folder not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_folder_helper(course_id, folder_id)
    
    formatted = "✅ Folder deleted successfully!\n\n"
    formatted += f"Deleted Folder: {result['deleted_folder']['name']}\n"
    formatted += f"Folder ID: {result['deleted_folder']['id']}\n"
    formatted += f"Course ID: {result['deleted_folder']['course_id']}\n"
    
    return formatted

# ============================================================================
# PHASE 5: ASSESSMENT & GRADING
# ============================================================================

# -----------------------------
# ASSIGNMENT GROUPS - Helper Functions
# -----------------------------

def create_assignment_group_helper(
    course_id: int,
    name: str,
    position: Optional[int] = None,
    group_weight: Optional[float] = None,
    rules: Optional[Dict[str, Any]] = None
) -> dict:
    """Create an assignment group."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    group_params = {"name": name}
    if position is not None:
        group_params["position"] = position
    if group_weight is not None:
        group_params["group_weight"] = group_weight
    if rules:
        group_params["rules"] = rules
    
    group = course.create_assignment_group(assignment_group=group_params)
    
    return {
        "id": group.id,
        "name": group.name,
        "course_id": course_id,
        "position": group.position,
        "group_weight": getattr(group, 'group_weight', None),
        "assignments_count": getattr(group, 'assignments_count', 0)
    }

def fetch_assignment_group(course_id: int, group_id: int) -> dict:
    """Fetch a specific assignment group."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    group = course.get_assignment_group(group_id)
    
    return {
        "id": group.id,
        "name": group.name,
        "course_id": course_id,
        "position": group.position,
        "group_weight": getattr(group, 'group_weight', None),
        "assignments_count": getattr(group, 'assignments_count', 0),
        "rules": getattr(group, 'rules', None)
    }

def fetch_assignment_groups(course_id: int) -> List[dict]:
    """Fetch all assignment groups for a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    groups = []
    for group in course.get_assignment_groups():
        groups.append({
            "id": group.id,
            "name": group.name,
            "position": group.position,
            "group_weight": getattr(group, 'group_weight', None),
            "assignments_count": getattr(group, 'assignments_count', 0)
        })
    
    return groups

def update_assignment_group_helper(
    course_id: int,
    group_id: int,
    name: Optional[str] = None,
    position: Optional[int] = None,
    group_weight: Optional[float] = None
) -> dict:
    """Update an assignment group."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    group = course.get_assignment_group(group_id)
    
    group_params = {}
    if name:
        group_params["name"] = name
    if position is not None:
        group_params["position"] = position
    if group_weight is not None:
        group_params["group_weight"] = group_weight
    
    updated_group = group.edit(assignment_group=group_params)
    
    return {
        "id": updated_group.id,
        "name": updated_group.name,
        "course_id": course_id,
        "position": updated_group.position
    }

def delete_assignment_group_helper(course_id: int, group_id: int) -> dict:
    """Delete an assignment group."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    group = course.get_assignment_group(group_id)
    
    group_info = {
        "id": group.id,
        "name": group.name,
        "course_id": course_id
    }
    
    group.delete()
    
    return {
        "success": True,
        "deleted_group": group_info
    }

# -----------------------------
# ASSIGNMENT GROUPS - MCP Tools
# -----------------------------

@handle_canvas_errors
@mcp.tool()
def create_assignment_group(
    course_id: int,
    name: str,
    position: Optional[int] = None,
    group_weight: Optional[float] = None
) -> str:
    """Create a new assignment group in a Canvas course.
    
    Args:
        course_id: The ID of the course
        name: Group name (required)
        position: Group position/order
        group_weight: Weight of this group (for weighted grading)
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    group = create_assignment_group_helper(
        course_id=course_id,
        name=name,
        position=position,
        group_weight=group_weight
    )
    
    formatted = "✅ Assignment group created successfully!\n\n"
    formatted += f"Name: {group['name']}\n"
    formatted += f"Group ID: {group['id']}\n"
    formatted += f"Course ID: {group['course_id']}\n"
    formatted += f"Position: {group['position']}\n"
    if group.get('group_weight'):
        formatted += f"Group Weight: {group['group_weight']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def get_assignment_group(course_id: int, group_id: int) -> str:
    """Get a specific assignment group.
    
    Args:
        course_id: The ID of the course
        group_id: The ID of the assignment group
    """
    group = fetch_assignment_group(course_id, group_id)
    
    formatted = f"Assignment Group Details:\n\n"
    formatted += f"Name: {group['name']}\n"
    formatted += f"Group ID: {group['id']}\n"
    formatted += f"Course ID: {group['course_id']}\n"
    formatted += f"Position: {group['position']}\n"
    formatted += f"Assignments: {group['assignments_count']}\n"
    if group.get('group_weight'):
        formatted += f"Group Weight: {group['group_weight']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def list_assignment_groups(course_id: int) -> str:
    """List all assignment groups for a course.
    
    Args:
        course_id: The ID of the course
    """
    groups = fetch_assignment_groups(course_id)
    
    if not groups:
        return f"No assignment groups found for course {course_id}."
    
    formatted = f"Assignment Groups for Course {course_id}:\n\n"
    for i, group in enumerate(groups, 1):
        formatted += f"{i}. {group['name']}\n"
        formatted += f"   Group ID: {group['id']}\n"
        formatted += f"   Position: {group['position']}\n"
        formatted += f"   Assignments: {group['assignments_count']}\n"
        if group.get('group_weight'):
            formatted += f"   Weight: {group['group_weight']}\n"
        formatted += "\n"
    
    formatted += f"Total: {len(groups)} group(s)"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_assignment_group(
    course_id: int,
    group_id: int,
    name: Optional[str] = None,
    position: Optional[int] = None,
    group_weight: Optional[float] = None
) -> str:
    """Update an assignment group.
    
    Args:
        course_id: The ID of the course
        group_id: The ID of the assignment group
        name: New group name
        position: New position
        group_weight: New group weight
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        group = course.get_assignment_group(group_id)
        _ = group.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or assignment group not found. {error_msg}"
        return f"Error: {error_msg}"
    
    group = update_assignment_group_helper(
        course_id=course_id,
        group_id=group_id,
        name=name,
        position=position,
        group_weight=group_weight
    )
    
    formatted = "✅ Assignment group updated successfully!\n\n"
    formatted += f"Group ID: {group['id']}\n"
    formatted += f"Name: {group['name']}\n"
    formatted += f"Position: {group['position']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_assignment_group(course_id: int, group_id: int) -> str:
    """Delete an assignment group (assignments must be moved first).
    
    Args:
        course_id: The ID of the course
        group_id: The ID of the assignment group to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        group = course.get_assignment_group(group_id)
        _ = group.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or assignment group not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_assignment_group_helper(course_id, group_id)
    
    formatted = "✅ Assignment group deleted successfully!\n\n"
    formatted += f"Deleted Group: {result['deleted_group']['name']}\n"
    formatted += f"Group ID: {result['deleted_group']['id']}\n"
    formatted += f"Course ID: {result['deleted_group']['course_id']}\n"
    
    return formatted

# -----------------------------
# MISSING COURSE OPERATIONS
# -----------------------------

def fetch_course(course_id: int) -> dict:
    """Fetch a specific course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    return {
        "id": course.id,
        "name": course.name,
        "course_code": course.course_code,
        "start_at": course.start_at,
        "end_at": course.end_at,
        "workflow_state": course.workflow_state,
        "html_url": course.html_url,
        "enrollment_term_id": getattr(course, 'enrollment_term_id', None)
    }

def update_course_helper(
    course_id: int,
    name: Optional[str] = None,
    course_code: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None
) -> dict:
    """Update a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    course_params = {}
    if name:
        course_params["name"] = name
    if course_code:
        course_params["course_code"] = course_code
    if start_at:
        course_params["start_at"] = start_at
    if end_at:
        course_params["end_at"] = end_at
    
    updated_course = course.edit(course=course_params)
    
    return {
        "id": updated_course.id,
        "name": updated_course.name,
        "course_code": updated_course.course_code,
        "workflow_state": updated_course.workflow_state
    }

def delete_course_helper(course_id: int) -> dict:
    """Delete a course."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    
    course_info = {
        "id": course.id,
        "name": course.name,
        "course_code": course.course_code
    }
    
    course.delete()
    
    return {
        "success": True,
        "deleted_course": course_info
    }

@handle_canvas_errors
@mcp.tool()
def get_course(course_id: int) -> str:
    """Get a specific course.
    
    Args:
        course_id: The ID of the course
    """
    course = fetch_course(course_id)
    
    formatted = f"Course Details:\n\n"
    formatted += f"Name: {course['name']}\n"
    formatted += f"Course ID: {course['id']}\n"
    if course.get('course_code'):
        formatted += f"Course Code: {course['course_code']}\n"
    if course.get('start_at'):
        start_local = convert_utc_to_local(course['start_at'])
        formatted += f"Start Date: {format_datetime_local(start_local)}\n"
    if course.get('end_at'):
        end_local = convert_utc_to_local(course['end_at'])
        formatted += f"End Date: {format_datetime_local(end_local)}\n"
    formatted += f"State: {course['workflow_state']}\n"
    formatted += f"URL: {course['html_url']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_course(
    course_id: int,
    name: Optional[str] = None,
    course_code: Optional[str] = None,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None
) -> str:
    """Update a course.
    
    Args:
        course_id: The ID of the course
        name: New course name
        course_code: New course code
        start_at: New start date in ISO 8601 format
        end_at: New end date in ISO 8601 format
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    course = update_course_helper(
        course_id=course_id,
        name=name,
        course_code=course_code,
        start_at=start_at,
        end_at=end_at
    )
    
    formatted = "✅ Course updated successfully!\n\n"
    formatted += f"Course ID: {course['id']}\n"
    formatted += f"Name: {course['name']}\n"
    if course.get('course_code'):
        formatted += f"Course Code: {course['course_code']}\n"
    formatted += f"State: {course['workflow_state']}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def delete_course(course_id: int) -> str:
    """Delete a course.
    
    Args:
        course_id: The ID of the course to delete
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course not found. {error_msg}"
        return f"Error: {error_msg}"
    
    result = delete_course_helper(course_id)
    
    formatted = "✅ Course deleted successfully!\n\n"
    formatted += f"Deleted Course: {result['deleted_course']['name']}\n"
    formatted += f"Course ID: {result['deleted_course']['id']}\n"
    if result['deleted_course'].get('course_code'):
        formatted += f"Course Code: {result['deleted_course']['course_code']}\n"
    
    return formatted

# -----------------------------
# MISSING ASSIGNMENT OPERATIONS
# -----------------------------

def fetch_assignment(course_id: int, assignment_id: int) -> dict:
    """Fetch a specific assignment."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    
    return {
        "id": assignment.id,
        "name": assignment.name,
        "course_id": course_id,
        "description": assignment.description,
        "due_at": assignment.due_at,
        "points_possible": assignment.points_possible,
        "submission_types": assignment.submission_types,
        "published": assignment.published,
        "html_url": assignment.html_url,
        "assignment_group_id": getattr(assignment, 'assignment_group_id', None)
    }

def update_assignment_helper(
    course_id: int,
    assignment_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    due_at: Optional[str] = None,
    points_possible: Optional[float] = None,
    published: Optional[bool] = None
) -> dict:
    """Update an assignment."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    assignment = course.get_assignment(assignment_id)
    
    assignment_params = {}
    if name:
        assignment_params["name"] = name
    if description is not None:
        assignment_params["description"] = description
    if due_at:
        assignment_params["due_at"] = due_at
    if points_possible is not None:
        assignment_params["points_possible"] = points_possible
    if published is not None:
        assignment_params["published"] = published
    
    updated_assignment = assignment.edit(assignment=assignment_params)
    
    return {
        "id": updated_assignment.id,
        "name": updated_assignment.name,
        "course_id": course_id,
        "published": updated_assignment.published,
        "html_url": updated_assignment.html_url
    }

@handle_canvas_errors
@mcp.tool()
def get_assignment(course_id: int, assignment_id: int) -> str:
    """Get a specific assignment.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
    """
    assignment = fetch_assignment(course_id, assignment_id)
    
    formatted = f"Assignment Details:\n\n"
    formatted += f"Name: {assignment['name']}\n"
    formatted += f"Assignment ID: {assignment['id']}\n"
    formatted += f"Course ID: {assignment['course_id']}\n"
    
    if assignment.get('points_possible'):
        formatted += f"Points: {assignment['points_possible']}\n"
    
    if assignment.get('due_at'):
        due_local = convert_utc_to_local(assignment['due_at'])
        formatted += f"Due Date: {format_datetime_local(due_local)}\n"
    
    if assignment.get('submission_types'):
        formatted += f"Submission Types: {', '.join(assignment['submission_types'])}\n"
    
    formatted += f"Published: {assignment['published']}\n"
    formatted += f"URL: {assignment['html_url']}\n"
    
    if assignment.get('description'):
        desc_preview = assignment['description'][:200] + "..." if len(assignment.get('description', '')) > 200 else assignment['description']
        formatted += f"\nDescription: {desc_preview}\n"
    
    return formatted

@handle_canvas_errors
@mcp.tool()
def update_assignment(
    course_id: int,
    assignment_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    due_at: Optional[str] = None,
    points_possible: Optional[float] = None,
    published: Optional[bool] = None
) -> str:
    """Update an assignment.
    
    Args:
        course_id: The ID of the course
        assignment_id: The ID of the assignment
        name: New assignment name
        description: New assignment description
        due_at: New due date in ISO 8601 format
        points_possible: New maximum points
        published: Whether to publish/unpublish
    """
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        _ = assignment.name
    except CanvasException as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f"Error: Course or assignment not found. {error_msg}"
        return f"Error: {error_msg}"
    
    assignment = update_assignment_helper(
        course_id=course_id,
        assignment_id=assignment_id,
        name=name,
        description=description,
        due_at=due_at,
        points_possible=points_possible,
        published=published
    )
    
    formatted = "✅ Assignment updated successfully!\n\n"
    formatted += f"Assignment ID: {assignment['id']}\n"
    formatted += f"Name: {assignment['name']}\n"
    formatted += f"Published: {assignment['published']}\n"
    formatted += f"URL: {assignment['html_url']}\n"
    
    return formatted

# NOTE: Remaining operations (~25 more): Rubrics (4), Outcomes (4), Enrollments (4), 
# Users (4), Groups (4), Sections (4), Collaborations (4), Calendar Events (4)
# The pattern is well-established. Due to file size, these can be added incrementally
# following the same pattern as above.

# -----------------------------
# MCP SERVER ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    mcp.run()
