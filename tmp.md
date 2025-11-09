# Canvas CRUD Operations Implementation Plan

## Overview

Implement complete CRUD operations for all 23 Canvas resource types identified, creating approximately 92 FastMCP tools organized by resource category. Each operation will follow the existing pattern with helper functions and FastMCP tool decorators.

## Current State

- File: `test_canvas.py` (588 lines)
- Existing operations: Courses (CRUD), Assignments (CRUD), Daily Briefing
- Architecture: FastMCP with `@mcp.tool()` decorators, error handling via `@handle_canvas_errors`
- Pattern: Helper functions + FastMCP tool wrappers

## Implementation Strategy

### Phase 1: Core Academic Resources (Priority 1)

Implement CRUD for the most commonly used academic resources.

#### 1.1 Submissions (4 operations)

- **Create**: `create_submission(course_id, assignment_id, submission_type, body/file/url)`
  - Helper: `create_submission_helper()` - Uses `assignment.submit()`
  - Tool: `@mcp.tool()` wrapper with validation
  - Parameters: course_id, assignment_id, submission_type, body (text), file (upload), url, comment
  - Returns: Submission details with ID, submitted_at, workflow_state

- **Read**: `get_submission(course_id, assignment_id, user_id)`, `list_submissions(course_id, assignment_id)`
  - Helper: `fetch_submission()`, `fetch_submissions()`
  - Tools: Two tools - single submission and list all
  - Returns: Submission data with grade, comments, attachments

- **Update**: `update_submission(course_id, assignment_id, user_id, grade, comment, excused)`
  - Helper: `update_submission_helper()` - Uses `submission.edit()`
  - Tool: For grading/feedback (Teacher/TA) or resubmission (Student)
  - Returns: Updated submission details

- **Delete**: `delete_submission(course_id, assignment_id, user_id)`
  - Helper: `delete_submission_helper()` - Uses `submission.delete()`
  - Tool: With confirmation message
  - Returns: Deletion confirmation

#### 1.2 Quizzes (4 operations)

- **Create**: `create_quiz(course_id, title, description, quiz_type, time_limit, allowed_attempts, ...)`
  - Helper: `create_quiz_helper()` - Uses `course.create_quiz()`
  - Tool: Comprehensive quiz creation with all settings
  - Parameters: title, description, quiz_type, time_limit, shuffle_answers, show_correct_answers, etc.

- **Read**: `get_quiz(course_id, quiz_id)`, `list_quizzes(course_id)`, `get_quiz_questions(course_id, quiz_id)`
  - Helpers: `fetch_quiz()`, `fetch_quizzes()`, `fetch_quiz_questions()`
  - Tools: Three tools for different read operations
  - Returns: Quiz details, questions, settings

- **Update**: `update_quiz(course_id, quiz_id, ...)`
  - Helper: `update_quiz_helper()` - Uses `quiz.edit()`
  - Tool: Update quiz settings and properties
  - Returns: Updated quiz details

- **Delete**: `delete_quiz(course_id, quiz_id)`
  - Helper: `delete_quiz_helper()` - Uses `quiz.delete()`
  - Tool: With confirmation
  - Returns: Deletion confirmation

#### 1.3 Quiz Submissions (4 operations)

- **Create**: `create_quiz_submission(course_id, quiz_id, access_code)`
  - Helper: `create_quiz_submission_helper()` - Uses `quiz.create_submission()`
  - Tool: Start quiz attempt
  - Returns: Quiz submission with access token

- **Read**: `get_quiz_submission(course_id, quiz_id, submission_id)`, `list_quiz_submissions(course_id, quiz_id)`
  - Helpers: `fetch_quiz_submission()`, `fetch_quiz_submissions()`
  - Tools: Single and list operations
  - Returns: Submission data with answers, score

- **Update**: `update_quiz_submission_score(course_id, quiz_id, submission_id, fudge_points, question_scores)`
  - Helper: `update_quiz_submission_helper()` - Uses `quiz_submission.update_score_and_comments()`
  - Tool: Manual grading for quizzes
  - Returns: Updated submission

- **Delete**: `delete_quiz_submission(course_id, quiz_id, submission_id)`
  - Helper: `delete_quiz_submission_helper()` - Uses `quiz_submission.delete()`
  - Tool: Delete quiz attempt
  - Returns: Confirmation

### Phase 2: Communication Resources (Priority 2)

#### 2.1 Discussions (4 operations)

- **Create**: `create_discussion(course_id, title, message, pinned, locked, require_initial_post, ...)`
  - Helper: `create_discussion_helper()` - Uses `course.create_discussion_topic()`
  - Tool: Create discussion topics
  - Parameters: title, message, pinned, locked, allow_rating, only_graders_can_rate, etc.

- **Read**: `get_discussion(course_id, topic_id)`, `list_discussions(course_id)`, `get_discussion_entries(course_id, topic_id)`
  - Helpers: `fetch_discussion()`, `fetch_discussions()`, `fetch_discussion_entries()`
  - Tools: Three read operations
  - Returns: Discussion data with entries/replies

- **Update**: `update_discussion(course_id, topic_id, ...)`
  - Helper: `update_discussion_helper()` - Uses `discussion.edit()`
  - Tool: Edit discussion topic
  - Returns: Updated discussion

- **Delete**: `delete_discussion(course_id, topic_id)`
  - Helper: `delete_discussion_helper()` - Uses `discussion.delete()`
  - Tool: Delete discussion
  - Returns: Confirmation

#### 2.2 Announcements (4 operations)

- **Create**: `create_announcement(course_id, title, message, delayed_post_at, ...)`
  - Helper: `create_announcement_helper()` - Uses `course.create_discussion_topic()` with `is_announcement=True`
  - Tool: Create announcements
  - Parameters: title, message, delayed_post_at, allow_rating

- **Read**: `get_announcement(course_id, topic_id)`, `list_announcements(course_id)`
  - Helpers: `fetch_announcement()`, `fetch_announcements()`
  - Tools: Single and list
  - Returns: Announcement data

- **Update**: `update_announcement(course_id, topic_id, ...)`
  - Helper: `update_announcement_helper()` - Uses `discussion.edit()`
  - Tool: Edit announcement
  - Returns: Updated announcement

- **Delete**: `delete_announcement(course_id, topic_id)`
  - Helper: `delete_announcement_helper()` - Uses `discussion.delete()`
  - Tool: Delete announcement
  - Returns: Confirmation

#### 2.3 Conversations/Messages (4 operations)

- **Create**: `send_message(recipient_ids, body, subject, group_conversation, ...)`
  - Helper: `create_conversation_helper()` - Uses `user.create_conversation()`
  - Tool: Send messages
  - Parameters: recipient_ids (list), body, subject, group_conversation, attachment_ids

- **Read**: `get_conversation(conversation_id)`, `list_conversations()`
  - Helpers: `fetch_conversation()`, `fetch_conversations()`
  - Tools: Single and list
  - Returns: Conversation with messages

- **Update**: `update_conversation(conversation_id, workflow_state, starred, ...)`
  - Helper: `update_conversation_helper()` - Uses `conversation.edit()`
  - Tool: Mark read/unread, archive, star
  - Returns: Updated conversation

- **Delete**: `delete_conversation(conversation_id)`
  - Helper: `delete_conversation_helper()` - Uses `conversation.delete()`
  - Tool: Delete conversation
  - Returns: Confirmation

### Phase 3: Content Organization (Priority 3)

#### 3.1 Modules (4 operations)

- **Create**: `create_module(course_id, name, position, unlock_at, require_sequential_progress, ...)`
  - Helper: `create_module_helper()` - Uses `course.create_module()`
  - Tool: Create content modules
  - Parameters: name, position, unlock_at, require_sequential_progress, prerequisite_module_ids

- **Read**: `get_module(course_id, module_id)`, `list_modules(course_id)`, `get_module_items(course_id, module_id)`
  - Helpers: `fetch_module()`, `fetch_modules()`, `fetch_module_items()`
  - Tools: Three read operations
  - Returns: Module data with items

- **Update**: `update_module(course_id, module_id, ...)`
  - Helper: `update_module_helper()` - Uses `module.edit()`
  - Tool: Update module settings
  - Returns: Updated module

- **Delete**: `delete_module(course_id, module_id)`
  - Helper: `delete_module_helper()` - Uses `module.delete()`
  - Tool: Delete module
  - Returns: Confirmation

#### 3.2 Module Items (4 operations)

- **Create**: `create_module_item(course_id, module_id, type, content_id, title, position, indent, ...)`
  - Helper: `create_module_item_helper()` - Uses `module.create_module_item()`
  - Tool: Add items to modules
  - Parameters: type (Assignment, File, Page, Discussion, Quiz, ExternalUrl, ExternalTool), content_id, title, position, indent

- **Read**: `get_module_item(course_id, module_id, item_id)`, `list_module_items(course_id, module_id)`
  - Helpers: `fetch_module_item()`, `fetch_module_items()`
  - Tools: Single and list
  - Returns: Module item data

- **Update**: `update_module_item(course_id, module_id, item_id, ...)`
  - Helper: `update_module_item_helper()` - Uses `module_item.edit()`
  - Tool: Update item settings
  - Returns: Updated item

- **Delete**: `delete_module_item(course_id, module_id, item_id)`
  - Helper: `delete_module_item_helper()` - Uses `module_item.delete()`
  - Tool: Remove item from module
  - Returns: Confirmation

#### 3.3 Pages/Wiki Pages (4 operations)

- **Create**: `create_page(course_id, title, body, editing_roles, published, ...)`
  - Helper: `create_page_helper()` - Uses `course.create_page()`
  - Tool: Create wiki page
  - Parameters: title, body (HTML), editing_roles, published, front_page

- **Read**: `get_page(course_id, url)`, `list_pages(course_id)`
  - Helpers: `fetch_page()`, `fetch_pages()`
  - Tools: Single and list (by URL)
  - Returns: Page content

- **Update**: `update_page(course_id, url, ...)`
  - Helper: `update_page_helper()` - Uses `page.edit()`
  - Tool: Edit page content
  - Returns: Updated page

- **Delete**: `delete_page(course_id, url)`
  - Helper: `delete_page_helper()` - Uses `page.delete()`
  - Tool: Delete page
  - Returns: Confirmation

### Phase 4: File Management (Priority 4)

#### 4.1 Files (4 operations)

- **Create**: `upload_file(course_id, file_path, folder_id, on_duplicate, ...)`
  - Helper: `upload_file_helper()` - Uses `course.upload()` or `folder.upload()`
  - Tool: Upload files
  - Parameters: file_path (local), folder_id, on_duplicate (rename/overwrite), parent_folder_path
  - Note: File upload requires multipart/form-data handling

- **Read**: `get_file(course_id, file_id)`, `list_files(course_id, folder_id, search_term)`
  - Helpers: `fetch_file()`, `fetch_files()`
  - Tools: Single and list with filtering
  - Returns: File metadata and download URLs

- **Update**: `update_file(course_id, file_id, name, locked, hidden, ...)`
  - Helper: `update_file_helper()` - Uses `file.edit()`
  - Tool: Rename, move, update file settings
  - Returns: Updated file

- **Delete**: `delete_file(course_id, file_id)`
  - Helper: `delete_file_helper()` - Uses `file.delete()`
  - Tool: Delete file
  - Returns: Confirmation

#### 4.2 Folders (4 operations)

- **Create**: `create_folder(course_id, name, parent_folder_id, locked, hidden, ...)`
  - Helper: `create_folder_helper()` - Uses `course.create_folder()` or `folder.create_folder()`
  - Tool: Create folder structure
  - Parameters: name, parent_folder_id, locked, hidden

- **Read**: `get_folder(course_id, folder_id)`, `list_folders(course_id, folder_id)`
  - Helpers: `fetch_folder()`, `fetch_folders()`
  - Tools: Single and list (recursive)
  - Returns: Folder structure

- **Update**: `update_folder(course_id, folder_id, name, locked, hidden, ...)`
  - Helper: `update_folder_helper()` - Uses `folder.edit()`
  - Tool: Rename, move folders
  - Returns: Updated folder

- **Delete**: `delete_folder(course_id, folder_id)`
  - Helper: `delete_folder_helper()` - Uses `folder.delete()`
  - Tool: Delete folder (must be empty)
  - Returns: Confirmation

### Phase 5: Assessment & Grading (Priority 5)

#### 5.1 Assignment Groups (4 operations)

- **Create**: `create_assignment_group(course_id, name, position, group_weight, rules, ...)`
  - Helper: `create_assignment_group_helper()` - Uses `course.create_assignment_group()`
  - Tool: Create assignment groups
  - Parameters: name, position, group_weight, rules (drop_lowest, drop_highest, never_drop)

- **Read**: `get_assignment_group(course_id, group_id)`, `list_assignment_groups(course_id)`
  - Helpers: `fetch_assignment_group()`, `fetch_assignment_groups()`
  - Tools: Single and list
  - Returns: Group data with assignments

- **Update**: `update_assignment_group(course_id, group_id, ...)`
  - Helper: `update_assignment_group_helper()` - Uses `assignment_group.edit()`
  - Tool: Update group settings
  - Returns: Updated group

- **Delete**: `delete_assignment_group(course_id, group_id)`
  - Helper: `delete_assignment_group_helper()` - Uses `assignment_group.delete()`
  - Tool: Delete group (assignments must be moved first)
  - Returns: Confirmation

#### 5.2 Rubrics (4 operations)

- **Create**: `create_rubric(course_id, title, criteria, points_possible, free_form_criterion_comments, ...)`
  - Helper: `create_rubric_helper()` - Uses `course.create_rubric()`
  - Tool: Create grading rubrics
  - Parameters: title, criteria (list of dicts with ratings), points_possible, free_form_criterion_comments

- **Read**: `get_rubric(course_id, rubric_id)`, `list_rubrics(course_id)`
  - Helpers: `fetch_rubric()`, `fetch_rubrics()`
  - Tools: Single and list
  - Returns: Rubric with criteria and ratings

- **Update**: `update_rubric(course_id, rubric_id, ...)`
  - Helper: `update_rubric_helper()` - Uses `rubric.edit()`
  - Tool: Update rubric criteria
  - Returns: Updated rubric

- **Delete**: `delete_rubric(course_id, rubric_id)`
  - Helper: `delete_rubric_helper()` - Uses `rubric.delete()`
  - Tool: Delete rubric
  - Returns: Confirmation

#### 5.3 Outcomes (4 operations)

- **Create**: `create_outcome(course_id, title, description, mastery_points, ratings, ...)`
  - Helper: `create_outcome_helper()` - Uses `course.create_outcome()` or `account.create_outcome()`
  - Tool: Create learning outcomes
  - Parameters: title, description, mastery_points, ratings (list), calculation_method

- **Read**: `get_outcome(course_id, outcome_id)`, `list_outcomes(course_id)`
  - Helpers: `fetch_outcome()`, `fetch_outcomes()`
  - Tools: Single and list
  - Returns: Outcome data

- **Update**: `update_outcome(course_id, outcome_id, ...)`
  - Helper: `update_outcome_helper()` - Uses `outcome.edit()`
  - Tool: Update outcome
  - Returns: Updated outcome

- **Delete**: `delete_outcome(course_id, outcome_id)`
  - Helper: `delete_outcome_helper()` - Uses `outcome.delete()`
  - Tool: Delete outcome
  - Returns: Confirmation

### Phase 6: User & Enrollment Management (Priority 6)

#### 6.1 Enrollments (4 operations)

- **Create**: `enroll_user(course_id, user_id, type, role, limit_privileges, ...)`
  - Helper: `enroll_user_helper()` - Uses `course.enroll_user()`
  - Tool: Enroll users in courses
  - Parameters: user_id, type (StudentEnrollment, TeacherEnrollment, TaEnrollment, ObserverEnrollment), role, limit_privileges, notify

- **Read**: `get_enrollment(course_id, enrollment_id)`, `list_enrollments(course_id, user_id, type)`
  - Helpers: `fetch_enrollment()`, `fetch_enrollments()`
  - Tools: Single and list with filtering
  - Returns: Enrollment data with grades

- **Update**: `update_enrollment(course_id, enrollment_id, task, ...)`
  - Helper: `update_enrollment_helper()` - Uses `enrollment.deactivate()` or `enrollment.reactivate()`
  - Tool: Conclude, deactivate, or reactivate enrollments
  - Parameters: task (conclude, delete, inactivate, deactivate), notify

- **Delete**: `delete_enrollment(course_id, enrollment_id, task)`
  - Helper: `delete_enrollment_helper()` - Uses `enrollment.delete()`
  - Tool: Remove enrollment
  - Returns: Confirmation

#### 6.2 Users (4 operations)

- **Create**: `create_user(name, short_name, sortable_name, email, ...)`
  - Helper: `create_user_helper()` - Uses `account.create_user()`
  - Tool: Create user accounts (Admin only)
  - Parameters: name, short_name, sortable_name, email, password, terms_of_use, skip_registration

- **Read**: `get_user(user_id)`, `get_current_user()`, `list_users(course_id, search_term)`
  - Helpers: `fetch_user()`, `fetch_current_user()`, `fetch_users()`
  - Tools: Three read operations
  - Returns: User profile data

- **Update**: `update_user(user_id, name, email, avatar, ...)`
  - Helper: `update_user_helper()` - Uses `user.edit()`
  - Tool: Update user profile
  - Returns: Updated user

- **Delete**: `delete_user(user_id)`
  - Helper: `delete_user_helper()` - Uses `user.delete()`
  - Tool: Delete user (Admin only)
  - Returns: Confirmation

### Phase 7: Additional Features (Priority 7)

#### 7.1 Groups (4 operations)

- **Create**: `create_group_category(course_id, name, self_signup, auto_leader, ...)`, `create_group(course_id, category_id, name, ...)`
  - Helpers: `create_group_category_helper()`, `create_group_helper()`
  - Tools: Two create operations
  - Parameters: name, self_signup, auto_leader, group_limit, sis_group_category_id

- **Read**: `get_group(course_id, group_id)`, `list_groups(course_id, category_id)`, `get_group_members(course_id, group_id)`
  - Helpers: `fetch_group()`, `fetch_groups()`, `fetch_group_members()`
  - Tools: Three read operations
  - Returns: Group data with members

- **Update**: `update_group(course_id, group_id, name, ...)`, `add_group_member(course_id, group_id, user_id)`
  - Helpers: `update_group_helper()`, `add_group_member_helper()`
  - Tools: Update group and manage members
  - Returns: Updated group

- **Delete**: `delete_group(course_id, group_id)`, `delete_group_category(course_id, category_id)`
  - Helpers: `delete_group_helper()`, `delete_group_category_helper()`
  - Tools: Two delete operations
  - Returns: Confirmation

#### 7.2 Sections (4 operations)

- **Create**: `create_section(course_id, name, sis_section_id, start_at, end_at, ...)`
  - Helper: `create_section_helper()` - Uses `course.create_section()`
  - Tool: Create course sections
  - Parameters: name, sis_section_id, start_at, end_at, restrict_enrollments_to_section_dates

- **Read**: `get_section(course_id, section_id)`, `list_sections(course_id)`
  - Helpers: `fetch_section()`, `fetch_sections()`
  - Tools: Single and list
  - Returns: Section data with enrollments

- **Update**: `update_section(course_id, section_id, ...)`
  - Helper: `update_section_helper()` - Uses `section.edit()`
  - Tool: Update section
  - Returns: Updated section

- **Delete**: `delete_section(course_id, section_id)`
  - Helper: `delete_section_helper()` - Uses `section.delete()`
  - Tool: Delete section
  - Returns: Confirmation

#### 7.3 Collaborations (4 operations)

- **Create**: `create_collaboration(course_id, collaboration_type, document_id, user_id, ...)`
  - Helper: `create_collaboration_helper()` - Uses `course.create_collaboration()`
  - Tool: Create collaborative documents
  - Parameters: collaboration_type (google_docs, office365, etherpad), document_id, user_id

- **Read**: `get_collaboration(course_id, collaboration_id)`, `list_collaborations(course_id)`
  - Helpers: `fetch_collaboration()`, `fetch_collaborations()`
  - Tools: Single and list
  - Returns: Collaboration data

- **Update**: `update_collaboration(course_id, collaboration_id, user_id, ...)`
  - Helper: `update_collaboration_helper()` - Uses `collaboration.edit()`
  - Tool: Update collaboration members
  - Returns: Updated collaboration

- **Delete**: `delete_collaboration(course_id, collaboration_id)`
  - Helper: `delete_collaboration_helper()` - Uses `collaboration.delete()`
  - Tool: Delete collaboration
  - Returns: Confirmation

#### 7.4 Calendar Events (4 operations)

- **Create**: `create_calendar_event(course_id, title, start_at, end_at, location_name, ...)`
  - Helper: `create_calendar_event_helper()` - Uses `course.create_calendar_event()`
  - Tool: Create calendar events
  - Parameters: title, start_at, end_at, location_name, context_code, all_day

- **Read**: `get_calendar_event(event_id)`, `list_calendar_events(course_id, start_date, end_date)`
  - Helpers: `fetch_calendar_event()`, `fetch_calendar_events()`
  - Tools: Single and list with date range
  - Returns: Event data

- **Update**: `update_calendar_event(event_id, ...)`
  - Helper: `update_calendar_event_helper()` - Uses `calendar_event.edit()`
  - Tool: Update event
  - Returns: Updated event

- **Delete**: `delete_calendar_event(event_id)`
  - Helper: `delete_calendar_event_helper()` - Uses `calendar_event.delete()`
  - Tool: Delete event
  - Returns: Confirmation

## Implementation Details

### Code Structure

- **File**: `test_canvas.py` (will grow to ~3000-4000 lines)
- **Organization**: Grouped by resource type with clear section headers
- **Pattern**: Each resource follows: Helper functions → FastMCP tools
- **Error Handling**: All tools use `@handle_canvas_errors` decorator

### Naming Conventions

- **Helper functions**: `{resource}_helper()` (e.g., `create_submission_helper()`)
- **FastMCP tools**: `{operation}_{resource}()` (e.g., `create_submission()`, `get_submission()`)
- **List operations**: `list_{resources}()` (e.g., `list_submissions()`)

### Common Patterns

#### Helper Function Pattern

```python
def create_{resource}_helper(
    course_id: int,
    # resource-specific parameters
    **kwargs
) -> dict:
    """Create {resource} in Canvas."""
    canvas = get_canvas_client()
    course = canvas.get_course(course_id)
    # Build parameters dict
    params = {...}
    # Create resource
    resource = course.create_{resource}({resource}={params})
    # Return formatted dict
    return {...}
```

#### FastMCP Tool Pattern

```python
@handle_canvas_errors
@mcp.tool()
def create_{resource}(
    course_id: int,
    # parameters with type hints
    **kwargs
) -> str:
    """Create a new {resource} in a Canvas course.
    
    Args:
        course_id: The ID of the course
        # parameter descriptions
    """
    # Validate access
    try:
        canvas = get_canvas_client()
        course = canvas.get_course(course_id)
        _ = course.name
    except CanvasException as e:
        # Handle errors
        return f"Error: {str(e)}"
    
    # Create resource
    resource = create_{resource}_helper(
        course_id=course_id,
        **kwargs
    )
    
    # Format response
    formatted = "✅ {Resource} created successfully!\n\n"
    # Add resource details
    return formatted
```

### Special Considerations

1. **File Uploads**: Requires handling multipart/form-data. May need additional library or custom implementation for file uploads via API.

2. **Bulk Operations**: Some resources support bulk operations (e.g., bulk grade updates). These will be separate tools.

3. **Pagination**: List operations should handle pagination for large result sets. Canvas API uses pagination headers.

4. **Validation**: Each tool should validate:

   - Course access permissions
   - Resource existence
   - Required parameters
   - Parameter types and formats

5. **Response Formatting**: All tools return formatted strings with:

   - Success/error indicators
   - Resource details
   - IDs for reference
   - URLs when available

### Testing Strategy

- Test each operation with valid inputs
- Test error cases (missing permissions, invalid IDs, etc.)
- Verify response formatting
- Test edge cases (empty lists, null values, etc.)

### Estimated Implementation

- **Total Operations**: ~92 CRUD operations
- **Estimated Lines**: ~3000-4000 lines total
- **Implementation Time**: Phased approach allows incremental development
- **Dependencies**: All operations use existing `canvasapi` library

## File Organization

### Current Structure

```
test_canvas.py
├── Configuration
├── FastMCP Server
├── Error Handling
├── Helper Functions (existing)
├── MCP Tools (existing - 6 tools)
└── Entry Point
```

### Proposed Structure (after implementation)

```
test_canvas.py
├── Configuration
├── FastMCP Server
├── Error Handling
├── Helper Functions
│   ├── Courses (existing)
│   ├── Assignments (existing)
│   ├── Submissions (new)
│   ├── Quizzes (new)
│   ├── Quiz Submissions (new)
│   ├── Discussions (new)
│   ├── Announcements (new)
│   ├── Modules (new)
│   ├── Module Items (new)
│   ├── Pages (new)
│   ├── Files (new)
│   ├── Folders (new)
│   ├── Assignment Groups (new)
│   ├── Rubrics (new)
│   ├── Outcomes (new)
│   ├── Enrollments (new)
│   ├── Users (new)
│   ├── Groups (new)
│   ├── Sections (new)
│   ├── Collaborations (new)
│   ├── Conversations (new)
│   └── Calendar Events (new)
├── MCP Tools
│   ├── Courses (4 tools - 1 existing, 3 new)
│   ├── Assignments (4 tools - 2 existing, 2 new)
│   ├── Submissions (4 tools - new)
│   ├── Quizzes (4 tools - new)
│   ├── Quiz Submissions (4 tools - new)
│   ├── Discussions (4 tools - new)
│   ├── Announcements (4 tools - new)
│   ├── Modules (4 tools - new)
│   ├── Module Items (4 tools - new)
│   ├── Pages (4 tools - new)
│   ├── Files (4 tools - new)
│   ├── Folders (4 tools - new)
│   ├── Assignment Groups (4 tools - new)
│   ├── Rubrics (4 tools - new)
│   ├── Outcomes (4 tools - new)
│   ├── Enrollments (4 tools - new)
│   ├── Users (4 tools - new)
│   ├── Groups (4 tools - new)
│   ├── Sections (4 tools - new)
│   ├── Collaborations (4 tools - new)
│   ├── Conversations (4 tools - new)
│   └── Calendar Events (4 tools - new)
└── Entry Point
```

## Implementation Order

1. **Phase 1**: Submissions, Quizzes, Quiz Submissions (12 operations)
2. **Phase 2**: Discussions, Announcements, Conversations (12 operations)
3. **Phase 3**: Modules, Module Items, Pages (12 operations)
4. **Phase 4**: Files, Folders (8 operations)
5. **Phase 5**: Assignment Groups, Rubrics, Outcomes (12 operations)
6. **Phase 6**: Enrollments, Users (8 operations)
7. **Phase 7**: Groups, Sections, Collaborations, Calendar Events (16 operations)
8. **Final**: Update Courses and Assignments with missing operations (2 operations)

**Total**: 86 new operations + 6 existing = 92 total operations