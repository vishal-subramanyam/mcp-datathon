"""
Flashcard MCP Server for creating, managing, and reviewing flashcards.
"""
import os
import asyncio
from typing import List, Any, Optional, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from backend.services.flashcard_storage import FlashcardStorage

# -----------------------------
# MCP SERVER
# -----------------------------
app = Server("flashcard-mcp-server")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def generate_flashcards_from_content(
    course_context: str,
    student_notes: str,
    num_flashcards: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate flashcards from course context and student notes.
    This is a placeholder - in practice, this would use an LLM to generate flashcards.
    For now, we'll create a simple structure that can be enhanced.
    """
    # This function will be enhanced to use Claude/OpenRouter to generate flashcards
    # For now, return empty list - the actual generation will happen via the API
    return []

# -----------------------------
# MCP TOOLS
# -----------------------------
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="create_flashcard_set",
            description="Create a new flashcard set for a course, optionally linked to an assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The ID of the course"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "The name of the course"
                    },
                    "assignment_id": {
                        "type": "integer",
                        "description": "Optional: The ID of the assignment this flashcard set is for"
                    },
                    "assignment_name": {
                        "type": "string",
                        "description": "Optional: The name of the assignment"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional: Student notes to include in flashcard generation"
                    }
                },
                "required": ["course_id", "course_name"]
            }
        ),
        Tool(
            name="add_flashcards_to_set",
            description="Add flashcards to an existing flashcard set. Flashcards should be provided as a list of objects with 'question' and 'answer' fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set"
                    },
                    "flashcards": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "The question/front of the flashcard"
                                },
                                "answer": {
                                    "type": "string",
                                    "description": "The answer/back of the flashcard"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional tags for categorizing the flashcard"
                                }
                            },
                            "required": ["question", "answer"]
                        },
                        "description": "List of flashcards to add"
                    }
                },
                "required": ["set_id", "flashcards"]
            }
        ),
        Tool(
            name="get_flashcard_set",
            description="Get a flashcard set by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set"
                    }
                },
                "required": ["set_id"]
            }
        ),
        Tool(
            name="get_flashcard_sets_by_course",
            description="Get all flashcard sets for a specific course",
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
            name="get_flashcards_needing_review",
            description="Get flashcards that need review (not mastered)",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of flashcards to return (optional)"
                    }
                },
                "required": ["set_id"]
            }
        ),
        Tool(
            name="record_flashcard_review",
            description="Record a flashcard review (correct or incorrect)",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set"
                    },
                    "flashcard_id": {
                        "type": "string",
                        "description": "The ID of the flashcard"
                    },
                    "correct": {
                        "type": "boolean",
                        "description": "Whether the student got the flashcard correct"
                    }
                },
                "required": ["set_id", "flashcard_id", "correct"]
            }
        ),
        Tool(
            name="get_flashcard_progress",
            description="Get progress statistics for a flashcard set",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set"
                    }
                },
                "required": ["set_id"]
            }
        ),
        Tool(
            name="get_all_flashcard_sets",
            description="Get all flashcard sets",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="delete_flashcard_set",
            description="Delete a flashcard set",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {
                        "type": "string",
                        "description": "The ID of the flashcard set to delete"
                    }
                },
                "required": ["set_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Optional[dict[str, Any]]) -> list[TextContent]:
    """Handle tool calls from the MCP client."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "create_flashcard_set":
            course_id = arguments.get("course_id")
            course_name = arguments.get("course_name")
            assignment_id = arguments.get("assignment_id")
            assignment_name = arguments.get("assignment_name")
            notes = arguments.get("notes")
            
            if not course_id or not course_name:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' and 'course_name' are required."
                )]
            
            set_id = FlashcardStorage.create_flashcard_set(
                course_id=course_id,
                course_name=course_name,
                assignment_id=assignment_id,
                assignment_name=assignment_name,
                notes=notes
            )
            
            formatted = "✅ Flashcard set created successfully!\n\n"
            formatted += f"Set ID: {set_id}\n"
            formatted += f"Course: {course_name} (ID: {course_id})\n"
            if assignment_name:
                formatted += f"Assignment: {assignment_name} (ID: {assignment_id})\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "add_flashcards_to_set":
            set_id = arguments.get("set_id")
            flashcards = arguments.get("flashcards", [])
            
            if not set_id:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id' is required."
                )]
            
            if not flashcards:
                return [TextContent(
                    type="text",
                    text="Error: 'flashcards' array is required."
                )]
            
            try:
                FlashcardStorage.add_flashcards_to_set(set_id, flashcards)
                formatted = f"✅ Added {len(flashcards)} flashcard(s) to set {set_id}!\n\n"
                return [TextContent(type="text", text=formatted)]
            except ValueError as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
        
        elif name == "get_flashcard_set":
            set_id = arguments.get("set_id")
            if not set_id:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id' is required."
                )]
            
            flashcard_set = FlashcardStorage.get_flashcard_set(set_id)
            if not flashcard_set:
                return [TextContent(
                    type="text",
                    text=f"Error: Flashcard set {set_id} not found."
                )]
            
            formatted = f"Flashcard Set: {flashcard_set['course_name']}\n\n"
            formatted += f"Set ID: {set_id}\n"
            formatted += f"Course ID: {flashcard_set['course_id']}\n"
            if flashcard_set.get('assignment_name'):
                formatted += f"Assignment: {flashcard_set['assignment_name']}\n"
            formatted += f"Flashcards: {len(flashcard_set.get('flashcards', []))}\n"
            formatted += f"Created: {flashcard_set.get('created_at')}\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_flashcard_sets_by_course":
            course_id = arguments.get("course_id")
            if not course_id:
                return [TextContent(
                    type="text",
                    text="Error: 'course_id' is required."
                )]
            
            sets = FlashcardStorage.get_flashcard_sets_by_course(course_id)
            if not sets:
                return [TextContent(
                    type="text",
                    text=f"No flashcard sets found for course {course_id}."
                )]
            
            formatted = f"Flashcard Sets for Course {course_id}:\n\n"
            for i, s in enumerate(sets, 1):
                formatted += f"{i}. Set ID: {s['id']}\n"
                formatted += f"   Course: {s['course_name']}\n"
                if s.get('assignment_name'):
                    formatted += f"   Assignment: {s['assignment_name']}\n"
                formatted += f"   Flashcards: {len(s.get('flashcards', []))}\n\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_flashcards_needing_review":
            set_id = arguments.get("set_id")
            limit = arguments.get("limit")
            
            if not set_id:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id' is required."
                )]
            
            flashcards = FlashcardStorage.get_flashcards_needing_review(set_id, limit)
            if not flashcards:
                return [TextContent(
                    type="text",
                    text=f"No flashcards needing review in set {set_id}."
                )]
            
            formatted = f"Flashcards Needing Review ({len(flashcards)}):\n\n"
            for i, card in enumerate(flashcards, 1):
                formatted += f"{i}. Q: {card.get('question', 'N/A')}\n"
                formatted += f"   A: {card.get('answer', 'N/A')}\n"
                formatted += f"   ID: {card.get('id')}\n\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "record_flashcard_review":
            set_id = arguments.get("set_id")
            flashcard_id = arguments.get("flashcard_id")
            correct = arguments.get("correct")
            
            if not set_id or not flashcard_id or correct is None:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id', 'flashcard_id', and 'correct' are required."
                )]
            
            FlashcardStorage.record_flashcard_review(set_id, flashcard_id, correct)
            
            status = "correct" if correct else "incorrect"
            formatted = f"✅ Recorded flashcard review: {status}\n\n"
            formatted += f"Set ID: {set_id}\n"
            formatted += f"Flashcard ID: {flashcard_id}\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_flashcard_progress":
            set_id = arguments.get("set_id")
            if not set_id:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id' is required."
                )]
            
            progress = FlashcardStorage.get_flashcard_progress(set_id)
            
            formatted = f"Flashcard Progress for Set {set_id}:\n\n"
            formatted += f"Total Reviews: {progress.get('total_reviews', 0)}\n"
            formatted += f"Mastered: {progress.get('mastered_count', 0)}\n"
            formatted += f"Needs Review: {progress.get('needs_review_count', 0)}\n"
            if progress.get('last_reviewed'):
                formatted += f"Last Reviewed: {progress['last_reviewed']}\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "get_all_flashcard_sets":
            sets = FlashcardStorage.get_all_sets()
            if not sets:
                return [TextContent(
                    type="text",
                    text="No flashcard sets found."
                )]
            
            formatted = f"All Flashcard Sets ({len(sets)}):\n\n"
            for i, s in enumerate(sets, 1):
                formatted += f"{i}. {s['course_name']}\n"
                formatted += f"   Set ID: {s['id']}\n"
                formatted += f"   Flashcards: {len(s.get('flashcards', []))}\n"
                if s.get('assignment_name'):
                    formatted += f"   Assignment: {s['assignment_name']}\n"
                formatted += "\n"
            
            return [TextContent(type="text", text=formatted)]
        
        elif name == "delete_flashcard_set":
            set_id = arguments.get("set_id")
            if not set_id:
                return [TextContent(
                    type="text",
                    text="Error: 'set_id' is required."
                )]
            
            try:
                FlashcardStorage.delete_flashcard_set(set_id)
                return [TextContent(
                    type="text",
                    text=f"✅ Flashcard set {set_id} deleted successfully."
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error deleting flashcard set: {str(e)}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
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

