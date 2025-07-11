#!/usr/bin/env python3
"""
Clean the gold wordlist by removing non-English words and replacing them 
with valid English words from our source.

UV Dependencies:
# Run this script: uv run python clean_wordlist.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import re
from pathlib import Path
from typing import List, Set, Tuple

from claude_criteria_validator import ClaudeCriteriaValidator
from generate_wordlist import load_or_download_words


def is_english_word(word: str) -> bool:
    """Check if a word is proper English (no accents, non-Latin characters)."""
    # Must be all ASCII alphabetic characters
    return word.isascii() and word.isalpha() and len(word) >= 3


def find_non_english_words(wordlist: List[str]) -> List[Tuple[int, str]]:
    """Find non-English words in the wordlist with their positions."""
    non_english = []
    
    for i, word in enumerate(wordlist):
        if not is_english_word(word):
            non_english.append((i, word))
    
    return non_english


def get_replacement_words(validator: ClaudeCriteriaValidator, existing_words: Set[str], count_needed: int) -> List[str]:
    """Get valid English replacement words that aren't already in the wordlist."""
    print(f"Finding {count_needed} replacement words...")
    
    # Load candidates from 100K wordlist
    _, top_100k = load_or_download_words()
    
    # Find words that aren't in our existing set
    candidates = []
    for word in top_100k:
        word_lower = word.lower().strip()
        
        # Skip if already in our wordlist
        if word_lower in existing_words:
            continue
        
        # Must be proper English
        if not is_english_word(word_lower):
            continue
        
        # Apply Claude's validation criteria
        is_valid, reason = validator.validate_word(word_lower)
        if is_valid:
            candidates.append(word_lower)
            
            # Stop when we have enough
            if len(candidates) >= count_needed:
                break
    
    print(f"Found {len(candidates)} valid replacement words")
    return candidates


def clean_wordlist():
    """Clean the gold wordlist by removing non-English words."""
    print("="*60)
    print("CLEANING GOLD WORDLIST")
    print("="*60)
    
    # Load the current gold wordlist
    gold_file = Path("wordlists/gold_wordlist_65536.txt")
    if not gold_file.exists():
        print(f"Error: {gold_file} not found")
        return
    
    with open(gold_file) as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(words)} words from gold wordlist")
    
    # Find non-English words
    non_english = find_non_english_words(words)
    
    if not non_english:
        print("✓ No non-English words found! Wordlist is already clean.")
        return
    
    print(f"\nFound {len(non_english)} non-English words:")
    for i, (pos, word) in enumerate(non_english[:10]):  # Show first 10
        print(f"  {pos+1}: {word}")
    if len(non_english) > 10:
        print(f"  ... and {len(non_english)-10} more")
    
    # Create validator to find replacements
    validator = ClaudeCriteriaValidator()
    
    # Get existing words as set for fast lookup
    existing_words = set(word.lower() for word in words)
    
    # Get replacement words
    replacements = get_replacement_words(validator, existing_words, len(non_english))
    
    if len(replacements) < len(non_english):
        print(f"Warning: Only found {len(replacements)} replacements for {len(non_english)} words")
    
    # Replace non-English words
    cleaned_words = words.copy()
    replacement_log = []
    
    for i, (pos, old_word) in enumerate(non_english):
        if i < len(replacements):
            new_word = replacements[i]
            cleaned_words[pos] = new_word
            replacement_log.append((pos+1, old_word, new_word))
            print(f"  Replaced position {pos+1}: '{old_word}' → '{new_word}'")
        else:
            print(f"  Warning: No replacement found for '{old_word}' at position {pos+1}")
    
    # Remove any remaining non-English words
    final_words = [word for word in cleaned_words if is_english_word(word)]
    
    # If we lost words, get more replacements
    if len(final_words) < 65536:
        shortage = 65536 - len(final_words)
        print(f"\nNeed {shortage} more words to reach 65536...")
        
        existing_final = set(word.lower() for word in final_words)
        more_replacements = get_replacement_words(validator, existing_final, shortage)
        
        final_words.extend(more_replacements[:shortage])
    
    # Ensure we have exactly 65536 words
    final_words = final_words[:65536]
    
    print(f"\nFinal wordlist: {len(final_words)} words")
    print(f"All words are English: {all(is_english_word(word) for word in final_words)}")
    
    # Save cleaned wordlist
    cleaned_file = Path("wordlists/gold_wordlist_65536_cleaned.txt")
    with open(cleaned_file, 'w') as f:
        for word in sorted(final_words):
            f.write(f"{word}\n")
    
    # Update the original file
    with open(gold_file, 'w') as f:
        for word in sorted(final_words):
            f.write(f"{word}\n")
    
    # Create replacement log
    log_file = Path("wordlists/cleaning_log.txt")
    with open(log_file, 'w') as f:
        f.write("WORDLIST CLEANING LOG\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total words processed: {len(words)}\n")
        f.write(f"Non-English words found: {len(non_english)}\n")
        f.write(f"Replacements made: {len(replacement_log)}\n")
        f.write(f"Final clean words: {len(final_words)}\n\n")
        
        f.write("REPLACEMENTS MADE:\n")
        f.write("-" * 40 + "\n")
        for pos, old_word, new_word in replacement_log:
            f.write(f"Position {pos}: '{old_word}' → '{new_word}'\n")
        
        f.write("\nALL NON-ENGLISH WORDS FOUND:\n")
        f.write("-" * 40 + "\n")
        for pos, word in non_english:
            f.write(f"Position {pos+1}: {word}\n")
    
    print(f"\nFiles saved:")
    print(f"  - {gold_file} (updated)")
    print(f"  - {cleaned_file} (backup)")
    print(f"  - {log_file} (cleaning log)")
    
    # Show sample of final words
    print(f"\nSample of cleaned wordlist:")
    print(f"  First 10: {sorted(final_words)[:10]}")
    print(f"  Last 10: {sorted(final_words)[-10:]}")
    
    print(f"\n✓ Wordlist cleaned successfully!")


if __name__ == "__main__":
    clean_wordlist()