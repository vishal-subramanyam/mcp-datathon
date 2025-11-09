"""
Service layer that provides programmatic access to MCP server tools.
This allows us to call MCP tools directly without going through stdio.
"""
import os
import sys
from typing import Dict, Any, List, Optional
import asyncio

# Explicit exports
__all__ = ['MCPService', 'health_check']

# Add parent directory to path to import MCP servers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import helper functions from MCP servers
# Canvas - Basic functions
from backend.mcp_servers.canvas_server import (
    fetch_courses,
    fetch_upcoming_assignments,
    build_daily_briefing,
    create_assignment,
    delete_assignment,
    create_course
)

# Canvas - Additional existing functions
from backend.mcp_servers.canvas_server import (
    get_assignment_details,
    get_course_modules,
    get_course_files,
    get_course_pages,
    get_page_content
)

# Canvas - Course operations
from backend.mcp_servers.canvas_server import (
    fetch_course,
    update_course_helper,
    delete_course_helper
)

# Canvas - Assignment operations
from backend.mcp_servers.canvas_server import (
    fetch_assignment,
    update_assignment_helper
)

# Canvas - Submission operations
from backend.mcp_servers.canvas_server import (
    create_submission_helper,
    fetch_submission,
    fetch_submissions,
    update_submission_helper,
    delete_submission_helper
)

# Canvas - Quiz operations
from backend.mcp_servers.canvas_server import (
    create_quiz_helper,
    fetch_quiz,
    fetch_quizzes,
    fetch_quiz_questions,
    update_quiz_helper,
    delete_quiz_helper
)

# Canvas - Quiz submission operations
from backend.mcp_servers.canvas_server import (
    create_quiz_submission_helper,
    fetch_quiz_submission,
    fetch_quiz_submissions,
    update_quiz_submission_helper,
    delete_quiz_submission_helper
)

# Canvas - Discussion operations
from backend.mcp_servers.canvas_server import (
    create_discussion_helper,
    fetch_discussion,
    fetch_discussions,
    fetch_discussion_entries,
    update_discussion_helper,
    delete_discussion_helper
)

# Canvas - Announcement operations
from backend.mcp_servers.canvas_server import (
    create_announcement_helper,
    fetch_announcement,
    fetch_announcements,
    update_announcement_helper,
    delete_announcement_helper
)

# Canvas - Conversation operations
from backend.mcp_servers.canvas_server import (
    create_conversation_helper,
    fetch_conversation,
    fetch_conversations,
    update_conversation_helper,
    delete_conversation_helper
)

# Canvas - Module operations
from backend.mcp_servers.canvas_server import (
    create_module_helper,
    fetch_module,
    fetch_modules,
    fetch_module_items,
    update_module_helper,
    delete_module_helper
)

# Canvas - Module item operations
from backend.mcp_servers.canvas_server import (
    create_module_item_helper,
    fetch_module_item,
    update_module_item_helper,
    delete_module_item_helper
)

# Canvas - Page operations
from backend.mcp_servers.canvas_server import (
    create_page_helper,
    fetch_page,
    fetch_pages,
    update_page_helper,
    delete_page_helper
)

# Canvas - File operations
from backend.mcp_servers.canvas_server import (
    upload_file_helper,
    fetch_file,
    fetch_files,
    update_file_helper,
    delete_file_helper
)

# Canvas - Folder operations
from backend.mcp_servers.canvas_server import (
    create_folder_helper,
    fetch_folder,
    fetch_folders,
    update_folder_helper,
    delete_folder_helper
)

# Canvas - Assignment group operations
from backend.mcp_servers.canvas_server import (
    create_assignment_group_helper,
    fetch_assignment_group,
    fetch_assignment_groups,
    update_assignment_group_helper,
    delete_assignment_group_helper
)

# Calendar
from backend.mcp_servers.calendar_server import (
    list_calendars,
    get_calendar_events,
    get_event,
    create_event,
    update_event,
    delete_event,
    parse_event
)

# Gmail
from backend.mcp_servers.gmail_server import (
    list_messages,
    get_message,
    parse_message,
    send_message,
    mark_as_read,
    mark_as_unread,
    delete_message
)

# Flashcard storage
from backend.services.flashcard_storage import FlashcardStorage

# Flashcard generation
from backend.services.flashcard_generator import generate_flashcards_from_content as generate_flashcards_from_context


class MCPService:
    """Service layer for MCP tools."""
    
    @staticmethod
    async def call_tool(server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None, credentials: Optional[Dict[str, Any]] = None) -> str:
        """
        Call a tool from an MCP server.
        
        Args:
            server_name: Name of the MCP server ('canvas', 'calendar', 'gmail', 'flashcard')
            tool_name: Name of the tool to call
            arguments: Tool arguments
            credentials: Optional user credentials for the service
            
        Returns:
            Tool response as a string
        """
        if arguments is None:
            arguments = {}
        
        try:
            if server_name == "canvas":
                return await MCPService._call_canvas_tool(tool_name, arguments, credentials)
            elif server_name == "calendar":
                return await MCPService._call_calendar_tool(tool_name, arguments, credentials)
            elif server_name == "gmail":
                return await MCPService._call_gmail_tool(tool_name, arguments, credentials)
            elif server_name == "flashcard":
                return await MCPService._call_flashcard_tool(tool_name, arguments, credentials)
            else:
                return f"Error: Unknown server '{server_name}'"
        except Exception as e:
            return f"Error calling tool: {str(e)}"
    
    @staticmethod
    async def _call_canvas_tool(tool_name: str, arguments: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None) -> str:
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
        
        # Course operations
        elif tool_name == "get_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                course = fetch_course(course_id)
                formatted = "Course Details:\n\n"
                formatted += f"Name: {course['name']}\n"
                formatted += f"Course ID: {course['id']}\n"
                if course.get('course_code'):
                    formatted += f"Course Code: {course['course_code']}\n"
                if course.get('start_at'):
                    formatted += f"Start Date: {course['start_at']}\n"
                if course.get('end_at'):
                    formatted += f"End Date: {course['end_at']}\n"
                formatted += f"State: {course['workflow_state']}\n"
                formatted += f"URL: {course['html_url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                course = update_course_helper(
                    course_id=course_id,
                    name=arguments.get("name"),
                    course_code=arguments.get("course_code"),
                    start_at=arguments.get("start_at"),
                    end_at=arguments.get("end_at")
                )
                formatted = "✅ Course updated successfully!\n\n"
                formatted += f"Course ID: {course['id']}\n"
                formatted += f"Name: {course['name']}\n"
                if course.get('course_code'):
                    formatted += f"Course Code: {course['course_code']}\n"
                formatted += f"State: {course['workflow_state']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                result = delete_course_helper(course_id)
                formatted = "✅ Course deleted successfully!\n\n"
                formatted += f"Deleted Course: {result['deleted_course']['name']}\n"
                formatted += f"Course ID: {result['deleted_course']['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Assignment operations
        elif tool_name == "get_assignment":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return "Error: 'course_id' and 'assignment_id' are required."
            try:
                assignment = fetch_assignment(course_id, assignment_id)
                formatted = "Assignment Details:\n\n"
                formatted += f"Name: {assignment['name']}\n"
                formatted += f"Assignment ID: {assignment['id']}\n"
                if assignment.get('points_possible'):
                    formatted += f"Points: {assignment['points_possible']}\n"
                if assignment.get('due_at'):
                    formatted += f"Due Date: {assignment['due_at']}\n"
                formatted += f"Published: {assignment['published']}\n"
                formatted += f"URL: {assignment['html_url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_assignment":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return "Error: 'course_id' and 'assignment_id' are required."
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
                formatted += f"Assignment ID: {assignment['id']}\n"
                formatted += f"Name: {assignment['name']}\n"
                formatted += f"Published: {assignment['published']}\n"
                formatted += f"URL: {assignment['html_url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Submission operations
        elif tool_name == "create_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            submission_type = arguments.get("submission_type")
            if not all([course_id, assignment_id, submission_type]):
                return "Error: 'course_id', 'assignment_id', and 'submission_type' are required."
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
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"Type: {submission['submission_type']}\n"
                formatted += f"State: {submission['workflow_state']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return "Error: 'course_id', 'assignment_id', and 'user_id' are required."
            try:
                submission = fetch_submission(course_id, assignment_id, user_id)
                formatted = "Submission Details:\n\n"
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"Type: {submission['submission_type']}\n"
                formatted += f"State: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_submissions":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            if not course_id or not assignment_id:
                return "Error: 'course_id' and 'assignment_id' are required."
            try:
                submissions = fetch_submissions(course_id, assignment_id)
                if not submissions:
                    return f"No submissions found for assignment {assignment_id}."
                formatted = f"Submissions for Assignment {assignment_id}:\n\n"
                for i, sub in enumerate(submissions, 1):
                    formatted += f"{i}. Submission ID: {sub['id']}, User ID: {sub['user_id']}, State: {sub['workflow_state']}\n"
                formatted += f"\nTotal: {len(submissions)} submission(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return "Error: 'course_id', 'assignment_id', and 'user_id' are required."
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
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"State: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_submission":
            course_id = arguments.get("course_id")
            assignment_id = arguments.get("assignment_id")
            user_id = arguments.get("user_id")
            if not all([course_id, assignment_id, user_id]):
                return "Error: 'course_id', 'assignment_id', and 'user_id' are required."
            try:
                result = delete_submission_helper(course_id, assignment_id, user_id)
                formatted = "✅ Submission deleted successfully!\n\n"
                formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Quiz operations
        elif tool_name == "create_quiz":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            if not course_id or not title:
                return "Error: 'course_id' and 'title' are required."
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
                formatted += f"Quiz ID: {quiz['id']}\n"
                formatted += f"Title: {quiz['title']}\n"
                formatted += f"Published: {quiz['published']}\n"
                formatted += f"URL: {quiz['html_url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
            try:
                quiz = fetch_quiz(course_id, quiz_id)
                formatted = "Quiz Details:\n\n"
                formatted += f"Title: {quiz['title']}\n"
                formatted += f"Quiz ID: {quiz['id']}\n"
                formatted += f"Type: {quiz['quiz_type']}\n"
                formatted += f"Published: {quiz['published']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_quizzes":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                quizzes = fetch_quizzes(course_id)
                if not quizzes:
                    return f"No quizzes found for course {course_id}."
                formatted = f"Quizzes for Course {course_id}:\n\n"
                for i, quiz in enumerate(quizzes, 1):
                    formatted += f"{i}. {quiz['title']} (ID: {quiz['id']})\n"
                formatted += f"\nTotal: {len(quizzes)} quiz(zes)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_quiz_questions":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
            try:
                questions = fetch_quiz_questions(course_id, quiz_id)
                if not questions:
                    return f"No questions found for quiz {quiz_id}."
                formatted = f"Questions for Quiz {quiz_id}:\n\n"
                for i, q in enumerate(questions, 1):
                    formatted += f"{i}. {q.get('question_name', 'Question')} (Type: {q['question_type']})\n"
                formatted += f"\nTotal: {len(questions)} question(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
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
                formatted += f"Quiz ID: {quiz['id']}\n"
                formatted += f"Title: {quiz['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_quiz":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
            try:
                result = delete_quiz_helper(course_id, quiz_id)
                formatted = "✅ Quiz deleted successfully!\n\n"
                formatted += f"Deleted Quiz: {result['deleted_quiz']['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Quiz submission operations
        elif tool_name == "create_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
            try:
                submission = create_quiz_submission_helper(course_id, quiz_id, arguments.get("access_code"))
                formatted = "✅ Quiz submission created successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"Attempt: {submission['attempt']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return "Error: 'course_id', 'quiz_id', and 'submission_id' are required."
            try:
                submission = fetch_quiz_submission(course_id, quiz_id, submission_id)
                formatted = "Quiz Submission Details:\n\n"
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"Attempt: {submission['attempt']}\n"
                formatted += f"State: {submission['workflow_state']}\n"
                if submission.get('score'):
                    formatted += f"Score: {submission['score']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_quiz_submissions":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            if not course_id or not quiz_id:
                return "Error: 'course_id' and 'quiz_id' are required."
            try:
                submissions = fetch_quiz_submissions(course_id, quiz_id)
                if not submissions:
                    return f"No submissions found for quiz {quiz_id}."
                formatted = f"Quiz Submissions for Quiz {quiz_id}:\n\n"
                for i, sub in enumerate(submissions, 1):
                    formatted += f"{i}. Submission ID: {sub['id']}, Attempt: {sub['attempt']}, State: {sub['workflow_state']}\n"
                formatted += f"\nTotal: {len(submissions)} submission(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_quiz_submission_score":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return "Error: 'course_id', 'quiz_id', and 'submission_id' are required."
            try:
                submission = update_quiz_submission_helper(
                    course_id=course_id,
                    quiz_id=quiz_id,
                    submission_id=submission_id,
                    fudge_points=arguments.get("fudge_points"),
                    comment=arguments.get("comment")
                )
                formatted = "✅ Quiz submission score updated successfully!\n\n"
                formatted += f"Submission ID: {submission['id']}\n"
                formatted += f"Score: {submission.get('score', 'N/A')}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_quiz_submission":
            course_id = arguments.get("course_id")
            quiz_id = arguments.get("quiz_id")
            submission_id = arguments.get("submission_id")
            if not all([course_id, quiz_id, submission_id]):
                return "Error: 'course_id', 'quiz_id', and 'submission_id' are required."
            try:
                result = delete_quiz_submission_helper(course_id, quiz_id, submission_id)
                formatted = "✅ Quiz submission deleted successfully!\n\n"
                formatted += f"Deleted Submission ID: {result['deleted_submission']['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Discussion operations
        elif tool_name == "create_discussion":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            message = arguments.get("message")
            if not all([course_id, title, message]):
                return "Error: 'course_id', 'title', and 'message' are required."
            try:
                discussion = create_discussion_helper(
                    course_id=course_id,
                    title=title,
                    message=message,
                    pinned=arguments.get("pinned", False),
                    locked=arguments.get("locked", False)
                )
                formatted = "✅ Discussion created successfully!\n\n"
                formatted += f"Discussion ID: {discussion['id']}\n"
                formatted += f"Title: {discussion['title']}\n"
                formatted += f"URL: {discussion['html_url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                discussion = fetch_discussion(course_id, topic_id)
                formatted = "Discussion Details:\n\n"
                formatted += f"Title: {discussion['title']}\n"
                formatted += f"Discussion ID: {discussion['id']}\n"
                formatted += f"Pinned: {discussion['pinned']}\n"
                formatted += f"Locked: {discussion['locked']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_discussions":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                discussions = fetch_discussions(course_id)
                if not discussions:
                    return f"No discussions found for course {course_id}."
                formatted = f"Discussions for Course {course_id}:\n\n"
                for i, disc in enumerate(discussions, 1):
                    formatted += f"{i}. {disc['title']} (ID: {disc['id']})\n"
                formatted += f"\nTotal: {len(discussions)} discussion(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_discussion_entries":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                entries = fetch_discussion_entries(course_id, topic_id)
                if not entries:
                    return f"No entries found for discussion {topic_id}."
                formatted = f"Discussion Entries for Topic {topic_id}:\n\n"
                for i, entry in enumerate(entries, 1):
                    formatted += f"{i}. Entry ID: {entry['id']}, User ID: {entry['user_id']}\n"
                formatted += f"\nTotal: {len(entries)} entry/entries"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
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
                formatted += f"Discussion ID: {discussion['id']}\n"
                formatted += f"Title: {discussion['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_discussion":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                result = delete_discussion_helper(course_id, topic_id)
                formatted = "✅ Discussion deleted successfully!\n\n"
                formatted += f"Deleted Discussion: {result['deleted_discussion']['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Announcement operations
        elif tool_name == "create_announcement":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            message = arguments.get("message")
            if not all([course_id, title, message]):
                return "Error: 'course_id', 'title', and 'message' are required."
            try:
                announcement = create_announcement_helper(
                    course_id=course_id,
                    title=title,
                    message=message,
                    delayed_post_at=arguments.get("delayed_post_at")
                )
                formatted = "✅ Announcement created successfully!\n\n"
                formatted += f"Announcement ID: {announcement['id']}\n"
                formatted += f"Title: {announcement['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                announcement = fetch_announcement(course_id, topic_id)
                formatted = "Announcement Details:\n\n"
                formatted += f"Title: {announcement['title']}\n"
                formatted += f"ID: {announcement['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_announcements":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                announcements = fetch_announcements(course_id)
                if not announcements:
                    return f"No announcements found for course {course_id}."
                formatted = f"Announcements for Course {course_id}:\n\n"
                for i, ann in enumerate(announcements, 1):
                    formatted += f"{i}. {ann['title']} (ID: {ann['id']})\n"
                formatted += f"\nTotal: {len(announcements)} announcement(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                announcement = update_announcement_helper(
                    course_id=course_id,
                    topic_id=topic_id,
                    title=arguments.get("title"),
                    message=arguments.get("message")
                )
                formatted = "✅ Announcement updated successfully!\n\n"
                formatted += f"Announcement ID: {announcement['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_announcement":
            course_id = arguments.get("course_id")
            topic_id = arguments.get("topic_id")
            if not course_id or not topic_id:
                return "Error: 'course_id' and 'topic_id' are required."
            try:
                result = delete_announcement_helper(course_id, topic_id)
                formatted = "✅ Announcement deleted successfully!\n\n"
                formatted += f"Deleted Announcement ID: {result['deleted_discussion']['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Conversation operations
        elif tool_name == "send_message":
            recipient_ids = arguments.get("recipient_ids")
            body = arguments.get("body")
            if not recipient_ids or not body:
                return "Error: 'recipient_ids' and 'body' are required."
            try:
                conversation = create_conversation_helper(
                    recipient_ids=recipient_ids,
                    body=body,
                    subject=arguments.get("subject"),
                    group_conversation=arguments.get("group_conversation", True)
                )
                formatted = "✅ Message sent successfully!\n\n"
                formatted += f"Conversation ID: {conversation['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return "Error: 'conversation_id' is required."
            try:
                conversation = fetch_conversation(conversation_id)
                formatted = "Conversation Details:\n\n"
                formatted += f"Conversation ID: {conversation['id']}\n"
                if conversation.get('subject'):
                    formatted += f"Subject: {conversation['subject']}\n"
                formatted += f"State: {conversation['workflow_state']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_conversations":
            try:
                conversations = fetch_conversations()
                if not conversations:
                    return "No conversations found."
                formatted = "Conversations:\n\n"
                for i, conv in enumerate(conversations, 1):
                    formatted += f"{i}. Conversation ID: {conv['id']}\n"
                formatted += f"\nTotal: {len(conversations)} conversation(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return "Error: 'conversation_id' is required."
            try:
                conversation = update_conversation_helper(
                    conversation_id=conversation_id,
                    workflow_state=arguments.get("workflow_state"),
                    starred=arguments.get("starred")
                )
                formatted = "✅ Conversation updated successfully!\n\n"
                formatted += f"Conversation ID: {conversation['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_conversation":
            conversation_id = arguments.get("conversation_id")
            if not conversation_id:
                return "Error: 'conversation_id' is required."
            try:
                result = delete_conversation_helper(conversation_id)
                formatted = "✅ Conversation deleted successfully!\n\n"
                formatted += f"Deleted Conversation ID: {result['deleted_conversation']['id']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Module operations
        elif tool_name == "create_module":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return "Error: 'course_id' and 'name' are required."
            try:
                module = create_module_helper(
                    course_id=course_id,
                    name=name,
                    position=arguments.get("position"),
                    unlock_at=arguments.get("unlock_at"),
                    require_sequential_progress=arguments.get("require_sequential_progress", False)
                )
                formatted = "✅ Module created successfully!\n\n"
                formatted += f"Module ID: {module['id']}\n"
                formatted += f"Name: {module['name']}\n"
                formatted += f"Items Count: {module['items_count']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return "Error: 'course_id' and 'module_id' are required."
            try:
                module = fetch_module(course_id, module_id)
                formatted = "Module Details:\n\n"
                formatted += f"Name: {module['name']}\n"
                formatted += f"Module ID: {module['id']}\n"
                formatted += f"Items Count: {module['items_count']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_modules":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                modules = fetch_modules(course_id)
                if not modules:
                    return f"No modules found for course {course_id}."
                formatted = f"Modules for Course {course_id}:\n\n"
                for i, mod in enumerate(modules, 1):
                    formatted += f"{i}. {mod['name']} (ID: {mod['id']})\n"
                formatted += f"\nTotal: {len(modules)} module(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_module_items":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return "Error: 'course_id' and 'module_id' are required."
            try:
                items = fetch_module_items(course_id, module_id)
                if not items:
                    return f"No items found for module {module_id}."
                formatted = f"Module Items for Module {module_id}:\n\n"
                for i, item in enumerate(items, 1):
                    formatted += f"{i}. {item['title']} (Type: {item['type']})\n"
                formatted += f"\nTotal: {len(items)} item(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return "Error: 'course_id' and 'module_id' are required."
            try:
                module = update_module_helper(
                    course_id=course_id,
                    module_id=module_id,
                    name=arguments.get("name"),
                    position=arguments.get("position"),
                    unlock_at=arguments.get("unlock_at")
                )
                formatted = "✅ Module updated successfully!\n\n"
                formatted += f"Module ID: {module['id']}\n"
                formatted += f"Name: {module['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_module":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            if not course_id or not module_id:
                return "Error: 'course_id' and 'module_id' are required."
            try:
                result = delete_module_helper(course_id, module_id)
                formatted = "✅ Module deleted successfully!\n\n"
                formatted += f"Deleted Module: {result['deleted_module']['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Module item operations
        elif tool_name == "create_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_type = arguments.get("type")
            if not all([course_id, module_id, item_type]):
                return "Error: 'course_id', 'module_id', and 'type' are required."
            try:
                item = create_module_item_helper(
                    course_id=course_id,
                    module_id=module_id,
                    type=item_type,
                    content_id=arguments.get("content_id"),
                    title=arguments.get("title"),
                    position=arguments.get("position"),
                    page_url=arguments.get("page_url"),
                    external_url=arguments.get("external_url")
                )
                formatted = "✅ Module item created successfully!\n\n"
                formatted += f"Item ID: {item['id']}\n"
                formatted += f"Title: {item['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return "Error: 'course_id', 'module_id', and 'item_id' are required."
            try:
                item = fetch_module_item(course_id, module_id, item_id)
                formatted = "Module Item Details:\n\n"
                formatted += f"Title: {item['title']}\n"
                formatted += f"Item ID: {item['id']}\n"
                formatted += f"Type: {item['type']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return "Error: 'course_id', 'module_id', and 'item_id' are required."
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
                formatted += f"Item ID: {item['id']}\n"
                formatted += f"Title: {item['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_module_item":
            course_id = arguments.get("course_id")
            module_id = arguments.get("module_id")
            item_id = arguments.get("item_id")
            if not all([course_id, module_id, item_id]):
                return "Error: 'course_id', 'module_id', and 'item_id' are required."
            try:
                result = delete_module_item_helper(course_id, module_id, item_id)
                formatted = "✅ Module item deleted successfully!\n\n"
                formatted += f"Deleted Item: {result['deleted_item']['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Page operations
        elif tool_name == "create_page":
            course_id = arguments.get("course_id")
            title = arguments.get("title")
            body = arguments.get("body")
            if not all([course_id, title, body]):
                return "Error: 'course_id', 'title', and 'body' are required."
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
                formatted += f"Page ID: {page['id']}\n"
                formatted += f"Title: {page['title']}\n"
                formatted += f"URL: {page['url']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return "Error: 'course_id' and 'url' are required."
            try:
                page = fetch_page(course_id, url)
                formatted = "Page Details:\n\n"
                formatted += f"Title: {page['title']}\n"
                formatted += f"Page ID: {page['id']}\n"
                formatted += f"URL: {page['url']}\n"
                formatted += f"Published: {page['published']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_pages":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                pages = fetch_pages(course_id)
                if not pages:
                    return f"No pages found for course {course_id}."
                formatted = f"Pages for Course {course_id}:\n\n"
                for i, page in enumerate(pages, 1):
                    formatted += f"{i}. {page['title']} (ID: {page['id']})\n"
                formatted += f"\nTotal: {len(pages)} page(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return "Error: 'course_id' and 'url' are required."
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
                formatted += f"Page ID: {page['id']}\n"
                formatted += f"Title: {page['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_page":
            course_id = arguments.get("course_id")
            url = arguments.get("url")
            if not course_id or not url:
                return "Error: 'course_id' and 'url' are required."
            try:
                result = delete_page_helper(course_id, url)
                formatted = "✅ Page deleted successfully!\n\n"
                formatted += f"Deleted Page: {result['deleted_page']['title']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # File operations
        elif tool_name == "upload_file":
            course_id = arguments.get("course_id")
            file_path = arguments.get("file_path")
            if not course_id or not file_path:
                return "Error: 'course_id' and 'file_path' are required."
            try:
                file_obj = upload_file_helper(
                    course_id=course_id,
                    file_path=file_path,
                    folder_id=arguments.get("folder_id"),
                    on_duplicate=arguments.get("on_duplicate", "rename")
                )
                formatted = "✅ File uploaded successfully!\n\n"
                formatted += f"File ID: {file_obj['id']}\n"
                formatted += f"Filename: {file_obj['filename']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return "Error: 'course_id' and 'file_id' are required."
            try:
                file_obj = fetch_file(course_id, file_id)
                formatted = "File Details:\n\n"
                formatted += f"Filename: {file_obj['filename']}\n"
                formatted += f"File ID: {file_obj['id']}\n"
                formatted += f"Size: {file_obj['size']} bytes\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_files":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                files = fetch_files(course_id, arguments.get("folder_id"), arguments.get("search_term"))
                if not files:
                    return f"No files found for course {course_id}."
                formatted = f"Files for Course {course_id}:\n\n"
                for i, file_obj in enumerate(files, 1):
                    formatted += f"{i}. {file_obj['filename']} (ID: {file_obj['id']})\n"
                formatted += f"\nTotal: {len(files)} file(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return "Error: 'course_id' and 'file_id' are required."
            try:
                file_obj = update_file_helper(
                    course_id=course_id,
                    file_id=file_id,
                    name=arguments.get("name"),
                    locked=arguments.get("locked"),
                    hidden=arguments.get("hidden")
                )
                formatted = "✅ File updated successfully!\n\n"
                formatted += f"File ID: {file_obj['id']}\n"
                formatted += f"Filename: {file_obj['filename']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_file":
            course_id = arguments.get("course_id")
            file_id = arguments.get("file_id")
            if not course_id or not file_id:
                return "Error: 'course_id' and 'file_id' are required."
            try:
                result = delete_file_helper(course_id, file_id)
                formatted = "✅ File deleted successfully!\n\n"
                formatted += f"Deleted File: {result['deleted_file']['filename']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Folder operations
        elif tool_name == "create_folder":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return "Error: 'course_id' and 'name' are required."
            try:
                folder = create_folder_helper(
                    course_id=course_id,
                    name=name,
                    parent_folder_id=arguments.get("parent_folder_id"),
                    locked=arguments.get("locked", False),
                    hidden=arguments.get("hidden", False)
                )
                formatted = "✅ Folder created successfully!\n\n"
                formatted += f"Folder ID: {folder['id']}\n"
                formatted += f"Name: {folder['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return "Error: 'course_id' and 'folder_id' are required."
            try:
                folder = fetch_folder(course_id, folder_id)
                formatted = "Folder Details:\n\n"
                formatted += f"Name: {folder['name']}\n"
                formatted += f"Folder ID: {folder['id']}\n"
                formatted += f"Files: {folder['files_count']}\n"
                formatted += f"Folders: {folder['folders_count']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_folders":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                folders = fetch_folders(course_id, arguments.get("folder_id"))
                if not folders:
                    return f"No folders found for course {course_id}."
                formatted = f"Folders for Course {course_id}:\n\n"
                for i, folder in enumerate(folders, 1):
                    formatted += f"{i}. {folder['name']} (ID: {folder['id']})\n"
                formatted += f"\nTotal: {len(folders)} folder(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return "Error: 'course_id' and 'folder_id' are required."
            try:
                folder = update_folder_helper(
                    course_id=course_id,
                    folder_id=folder_id,
                    name=arguments.get("name"),
                    locked=arguments.get("locked"),
                    hidden=arguments.get("hidden")
                )
                formatted = "✅ Folder updated successfully!\n\n"
                formatted += f"Folder ID: {folder['id']}\n"
                formatted += f"Name: {folder['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_folder":
            course_id = arguments.get("course_id")
            folder_id = arguments.get("folder_id")
            if not course_id or not folder_id:
                return "Error: 'course_id' and 'folder_id' are required."
            try:
                result = delete_folder_helper(course_id, folder_id)
                formatted = "✅ Folder deleted successfully!\n\n"
                formatted += f"Deleted Folder: {result['deleted_folder']['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Assignment group operations
        elif tool_name == "create_assignment_group":
            course_id = arguments.get("course_id")
            name = arguments.get("name")
            if not course_id or not name:
                return "Error: 'course_id' and 'name' are required."
            try:
                group = create_assignment_group_helper(
                    course_id=course_id,
                    name=name,
                    position=arguments.get("position"),
                    group_weight=arguments.get("group_weight")
                )
                formatted = "✅ Assignment group created successfully!\n\n"
                formatted += f"Group ID: {group['id']}\n"
                formatted += f"Name: {group['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "get_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return "Error: 'course_id' and 'group_id' are required."
            try:
                group = fetch_assignment_group(course_id, group_id)
                formatted = "Assignment Group Details:\n\n"
                formatted += f"Name: {group['name']}\n"
                formatted += f"Group ID: {group['id']}\n"
                formatted += f"Assignments Count: {group['assignments_count']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "list_assignment_groups":
            course_id = arguments.get("course_id")
            if not course_id:
                return "Error: 'course_id' is required."
            try:
                groups = fetch_assignment_groups(course_id)
                if not groups:
                    return f"No assignment groups found for course {course_id}."
                formatted = f"Assignment Groups for Course {course_id}:\n\n"
                for i, group in enumerate(groups, 1):
                    formatted += f"{i}. {group['name']} (ID: {group['id']})\n"
                formatted += f"\nTotal: {len(groups)} group(s)"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "update_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return "Error: 'course_id' and 'group_id' are required."
            try:
                group = update_assignment_group_helper(
                    course_id=course_id,
                    group_id=group_id,
                    name=arguments.get("name"),
                    position=arguments.get("position"),
                    group_weight=arguments.get("group_weight")
                )
                formatted = "✅ Assignment group updated successfully!\n\n"
                formatted += f"Group ID: {group['id']}\n"
                formatted += f"Name: {group['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        elif tool_name == "delete_assignment_group":
            course_id = arguments.get("course_id")
            group_id = arguments.get("group_id")
            if not course_id or not group_id:
                return "Error: 'course_id' and 'group_id' are required."
            try:
                result = delete_assignment_group_helper(course_id, group_id)
                formatted = "✅ Assignment group deleted successfully!\n\n"
                formatted += f"Deleted Group: {result['deleted_group']['name']}\n"
                return formatted
            except Exception as e:
                return f"Error: {str(e)}"
        
        else:
            return f"Error: Unknown Canvas tool '{tool_name}'"
    
    @staticmethod
    async def _call_calendar_tool(tool_name: str, arguments: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None) -> str:
        """Call a Calendar tool."""
        if tool_name == "list_calendars":
            calendars = list_calendars(credentials=credentials)
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
                query=arguments.get("query"),
                credentials=credentials
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
            event = get_event(calendar_id, event_id, credentials=credentials)
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
                all_day=arguments.get("all_day", False),
                credentials=credentials
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
                timezone=arguments.get("timezone", "UTC"),
                credentials=credentials
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
            delete_event(calendar_id, event_id, credentials=credentials)
            return f"✅ Event {event_id} deleted successfully."
        
        else:
            return f"Error: Unknown Calendar tool '{tool_name}'"
    
    @staticmethod
    async def _call_gmail_tool(tool_name: str, arguments: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None) -> str:
        """Call a Gmail tool."""
        if tool_name == "list_emails":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 10)
            messages = list_messages(query=query, max_results=max_results, credentials=credentials)
            if not messages:
                return "No emails found."
            email_list = []
            for msg in messages:
                try:
                    message_detail = get_message(msg['id'], credentials=credentials)
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
            message = get_message(message_id, credentials=credentials)
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
                bcc=arguments.get("bcc"),
                credentials=credentials
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
            mark_as_read(message_id, credentials=credentials)
            return f"✅ Email {message_id} marked as read."
        
        elif tool_name == "mark_email_unread":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            mark_as_unread(message_id, credentials=credentials)
            return f"✅ Email {message_id} marked as unread."
        
        elif tool_name == "delete_email":
            message_id = arguments.get("message_id")
            if not message_id:
                return "Error: 'message_id' is required."
            delete_message(message_id, credentials=credentials)
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
            messages = list_messages(query=query, max_results=max_results, credentials=credentials)
            if not messages:
                return "No emails found matching the search criteria."
            email_list = []
            for msg in messages:
                try:
                    message_detail = get_message(msg['id'], credentials=credentials)
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
    async def _call_flashcard_tool(tool_name: str, arguments: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None) -> str:
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
            },
            # Additional Course operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_course",
                    "description": "Get detailed information about a specific course",
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
                    "name": "canvas_update_course",
                    "description": "Update a course's information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "name": {"type": "string", "description": "Course name"},
                            "course_code": {"type": "string", "description": "Course code"},
                            "start_at": {"type": "string", "description": "Start date (ISO 8601)"},
                            "end_at": {"type": "string", "description": "End date (ISO 8601)"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_course",
                    "description": "Delete a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course to delete"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            # Assignment operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_assignment",
                    "description": "Get detailed information about a specific assignment",
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
                    "name": "canvas_update_assignment",
                    "description": "Update an assignment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "assignment_id": {"type": "integer", "description": "The ID of the assignment"},
                            "name": {"type": "string", "description": "Assignment name"},
                            "description": {"type": "string", "description": "Assignment description"},
                            "due_at": {"type": "string", "description": "Due date (ISO 8601)"},
                            "points_possible": {"type": "number", "description": "Maximum points"},
                            "published": {"type": "boolean", "description": "Whether to publish"}
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            },
            # Submission operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_submission",
                    "description": "Create a submission for an assignment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "The ID of the course"},
                            "assignment_id": {"type": "integer", "description": "The ID of the assignment"},
                            "submission_type": {"type": "string", "description": "Type: online_text_entry, online_url, online_upload"},
                            "body": {"type": "string", "description": "Text submission body"},
                            "url": {"type": "string", "description": "URL submission"},
                            "file_ids": {"type": "array", "items": {"type": "integer"}, "description": "File IDs for upload"},
                            "comment": {"type": "string", "description": "Submission comment"}
                        },
                        "required": ["course_id", "assignment_id", "submission_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_submission",
                    "description": "Get a specific submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "assignment_id": {"type": "integer"},
                            "user_id": {"type": "integer"}
                        },
                        "required": ["course_id", "assignment_id", "user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_submissions",
                    "description": "List all submissions for an assignment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "assignment_id": {"type": "integer"}
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_submission",
                    "description": "Update/grade a submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "assignment_id": {"type": "integer"},
                            "user_id": {"type": "integer"},
                            "grade": {"type": "string", "description": "Grade to assign"},
                            "comment": {"type": "string"},
                            "excused": {"type": "boolean"}
                        },
                        "required": ["course_id", "assignment_id", "user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_submission",
                    "description": "Delete a submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "assignment_id": {"type": "integer"},
                            "user_id": {"type": "integer"}
                        },
                        "required": ["course_id", "assignment_id", "user_id"]
                    }
                }
            },
            # Quiz operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_quiz",
                    "description": "Create a new quiz",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "quiz_type": {"type": "string", "description": "assignment, practice_quiz, or graded_survey"},
                            "time_limit": {"type": "integer"},
                            "allowed_attempts": {"type": "integer"},
                            "due_at": {"type": "string"},
                            "published": {"type": "boolean"}
                        },
                        "required": ["course_id", "title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_quiz",
                    "description": "Get quiz details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_quizzes",
                    "description": "List all quizzes in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_quiz_questions",
                    "description": "Get questions for a quiz",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_quiz",
                    "description": "Update a quiz",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "due_at": {"type": "string"},
                            "published": {"type": "boolean"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_quiz",
                    "description": "Delete a quiz",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            # Quiz submission operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_quiz_submission",
                    "description": "Start a quiz submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"},
                            "access_code": {"type": "string"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_quiz_submission",
                    "description": "Get a quiz submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"},
                            "submission_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id", "submission_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_quiz_submissions",
                    "description": "List quiz submissions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_quiz_submission_score",
                    "description": "Update quiz submission score",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"},
                            "submission_id": {"type": "integer"},
                            "fudge_points": {"type": "number"},
                            "comment": {"type": "string"}
                        },
                        "required": ["course_id", "quiz_id", "submission_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_quiz_submission",
                    "description": "Delete a quiz submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "quiz_id": {"type": "integer"},
                            "submission_id": {"type": "integer"}
                        },
                        "required": ["course_id", "quiz_id", "submission_id"]
                    }
                }
            },
            # Discussion operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_discussion",
                    "description": "Create a discussion topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "message": {"type": "string"},
                            "pinned": {"type": "boolean"},
                            "locked": {"type": "boolean"}
                        },
                        "required": ["course_id", "title", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_discussion",
                    "description": "Get a discussion topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_discussions",
                    "description": "List all discussions in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_discussion_entries",
                    "description": "Get entries/replies in a discussion",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_discussion",
                    "description": "Update a discussion topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "message": {"type": "string"},
                            "pinned": {"type": "boolean"},
                            "locked": {"type": "boolean"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_discussion",
                    "description": "Delete a discussion topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            # Announcement operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_announcement",
                    "description": "Create an announcement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "message": {"type": "string"},
                            "delayed_post_at": {"type": "string"}
                        },
                        "required": ["course_id", "title", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_announcement",
                    "description": "Get an announcement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_announcements",
                    "description": "List all announcements in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_announcement",
                    "description": "Update an announcement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_announcement",
                    "description": "Delete an announcement",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "topic_id": {"type": "integer"}
                        },
                        "required": ["course_id", "topic_id"]
                    }
                }
            },
            # Conversation operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_send_message",
                    "description": "Send a Canvas message/conversation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient_ids": {"type": "array", "items": {"type": "string"}},
                            "body": {"type": "string"},
                            "subject": {"type": "string"},
                            "group_conversation": {"type": "boolean"}
                        },
                        "required": ["recipient_ids", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_conversation",
                    "description": "Get a conversation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_id": {"type": "integer"}
                        },
                        "required": ["conversation_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_conversations",
                    "description": "List all conversations",
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
                    "name": "canvas_update_conversation",
                    "description": "Update conversation state",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_id": {"type": "integer"},
                            "workflow_state": {"type": "string"},
                            "starred": {"type": "boolean"}
                        },
                        "required": ["conversation_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_conversation",
                    "description": "Delete a conversation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_id": {"type": "integer"}
                        },
                        "required": ["conversation_id"]
                    }
                }
            },
            # Module operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_module",
                    "description": "Create a new module",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "position": {"type": "integer"},
                            "unlock_at": {"type": "string"},
                            "require_sequential_progress": {"type": "boolean"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_module",
                    "description": "Get module details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_modules",
                    "description": "List all modules in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_module_items",
                    "description": "Get items in a module",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_module",
                    "description": "Update a module",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "position": {"type": "integer"},
                            "unlock_at": {"type": "string"}
                        },
                        "required": ["course_id", "module_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_module",
                    "description": "Delete a module",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id"]
                    }
                }
            },
            # Module item operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_module_item",
                    "description": "Create a module item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"},
                            "type": {"type": "string", "description": "Type: Assignment, Quiz, File, Page, Discussion, ExternalUrl, ExternalTool"},
                            "content_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "position": {"type": "integer"},
                            "page_url": {"type": "string"},
                            "external_url": {"type": "string"}
                        },
                        "required": ["course_id", "module_id", "type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_module_item",
                    "description": "Get a module item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"},
                            "item_id": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id", "item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_module_item",
                    "description": "Update a module item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"},
                            "item_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "position": {"type": "integer"},
                            "indent": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id", "item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_module_item",
                    "description": "Delete a module item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "module_id": {"type": "integer"},
                            "item_id": {"type": "integer"}
                        },
                        "required": ["course_id", "module_id", "item_id"]
                    }
                }
            },
            # Page operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_page",
                    "description": "Create a new page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "editing_roles": {"type": "string"},
                            "published": {"type": "boolean"},
                            "front_page": {"type": "boolean"}
                        },
                        "required": ["course_id", "title", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_page",
                    "description": "Get a page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "url": {"type": "string"}
                        },
                        "required": ["course_id", "url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_pages",
                    "description": "List all pages in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_page",
                    "description": "Update a page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "url": {"type": "string"},
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "published": {"type": "boolean"},
                            "front_page": {"type": "boolean"}
                        },
                        "required": ["course_id", "url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_page",
                    "description": "Delete a page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "url": {"type": "string"}
                        },
                        "required": ["course_id", "url"]
                    }
                }
            },
            # File operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_upload_file",
                    "description": "Upload a file to a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "file_path": {"type": "string"},
                            "folder_id": {"type": "integer"},
                            "on_duplicate": {"type": "string", "description": "rename, overwrite, or skip"}
                        },
                        "required": ["course_id", "file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_file",
                    "description": "Get file details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "file_id": {"type": "integer"}
                        },
                        "required": ["course_id", "file_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_files",
                    "description": "List files in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "folder_id": {"type": "integer"},
                            "search_term": {"type": "string"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_file",
                    "description": "Update file properties",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "file_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "locked": {"type": "boolean"},
                            "hidden": {"type": "boolean"}
                        },
                        "required": ["course_id", "file_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_file",
                    "description": "Delete a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "file_id": {"type": "integer"}
                        },
                        "required": ["course_id", "file_id"]
                    }
                }
            },
            # Folder operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_folder",
                    "description": "Create a new folder",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "parent_folder_id": {"type": "integer"},
                            "locked": {"type": "boolean"},
                            "hidden": {"type": "boolean"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_folder",
                    "description": "Get folder details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "folder_id": {"type": "integer"}
                        },
                        "required": ["course_id", "folder_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_folders",
                    "description": "List folders in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "folder_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_folder",
                    "description": "Update folder properties",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "folder_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "locked": {"type": "boolean"},
                            "hidden": {"type": "boolean"}
                        },
                        "required": ["course_id", "folder_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_folder",
                    "description": "Delete a folder",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "folder_id": {"type": "integer"}
                        },
                        "required": ["course_id", "folder_id"]
                    }
                }
            },
            # Assignment group operations
            {
                "type": "function",
                "function": {
                    "name": "canvas_create_assignment_group",
                    "description": "Create an assignment group",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "position": {"type": "integer"},
                            "group_weight": {"type": "number"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_get_assignment_group",
                    "description": "Get assignment group details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "group_id": {"type": "integer"}
                        },
                        "required": ["course_id", "group_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_list_assignment_groups",
                    "description": "List assignment groups in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_update_assignment_group",
                    "description": "Update an assignment group",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "group_id": {"type": "integer"},
                            "name": {"type": "string"},
                            "position": {"type": "integer"},
                            "group_weight": {"type": "number"}
                        },
                        "required": ["course_id", "group_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "canvas_delete_assignment_group",
                    "description": "Delete an assignment group",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer"},
                            "group_id": {"type": "integer"}
                        },
                        "required": ["course_id", "group_id"]
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


# Health check function for API
async def health_check() -> Dict[str, Any]:
    """
    Perform a health check on all MCP services.
    Returns health status and available services.
    """
    from datetime import datetime
    
    services_status = {}
    overall_status = "healthy"
    
    try:
        # Check Canvas service
        try:
            from backend.mcp_servers.canvas_server import fetch_courses
            # Quick test - just check if the function is available
            services_status["canvas"] = {
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            services_status["canvas"] = {
                "status": "degraded",
                "available": False,
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check Calendar service
        try:
            from backend.mcp_servers.calendar_server import list_calendars
            services_status["calendar"] = {
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            services_status["calendar"] = {
                "status": "degraded",
                "available": False,
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check Gmail service
        try:
            from backend.mcp_servers.gmail_server import list_labels
            services_status["gmail"] = {
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            services_status["gmail"] = {
                "status": "degraded",
                "available": False,
                "error": str(e)
            }
            overall_status = "degraded"
        
        # Check Flashcard service
        try:
            from backend.services.flashcard_storage import get_all_flashcard_sets
            services_status["flashcard"] = {
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            services_status["flashcard"] = {
                "status": "degraded",
                "available": False,
                "error": str(e)
            }
            overall_status = "degraded"
        
    except Exception as e:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }
