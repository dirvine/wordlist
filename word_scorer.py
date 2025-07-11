#!/usr/bin/env python3
"""
Score words based on readability, speakability, and distinctiveness.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python word_scorer.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "nltk>=3.8.1",
# ]
# ///

from dataclasses import dataclass
from typing import Set, Optional
import re


@dataclass
class WordScore:
    """Score components for a word."""
    word: str
    length_score: float
    phonetic_score: float
    pattern_score: float
    total_score: float
    reasons: list[str]


class WordScorer:
    """Score words for readability and speakability."""
    
    # Common problematic patterns
    DIFFICULT_PATTERNS = [
        r'[xz]{2,}',  # Multiple x or z
        r'[bcdfghjklmnpqrstvwxyz]{4,}',  # 4+ consonants in a row
        r'^[bcdfghjklmnpqrstvwxyz]{3,}',  # 3+ consonants at start
        r'[bcdfghjklmnpqrstvwxyz]{3,}$',  # 3+ consonants at end
        r'q(?!u)',  # q not followed by u
        r'[aeiou]{4,}',  # 4+ vowels in a row
    ]
    
    # Preferred patterns
    GOOD_PATTERNS = [
        r'^[bcdfghjklmnpqrstvwxyz][aeiou]',  # Consonant-vowel start
        r'[aeiou][bcdfghjklmnpqrstvwxyz]$',  # Vowel-consonant end
        r'[aeiou][bcdfghjklmnpqrstvwxyz][aeiou]',  # CVC pattern
    ]
    
    # Common confusable endings
    CONFUSABLE_ENDINGS = [
        ('tion', 'sion'),
        ('able', 'ible'),
        ('ant', 'ent'),
        ('ance', 'ence'),
    ]
    
    def __init__(self):
        """Initialize the word scorer."""
        self.scored_words: dict[str, WordScore] = {}
    
    def score_word(self, word: str) -> WordScore:
        """Score a single word."""
        word = word.lower().strip()
        
        # Check cache
        if word in self.scored_words:
            return self.scored_words[word]
        
        reasons = []
        
        # Length score (prefer 4-7 letters)
        length = len(word)
        if 4 <= length <= 7:
            length_score = 1.0
        elif 3 <= length <= 8:
            length_score = 0.8
        elif 2 <= length <= 10:
            length_score = 0.5
        else:
            length_score = 0.2
            reasons.append(f"Length {length} is not ideal")
        
        # Phonetic score
        phonetic_score = 1.0
        
        # Check difficult patterns
        for pattern in self.DIFFICULT_PATTERNS:
            if re.search(pattern, word):
                phonetic_score *= 0.7
                reasons.append(f"Contains difficult pattern: {pattern}")
        
        # Check good patterns
        good_pattern_count = 0
        for pattern in self.GOOD_PATTERNS:
            if re.search(pattern, word):
                good_pattern_count += 1
        
        if good_pattern_count > 0:
            phonetic_score = min(1.0, phonetic_score * (1.0 + 0.1 * good_pattern_count))
        
        # Pattern score (check for confusable elements)
        pattern_score = 1.0
        
        # Check for double letters
        if re.search(r'(.)\1', word):
            pattern_score *= 0.9
            reasons.append("Contains double letters")
        
        # Check for confusable endings
        for end1, end2 in self.CONFUSABLE_ENDINGS:
            if word.endswith(end1) or word.endswith(end2):
                pattern_score *= 0.9
                reasons.append(f"Has confusable ending: {end1}/{end2}")
                break
        
        # Silent letters penalty
        silent_patterns = [
            (r'mb$', 'silent b'),
            (r'kn', 'silent k'),
            (r'wr', 'silent w'),
            (r'ps', 'silent p'),
            (r'gn', 'silent g'),
        ]
        
        for pattern, reason in silent_patterns:
            if re.search(pattern, word):
                phonetic_score *= 0.8
                reasons.append(f"Contains {reason}")
        
        # Calculate total score
        total_score = (length_score * 0.3 + 
                      phonetic_score * 0.5 + 
                      pattern_score * 0.2)
        
        score = WordScore(
            word=word,
            length_score=length_score,
            phonetic_score=phonetic_score,
            pattern_score=pattern_score,
            total_score=total_score,
            reasons=reasons
        )
        
        self.scored_words[word] = score
        return score
    
    def is_good_word(self, word: str, threshold: float = 0.7) -> bool:
        """Check if a word meets the quality threshold."""
        score = self.score_word(word)
        return score.total_score >= threshold


def main():
    """Test the word scorer."""
    scorer = WordScorer()
    
    test_words = [
        "cat", "dog", "rhythm", "strength", "beautiful",
        "xylophone", "queue", "through", "knight", "write",
        "happy", "sad", "run", "jump", "sleep"
    ]
    
    print("Word Scoring Examples:\n")
    for word in test_words:
        score = scorer.score_word(word)
        print(f"{word:12} Score: {score.total_score:.2f}")
        if score.reasons:
            for reason in score.reasons:
                print(f"             - {reason}")
        print()


if __name__ == "__main__":
    main()