"""
Flashcard storage system for managing flashcards and review progress.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

# Storage directory
STORAGE_DIR = Path("flashcard_data")
STORAGE_DIR.mkdir(exist_ok=True)

# File paths
FLASHCARDS_FILE = STORAGE_DIR / "flashcards.json"
PROGRESS_FILE = STORAGE_DIR / "progress.json"


class FlashcardStorage:
    """Manages flashcard storage and retrieval."""
    
    @staticmethod
    def _load_json(file_path: Path, default: Any = None) -> Any:
        """Load JSON from file."""
        if default is None:
            default = {}
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    @staticmethod
    def _save_json(file_path: Path, data: Any):
        """Save JSON to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def create_flashcard_set(
        course_id: int,
        course_name: str,
        assignment_id: Optional[int] = None,
        assignment_name: Optional[str] = None,
        notes: Optional[str] = None,
        flashcards: List[Dict[str, Any]] = None
    ) -> str:
        """Create a new flashcard set."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        
        set_id = str(uuid.uuid4())
        flashcard_set = {
            "id": set_id,
            "course_id": course_id,
            "course_name": course_name,
            "assignment_id": assignment_id,
            "assignment_name": assignment_name,
            "notes": notes,
            "flashcards": flashcards or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if "sets" not in flashcards_data:
            flashcards_data["sets"] = []
        flashcards_data["sets"].append(flashcard_set)
        
        FlashcardStorage._save_json(FLASHCARDS_FILE, flashcards_data)
        
        # Initialize progress tracking
        progress_data = FlashcardStorage._load_json(PROGRESS_FILE, {})
        if "sets" not in progress_data:
            progress_data["sets"] = {}
        
        progress_data["sets"][set_id] = {
            "flashcard_reviews": {},
            "last_reviewed": None,
            "total_reviews": 0,
            "mastered_count": 0,
            "needs_review_count": 0
        }
        
        FlashcardStorage._save_json(PROGRESS_FILE, progress_data)
        
        return set_id
    
    @staticmethod
    def get_flashcard_set(set_id: str) -> Optional[Dict[str, Any]]:
        """Get a flashcard set by ID."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        sets = flashcards_data.get("sets", [])
        for flashcard_set in sets:
            if flashcard_set.get("id") == set_id:
                return flashcard_set
        return None
    
    @staticmethod
    def get_flashcard_sets_by_course(course_id: int) -> List[Dict[str, Any]]:
        """Get all flashcard sets for a course."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        sets = flashcards_data.get("sets", [])
        return [s for s in sets if s.get("course_id") == course_id]
    
    @staticmethod
    def add_flashcards_to_set(set_id: str, flashcards: List[Dict[str, Any]]):
        """Add flashcards to an existing set."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        sets = flashcards_data.get("sets", [])
        
        for flashcard_set in sets:
            if flashcard_set.get("id") == set_id:
                if "flashcards" not in flashcard_set:
                    flashcard_set["flashcards"] = []
                
                # Add IDs to flashcards if they don't have them
                for card in flashcards:
                    if "id" not in card:
                        card["id"] = str(uuid.uuid4())
                    card["created_at"] = datetime.now(timezone.utc).isoformat()
                
                flashcard_set["flashcards"].extend(flashcards)
                flashcard_set["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                FlashcardStorage._save_json(FLASHCARDS_FILE, flashcards_data)
                
                # Update progress tracking
                progress_data = FlashcardStorage._load_json(PROGRESS_FILE, {})
                if "sets" not in progress_data:
                    progress_data["sets"] = {}
                if set_id not in progress_data["sets"]:
                    progress_data["sets"][set_id] = {
                        "flashcard_reviews": {},
                        "last_reviewed": None,
                        "total_reviews": 0,
                        "mastered_count": 0,
                        "needs_review_count": 0
                    }
                
                # Initialize progress for new flashcards
                if "flashcard_reviews" not in progress_data["sets"][set_id]:
                    progress_data["sets"][set_id]["flashcard_reviews"] = {}
                
                for card in flashcards:
                    card_id = card.get("id")
                    if card_id and card_id not in progress_data["sets"][set_id]["flashcard_reviews"]:
                        progress_data["sets"][set_id]["flashcard_reviews"][card_id] = {
                            "times_reviewed": 0,
                            "times_correct": 0,
                            "times_incorrect": 0,
                            "last_reviewed": None,
                            "mastered": False,
                            "difficulty": "medium"
                        }
                
                FlashcardStorage._save_json(PROGRESS_FILE, progress_data)
                return
        
        raise ValueError(f"Flashcard set {set_id} not found")
    
    @staticmethod
    def record_flashcard_review(
        set_id: str,
        flashcard_id: str,
        correct: bool
    ):
        """Record a flashcard review."""
        progress_data = FlashcardStorage._load_json(PROGRESS_FILE, {})
        
        if "sets" not in progress_data:
            progress_data["sets"] = {}
        if set_id not in progress_data["sets"]:
            progress_data["sets"][set_id] = {
                "flashcard_reviews": {},
                "last_reviewed": None,
                "total_reviews": 0,
                "mastered_count": 0,
                "needs_review_count": 0
            }
        
        set_progress = progress_data["sets"][set_id]
        
        if "flashcard_reviews" not in set_progress:
            set_progress["flashcard_reviews"] = {}
        
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
        card_progress["last_reviewed"] = datetime.now(timezone.utc).isoformat()
        
        if correct:
            card_progress["times_correct"] += 1
            # Mark as mastered if correct 3+ times in a row
            if card_progress["times_correct"] >= 3 and card_progress["times_incorrect"] == 0:
                card_progress["mastered"] = True
        else:
            card_progress["times_incorrect"] += 1
            card_progress["mastered"] = False
        
        # Update set-level statistics
        set_progress["last_reviewed"] = datetime.now(timezone.utc).isoformat()
        set_progress["total_reviews"] += 1
        
        # Recalculate mastered and needs review counts
        mastered = sum(1 for c in set_progress["flashcard_reviews"].values() if c.get("mastered", False))
        needs_review = sum(1 for c in set_progress["flashcard_reviews"].values() if not c.get("mastered", False))
        
        set_progress["mastered_count"] = mastered
        set_progress["needs_review_count"] = needs_review
        
        FlashcardStorage._save_json(PROGRESS_FILE, progress_data)
    
    @staticmethod
    def get_flashcard_progress(set_id: str) -> Dict[str, Any]:
        """Get progress statistics for a flashcard set."""
        progress_data = FlashcardStorage._load_json(PROGRESS_FILE, {})
        sets = progress_data.get("sets", {})
        return sets.get(set_id, {
            "flashcard_reviews": {},
            "last_reviewed": None,
            "total_reviews": 0,
            "mastered_count": 0,
            "needs_review_count": 0
        })
    
    @staticmethod
    def get_flashcards_needing_review(set_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get flashcards that need review (not mastered or incorrect recently)."""
        flashcard_set = FlashcardStorage.get_flashcard_set(set_id)
        if not flashcard_set:
            return []
        
        progress = FlashcardStorage.get_flashcard_progress(set_id)
        reviews = progress.get("flashcard_reviews", {})
        
        flashcards = flashcard_set.get("flashcards", [])
        needs_review = []
        
        for card in flashcards:
            card_id = card.get("id")
            card_review = reviews.get(card_id, {})
            
            # Include if not mastered or never reviewed
            if not card_review.get("mastered", False) or card_id not in reviews:
                needs_review.append(card)
        
        if limit:
            needs_review = needs_review[:limit]
        
        return needs_review
    
    @staticmethod
    def get_all_sets() -> List[Dict[str, Any]]:
        """Get all flashcard sets."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        return flashcards_data.get("sets", [])
    
    @staticmethod
    def delete_flashcard_set(set_id: str):
        """Delete a flashcard set and its progress."""
        flashcards_data = FlashcardStorage._load_json(FLASHCARDS_FILE, {})
        sets = flashcards_data.get("sets", [])
        flashcards_data["sets"] = [s for s in sets if s.get("id") != set_id]
        FlashcardStorage._save_json(FLASHCARDS_FILE, flashcards_data)
        
        # Delete progress
        progress_data = FlashcardStorage._load_json(PROGRESS_FILE, {})
        if "sets" in progress_data and set_id in progress_data["sets"]:
            del progress_data["sets"][set_id]
            FlashcardStorage._save_json(PROGRESS_FILE, progress_data)

