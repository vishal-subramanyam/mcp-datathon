"""
Flashcard Storage System
Handles storage and management of flashcards in JSON format.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

FLASHCARD_FILE = "flashcards.json"

class FlashcardStorage:
    """Manages flashcard storage and operations."""
    
    def __init__(self, storage_file: str = FLASHCARD_FILE):
        """Initialize flashcard storage.
        
        Args:
            storage_file: Path to the JSON file for storing flashcards
        """
        self.storage_file = storage_file
        self.flashcards = self.load_flashcards()
    
    def load_flashcards(self) -> Dict[str, Any]:
        """Load flashcards from JSON file.
        
        Returns:
            Dictionary containing decks, cards, and study sessions
        """
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, create a new one
                print(f"Warning: Could not load flashcard file: {e}. Creating new file.")
                return self._create_empty_structure()
        return self._create_empty_structure()
    
    def _create_empty_structure(self) -> Dict[str, Any]:
        """Create an empty flashcard structure.
        
        Returns:
            Empty flashcard structure dictionary
        """
        return {
            "decks": {},
            "cards": {},
            "study_sessions": [],
            "version": "1.0"
        }
    
    def save_flashcards(self):
        """Save flashcards to JSON file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.flashcards, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Failed to save flashcards: {e}")
    
    def create_deck(
        self, 
        deck_name: str, 
        course_id: Optional[int] = None, 
        course_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create a new flashcard deck.
        
        Args:
            deck_name: Name of the deck
            course_id: Optional Canvas course ID
            course_name: Optional course name
            description: Optional deck description
        
        Returns:
            Deck ID
        """
        deck_id = f"deck_{int(datetime.now().timestamp() * 1000)}"
        self.flashcards['decks'][deck_id] = {
            "id": deck_id,
            "name": deck_name,
            "description": description,
            "course_id": course_id,
            "course_name": course_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "card_ids": []
        }
        self.save_flashcards()
        return deck_id
    
    def add_flashcard(
        self, 
        deck_id: str, 
        front: str, 
        back: str, 
        tags: Optional[List[str]] = None,
        difficulty: str = "medium"
    ) -> str:
        """Add a flashcard to a deck.
        
        Args:
            deck_id: ID of the deck
            front: Front of the flashcard (question)
            back: Back of the flashcard (answer)
            tags: Optional list of tags
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            Card ID
        """
        if deck_id not in self.flashcards['decks']:
            raise ValueError(f"Deck {deck_id} does not exist")
        
        card_id = f"card_{int(datetime.now().timestamp() * 1000)}"
        self.flashcards['cards'][card_id] = {
            "id": card_id,
            "deck_id": deck_id,
            "front": front,
            "back": back,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "times_studied": 0,
            "times_correct": 0,
            "times_incorrect": 0,
            "last_studied": None,
            "difficulty": difficulty,
            "mastery_level": 0  # 0-100, based on performance
        }
        self.flashcards['decks'][deck_id]["card_ids"].append(card_id)
        self.flashcards['decks'][deck_id]["updated_at"] = datetime.now().isoformat()
        self.save_flashcards()
        return card_id
    
    def get_deck_cards(self, deck_id: str) -> List[Dict[str, Any]]:
        """Get all cards in a deck.
        
        Args:
            deck_id: ID of the deck
        
        Returns:
            List of card dictionaries
        """
        if deck_id not in self.flashcards['decks']:
            raise ValueError(f"Deck {deck_id} does not exist")
        
        card_ids = self.flashcards['decks'][deck_id]["card_ids"]
        return [self.flashcards['cards'][card_id] for card_id in card_ids if card_id in self.flashcards['cards']]
    
    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific card by ID.
        
        Args:
            card_id: ID of the card
        
        Returns:
            Card dictionary or None if not found
        """
        return self.flashcards['cards'].get(card_id)
    
    def update_card(
        self, 
        card_id: str, 
        front: Optional[str] = None, 
        back: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None
    ):
        """Update a flashcard.
        
        Args:
            card_id: ID of the card
            front: New front text (optional)
            back: New back text (optional)
            tags: New tags (optional)
            difficulty: New difficulty (optional)
        """
        if card_id not in self.flashcards['cards']:
            raise ValueError(f"Card {card_id} does not exist")
        
        card = self.flashcards['cards'][card_id]
        if front is not None:
            card["front"] = front
        if back is not None:
            card["back"] = back
        if tags is not None:
            card["tags"] = tags
        if difficulty is not None:
            card["difficulty"] = difficulty
        
        card["updated_at"] = datetime.now().isoformat()
        self.save_flashcards()
    
    def update_card_stats(self, card_id: str, correct: bool):
        """Update card statistics after studying.
        
        Args:
            card_id: ID of the card
            correct: Whether the answer was correct
        """
        if card_id not in self.flashcards['cards']:
            raise ValueError(f"Card {card_id} does not exist")
        
        card = self.flashcards['cards'][card_id]
        card["times_studied"] += 1
        if correct:
            card["times_correct"] += 1
        else:
            card["times_incorrect"] += 1
        card["last_studied"] = datetime.now().isoformat()
        
        # Calculate mastery level (0-100)
        total = card["times_studied"]
        if total > 0:
            accuracy = card["times_correct"] / total
            card["mastery_level"] = int(accuracy * 100)
        
        self.save_flashcards()
    
    def get_all_decks(self) -> List[Dict[str, Any]]:
        """Get all flashcard decks.
        
        Returns:
            List of deck dictionaries
        """
        decks = list(self.flashcards['decks'].values())
        # Add card count to each deck
        for deck in decks:
            deck["card_count"] = len(deck["card_ids"])
        return decks
    
    def get_deck(self, deck_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific deck by ID.
        
        Args:
            deck_id: ID of the deck
        
        Returns:
            Deck dictionary or None if not found
        """
        if deck_id not in self.flashcards['decks']:
            return None
        
        deck = self.flashcards['decks'][deck_id].copy()
        deck["card_count"] = len(deck["card_ids"])
        return deck
    
    def delete_card(self, card_id: str):
        """Delete a flashcard.
        
        Args:
            card_id: ID of the card to delete
        """
        if card_id not in self.flashcards['cards']:
            raise ValueError(f"Card {card_id} does not exist")
        
        card = self.flashcards['cards'][card_id]
        deck_id = card["deck_id"]
        
        if deck_id in self.flashcards['decks']:
            if card_id in self.flashcards['decks'][deck_id]["card_ids"]:
                self.flashcards['decks'][deck_id]["card_ids"].remove(card_id)
            self.flashcards['decks'][deck_id]["updated_at"] = datetime.now().isoformat()
        
        del self.flashcards['cards'][card_id]
        self.save_flashcards()
    
    def delete_deck(self, deck_id: str):
        """Delete a flashcard deck and all its cards.
        
        Args:
            deck_id: ID of the deck to delete
        """
        if deck_id not in self.flashcards['decks']:
            raise ValueError(f"Deck {deck_id} does not exist")
        
        # Delete all cards in the deck
        card_ids = self.flashcards['decks'][deck_id]["card_ids"].copy()
        for card_id in card_ids:
            if card_id in self.flashcards['cards']:
                del self.flashcards['cards'][card_id]
        
        # Delete the deck
        del self.flashcards['decks'][deck_id]
        self.save_flashcards()
    
    def get_cards_for_study(self, deck_id: str, num_cards: Optional[int] = None, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cards for studying, optionally filtered by difficulty.
        
        Args:
            deck_id: ID of the deck
            num_cards: Maximum number of cards to return (None for all)
            difficulty: Filter by difficulty (easy, medium, hard, or None for all)
        
        Returns:
            List of card dictionaries
        """
        cards = self.get_deck_cards(deck_id)
        
        # Filter by difficulty if specified
        if difficulty:
            cards = [c for c in cards if c.get("difficulty") == difficulty]
        
        # Sort by mastery level (least mastered first) and last studied
        cards.sort(key=lambda c: (
            c.get("mastery_level", 100),  # Lower mastery first
            c.get("times_studied", 0)  # Less studied first
        ))
        
        # Limit number of cards
        if num_cards:
            cards = cards[:num_cards]
        
        return cards
    
    def add_study_session(self, deck_id: str, cards_studied: int, cards_correct: int, duration_seconds: int):
        """Record a study session.
        
        Args:
            deck_id: ID of the deck studied
            cards_studied: Number of cards studied
            cards_correct: Number of cards answered correctly
            duration_seconds: Duration of study session in seconds
        """
        session = {
            "id": f"session_{int(datetime.now().timestamp() * 1000)}",
            "deck_id": deck_id,
            "cards_studied": cards_studied,
            "cards_correct": cards_correct,
            "accuracy": cards_correct / cards_studied if cards_studied > 0 else 0,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat()
        }
        self.flashcards['study_sessions'].append(session)
        self.save_flashcards()
        return session["id"]
    
    def get_study_stats(self, deck_id: Optional[str] = None) -> Dict[str, Any]:
        """Get study statistics.
        
        Args:
            deck_id: Optional deck ID to filter by (None for all decks)
        
        Returns:
            Dictionary with study statistics
        """
        sessions = self.flashcards['study_sessions']
        if deck_id:
            sessions = [s for s in sessions if s.get("deck_id") == deck_id]
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_cards_studied": 0,
                "total_cards_correct": 0,
                "average_accuracy": 0,
                "total_study_time_seconds": 0
            }
        
        total_cards_studied = sum(s["cards_studied"] for s in sessions)
        total_cards_correct = sum(s["cards_correct"] for s in sessions)
        total_time = sum(s["duration_seconds"] for s in sessions)
        
        return {
            "total_sessions": len(sessions),
            "total_cards_studied": total_cards_studied,
            "total_cards_correct": total_cards_correct,
            "average_accuracy": total_cards_correct / total_cards_studied if total_cards_studied > 0 else 0,
            "total_study_time_seconds": total_time,
            "average_study_time_seconds": total_time / len(sessions) if sessions else 0
        }
    
    def export_deck_to_csv(self, deck_id: str, output_file: str):
        """Export a deck to CSV format.
        
        Args:
            deck_id: ID of the deck to export
            output_file: Path to output CSV file
        """
        import csv
        
        cards = self.get_deck_cards(deck_id)
        deck = self.get_deck(deck_id)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Front', 'Back', 'Tags', 'Difficulty', 'Times Studied', 'Mastery Level'])
            for card in cards:
                writer.writerow([
                    card['front'],
                    card['back'],
                    ', '.join(card.get('tags', [])),
                    card.get('difficulty', 'medium'),
                    card.get('times_studied', 0),
                    card.get('mastery_level', 0)
                ])
    
    def export_deck_to_json(self, deck_id: str, output_file: str):
        """Export a deck to JSON format.
        
        Args:
            deck_id: ID of the deck to export
            output_file: Path to output JSON file
        """
        deck = self.get_deck(deck_id)
        cards = self.get_deck_cards(deck_id)
        
        export_data = {
            "deck": deck,
            "cards": cards,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def export_deck_to_anki(self, deck_id: str, output_file: str):
        """Export a deck to Anki-compatible format (CSV with Anki fields).
        
        Args:
            deck_id: ID of the deck to export
            output_file: Path to output CSV file
        """
        import csv
        
        cards = self.get_deck_cards(deck_id)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Anki format: Front, Back
            writer.writerow(['Front', 'Back'])
            for card in cards:
                writer.writerow([card['front'], card['back']])


# ============================================================================
# Static Methods for "Sets" JSON Structure (used by MCP service)
# ============================================================================

import uuid

FLASHCARD_SETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "flashcards", "flashcards.json")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "flashcards", "progress.json")


def _load_sets_data() -> Dict[str, Any]:
    """Load flashcard sets from JSON file."""
    if os.path.exists(FLASHCARD_SETS_FILE):
        try:
            with open(FLASHCARD_SETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"sets": []}
    return {"sets": []}


def _save_sets_data(data: Dict[str, Any]):
    """Save flashcard sets to JSON file."""
    os.makedirs(os.path.dirname(FLASHCARD_SETS_FILE), exist_ok=True)
    with open(FLASHCARD_SETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_progress_data() -> Dict[str, Any]:
    """Load progress data from JSON file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"sets": {}}
    return {"sets": {}}


def _save_progress_data(data: Dict[str, Any]):
    """Save progress data to JSON file."""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Static methods for MCP service
class FlashcardStorageStatic:
    """Static methods for flashcard operations using the sets JSON structure."""
    
    @staticmethod
    def create_flashcard_set(
        course_id: int,
        course_name: str,
        assignment_id: Optional[int] = None,
        assignment_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Create a new flashcard set.
        
        Args:
            course_id: Canvas course ID
            course_name: Course name
            assignment_id: Optional assignment ID
            assignment_name: Optional assignment name
            notes: Optional notes
            
        Returns:
            Set ID
        """
        data = _load_sets_data()
        
        set_id = str(uuid.uuid4())
        new_set = {
            "id": set_id,
            "course_id": course_id,
            "course_name": course_name,
            "assignment_id": assignment_id,
            "assignment_name": assignment_name,
            "notes": notes,
            "flashcards": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        data["sets"].append(new_set)
        _save_sets_data(data)
        
        # Initialize progress tracking for this set
        progress_data = _load_progress_data()
        progress_data["sets"][set_id] = {
            "flashcard_reviews": {},
            "last_reviewed": None,
            "total_reviews": 0,
            "mastered_count": 0,
            "needs_review_count": 0
        }
        _save_progress_data(progress_data)
        
        return set_id
    
    @staticmethod
    def add_flashcards_to_set(set_id: str, flashcards: List[Dict[str, Any]]):
        """Add flashcards to a set.
        
        Args:
            set_id: Set ID
            flashcards: List of flashcard dicts with 'question' and 'answer' keys
        """
        data = _load_sets_data()
        
        # Find the set
        target_set = None
        for s in data["sets"]:
            if s["id"] == set_id:
                target_set = s
                break
        
        if not target_set:
            raise ValueError(f"Flashcard set {set_id} not found")
        
        # Add flashcards
        for card in flashcards:
            card_id = str(uuid.uuid4())
            new_card = {
                "question": card.get("question", ""),
                "answer": card.get("answer", ""),
                "tags": card.get("tags", []),
                "id": card_id,
                "created_at": datetime.now().isoformat()
            }
            target_set["flashcards"].append(new_card)
            
            # Initialize progress tracking for this card
            progress_data = _load_progress_data()
            if set_id not in progress_data["sets"]:
                progress_data["sets"][set_id] = {
                    "flashcard_reviews": {},
                    "last_reviewed": None,
                    "total_reviews": 0,
                    "mastered_count": 0,
                    "needs_review_count": 0
                }
            
            progress_data["sets"][set_id]["flashcard_reviews"][card_id] = {
                "times_reviewed": 0,
                "times_correct": 0,
                "times_incorrect": 0,
                "last_reviewed": None,
                "mastered": False,
                "difficulty": "medium"
            }
            _save_progress_data(progress_data)
        
        target_set["updated_at"] = datetime.now().isoformat()
        _save_sets_data(data)
    
    @staticmethod
    def get_flashcard_set(set_id: str) -> Optional[Dict[str, Any]]:
        """Get a flashcard set by ID.
        
        Args:
            set_id: Set ID
            
        Returns:
            Flashcard set dict or None
        """
        data = _load_sets_data()
        for s in data["sets"]:
            if s["id"] == set_id:
                return s
        return None
    
    @staticmethod
    def get_flashcard_sets_by_course(course_id: int) -> List[Dict[str, Any]]:
        """Get all flashcard sets for a course.
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of flashcard sets
        """
        data = _load_sets_data()
        return [s for s in data["sets"] if s.get("course_id") == course_id]
    
    @staticmethod
    def get_flashcards_needing_review(set_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get flashcards that need review.
        
        Args:
            set_id: Set ID
            limit: Optional limit on number of cards
            
        Returns:
            List of flashcards
        """
        flashcard_set = FlashcardStorageStatic.get_flashcard_set(set_id)
        if not flashcard_set:
            return []
        
        progress_data = _load_progress_data()
        set_progress = progress_data.get("sets", {}).get(set_id, {})
        reviews = set_progress.get("flashcard_reviews", {})
        
        # Get cards that haven't been mastered
        cards_needing_review = []
        for card in flashcard_set.get("flashcards", []):
            card_id = card["id"]
            review_data = reviews.get(card_id, {})
            if not review_data.get("mastered", False):
                cards_needing_review.append(card)
        
        # Sort by times reviewed (least reviewed first)
        cards_needing_review.sort(key=lambda c: reviews.get(c["id"], {}).get("times_reviewed", 0))
        
        if limit:
            return cards_needing_review[:limit]
        return cards_needing_review
    
    @staticmethod
    def record_flashcard_review(set_id: str, flashcard_id: str, correct: bool):
        """Record a flashcard review.
        
        Args:
            set_id: Set ID
            flashcard_id: Flashcard ID
            correct: Whether the answer was correct
        """
        progress_data = _load_progress_data()
        
        if set_id not in progress_data["sets"]:
            progress_data["sets"][set_id] = {
                "flashcard_reviews": {},
                "last_reviewed": None,
                "total_reviews": 0,
                "mastered_count": 0,
                "needs_review_count": 0
            }
        
        set_progress = progress_data["sets"][set_id]
        
        if flashcard_id not in set_progress["flashcard_reviews"]:
            set_progress["flashcard_reviews"][flashcard_id] = {
                "times_reviewed": 0,
                "times_correct": 0,
                "times_incorrect": 0,
                "last_reviewed": None,
                "mastered": False,
                "difficulty": "medium"
            }
        
        card_progress = set_progress["flashcard_reviews"][flashcard_id]
        card_progress["times_reviewed"] += 1
        if correct:
            card_progress["times_correct"] += 1
        else:
            card_progress["times_incorrect"] += 1
        card_progress["last_reviewed"] = datetime.now().isoformat()
        
        # Check if mastered (correct 3 times in a row or 80% accuracy with 5+ reviews)
        if card_progress["times_reviewed"] >= 5:
            accuracy = card_progress["times_correct"] / card_progress["times_reviewed"]
            if accuracy >= 0.8:
                card_progress["mastered"] = True
        
        set_progress["last_reviewed"] = datetime.now().isoformat()
        set_progress["total_reviews"] += 1
        
        # Update counts
        mastered_count = sum(1 for c in set_progress["flashcard_reviews"].values() if c.get("mastered", False))
        set_progress["mastered_count"] = mastered_count
        set_progress["needs_review_count"] = len(set_progress["flashcard_reviews"]) - mastered_count
        
        _save_progress_data(progress_data)
    
    @staticmethod
    def get_flashcard_progress(set_id: str) -> Dict[str, Any]:
        """Get progress for a flashcard set.
        
        Args:
            set_id: Set ID
            
        Returns:
            Progress dictionary
        """
        progress_data = _load_progress_data()
        return progress_data.get("sets", {}).get(set_id, {
            "total_reviews": 0,
            "mastered_count": 0,
            "needs_review_count": 0,
            "last_reviewed": None
        })
    
    @staticmethod
    def get_all_sets() -> List[Dict[str, Any]]:
        """Get all flashcard sets.
        
        Returns:
            List of all flashcard sets
        """
        data = _load_sets_data()
        return data.get("sets", [])
    
    @staticmethod
    def delete_flashcard_set(set_id: str):
        """Delete a flashcard set.
        
        Args:
            set_id: Set ID
        """
        data = _load_sets_data()
        data["sets"] = [s for s in data["sets"] if s["id"] != set_id]
        _save_sets_data(data)
        
        # Remove progress data
        progress_data = _load_progress_data()
        if set_id in progress_data.get("sets", {}):
            del progress_data["sets"][set_id]
            _save_progress_data(progress_data)


# Alias for backward compatibility with MCP service
FlashcardStorage.create_flashcard_set = FlashcardStorageStatic.create_flashcard_set
FlashcardStorage.add_flashcards_to_set = FlashcardStorageStatic.add_flashcards_to_set
FlashcardStorage.get_flashcard_set = FlashcardStorageStatic.get_flashcard_set
FlashcardStorage.get_flashcard_sets_by_course = FlashcardStorageStatic.get_flashcard_sets_by_course
FlashcardStorage.get_flashcards_needing_review = FlashcardStorageStatic.get_flashcards_needing_review
FlashcardStorage.record_flashcard_review = FlashcardStorageStatic.record_flashcard_review
FlashcardStorage.get_flashcard_progress = FlashcardStorageStatic.get_flashcard_progress
FlashcardStorage.get_all_sets = FlashcardStorageStatic.get_all_sets
FlashcardStorage.delete_flashcard_set = FlashcardStorageStatic.delete_flashcard_set


# Standalone function for health check
def get_all_flashcard_sets() -> List[Dict[str, Any]]:
    """Get all flashcard sets (standalone function for health check)."""
    return FlashcardStorageStatic.get_all_sets()
