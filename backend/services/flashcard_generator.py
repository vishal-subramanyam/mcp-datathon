"""
Flashcard Generator
Handles generation of flashcards from text content.
"""

import re
from html import unescape
from typing import List, Dict, Any, Optional


def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML content.
    
    Args:
        html_content: HTML string
    
    Returns:
        Plain text content
    """
    if not html_content:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Decode HTML entities
    text = unescape(text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences.
    
    Args:
        text: Input text
    
    Returns:
        List of sentences
    """
    # Split by sentence endings
    sentences = re.split(r'[.!?]\s+', text)
    # Filter out very short sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    return sentences


def extract_key_terms(text: str, min_length: int = 3) -> List[str]:
    """Extract key terms from text (simple keyword extraction).
    
    Args:
        text: Input text
        min_length: Minimum length of terms to extract
    
    Returns:
        List of key terms
    """
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    # Split into words
    words = text.split()
    # Filter common stop words (basic list)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'our', 'you', 'your', 'i', 'my', 'me'}
    # Extract words that are not stop words and meet length requirement
    key_terms = [w for w in words if len(w) >= min_length and w not in stop_words]
    # Count frequency and return unique terms
    term_freq = {}
    for term in key_terms:
        term_freq[term] = term_freq.get(term, 0) + 1
    # Return terms sorted by frequency
    sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
    return [term for term, freq in sorted_terms[:20]]  # Top 20 terms


def generate_flashcards_from_content(
    content: str, 
    num_cards: int = 10,
    method: str = "simple"
) -> List[Dict[str, str]]:
    """Generate flashcards from content.
    
    Args:
        content: Text content to generate flashcards from
        num_cards: Number of flashcards to generate
        method: Generation method ("simple" or "key_terms")
    
    Returns:
        List of flashcard dictionaries with 'front' and 'back' keys
    """
    if not content or len(content.strip()) < 50:
        return []
    
    # Extract plain text from HTML if needed
    text_content = extract_text_from_html(content)
    
    if method == "key_terms":
        return _generate_from_key_terms(text_content, num_cards)
    else:
        return _generate_simple_flashcards(text_content, num_cards)


def _generate_simple_flashcards(text: str, num_cards: int) -> List[Dict[str, str]]:
    """Generate simple flashcards from text.
    
    Args:
        text: Input text
        num_cards: Number of flashcards to generate
    
    Returns:
        List of flashcard dictionaries
    """
    sentences = split_into_sentences(text)
    flashcards = []
    
    # Create flashcards from sentences
    for i, sentence in enumerate(sentences[:num_cards * 2]):
        if len(sentence) > 20:  # Only use substantial sentences
            # Create a question-answer pair
            # Front: Truncated sentence or question format
            # Back: Full sentence
            front = sentence[:100] + "..." if len(sentence) > 100 else sentence
            flashcards.append({
                "front": f"Explain: {front}",
                "back": sentence
            })
    
    # Limit to requested number
    return flashcards[:num_cards]


def _generate_from_key_terms(text: str, num_cards: int) -> List[Dict[str, str]]:
    """Generate flashcards using key terms extraction.
    
    Args:
        text: Input text
        num_cards: Number of flashcards to generate
    
    Returns:
        List of flashcard dictionaries
    """
    key_terms = extract_key_terms(text)
    sentences = split_into_sentences(text)
    flashcards = []
    
    # Create flashcards for key terms
    for term in key_terms[:num_cards]:
        # Find sentences containing this term
        relevant_sentences = [s for s in sentences if term.lower() in s.lower()]
        if relevant_sentences:
            # Use the first relevant sentence as the answer
            answer = relevant_sentences[0]
            # Create question
            question = f"What is {term}?" if term[0].isupper() else f"Define {term}."
            flashcards.append({
                "front": question,
                "back": answer
            })
    
    return flashcards[:num_cards]


def generate_qa_pairs_from_content(
    content: str,
    num_pairs: int = 10
) -> List[Dict[str, str]]:
    """Generate question-answer pairs from content (enhanced method).
    
    This method tries to create better Q&A pairs by identifying
    definition patterns, concept explanations, and key facts.
    
    Args:
        content: Text content
        num_pairs: Number of Q&A pairs to generate
    
    Returns:
        List of dictionaries with 'front' (question) and 'back' (answer)
    """
    text = extract_text_from_html(content)
    sentences = split_into_sentences(text)
    qa_pairs = []
    
    # Pattern 1: Definition patterns (e.g., "X is Y", "X refers to Y")
    definition_pattern = re.compile(r'(\w+(?:\s+\w+){0,3})\s+(?:is|are|refers to|means|defined as)\s+(.+)', re.IGNORECASE)
    
    for sentence in sentences:
        match = definition_pattern.search(sentence)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if len(definition) > 10 and len(term) < 50:
                qa_pairs.append({
                    "front": f"What is {term}?",
                    "back": definition
                })
                if len(qa_pairs) >= num_pairs:
                    break
    
    # Pattern 2: Question-answer format (if content already has Q&A)
    qa_pattern = re.compile(r'[Qq]uestion:\s*(.+?)\s*[Aa]nswer:\s*(.+?)(?:\n|$)', re.DOTALL)
    matches = qa_pattern.findall(text)
    for question, answer in matches[:num_pairs]:
        qa_pairs.append({
            "front": question.strip(),
            "back": answer.strip()
        })
    
    # Pattern 3: Lists and bullet points
    list_pattern = re.compile(r'[-*•]\s*(.+?)(?:\n|$)', re.MULTILINE)
    list_items = list_pattern.findall(text)
    for item in list_items[:min(num_pairs, len(list_items))]:
        if len(item) > 20:
            # Split into term and explanation if possible
            if ':' in item:
                parts = item.split(':', 1)
                qa_pairs.append({
                    "front": f"What is {parts[0].strip()}?",
                    "back": parts[1].strip()
                })
    
    # Fill remaining with simple sentence-based cards
    if len(qa_pairs) < num_pairs:
        simple_cards = _generate_simple_flashcards(text, num_pairs - len(qa_pairs))
        qa_pairs.extend(simple_cards)
    
    return qa_pairs[:num_pairs]


def create_flashcards_from_canvas_content(
    content: str,
    course_name: str,
    source_type: str = "page",
    source_name: str = "Untitled"
) -> Dict[str, Any]:
    """Create flashcards from Canvas content with metadata.
    
    Args:
        content: Content text (HTML or plain text)
        course_name: Name of the course
        source_type: Type of source (page, assignment, file, etc.)
        source_name: Name of the source
    
    Returns:
        Dictionary with flashcards and metadata
    """
    # Extract text
    text = extract_text_from_html(content)
    
    # Generate flashcards using enhanced method
    flashcards = generate_qa_pairs_from_content(text, num_pairs=10)
    
    # If enhanced method didn't generate enough, use simple method
    if len(flashcards) < 5:
        simple_flashcards = _generate_simple_flashcards(text, 10)
        # Merge, avoiding duplicates
        existing_fronts = {f['front'] for f in flashcards}
        for card in simple_flashcards:
            if card['front'] not in existing_fronts:
                flashcards.append(card)
                existing_fronts.add(card['front'])
    
    return {
        "flashcards": flashcards[:10],  # Limit to 10
        "metadata": {
            "course_name": course_name,
            "source_type": source_type,
            "source_name": source_name,
            "num_cards": len(flashcards),
            "content_length": len(text)
        }
    }

