#!/usr/bin/env python3
"""
Enhanced wordlist generator with stricter quality controls.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python enhanced_generator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
#     "nltk>=3.8.1",
# ]
# ///

from pathlib import Path
from typing import List, Set, Tuple
import json
import re
from collections import Counter

from word_scorer import WordScorer
from generate_wordlist import load_or_download_words, save_wordlist


TARGET_SIZE = 65536  # 2^16


class EnhancedWordFilter:
    """Enhanced word filtering with stricter quality controls."""
    
    def __init__(self):
        self.scorer = WordScorer()
        
        # Common letter frequencies in English
        self.expected_frequencies = {
            'e': 0.127, 't': 0.091, 'a': 0.082, 'o': 0.075,
            'i': 0.070, 'n': 0.067, 's': 0.063, 'h': 0.061,
            'r': 0.060, 'd': 0.043, 'l': 0.040, 'c': 0.028,
            'u': 0.028, 'm': 0.024, 'w': 0.024, 'f': 0.022,
            'g': 0.020, 'y': 0.020, 'p': 0.019, 'b': 0.015,
            'v': 0.010, 'k': 0.008, 'j': 0.002, 'x': 0.002,
            'q': 0.001, 'z': 0.001
        }
    
    def is_valid_word(self, word: str) -> bool:
        """Check if word meets basic validity criteria."""
        word = word.lower().strip()
        
        # Length check
        if len(word) < 3 or len(word) > 10:
            return False
        
        # Must be alphabetic
        if not word.isalpha():
            return False
        
        # No repeated letters more than twice
        for i in range(len(word) - 2):
            if word[i] == word[i+1] == word[i+2]:
                return False
        
        # No words that are just repeated patterns
        if len(set(word)) < len(word) * 0.4:  # At least 40% unique letters
            return False
        
        # Check for reasonable letter distribution
        letter_counts = Counter(word)
        rare_letters = sum(1 for letter in 'xzqj' if letter in letter_counts)
        if rare_letters > 2:  # Too many rare letters
            return False
        
        return True
    
    def categorize_word(self, word: str) -> Tuple[str, float]:
        """Categorize word by quality tier."""
        score = self.scorer.score_word(word)
        
        # Tier 1: Excellent (score >= 0.9, no issues)
        if score.total_score >= 0.9 and not score.reasons:
            return "excellent", score.total_score
        
        # Tier 2: Very Good (score >= 0.8)
        elif score.total_score >= 0.8:
            return "very_good", score.total_score
        
        # Tier 3: Good (score >= 0.7)
        elif score.total_score >= 0.7:
            return "good", score.total_score
        
        # Tier 4: Acceptable (score >= 0.6)
        elif score.total_score >= 0.6:
            return "acceptable", score.total_score
        
        # Tier 5: Poor (below 0.6)
        else:
            return "poor", score.total_score
    
    def filter_by_phonetics(self, word: str) -> bool:
        """Apply phonetic filters."""
        # Avoid words with ambiguous pronunciation
        ambiguous_patterns = [
            r'ough$',  # tough, though, through all different
            r'ead$',   # read (present) vs read (past)
            r'ow$',    # bow (weapon) vs bow (gesture)
            r'ive$',   # live (verb) vs live (adjective)
        ]
        
        for pattern in ambiguous_patterns:
            if re.search(pattern, word):
                return False
        
        return True
    
    def filter_homophones(self, word: str, existing_words: Set[str]) -> bool:
        """Filter out common homophones."""
        # Common homophone pairs to avoid
        homophone_pairs = [
            ('to', 'too', 'two'), ('there', 'their', 'they\'re'),
            ('your', 'you\'re'), ('its', 'it\'s'), ('whose', 'who\'s'),
            ('accept', 'except'), ('affect', 'effect'), ('than', 'then'),
            ('lose', 'loose'), ('choose', 'chose'), ('advice', 'advise'),
            ('break', 'brake'), ('coarse', 'course'), ('fair', 'fare'),
            ('hear', 'here'), ('hole', 'whole'), ('knew', 'new'),
            ('know', 'no'), ('made', 'maid'), ('mail', 'male'),
            ('meat', 'meet'), ('pair', 'pear'), ('peace', 'piece'),
            ('plain', 'plane'), ('principal', 'principle'), ('rain', 'reign'),
            ('right', 'write'), ('role', 'roll'), ('sail', 'sale'),
            ('scene', 'seen'), ('sea', 'see'), ('some', 'sum'),
            ('son', 'sun'), ('steal', 'steel'), ('tail', 'tale'),
            ('wait', 'weight'), ('waste', 'waist'), ('weak', 'week'),
            ('weather', 'whether'), ('where', 'wear'), ('which', 'witch'),
        ]
        
        # If this word is part of a homophone group and another is already in set
        for group in homophone_pairs:
            if word in group:
                for other in group:
                    if other != word and other in existing_words:
                        return False
        
        return True


def generate_enhanced_wordlist() -> List[str]:
    """Generate wordlist with enhanced quality controls."""
    filter = EnhancedWordFilter()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Start with BIP39 words
    final_words = set(bip39_words)
    print(f"Starting with {len(final_words)} BIP39 words")
    
    # Categorize all candidate words
    print("\nCategorizing candidate words by quality...")
    categorized = {
        "excellent": [],
        "very_good": [],
        "good": [],
        "acceptable": [],
        "poor": []
    }
    
    processed = 0
    for word in top_english[:80000]:  # Process more words
        word = word.lower().strip()
        
        if word in final_words:
            continue
        
        if not filter.is_valid_word(word):
            continue
        
        if not filter.filter_by_phonetics(word):
            continue
        
        if not filter.filter_homophones(word, final_words):
            continue
        
        category, score = filter.categorize_word(word)
        if category != "poor":
            categorized[category].append((word, score))
        
        processed += 1
        if processed % 5000 == 0:
            print(f"Processed {processed} words...")
    
    # Sort each category by score
    for category in categorized:
        categorized[category].sort(key=lambda x: x[1], reverse=True)
    
    # Add words in order of quality
    print("\nAdding words by quality tier...")
    words_needed = TARGET_SIZE - len(final_words)
    
    for category in ["excellent", "very_good", "good", "acceptable"]:
        print(f"\nAdding {category} words...")
        added_from_category = 0
        
        for word, score in categorized[category]:
            if len(final_words) >= TARGET_SIZE:
                break
            
            # Final homophone check
            if filter.filter_homophones(word, final_words):
                final_words.add(word)
                added_from_category += 1
        
        print(f"Added {added_from_category} {category} words (total: {len(final_words)})")
        
        if len(final_words) >= TARGET_SIZE:
            break
    
    # Convert to sorted list
    wordlist = sorted(list(final_words))[:TARGET_SIZE]
    
    return wordlist


def analyze_wordlist_quality(words: List[str]) -> dict:
    """Analyze the quality distribution of the wordlist."""
    filter = EnhancedWordFilter()
    
    quality_dist = Counter()
    length_dist = Counter()
    
    for word in words:
        category, _ = filter.categorize_word(word)
        quality_dist[category] += 1
        length_dist[len(word)] += 1
    
    return {
        "quality_distribution": dict(quality_dist),
        "length_distribution": dict(length_dist),
        "total_words": len(words)
    }


def main():
    """Generate enhanced wordlist."""
    print("Enhanced Wordlist Generator")
    print(f"Target: {TARGET_SIZE} words\n")
    
    wordlist = generate_enhanced_wordlist()
    
    print(f"\n✓ Generated {len(wordlist)} words!")
    
    # Analyze quality
    print("\nAnalyzing wordlist quality...")
    analysis = analyze_wordlist_quality(wordlist)
    
    print("\nQuality Distribution:")
    for category, count in analysis["quality_distribution"].items():
        percentage = (count / analysis["total_words"]) * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    print("\nLength Distribution:")
    for length in sorted(analysis["length_distribution"].keys()):
        count = analysis["length_distribution"][length]
        print(f"  {length} letters: {count}")
    
    print(f"\nFirst 20 words: {wordlist[:20]}")
    print(f"Last 20 words: {wordlist[-20:]}")
    
    # Save outputs
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save wordlist
    save_wordlist(wordlist, "../output/enhanced_wordlist_65536.txt")
    
    # Save with metadata
    metadata = {
        "version": "2.0",
        "word_count": len(wordlist),
        "includes_bip39": True,
        "quality_analysis": analysis,
        "generation_method": "enhanced_phonetic_filtering",
        "words": wordlist
    }
    
    with open(output_dir / "enhanced_wordlist_65536.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved enhanced wordlist to output/enhanced_wordlist_65536.txt")
    print("✓ Saved metadata to output/enhanced_wordlist_65536.json")


if __name__ == "__main__":
    main()