#!/usr/bin/env python3
"""
Analyze words using Claude's knowledge of readability and phonetics.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python analyze_words.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

from pathlib import Path
from typing import List, Set, Dict
import json

from word_scorer import WordScorer
from generate_wordlist import load_or_download_words


def get_claude_criteria() -> Dict[str, List[str]]:
    """Define criteria for Claude to evaluate words."""
    return {
        "excellent_patterns": [
            # CV patterns
            "words with consonant-vowel alternation (like 'banana', 'tomato')",
            "words ending in vowel-consonant (like 'cat', 'dog')",
            "words with simple CVC structure (like 'hat', 'pen')",
            
            # Common words
            "everyday objects (like 'table', 'chair', 'window')",
            "basic actions (like 'walk', 'talk', 'jump')",
            "simple emotions (like 'happy', 'sad', 'angry')",
            "colors (like 'blue', 'green', 'yellow')",
            "animals (like 'bird', 'fish', 'bear')",
            "body parts (like 'hand', 'foot', 'head')",
            "nature words (like 'tree', 'rock', 'rain')",
            "food items (like 'apple', 'bread', 'milk')",
            
            # Phonetic clarity
            "words with distinct consonant sounds",
            "words avoiding similar-sounding syllables",
            "words with clear vowel sounds",
        ],
        
        "avoid_patterns": [
            # Difficult clusters
            "multiple consonants together (like 'strength', 'twelfth')",
            "silent letters (like 'knight', 'gnome', 'psalm')",
            "unusual letter combinations (like 'phlegm', 'rhythm')",
            
            # Confusable sounds
            "words ending in -tion/-sion (easily confused)",
            "words with 'th' sounds (hard for non-native speakers)",
            "words with 'ough' (multiple pronunciations)",
            
            # Other issues
            "homophones (sound the same as other words)",
            "words easily misheard over phone/radio",
            "technical or specialized vocabulary",
            "archaic or obsolete words",
            "slang or informal words",
            "words with multiple meanings",
        ],
        
        "ideal_characteristics": [
            "3-7 letters long",
            "1-3 syllables",
            "stress on first syllable",
            "common in everyday speech",
            "easy to spell",
            "distinct from other words when spoken",
            "culturally neutral",
            "appropriate for all ages",
        ]
    }


def analyze_word_batch(words: List[str], scorer: WordScorer) -> Dict[str, Dict]:
    """Analyze a batch of words for readability characteristics."""
    criteria = get_claude_criteria()
    results = {}
    
    for word in words:
        score = scorer.score_word(word)
        
        # Analyze based on criteria
        analysis = {
            "word": word,
            "score": score.total_score,
            "length": len(word),
            "reasons": score.reasons,
            "characteristics": []
        }
        
        # Check for good patterns
        if len(word) >= 3 and len(word) <= 7:
            analysis["characteristics"].append("ideal length")
        
        # Check for CV alternation
        vowels = set('aeiou')
        has_cv_pattern = False
        for i in range(len(word) - 1):
            if (word[i] not in vowels and word[i+1] in vowels) or \
               (word[i] in vowels and word[i+1] not in vowels):
                has_cv_pattern = True
                break
        
        if has_cv_pattern:
            analysis["characteristics"].append("good CV pattern")
        
        # Check syllable count (rough approximation)
        syllable_count = sum(1 for char in word if char in vowels)
        if syllable_count <= 3:
            analysis["characteristics"].append(f"{syllable_count} syllables")
        
        results[word] = analysis
    
    return results


def find_excellent_words(top_english: List[str], bip39: Set[str], limit: int = 100) -> List[str]:
    """Find excellent candidate words based on Claude's criteria."""
    scorer = WordScorer()
    excellent = []
    
    # Categories of excellent words
    categories = {
        "animals": ["cat", "dog", "bird", "fish", "bear", "wolf", "fox", "deer", 
                   "mouse", "horse", "sheep", "goat", "duck", "frog", "snake"],
        "colors": ["red", "blue", "green", "yellow", "orange", "purple", "pink",
                  "brown", "black", "white", "gray", "gold", "silver"],
        "nature": ["tree", "rock", "hill", "lake", "river", "rain", "snow", 
                  "wind", "cloud", "star", "moon", "sun", "sky", "grass"],
        "objects": ["book", "door", "chair", "table", "window", "lamp", "phone",
                   "clock", "key", "box", "bag", "cup", "plate", "fork"],
        "actions": ["walk", "talk", "run", "jump", "sit", "stand", "sleep",
                   "eat", "drink", "read", "write", "play", "work", "help"],
        "body": ["hand", "foot", "head", "arm", "leg", "eye", "ear", "nose",
                "mouth", "face", "hair", "back", "chest", "finger"],
        "food": ["apple", "bread", "milk", "water", "rice", "meat", "fish",
                "egg", "salt", "sugar", "tea", "soup", "cake", "fruit"],
    }
    
    # Collect excellent examples
    for category, examples in categories.items():
        for word in examples:
            if word not in bip39 and scorer.is_good_word(word, threshold=0.8):
                excellent.append(word)
    
    # Find similar patterns in top English words
    for word in top_english[:10000]:
        if len(excellent) >= limit:
            break
            
        word = word.lower().strip()
        if word in bip39 or word in excellent:
            continue
            
        # Check if it matches our ideal criteria
        if (3 <= len(word) <= 7 and
            word.isalpha() and
            scorer.is_good_word(word, threshold=0.85)):
            
            # Additional checks for excellent words
            score = scorer.score_word(word)
            if score.total_score >= 0.85 and not score.reasons:
                excellent.append(word)
    
    return excellent


def main():
    """Run word analysis."""
    print("Word Analysis Tool\n")
    
    # Load wordlists
    bip39_words, top_english = load_or_download_words()
    bip39_set = set(bip39_words)
    
    # Find excellent candidate words
    print("Finding excellent candidate words based on readability criteria...\n")
    excellent = find_excellent_words(top_english, bip39_set, limit=50)
    
    print(f"Top {len(excellent)} excellent words not in BIP39:")
    for i, word in enumerate(excellent, 1):
        print(f"{i:3d}. {word}")
    
    # Analyze a sample
    print("\n\nDetailed analysis of first 10 excellent words:")
    scorer = WordScorer()
    analysis = analyze_word_batch(excellent[:10], scorer)
    
    for word, data in analysis.items():
        print(f"\n{word}:")
        print(f"  Score: {data['score']:.2f}")
        print(f"  Length: {data['length']}")
        if data['characteristics']:
            print(f"  Characteristics: {', '.join(data['characteristics'])}")
        if data['reasons']:
            print(f"  Issues: {', '.join(data['reasons'])}")
    
    # Save analysis
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "word_analysis.json", 'w') as f:
        json.dump({
            "excellent_words": excellent,
            "criteria": get_claude_criteria(),
            "sample_analysis": analysis
        }, f, indent=2)
    
    print(f"\n\nAnalysis saved to {output_dir / 'word_analysis.json'}")


if __name__ == "__main__":
    main()