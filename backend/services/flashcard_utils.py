"""
Flashcard Utility Functions
Helper functions for working with flashcards and Canvas content.
"""

import re
from typing import List, Dict, Any, Optional
from backend.services.flashcard_generator import (
    extract_text_from_html,
    generate_flashcards_from_content,
    create_flashcards_from_canvas_content
)
from backend.services.flashcard_storage import FlashcardStorage


def create_flashcards_from_canvas_page(
    page_content: str,
    page_title: str,
    course_id: int,
    course_name: str,
    deck_name: Optional[str] = None,
    num_cards: int = 10
) -> Dict[str, Any]:
    """Create flashcards from a Canvas page.
    
    Args:
        page_content: HTML content of the page
        page_title: Title of the page
        course_id: Canvas course ID
        course_name: Name of the course
        deck_name: Name for the flashcard deck (defaults to page title)
        num_cards: Number of flashcards to generate
    
    Returns:
        Dictionary with deck_id and card information
    """
    storage = FlashcardStorage()
    
    # Generate flashcards
    flashcard_data = create_flashcards_from_canvas_content(
        content=page_content,
        course_name=course_name,
        source_type="page",
        source_name=page_title
    )
    
    flashcards = flashcard_data["flashcards"][:num_cards]
    
    # Create deck
    if not deck_name:
        deck_name = f"{course_name} - {page_title}"
    
    deck_id = storage.create_deck(
        deck_name=deck_name,
        course_id=course_id,
        course_name=course_name,
        description=f"Flashcards from page: {page_title}"
    )
    
    # Add flashcards to deck
    card_ids = []
    for card in flashcards:
        card_id = storage.add_flashcard(
            deck_id=deck_id,
            front=card['front'],
            back=card['back']
        )
        card_ids.append(card_id)
    
    return {
        "deck_id": deck_id,
        "deck_name": deck_name,
        "num_cards": len(card_ids),
        "card_ids": card_ids,
        "course_id": course_id,
        "course_name": course_name
    }


def create_flashcards_from_assignment(
    assignment_description: str,
    assignment_name: str,
    course_id: int,
    course_name: str,
    deck_name: Optional[str] = None,
    num_cards: int = 10
) -> Dict[str, Any]:
    """Create flashcards from an assignment description.
    
    Args:
        assignment_description: HTML description of the assignment
        assignment_name: Name of the assignment
        course_id: Canvas course ID
        course_name: Name of the course
        deck_name: Name for the flashcard deck (defaults to assignment name)
        num_cards: Number of flashcards to generate
    
    Returns:
        Dictionary with deck_id and card information
    """
    storage = FlashcardStorage()
    
    # Generate flashcards
    flashcard_data = create_flashcards_from_canvas_content(
        content=assignment_description,
        course_name=course_name,
        source_type="assignment",
        source_name=assignment_name
    )
    
    flashcards = flashcard_data["flashcards"][:num_cards]
    
    # Create deck
    if not deck_name:
        deck_name = f"{course_name} - {assignment_name}"
    
    deck_id = storage.create_deck(
        deck_name=deck_name,
        course_id=course_id,
        course_name=course_name,
        description=f"Flashcards from assignment: {assignment_name}"
    )
    
    # Add flashcards to deck
    card_ids = []
    for card in flashcards:
        card_id = storage.add_flashcard(
            deck_id=deck_id,
            front=card['front'],
            back=card['back']
        )
        card_ids.append(card_id)
    
    return {
        "deck_id": deck_id,
        "deck_name": deck_name,
        "num_cards": len(card_ids),
        "card_ids": card_ids,
        "course_id": course_id,
        "course_name": course_name
    }


def merge_decks(source_deck_id: str, target_deck_id: str) -> Dict[str, Any]:
    """Merge cards from one deck into another.
    
    Args:
        source_deck_id: ID of the source deck
        target_deck_id: ID of the target deck
    
    Returns:
        Dictionary with merge results
    """
    storage = FlashcardStorage()
    
    source_cards = storage.get_deck_cards(source_deck_id)
    target_cards = storage.get_deck_cards(target_deck_id)
    
    # Get existing fronts to avoid duplicates
    existing_fronts = {c['front'] for c in target_cards}
    
    merged_count = 0
    for card in source_cards:
        if card['front'] not in existing_fronts:
            storage.add_flashcard(
                deck_id=target_deck_id,
                front=card['front'],
                back=card['back'],
                tags=card.get('tags', [])
            )
            merged_count += 1
            existing_fronts.add(card['front'])
    
    return {
        "merged_count": merged_count,
        "total_cards_in_target": len(target_cards) + merged_count
    }


def get_deck_statistics(deck_id: str) -> Dict[str, Any]:
    """Get statistics for a flashcard deck.
    
    Args:
        deck_id: ID of the deck
    
    Returns:
        Dictionary with statistics
    """
    storage = FlashcardStorage()
    cards = storage.get_deck_cards(deck_id)
    deck = storage.get_deck(deck_id)
    study_stats = storage.get_study_stats(deck_id)
    
    if not cards:
        return {
            "deck_id": deck_id,
            "deck_name": deck.get("name", "Unknown"),
            "total_cards": 0,
            "cards_studied": 0,
            "average_mastery": 0,
            "study_sessions": 0
        }
    
    total_studied = sum(c.get("times_studied", 0) for c in cards)
    total_correct = sum(c.get("times_correct", 0) for c in cards)
    average_mastery = sum(c.get("mastery_level", 0) for c in cards) / len(cards) if cards else 0
    
    return {
        "deck_id": deck_id,
        "deck_name": deck.get("name", "Unknown"),
        "total_cards": len(cards),
        "cards_studied": total_studied,
        "cards_correct": total_correct,
        "average_accuracy": total_correct / total_studied if total_studied > 0 else 0,
        "average_mastery": average_mastery,
        "study_sessions": study_stats.get("total_sessions", 0),
        "total_study_time_seconds": study_stats.get("total_study_time_seconds", 0)
    }


def search_flashcards(query: str, deck_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search flashcards by query.
    
    Args:
        query: Search query
        deck_id: Optional deck ID to search within (None for all decks)
    
    Returns:
        List of matching flashcards
    """
    storage = FlashcardStorage()
    query_lower = query.lower()
    results = []
    
    if deck_id:
        cards = storage.get_deck_cards(deck_id)
    else:
        # Search all cards
        cards = list(storage.flashcards['cards'].values())
    
    for card in cards:
        # Search in front, back, and tags
        if (query_lower in card['front'].lower() or 
            query_lower in card['back'].lower() or
            any(query_lower in tag.lower() for tag in card.get('tags', []))):
            results.append(card)
    
    return results


def export_flashcards_for_anki(deck_id: str, output_file: str):
    """Export flashcards in Anki-compatible format.
    
    Args:
        deck_id: ID of the deck to export
        output_file: Path to output file
    """
    storage = FlashcardStorage()
    storage.export_deck_to_anki(deck_id, output_file)


def export_flashcards_for_quizlet(deck_id: str, output_file: str):
    """Export flashcards in Quizlet-compatible format (CSV).
    
    Args:
        deck_id: ID of the deck to export
        output_file: Path to output CSV file
    """
    storage = FlashcardStorage()
    storage.export_deck_to_csv(deck_id, output_file)

