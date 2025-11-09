"""
Flashcard generation helper that uses Claude/OpenRouter to generate flashcards from course context.
"""
import os
import httpx
import json
from typing import List, Dict, Any, Optional

# Get OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet"


async def generate_flashcards_from_context(
    course_context: str,
    student_notes: Optional[str] = None,
    assignment_context: Optional[str] = None,
    num_flashcards: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate flashcards using Claude based on course context and student notes.
    
    Args:
        course_context: Course materials, assignment details, modules, etc.
        student_notes: Optional student notes
        assignment_context: Optional assignment-specific context
        num_flashcards: Number of flashcards to generate (default: 5)
    
    Returns:
        List of flashcards with 'question' and 'answer' fields
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is required for flashcard generation")
    
    # Truncate context to avoid timeout (limit to ~3000 chars total)
    MAX_CONTEXT_LENGTH = 3000
    if len(course_context) > MAX_CONTEXT_LENGTH:
        course_context = course_context[:MAX_CONTEXT_LENGTH] + "... [truncated]"
    
    if student_notes and len(student_notes) > 1000:
        student_notes = student_notes[:1000] + "... [truncated]"
    
    if assignment_context and len(assignment_context) > 1000:
        assignment_context = assignment_context[:1000] + "... [truncated]"
    
    # Build simple, concise prompt
    prompt_parts = [f"Content:\n{course_context}"]
    if student_notes:
        prompt_parts.append(f"\nNotes:\n{student_notes}")
    if assignment_context:
        prompt_parts.append(f"\nAssignment:\n{assignment_context}")
    
    prompt = f"""Create {num_flashcards} study flashcards from:

{"".join(prompt_parts)}

Return ONLY JSON: [{{"question": "Q", "answer": "A"}}, ...]"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Generate flashcards. Return only valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 1000
            }
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Canvas MCP Flashcard Generator"
            }
            
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            content = response_data["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            # Claude might wrap JSON in markdown code blocks
            if "```json" in content:
                # Extract JSON from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                # Extract from generic code block
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            # Parse JSON
            flashcards = json.loads(content)
            
            # Validate structure
            if not isinstance(flashcards, list):
                raise ValueError("Expected a list of flashcards")
            
            # Ensure each flashcard has question and answer
            validated_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and "question" in card and "answer" in card:
                    validated_flashcards.append({
                        "question": card["question"],
                        "answer": card["answer"],
                        "tags": card.get("tags", [])
                    })
            
            return validated_flashcards[:num_flashcards]
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse flashcards from Claude response: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error generating flashcards: {str(e)}")

