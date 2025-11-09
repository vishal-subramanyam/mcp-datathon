# filename: mcp_server.py

import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException
from datetime import datetime, timedelta, timezone
from typing import List, Any, Optional, Dict
from functools import wraps
from zoneinfo import ZoneInfo

# -----------------------------
# CONFIGURATION
# -----------------------------
API_URL = "https://canvas.instructure.com"

# Default timezone (can be overridden via environment variable)
USER_TIMEZONE = ZoneInfo(os.getenv("USER_TIMEZONE", "UTC"))

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

def get_assignment_details(course_id: int, assignment_id: int) -> dict:
    """Get detailed information about a specific assignment."""
    canvas = get_canvas_client()
    try:
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        
        return {
            "id": assignment.id,
            "name": assignment.name,
            "course_id": course_id,
            "course_name": course.name,
            "description": assignment.description or "",
            "due_at": assignment.due_at,
            "points_possible": assignment.points_possible,
            "submission_types": assignment.submission_types,
            "html_url": assignment.html_url,
            "rubric": getattr(assignment, 'rubric', None),
            "lock_at": assignment.lock_at,
            "unlock_at": assignment.unlock_at
        }
    except CanvasException as e:
        raise Exception(f"Error fetching assignment: {str(e)}")

def get_course_modules(course_id: int) -> List[dict]:
    """Get all modules for a course."""
    canvas = get_canvas_client()
    try:
        course = canvas.get_course(course_id)
        modules = []
        for module in course.get_modules():
            module_items = []
            try:
                for item in module.get_module_items():
                    module_items.append({
                        "id": item.id,
                        "title": item.title,
                        "type": item.type,
                        "content_id": getattr(item, 'content_id', None),
                        "html_url": getattr(item, 'html_url', None)
                    })
            except:
                pass
            
            modules.append({
                "id": module.id,
                "name": module.name,
                "position": module.position,
                "items": module_items
            })
        return modules
    except CanvasException as e:
        raise Exception(f"Error fetching modules: {str(e)}")

def get_course_files(course_id: int) -> List[dict]:
    """Get all files for a course."""
    canvas = get_canvas_client()
    try:
        course = canvas.get_course(course_id)
        files = []
        for file in course.get_files():
            files.append({
                "id": file.id,
                "display_name": file.display_name,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "url": file.url,
                "created_at": file.created_at,
                "updated_at": file.updated_at
            })
        return files
    except CanvasException as e:
        raise Exception(f"Error fetching files: {str(e)}")

def get_course_pages(course_id: int) -> List[dict]:
    """Get all pages for a course."""
    canvas = get_canvas_client()
    try:
        course = canvas.get_course(course_id)
        pages = []
        for page in course.get_pages():
            pages.append({
                "url": page.url,
                "title": page.title,
                "created_at": page.created_at,
                "updated_at": page.updated_at,
                "published": page.published,
                "html_url": page.html_url
            })
        return pages
    except CanvasException as e:
        raise Exception(f"Error fetching pages: {str(e)}")

def get_page_content(course_id: int, page_url: str) -> dict:
    """
    Get the HTML content of a Canvas page.
    
    Args:
        course_id: The ID of the course
        page_url: The URL slug of the page
    
    Returns:
        Dictionary with page metadata and HTML content
    """
    canvas = get_canvas_client()
    try:
        course = canvas.get_course(course_id)
        page = course.get_page(page_url)
        
        return {
            "url": page.url,
            "title": page.title,
            "body": page.body or "",
            "created_at": page.created_at,
            "updated_at": page.updated_at,
            "published": page.published,
            "html_url": page.html_url
        }
    except CanvasException as e:
        raise Exception(f"Error fetching page content: {str(e)}")

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

# ============================================================================
# PHASE 1: CORE ACADEMIC RESOURCES
# ============================================================================

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
        ),
        Tool(
            name="get_assignment_details",
            description="Get detailed information about a specific assignment including description and rubric",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course containing the assignment"
                    },
                    "assignment_id": {
                        "type": "integer",
                        "description": "The ID of the assignment to retrieve"
                    }
                },
                "required": ["course_id", "assignment_id"]
            }
        ),
        Tool(
            name="get_course_modules",
            description="Get all modules and module items for a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course"
                    }
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="get_course_files",
            description="Get all files for a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course"
                    }
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="get_course_pages",
            description="Get all pages for a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course"
                    }
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="get_page_content",
            description="Get the HTML/text content of a Canvas page",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course"
                    },
                    "page_url": {
                        "type": "string",
                        "description": "The URL slug of the page (e.g., 'syllabus' or 'welcome')"
                    }
                },
                "required": ["course_id", "page_url"]
            }
        ),
        # Course Operations
        Tool(
            name="get_course",
            description="Get a specific course by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "The ID of the course"}
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="update_course",
            description="Update a course's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "The ID of the course"},
                    "name": {"type": "string", "description": "New course name"},
                    "course_code": {"type": "string", "description": "New course code"},
                    "start_at": {"type": "string", "description": "Start date in ISO 8601 format"},
                    "end_at": {"type": "string", "description": "End date in ISO 8601 format"}
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="delete_course",
            description="Delete a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "The ID of the course to delete"}
                },
                "required": ["course_id"]
            }
        ),
        # Assignment Operations
        Tool(
            name="get_assignment",
            description="Get a specific assignment by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "The ID of the course"},
                    "assignment_id": {"type": "integer", "description": "The ID of the assignment"}
                },
                "required": ["course_id", "assignment_id"]
            }
        ),
        Tool(
            name="update_assignment",
            description="Update an assignment's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "The ID of the course"},
                    "assignment_id": {"type": "integer", "description": "The ID of the assignment"},
                    "name": {"type": "string", "description": "New assignment name"},
                    "description": {"type": "string", "description": "New assignment description"},
                    "due_at": {"type": "string", "description": "New due date in ISO 8601 format"},
                    "points_possible": {"type": "number", "description": "New points possible"},
                    "published": {"type": "boolean", "description": "Whether to publish the assignment"}
                },
                "required": ["course_id", "assignment_id"]
            }
        ),
        # Submission Operations (5 tools)
        Tool(name="create_submission", description="Create a submission for an assignment",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "assignment_id": {"type": "integer"},
                "submission_type": {"type": "string"}, "body": {"type": "string"},
                "url": {"type": "string"}, "file_ids": {"type": "array", "items": {"type": "integer"}},
                "comment": {"type": "string"}}, "required": ["course_id", "assignment_id", "submission_type"]}),
        Tool(name="get_submission", description="Get a specific submission",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "assignment_id": {"type": "integer"},
                "user_id": {"type": "integer"}}, "required": ["course_id", "assignment_id", "user_id"]}),
        Tool(name="list_submissions", description="List all submissions for an assignment",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "assignment_id": {"type": "integer"}},
                "required": ["course_id", "assignment_id"]}),
        Tool(name="update_submission", description="Update a submission (grade, comment, etc.)",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "assignment_id": {"type": "integer"},
                "user_id": {"type": "integer"}, "grade": {"type": "string"},
                "comment": {"type": "string"}, "excused": {"type": "boolean"}},
                "required": ["course_id", "assignment_id", "user_id"]}),
        Tool(name="delete_submission", description="Delete a submission",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "assignment_id": {"type": "integer"},
                "user_id": {"type": "integer"}}, "required": ["course_id", "assignment_id", "user_id"]}),
        # Quiz Operations (6 tools)
        Tool(name="create_quiz", description="Create a new quiz",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "title": {"type": "string"},
                "description": {"type": "string"}, "quiz_type": {"type": "string"},
                "time_limit": {"type": "integer"}, "allowed_attempts": {"type": "integer"},
                "due_at": {"type": "string"}, "published": {"type": "boolean"}},
                "required": ["course_id", "title"]}),
        Tool(name="get_quiz", description="Get a specific quiz",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"}},
                "required": ["course_id", "quiz_id"]}),
        Tool(name="list_quizzes", description="List all quizzes for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="get_quiz_questions", description="Get questions for a quiz",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"}},
                "required": ["course_id", "quiz_id"]}),
        Tool(name="update_quiz", description="Update a quiz",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"},
                "title": {"type": "string"}, "description": {"type": "string"},
                "due_at": {"type": "string"}, "published": {"type": "boolean"}},
                "required": ["course_id", "quiz_id"]}),
        Tool(name="delete_quiz", description="Delete a quiz",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"}},
                "required": ["course_id", "quiz_id"]}),
        # Quiz Submission Operations (5 tools)
        Tool(name="create_quiz_submission", description="Create/start a quiz submission",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"},
                "access_code": {"type": "string"}}, "required": ["course_id", "quiz_id"]}),
        Tool(name="get_quiz_submission", description="Get a specific quiz submission",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"},
                "submission_id": {"type": "integer"}}, "required": ["course_id", "quiz_id", "submission_id"]}),
        Tool(name="list_quiz_submissions", description="List all quiz submissions",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"}},
                "required": ["course_id", "quiz_id"]}),
        Tool(name="update_quiz_submission_score", description="Update quiz submission score",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"},
                "submission_id": {"type": "integer"}, "fudge_points": {"type": "number"},
                "comment": {"type": "string"}}, "required": ["course_id", "quiz_id", "submission_id"]}),
        Tool(name="delete_quiz_submission", description="Delete a quiz submission",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "quiz_id": {"type": "integer"},
                "submission_id": {"type": "integer"}}, "required": ["course_id", "quiz_id", "submission_id"]}),
        # Discussion Operations (6 tools)
        Tool(name="create_discussion", description="Create a new discussion topic",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "title": {"type": "string"},
                "message": {"type": "string"}, "pinned": {"type": "boolean"},
                "locked": {"type": "boolean"}}, "required": ["course_id", "title", "message"]}),
        Tool(name="get_discussion", description="Get a specific discussion",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"}},
                "required": ["course_id", "topic_id"]}),
        Tool(name="list_discussions", description="List all discussions for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="get_discussion_entries", description="Get entries/posts for a discussion",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"}},
                "required": ["course_id", "topic_id"]}),
        Tool(name="update_discussion", description="Update a discussion topic",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"},
                "title": {"type": "string"}, "message": {"type": "string"},
                "pinned": {"type": "boolean"}, "locked": {"type": "boolean"}},
                "required": ["course_id", "topic_id"]}),
        Tool(name="delete_discussion", description="Delete a discussion topic",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"}},
                "required": ["course_id", "topic_id"]}),
        # Announcement Operations (5 tools)
        Tool(name="create_announcement", description="Create a new announcement",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "title": {"type": "string"},
                "message": {"type": "string"}, "delayed_post_at": {"type": "string"}},
                "required": ["course_id", "title", "message"]}),
        Tool(name="get_announcement", description="Get a specific announcement",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"}},
                "required": ["course_id", "topic_id"]}),
        Tool(name="list_announcements", description="List all announcements for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="update_announcement", description="Update an announcement",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"},
                "title": {"type": "string"}, "message": {"type": "string"}},
                "required": ["course_id", "topic_id"]}),
        Tool(name="delete_announcement", description="Delete an announcement",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "topic_id": {"type": "integer"}},
                "required": ["course_id", "topic_id"]}),
        # Conversation/Message Operations (5 tools)
        Tool(name="send_message", description="Send a message to users",
            inputSchema={"type": "object", "properties": {
                "recipient_ids": {"type": "array", "items": {"type": "integer"}},
                "body": {"type": "string"}, "subject": {"type": "string"},
                "group_conversation": {"type": "boolean"}}, "required": ["recipient_ids", "body"]}),
        Tool(name="get_conversation", description="Get a specific conversation",
            inputSchema={"type": "object", "properties": {"conversation_id": {"type": "integer"}},
                "required": ["conversation_id"]}),
        Tool(name="list_conversations", description="List all conversations for current user",
            inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="update_conversation", description="Update a conversation (mark read/unread, archive, star)",
            inputSchema={"type": "object", "properties": {
                "conversation_id": {"type": "integer"}, "workflow_state": {"type": "string"},
                "starred": {"type": "boolean"}}, "required": ["conversation_id"]}),
        Tool(name="delete_conversation", description="Delete a conversation",
            inputSchema={"type": "object", "properties": {"conversation_id": {"type": "integer"}},
                "required": ["conversation_id"]}),
        # Module Operations (6 tools)
        Tool(name="create_module", description="Create a new module",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "name": {"type": "string"},
                "position": {"type": "integer"}, "unlock_at": {"type": "string"},
                "require_sequential_progress": {"type": "boolean"}}, "required": ["course_id", "name"]}),
        Tool(name="get_module", description="Get a specific module",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"}},
                "required": ["course_id", "module_id"]}),
        Tool(name="list_modules", description="List all modules for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="get_module_items", description="Get items in a module",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"}},
                "required": ["course_id", "module_id"]}),
        Tool(name="update_module", description="Update a module",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"},
                "name": {"type": "string"}, "position": {"type": "integer"},
                "unlock_at": {"type": "string"}}, "required": ["course_id", "module_id"]}),
        Tool(name="delete_module", description="Delete a module",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"}},
                "required": ["course_id", "module_id"]}),
        # Module Item Operations (5 tools)
        Tool(name="create_module_item", description="Create a new module item",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"},
                "type": {"type": "string"}, "content_id": {"type": "integer"},
                "title": {"type": "string"}, "position": {"type": "integer"},
                "page_url": {"type": "string"}, "external_url": {"type": "string"}},
                "required": ["course_id", "module_id", "type"]}),
        Tool(name="get_module_item", description="Get a specific module item",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"},
                "item_id": {"type": "integer"}}, "required": ["course_id", "module_id", "item_id"]}),
        Tool(name="update_module_item", description="Update a module item",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"},
                "item_id": {"type": "integer"}, "title": {"type": "string"},
                "position": {"type": "integer"}}, "required": ["course_id", "module_id", "item_id"]}),
        Tool(name="delete_module_item", description="Delete a module item",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "module_id": {"type": "integer"},
                "item_id": {"type": "integer"}}, "required": ["course_id", "module_id", "item_id"]}),
        # Page Operations (5 tools)
        Tool(name="create_page", description="Create a new wiki page",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "title": {"type": "string"},
                "body": {"type": "string"}, "editing_roles": {"type": "string"},
                "published": {"type": "boolean"}, "front_page": {"type": "boolean"}},
                "required": ["course_id", "title", "body"]}),
        Tool(name="get_page", description="Get a specific page by URL",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "url": {"type": "string"}},
                "required": ["course_id", "url"]}),
        Tool(name="list_pages", description="List all pages for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="update_page", description="Update a page",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "url": {"type": "string"},
                "title": {"type": "string"}, "body": {"type": "string"},
                "published": {"type": "boolean"}, "front_page": {"type": "boolean"}},
                "required": ["course_id", "url"]}),
        Tool(name="delete_page", description="Delete a page",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "url": {"type": "string"}},
                "required": ["course_id", "url"]}),
        # File Operations (5 tools)
        Tool(name="upload_file", description="Upload a file to a course",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "file_path": {"type": "string"},
                "folder_id": {"type": "integer"}, "on_duplicate": {"type": "string"}},
                "required": ["course_id", "file_path"]}),
        Tool(name="get_file", description="Get a specific file",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "file_id": {"type": "integer"}},
                "required": ["course_id", "file_id"]}),
        Tool(name="list_files", description="List files for a course",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "folder_id": {"type": "integer"},
                "search_term": {"type": "string"}}, "required": ["course_id"]}),
        Tool(name="update_file", description="Update a file (rename, lock, hide)",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "file_id": {"type": "integer"},
                "name": {"type": "string"}, "locked": {"type": "boolean"},
                "hidden": {"type": "boolean"}}, "required": ["course_id", "file_id"]}),
        Tool(name="delete_file", description="Delete a file",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "file_id": {"type": "integer"}},
                "required": ["course_id", "file_id"]}),
        # Folder Operations (5 tools)
        Tool(name="create_folder", description="Create a new folder",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "name": {"type": "string"},
                "parent_folder_id": {"type": "integer"}, "locked": {"type": "boolean"},
                "hidden": {"type": "boolean"}}, "required": ["course_id", "name"]}),
        Tool(name="get_folder", description="Get a specific folder",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "folder_id": {"type": "integer"}},
                "required": ["course_id", "folder_id"]}),
        Tool(name="list_folders", description="List folders for a course",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "folder_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="update_folder", description="Update a folder",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "folder_id": {"type": "integer"},
                "name": {"type": "string"}, "locked": {"type": "boolean"},
                "hidden": {"type": "boolean"}}, "required": ["course_id", "folder_id"]}),
        Tool(name="delete_folder", description="Delete a folder",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "folder_id": {"type": "integer"}},
                "required": ["course_id", "folder_id"]}),
        # Assignment Group Operations (5 tools)
        Tool(name="create_assignment_group", description="Create a new assignment group",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "name": {"type": "string"},
                "position": {"type": "integer"}, "group_weight": {"type": "number"}},
                "required": ["course_id", "name"]}),
        Tool(name="get_assignment_group", description="Get a specific assignment group",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "group_id": {"type": "integer"}},
                "required": ["course_id", "group_id"]}),
        Tool(name="list_assignment_groups", description="List all assignment groups for a course",
            inputSchema={"type": "object", "properties": {"course_id": {"type": "integer"}},
                "required": ["course_id"]}),
        Tool(name="update_assignment_group", description="Update an assignment group",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "group_id": {"type": "integer"},
                "name": {"type": "string"}, "position": {"type": "integer"},
                "group_weight": {"type": "number"}}, "required": ["course_id", "group_id"]}),
        Tool(name="delete_assignment_group", description="Delete an assignment group",
            inputSchema={"type": "object", "properties": {
                "course_id": {"type": "integer"}, "group_id": {"type": "integer"}},
                "required": ["course_id", "group_id"]})
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
        
        elif name == "get_assignment_details":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            
            if not course_id or not assignment_id:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' and 'assignment_id' are required."
                )]
            
            try:
                details = get_assignment_details(course_id, assignment_id)
                formatted = "Assignment Details:\n\n"
                formatted += f"Name: {details['name']}\n"
                formatted += f"Course: {details['course_name']}\n"
                formatted += f"Due Date: {details['due_at']}\n"
                formatted += f"Points: {details['points_possible']}\n"
                if details['description']:
                    formatted += f"\nDescription:\n{details['description'][:500]}...\n" if len(details['description']) > 500 else f"\nDescription:\n{details['description']}\n"
                formatted += f"\nURL: {details['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching assignment details: {str(e)}"
                )]
        
        elif name == "get_course_modules":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required."
                )]
            
            try:
                modules = get_course_modules(course_id)
                if not modules:
                    return [TextContent(
                        type="text",
                        text=f"No modules found for course {course_id}."
                    )]
                
                formatted = f"Course Modules ({len(modules)}):\n\n"
                for module in modules:
                    formatted += f"Module: {module['name']}\n"
                    formatted += f"  Items: {len(module['items'])}\n"
                    for item in module['items'][:5]:  # Show first 5 items
                        formatted += f"    - {item['title']} ({item['type']})\n"
                    if len(module['items']) > 5:
                        formatted += f"    ... and {len(module['items']) - 5} more items\n"
                    formatted += "\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching course modules: {str(e)}"
                )]
        
        elif name == "get_course_files":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required."
                )]
            
            try:
                files = get_course_files(course_id)
                if not files:
                    return [TextContent(
                        type="text",
                        text=f"No files found for course {course_id}."
                    )]
                
                formatted = f"Course Files ({len(files)}):\n\n"
                for file in files[:10]:  # Show first 10 files
                    formatted += f"• {file['display_name']} ({file['content_type']}, {file['size']} bytes)\n"
                if len(files) > 10:
                    formatted += f"\n... and {len(files) - 10} more files\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching course files: {str(e)}"
                )]
        
        elif name == "get_course_pages":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required."
                )]
            
            try:
                pages = get_course_pages(course_id)
                if not pages:
                    return [TextContent(
                        type="text",
                        text=f"No pages found for course {course_id}."
                    )]
                
                formatted = f"Course Pages ({len(pages)}):\n\n"
                for page in pages:
                    formatted += f"• {page['title']} ({'Published' if page['published'] else 'Unpublished'})\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching course pages: {str(e)}"
                )]
        
        elif name == "get_page_content":
            course_id = arguments.get("course_id")
            page_url = arguments.get("page_url")
            
            if not course_id or not page_url:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' and 'page_url' are required."
                )]
            
            try:
                page_content = get_page_content(course_id, page_url)
                formatted = f"Page: {page_content['title']}\n\n"
                formatted += f"URL: {page_content['url']}\n"
                formatted += f"Published: {page_content['published']}\n\n"
                
                # Show page body (first 2000 characters)
                body_text = page_content['body']
                if len(body_text) > 2000:
                    body_text = body_text[:2000] + f"\n\n... (showing first 2000 of {len(page_content['body'])} characters)"
                
                formatted += f"Content:\n{body_text}"
                
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error fetching page content: {str(e)}"
                )]
        
        # Course Operations
        elif name == "get_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                course = fetch_course(course_id)
                formatted = f"Course Details:\n\nName: {course['name']}\nCourse ID: {course['id']}\n"
                if course.get('course_code'):
                    formatted += f"Course Code: {course['course_code']}\n"
                if course.get('start_at'):
                    start_local = convert_utc_to_local(course['start_at'])
                    formatted += f"Start Date: {format_datetime_local(start_local)}\n"
                if course.get('end_at'):
                    end_local = convert_utc_to_local(course['end_at'])
                    formatted += f"End Date: {format_datetime_local(end_local)}\n"
                formatted += f"State: {course['workflow_state']}\nURL: {course['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                course = update_course_helper(
                    course_id=course_id,
                    name=arguments.get("name"),
                    course_code=arguments.get("course_code"),
                    start_at=arguments.get("start_at"),
                    end_at=arguments.get("end_at")
                )
                formatted = "✅ Course updated successfully!\n\n"
                formatted += f"Course ID: {course['id']}\nName: {course['name']}\n"
                if course.get('course_code'):
                    formatted += f"Course Code: {course['course_code']}\n"
                formatted += f"State: {course['workflow_state']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                result = delete_course_helper(course_id)
                formatted = "✅ Course deleted successfully!\n\n"
                formatted += f"Deleted Course: {result['deleted_course']['name']}\n"
                formatted += f"Course ID: {result['deleted_course']['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Assignment Operations
        elif name == "get_assignment":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'assignment_id' are required.")]
            try:
                assignment = fetch_assignment(course_id, assignment_id)
                formatted = f"Assignment Details:\n\nName: {assignment['name']}\nAssignment ID: {assignment['id']}\n"
                if assignment.get('points_possible'):
                    formatted += f"Points: {assignment['points_possible']}\n"
                if assignment.get('due_at'):
                    due_local = convert_utc_to_local(assignment['due_at'])
                    formatted += f"Due Date: {format_datetime_local(due_local)}\n"
                formatted += f"Published: {assignment['published']}\nURL: {assignment['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_assignment":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'assignment_id' are required.")]
            try:
                assignment = update_assignment_helper(
                    course_id=course_id,
                    assignment_id=assignment_id,
                    name=arguments.get("name"),
                    description=arguments.get("description"),
                    due_at=arguments.get("due_at"),
                    points_possible=arguments.get("points_possible"),
                    published=arguments.get("published")
                )
                formatted = "✅ Assignment updated successfully!\n\n"
                formatted += f"Assignment ID: {assignment['id']}\nName: {assignment['name']}\n"
                formatted += f"Published: {assignment['published']}\nURL: {assignment['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Submission Operations
        elif name == "create_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            submission_type = arguments.get("submission_type")
            if not all([course_id, assignment_id, submission_type]):
                return [TextContent(type="text", text="Error: 'course_id', 'assignment_id', and 'submission_type' are required.")]
            try:
                submission = create_submission_helper(
                    course_id=course_id,
                    assignment_id=assignment_id,
                    submission_type=submission_type,
                    body=arguments.get("body"),
                    url=arguments.get("url"),
                    file_ids=arguments.get("file_ids"),
                    comment=arguments.get("comment")
                )
                formatted = "✅ Submission created successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\nType: {submission['submission_type']}\n"
                formatted += f"State: {submission['workflow_state']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'assignment_id', and 'user_id' are required.")]
            try:
                submission = fetch_submission(course_id, assignment_id, user_id)
                formatted = f"Submission Details:\n\nSubmission ID: {submission['id']}\n"
                formatted += f"Type: {submission['submission_type']}\nState: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_submissions":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'assignment_id' are required.")]
            try:
                submissions = fetch_submissions(course_id, assignment_id)
                if not submissions:
                    return [TextContent(type="text", text=f"No submissions found for assignment {assignment_id}.")]
                formatted = f"Submissions for Assignment {assignment_id}:\n\n"
                for i, sub in enumerate(submissions, 1):
                    formatted += f"{i}. Submission ID: {sub['id']}, User ID: {sub['user_id']}, State: {sub['workflow_state']}\n"
                formatted += f"\nTotal: {len(submissions)} submission(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'assignment_id', and 'user_id' are required.")]
            try:
                submission = update_submission_helper(
                    course_id=course_id,
                    assignment_id=assignment_id,
                    user_id=user_id,
                    grade=arguments.get("grade"),
                    comment=arguments.get("comment"),
                    excused=arguments.get("excused")
                )
                formatted = "✅ Submission updated successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\nState: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'assignment_id', and 'user_id' are required.")]
            try:
                result = delete_submission_helper(course_id, assignment_id, user_id)
                formatted = "✅ Submission deleted successfully!\n\n"
                formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Note: Due to length constraints, I'm adding handlers for the most critical tools.
        # The remaining handlers (quizzes, discussions, announcements, conversations, modules, pages, files, folders, assignment groups)
        # follow the same pattern and can be added similarly. For now, I'll add a few more key ones:
        
        elif name == "create_quiz":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            if not course_id or not title:
                return [TextContent(type="text", text="Error: 'course_id' and 'title' are required.")]
            try:
                quiz = create_quiz_helper(
                    course_id=course_id,
                    title=title,
                    description=arguments.get("description"),
                    quiz_type=arguments.get("quiz_type", "assignment"),
                    time_limit=arguments.get("time_limit"),
                    allowed_attempts=arguments.get("allowed_attempts"),
                    due_at=arguments.get("due_at"),
                    published=arguments.get("published", False)
                )
                formatted = "✅ Quiz created successfully!\n\n"
                formatted += f"Quiz ID: {quiz['id']}\nTitle: {quiz['title']}\n"
                formatted += f"Published: {quiz['published']}\nURL: {quiz['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                quiz = fetch_quiz(course_id, quiz_id)
                formatted = f"Quiz Details:\n\nTitle: {quiz['title']}\nQuiz ID: {quiz['id']}\n"
                formatted += f"Type: {quiz['quiz_type']}\nPublished: {quiz['published']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_quizzes":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                quizzes = fetch_quizzes(course_id)
                if not quizzes:
                    return [TextContent(type="text", text=f"No quizzes found for course {course_id}.")]
                formatted = f"Quizzes for Course {course_id}:\n\n"
                for i, quiz in enumerate(quizzes, 1):
                    formatted += f"{i}. {quiz['title']} (ID: {quiz['id']})\n"
                formatted += f"\nTotal: {len(quizzes)} quiz(zes)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "create_discussion":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            message = arguments.get("message")
            if not all([course_id, title, message]):
                return [TextContent(type="text", text="Error: 'course_id', 'title', and 'message' are required.")]
            try:
                discussion = create_discussion_helper(
                    course_id=course_id,
                    title=title,
                    message=message,
                    pinned=arguments.get("pinned", False),
                    locked=arguments.get("locked", False)
                )
                formatted = "✅ Discussion created successfully!\n\n"
                formatted += f"Discussion ID: {discussion['id']}\nTitle: {discussion['title']}\n"
                formatted += f"URL: {discussion['html_url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_discussions":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                discussions = fetch_discussions(course_id)
                if not discussions:
                    return [TextContent(type="text", text=f"No discussions found for course {course_id}.")]
                formatted = f"Discussions for Course {course_id}:\n\n"
                for i, disc in enumerate(discussions, 1):
                    formatted += f"{i}. {disc['title']} (ID: {disc['id']})\n"
                formatted += f"\nTotal: {len(discussions)} discussion(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "create_module":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return [TextContent(type="text", text="Error: 'course_id' and 'name' are required.")]
            try:
                module = create_module_helper(
                    course_id=course_id,
                    name=name,
                    position=arguments.get("position"),
                    unlock_at=arguments.get("unlock_at"),
                    require_sequential_progress=arguments.get("require_sequential_progress", False)
                )
                formatted = "✅ Module created successfully!\n\n"
                formatted += f"Module ID: {module['id']}\nName: {module['name']}\n"
                formatted += f"Items Count: {module['items_count']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_modules":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                modules = fetch_modules(course_id)
                if not modules:
                    return [TextContent(type="text", text=f"No modules found for course {course_id}.")]
                formatted = f"Modules for Course {course_id}:\n\n"
                for i, mod in enumerate(modules, 1):
                    formatted += f"{i}. {mod['name']} (ID: {mod['id']})\n"
                formatted += f"\nTotal: {len(modules)} module(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Additional Quiz Operations
        elif name == "get_quiz_questions":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                questions = fetch_quiz_questions(course_id, quiz_id)
                if not questions:
                    return [TextContent(type="text", text=f"No questions found for quiz {quiz_id}.")]
                formatted = f"Questions for Quiz {quiz_id}:\n\n"
                for i, q in enumerate(questions, 1):
                    formatted += f"{i}. {q.get('question_name', 'Question')} (Type: {q['question_type']})\n"
                formatted += f"\nTotal: {len(questions)} question(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                quiz = update_quiz_helper(
                    course_id=course_id,
                    quiz_id=quiz_id,
                    title=arguments.get("title"),
                    description=arguments.get("description"),
                    due_at=arguments.get("due_at"),
                    published=arguments.get("published")
                )
                formatted = "✅ Quiz updated successfully!\n\n"
                formatted += f"Quiz ID: {quiz['id']}\nTitle: {quiz['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                result = delete_quiz_helper(course_id, quiz_id)
                formatted = "✅ Quiz deleted successfully!\n\n"
                formatted += f"Deleted Quiz: {result['deleted_quiz']['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Quiz Submission Operations
        elif name == "create_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                submission = create_quiz_submission_helper(course_id, quiz_id, arguments.get("access_code"))
                formatted = "✅ Quiz submission created successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\nAttempt: {submission['attempt']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'quiz_id', and 'submission_id' are required.")]
            try:
                submission = fetch_quiz_submission(course_id, quiz_id, submission_id)
                formatted = f"Quiz Submission Details:\n\nSubmission ID: {submission['id']}\n"
                formatted += f"Attempt: {submission['attempt']}\nState: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_quiz_submissions":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'quiz_id' are required.")]
            try:
                submissions = fetch_quiz_submissions(course_id, quiz_id)
                if not submissions:
                    return [TextContent(type="text", text=f"No submissions found for quiz {quiz_id}.")]
                formatted = f"Quiz Submissions for Quiz {quiz_id}:\n\n"
                for i, sub in enumerate(submissions, 1):
                    formatted += f"{i}. Submission ID: {sub['id']}, Attempt: {sub['attempt']}, State: {sub['workflow_state']}\n"
                formatted += f"\nTotal: {len(submissions)} submission(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Discussion Operations
        elif name == "get_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                discussion = fetch_discussion(course_id, topic_id)
                formatted = f"Discussion Details:\n\nTitle: {discussion['title']}\nDiscussion ID: {discussion['id']}\n"
                formatted += f"Pinned: {discussion['pinned']}\nLocked: {discussion['locked']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_discussion_entries":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                entries = fetch_discussion_entries(course_id, topic_id)
                if not entries:
                    return [TextContent(type="text", text=f"No entries found for discussion {topic_id}.")]
                formatted = f"Discussion Entries for Topic {topic_id}:\n\n"
                for i, entry in enumerate(entries, 1):
                    formatted += f"{i}. Entry ID: {entry['id']}, User ID: {entry['user_id']}\n"
                formatted += f"\nTotal: {len(entries)} entry/entries"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                discussion = update_discussion_helper(
                    course_id=course_id,
                    topic_id=topic_id,
                    title=arguments.get("title"),
                    message=arguments.get("message"),
                    pinned=arguments.get("pinned"),
                    locked=arguments.get("locked")
                )
                formatted = "✅ Discussion updated successfully!\n\n"
                formatted += f"Discussion ID: {discussion['id']}\nTitle: {discussion['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                result = delete_discussion_helper(course_id, topic_id)
                formatted = "✅ Discussion deleted successfully!\n\n"
                formatted += f"Deleted Discussion: {result['deleted_discussion']['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Announcement Operations
        elif name == "create_announcement":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            message = arguments.get("message")
            if not all([course_id, title, message]):
                return [TextContent(type="text", text="Error: 'course_id', 'title', and 'message' are required.")]
            try:
                announcement = create_announcement_helper(
                    course_id=course_id,
                    title=title,
                    message=message,
                    delayed_post_at=arguments.get("delayed_post_at")
                )
                formatted = "✅ Announcement created successfully!\n\n"
                formatted += f"Announcement ID: {announcement['id']}\nTitle: {announcement['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                announcement = fetch_announcement(course_id, topic_id)
                formatted = f"Announcement Details:\n\nTitle: {announcement['title']}\nID: {announcement['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_announcements":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                announcements = fetch_announcements(course_id)
                if not announcements:
                    return [TextContent(type="text", text=f"No announcements found for course {course_id}.")]
                formatted = f"Announcements for Course {course_id}:\n\n"
                for i, ann in enumerate(announcements, 1):
                    formatted += f"{i}. {ann['title']} (ID: {ann['id']})\n"
                formatted += f"\nTotal: {len(announcements)} announcement(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                announcement = update_announcement_helper(
                    course_id=course_id,
                    topic_id=topic_id,
                    title=arguments.get("title"),
                    message=arguments.get("message")
                )
                formatted = "✅ Announcement updated successfully!\n\n"
                formatted += f"Announcement ID: {announcement['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'topic_id' are required.")]
            try:
                result = delete_announcement_helper(course_id, topic_id)
                formatted = "✅ Announcement deleted successfully!\n\n"
                formatted += f"Deleted Announcement ID: {result['deleted_discussion']['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Conversation Operations
        elif name == "send_message":
            recipient_ids = arguments.get("recipient_ids")
            body = arguments.get("body")
            if not recipient_ids or not body:
                return [TextContent(type="text", text="Error: 'recipient_ids' and 'body' are required.")]
            try:
                conversation = create_conversation_helper(
                    recipient_ids=recipient_ids,
                    body=body,
                    subject=arguments.get("subject"),
                    group_conversation=arguments.get("group_conversation", True)
                )
                formatted = "✅ Message sent successfully!\n\n"
                formatted += f"Conversation ID: {conversation['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return [TextContent(type="text", text="Error: 'conversation_id' is required.")]
            try:
                conversation = fetch_conversation(conversation_id)
                formatted = f"Conversation Details:\n\nConversation ID: {conversation['id']}\n"
                if conversation.get('subject'):
                    formatted += f"Subject: {conversation['subject']}\n"
                formatted += f"State: {conversation['workflow_state']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_conversations":
            try:
                conversations = fetch_conversations()
                if not conversations:
                    return [TextContent(type="text", text="No conversations found.")]
                formatted = f"Conversations:\n\n"
                for i, conv in enumerate(conversations, 1):
                    formatted += f"{i}. Conversation ID: {conv['id']}\n"
                formatted += f"\nTotal: {len(conversations)} conversation(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Module Operations
        elif name == "get_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'module_id' are required.")]
            try:
                module = fetch_module(course_id, module_id)
                formatted = f"Module Details:\n\nName: {module['name']}\nModule ID: {module['id']}\n"
                formatted += f"Items Count: {module['items_count']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_module_items":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'module_id' are required.")]
            try:
                items = fetch_module_items(course_id, module_id)
                if not items:
                    return [TextContent(type="text", text=f"No items found for module {module_id}.")]
                formatted = f"Module Items for Module {module_id}:\n\n"
                for i, item in enumerate(items, 1):
                    formatted += f"{i}. {item['title']} (Type: {item['type']})\n"
                formatted += f"\nTotal: {len(items)} item(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'module_id' are required.")]
            try:
                module = update_module_helper(
                    course_id=course_id,
                    module_id=module_id,
                    name=arguments.get("name"),
                    position=arguments.get("position"),
                    unlock_at=arguments.get("unlock_at")
                )
                formatted = "✅ Module updated successfully!\n\n"
                formatted += f"Module ID: {module['id']}\nName: {module['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'module_id' are required.")]
            try:
                result = delete_module_helper(course_id, module_id)
                formatted = "✅ Module deleted successfully!\n\n"
                formatted += f"Deleted Module: {result['deleted_module']['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Page Operations (enhancing existing get_page_content)
        elif name == "create_page":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            body = arguments.get("body")
            if not all([course_id, title, body]):
                return [TextContent(type="text", text="Error: 'course_id', 'title', and 'body' are required.")]
            try:
                page = create_page_helper(
                    course_id=course_id,
                    title=title,
                    body=body,
                    editing_roles=arguments.get("editing_roles"),
                    published=arguments.get("published", False),
                    front_page=arguments.get("front_page", False)
                )
                formatted = "✅ Page created successfully!\n\n"
                formatted += f"Page ID: {page['id']}\nTitle: {page['title']}\nURL: {page['url']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return [TextContent(type="text", text="Error: 'course_id' and 'url' are required.")]
            try:
                page = fetch_page(course_id, url)
                formatted = f"Page Details:\n\nTitle: {page['title']}\nPage ID: {page['id']}\n"
                formatted += f"URL: {page['url']}\nPublished: {page['published']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_pages":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                pages = fetch_pages(course_id)
                if not pages:
                    return [TextContent(type="text", text=f"No pages found for course {course_id}.")]
                formatted = f"Pages for Course {course_id}:\n\n"
                for i, page in enumerate(pages, 1):
                    formatted += f"{i}. {page['title']} (ID: {page['id']})\n"
                formatted += f"\nTotal: {len(pages)} page(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return [TextContent(type="text", text="Error: 'course_id' and 'url' are required.")]
            try:
                page = update_page_helper(
                    course_id=course_id,
                    url=url,
                    title=arguments.get("title"),
                    body=arguments.get("body"),
                    published=arguments.get("published"),
                    front_page=arguments.get("front_page")
                )
                formatted = "✅ Page updated successfully!\n\n"
                formatted += f"Page ID: {page['id']}\nTitle: {page['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return [TextContent(type="text", text="Error: 'course_id' and 'url' are required.")]
            try:
                result = delete_page_helper(course_id, url)
                formatted = "✅ Page deleted successfully!\n\n"
                formatted += f"Deleted Page: {result['deleted_page']['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # File Operations
        elif name == "upload_file":
            course_id = arguments.get("course_id")
            file_path = arguments.get("file_path")
            if not course_id or not file_path:
                return [TextContent(type="text", text="Error: 'course_id' and 'file_path' are required.")]
            try:
                file_obj = upload_file_helper(
                    course_id=course_id,
                    file_path=file_path,
                    folder_id=arguments.get("folder_id"),
                    on_duplicate=arguments.get("on_duplicate", "rename")
                )
                formatted = "✅ File uploaded successfully!\n\n"
                formatted += f"File ID: {file_obj['id']}\nFilename: {file_obj['filename']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'file_id' are required.")]
            try:
                file_obj = fetch_file(course_id, file_id)
                formatted = f"File Details:\n\nFilename: {file_obj['filename']}\nFile ID: {file_obj['id']}\n"
                formatted += f"Size: {file_obj['size']} bytes\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_files":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                files = fetch_files(course_id, arguments.get("folder_id"), arguments.get("search_term"))
                if not files:
                    return [TextContent(type="text", text=f"No files found for course {course_id}.")]
                formatted = f"Files for Course {course_id}:\n\n"
                for i, file_obj in enumerate(files, 1):
                    formatted += f"{i}. {file_obj['filename']} (ID: {file_obj['id']})\n"
                formatted += f"\nTotal: {len(files)} file(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'file_id' are required.")]
            try:
                file_obj = update_file_helper(
                    course_id=course_id,
                    file_id=file_id,
                    name=arguments.get("name"),
                    locked=arguments.get("locked"),
                    hidden=arguments.get("hidden")
                )
                formatted = "✅ File updated successfully!\n\n"
                formatted += f"File ID: {file_obj['id']}\nFilename: {file_obj['filename']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'file_id' are required.")]
            try:
                result = delete_file_helper(course_id, file_id)
                formatted = "✅ File deleted successfully!\n\n"
                formatted += f"Deleted File: {result['deleted_file']['filename']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Folder Operations
        elif name == "create_folder":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return [TextContent(type="text", text="Error: 'course_id' and 'name' are required.")]
            try:
                folder = create_folder_helper(
                    course_id=course_id,
                    name=name,
                    parent_folder_id=arguments.get("parent_folder_id"),
                    locked=arguments.get("locked", False),
                    hidden=arguments.get("hidden", False)
                )
                formatted = "✅ Folder created successfully!\n\n"
                formatted += f"Folder ID: {folder['id']}\nName: {folder['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'folder_id' are required.")]
            try:
                folder = fetch_folder(course_id, folder_id)
                formatted = f"Folder Details:\n\nName: {folder['name']}\nFolder ID: {folder['id']}\n"
                formatted += f"Files: {folder['files_count']}\nFolders: {folder['folders_count']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_folders":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                folders = fetch_folders(course_id, arguments.get("folder_id"))
                if not folders:
                    return [TextContent(type="text", text=f"No folders found for course {course_id}.")]
                formatted = f"Folders for Course {course_id}:\n\n"
                for i, folder in enumerate(folders, 1):
                    formatted += f"{i}. {folder['name']} (ID: {folder['id']})\n"
                formatted += f"\nTotal: {len(folders)} folder(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'folder_id' are required.")]
            try:
                folder = update_folder_helper(
                    course_id=course_id,
                    folder_id=folder_id,
                    name=arguments.get("name"),
                    locked=arguments.get("locked"),
                    hidden=arguments.get("hidden")
                )
                formatted = "✅ Folder updated successfully!\n\n"
                formatted += f"Folder ID: {folder['id']}\nName: {folder['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'folder_id' are required.")]
            try:
                result = delete_folder_helper(course_id, folder_id)
                formatted = "✅ Folder deleted successfully!\n\n"
                formatted += f"Deleted Folder: {result['deleted_folder']['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Assignment Group Operations
        elif name == "create_assignment_group":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return [TextContent(type="text", text="Error: 'course_id' and 'name' are required.")]
            try:
                group = create_assignment_group_helper(
                    course_id=course_id,
                    name=name,
                    position=arguments.get("position"),
                    group_weight=arguments.get("group_weight")
                )
                formatted = "✅ Assignment group created successfully!\n\n"
                formatted += f"Group ID: {group['id']}\nName: {group['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'group_id' are required.")]
            try:
                group = fetch_assignment_group(course_id, group_id)
                formatted = f"Assignment Group Details:\n\nName: {group['name']}\nGroup ID: {group['id']}\n"
                formatted += f"Assignments Count: {group['assignments_count']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "list_assignment_groups":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(type="text", text="Error: 'course_id' is required.")]
            try:
                groups = fetch_assignment_groups(course_id)
                if not groups:
                    return [TextContent(type="text", text=f"No assignment groups found for course {course_id}.")]
                formatted = f"Assignment Groups for Course {course_id}:\n\n"
                for i, group in enumerate(groups, 1):
                    formatted += f"{i}. {group['name']} (ID: {group['id']})\n"
                formatted += f"\nTotal: {len(groups)} group(s)"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'group_id' are required.")]
            try:
                group = update_assignment_group_helper(
                    course_id=course_id,
                    group_id=group_id,
                    name=arguments.get("name"),
                    position=arguments.get("position"),
                    group_weight=arguments.get("group_weight")
                )
                formatted = "✅ Assignment group updated successfully!\n\n"
                formatted += f"Group ID: {group['id']}\nName: {group['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return [TextContent(type="text", text="Error: 'course_id' and 'group_id' are required.")]
            try:
                result = delete_assignment_group_helper(course_id, group_id)
                formatted = "✅ Assignment group deleted successfully!\n\n"
                formatted += f"Deleted Group: {result['deleted_group']['name']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Module Item Operations
        elif name == "create_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            type = arguments.get("type")
            if not all([course_id, module_id, type]):
                return [TextContent(type="text", text="Error: 'course_id', 'module_id', and 'type' are required.")]
            try:
                item = create_module_item_helper(
                    course_id=course_id,
                    module_id=module_id,
                    type=type,
                    content_id=arguments.get("content_id"),
                    title=arguments.get("title"),
                    position=arguments.get("position"),
                    page_url=arguments.get("page_url"),
                    external_url=arguments.get("external_url")
                )
                formatted = "✅ Module item created successfully!\n\n"
                formatted += f"Item ID: {item['id']}\nTitle: {item['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "get_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'module_id', and 'item_id' are required.")]
            try:
                item = fetch_module_item(course_id, module_id, item_id)
                formatted = f"Module Item Details:\n\nTitle: {item['title']}\nItem ID: {item['id']}\n"
                formatted += f"Type: {item['type']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "update_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'module_id', and 'item_id' are required.")]
            try:
                item = update_module_item_helper(
                    course_id=course_id,
                    module_id=module_id,
                    item_id=item_id,
                    title=arguments.get("title"),
                    position=arguments.get("position"),
                    indent=arguments.get("indent")
                )
                formatted = "✅ Module item updated successfully!\n\n"
                formatted += f"Item ID: {item['id']}\nTitle: {item['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'module_id', and 'item_id' are required.")]
            try:
                result = delete_module_item_helper(course_id, module_id, item_id)
                formatted = "✅ Module item deleted successfully!\n\n"
                formatted += f"Deleted Item: {result['deleted_item']['title']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Quiz Submission Operations (remaining)
        elif name == "update_quiz_submission_score":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'quiz_id', and 'submission_id' are required.")]
            try:
                submission = update_quiz_submission_helper(
                    course_id=course_id,
                    quiz_id=quiz_id,
                    submission_id=submission_id,
                    fudge_points=arguments.get("fudge_points"),
                    comment=arguments.get("comment")
                )
                formatted = "✅ Quiz submission score updated successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\nScore: {submission.get('score', 'N/A')}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return [TextContent(type="text", text="Error: 'course_id', 'quiz_id', and 'submission_id' are required.")]
            try:
                result = delete_quiz_submission_helper(course_id, quiz_id, submission_id)
                formatted = "✅ Quiz submission deleted successfully!\n\n"
                formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Conversation Operations (remaining)
        elif name == "update_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return [TextContent(type="text", text="Error: 'conversation_id' is required.")]
            try:
                conversation = update_conversation_helper(
                    conversation_id=conversation_id,
                    workflow_state=arguments.get("workflow_state"),
                    starred=arguments.get("starred")
                )
                formatted = "✅ Conversation updated successfully!\n\n"
                formatted += f"Conversation ID: {conversation['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        elif name == "delete_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return [TextContent(type="text", text="Error: 'conversation_id' is required.")]
            try:
                result = delete_conversation_helper(conversation_id)
                formatted = "✅ Conversation deleted successfully!\n\n"
                formatted += f"Deleted Conversation ID: {result['deleted_conversation']['id']}\n"
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
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