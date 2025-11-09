# Flashcard System Usage Guide

## Overview

The flashcard system allows you to create, manage, and review flashcards based on your Canvas courses. Flashcards can be generated automatically from course content using AI, and you can track your review progress.

## Features

- **Create Flashcard Sets**: Organize flashcards by course and assignment
- **AI-Powered Generation**: Automatically generate flashcards from course content
- **Progress Tracking**: Track which flashcards you've mastered
- **Review System**: Focus on flashcards that need review
- **Analytics**: View your progress statistics

## Usage Examples

### Creating Flashcards from Course Content

**Example Query:**
```
Create flashcards for course ID 12345, assignment ID 67890. 
Generate 15 flashcards based on the assignment details and course modules.
```

The system will:
1. Fetch course and assignment details
2. Get course modules and materials
3. Create a flashcard set
4. Generate flashcards using AI
5. Add them to the set

### Creating Flashcards with Student Notes

**Example Query:**
```
Create flashcards for course "Introduction to Python" (ID: 12345). 
Here are my notes: [your notes here]. Generate 20 flashcards.
```

### Reviewing Flashcards

**Example Query:**
```
Show me flashcards that need review from set [set_id]
```

**Example Query:**
```
Record that I got flashcard [flashcard_id] correct in set [set_id]
```

### Viewing Progress

**Example Query:**
```
Show me my progress for flashcard set [set_id]
```

**Example Query:**
```
List all my flashcard sets
```

## Flashcard Storage

Flashcards are stored in the `flashcard_data/` directory:
- `flashcards.json`: Contains all flashcard sets and their cards
- `progress.json`: Tracks review progress and statistics

## Flashcard Structure

Each flashcard has:
- `id`: Unique identifier
- `question`: The front of the card
- `answer`: The back of the card
- `tags`: Optional tags for categorization
- `created_at`: Timestamp

## Progress Tracking

The system tracks:
- `times_reviewed`: How many times you've reviewed the card
- `times_correct`: How many times you got it correct
- `times_incorrect`: How many times you got it incorrect
- `mastered`: Whether the card is mastered (3+ correct, 0 incorrect)
- `last_reviewed`: When you last reviewed it

## Tips

1. **Gather Context First**: The more course context you provide, the better the flashcards will be
2. **Review Regularly**: Use the review system to focus on cards you haven't mastered
3. **Use Tags**: Tag flashcards by topic for better organization
4. **Combine Sources**: Include assignment details, course modules, and your notes for comprehensive flashcards

## API Tools

### Flashcard Management
- `flashcard_create_set`: Create a new flashcard set
- `flashcard_add_flashcards`: Add flashcards to a set
- `flashcard_get_set`: Get a flashcard set by ID
- `flashcard_get_sets_by_course`: Get all sets for a course
- `flashcard_get_all_sets`: Get all flashcard sets
- `flashcard_delete_set`: Delete a flashcard set

### Flashcard Generation
- `flashcard_generate`: Generate flashcards using AI from course context

### Review & Progress
- `flashcard_get_needing_review`: Get flashcards that need review
- `flashcard_record_review`: Record a review (correct/incorrect)
- `flashcard_get_progress`: Get progress statistics

## Canvas Integration

The flashcard system integrates with Canvas to:
- Fetch assignment details and descriptions
- Get course modules and materials
- Access Canvas pages and extract their content
- Link flashcards to specific courses and assignments

This allows you to create context-aware flashcards that align with your course materials.

### Content Sources

The system can extract content from:

**Canvas Pages:**
- Use `canvas_get_course_pages` to list all pages in a course
- Use `canvas_get_page_content` to get the full HTML/text content from pages
- Pages often contain lecture notes, reading materials, and course content

**Assignment Descriptions:**
- Use `canvas_get_assignment_details` to get assignment information
- Includes assignment descriptions, requirements, and rubric information

**Example Workflow:**
1. List pages: `canvas_get_course_pages` (course_id: 12345)
2. Get page content: `canvas_get_page_content` (course_id: 12345, page_url: "lecture-1")
3. Get assignment details: `canvas_get_assignment_details` (course_id: 12345, assignment_id: 67890)
4. Use the extracted content in flashcard generation

The extracted page and assignment content is automatically included when generating flashcards, so you can create flashcards from Canvas pages and assignment materials!

