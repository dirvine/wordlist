#!/usr/bin/env python3
"""
Generate a wordlist of 65,536 easy-to-read words.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python generate_wordlist.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
#     "nltk>=3.8.1",
# ]
# ///

from pathlib import Path
from typing import List, Set
import json

from word_scorer import WordScorer, WordScore
from download_sources import download_bip39, download_top_english, save_wordlist


TARGET_SIZE = 65536  # 2^16


def load_or_download_words() -> tuple[List[str], List[str]]:
    """Load wordlists from disk or download if needed."""
    wordlist_dir = Path("wordlists")
    bip39_path = wordlist_dir / "bip39_english.txt"
    top_english_path = wordlist_dir / "top_english_100000.txt"
    
    # Download if files don't exist
    if not bip39_path.exists() or not top_english_path.exists():
        print("Wordlists not found. Downloading...")
        bip39_words = download_bip39()
        save_wordlist(bip39_words, "bip39_english.txt")
        
        top_english = download_top_english()
        save_wordlist(top_english, "top_english_100000.txt")
    else:
        # Load from disk
        with open(bip39_path) as f:
            bip39_words = [line.strip() for line in f if line.strip()]
        
        with open(top_english_path) as f:
            top_english = [line.strip() for line in f if line.strip()]
    
    return bip39_words, top_english


def filter_candidates(words: List[str], existing: Set[str], scorer: WordScorer) -> List[tuple[str, float]]:
    """Filter and score candidate words."""
    candidates = []
    
    for word in words:
        word = word.lower().strip()
        
        # Skip if already in set
        if word in existing:
            continue
        
        # Basic filters
        if len(word) < 3 or len(word) > 10:
            continue
        
        # Must be alphabetic
        if not word.isalpha():
            continue
        
        # Score the word
        if scorer.is_good_word(word, threshold=0.6):
            score = scorer.score_word(word)
            candidates.append((word, score.total_score))
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def generate_wordlist() -> List[str]:
    """Generate the complete wordlist."""
    scorer = WordScorer()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Start with BIP39 words (all pass our criteria by design)
    final_words = set(bip39_words)
    print(f"Starting with {len(final_words)} BIP39 words")
    
    # Score and filter candidates from top English words
    print("\nAnalyzing top English words...")
    candidates = filter_candidates(top_english[:50000], final_words, scorer)
    
    # Add best candidates until we reach target size
    words_needed = TARGET_SIZE - len(final_words)
    print(f"\nNeed to add {words_needed} more words")
    
    added = 0
    for word, score in candidates:
        if len(final_words) >= TARGET_SIZE:
            break
        
        final_words.add(word)
        added += 1
        
        if added % 1000 == 0:
            print(f"Added {added} words... (total: {len(final_words)})")
    
    # If we still need more words, lower the threshold
    if len(final_words) < TARGET_SIZE:
        print(f"\nStill need {TARGET_SIZE - len(final_words)} words. Lowering threshold...")
        
        # Re-analyze with lower threshold
        scorer_relaxed = WordScorer()
        remaining_candidates = filter_candidates(
            top_english[50000:], 
            final_words, 
            scorer_relaxed
        )
        
        for word, score in remaining_candidates:
            if len(final_words) >= TARGET_SIZE:
                break
            
            if score >= 0.5:  # Lower threshold
                final_words.add(word)
    
    # Convert to sorted list
    wordlist = sorted(list(final_words))
    
    # Ensure we have exactly the target size
    if len(wordlist) > TARGET_SIZE:
        wordlist = wordlist[:TARGET_SIZE]
    elif len(wordlist) < TARGET_SIZE:
        print(f"WARNING: Only generated {len(wordlist)} words (target: {TARGET_SIZE})")
    
    return wordlist


def save_final_wordlist(words: List[str]) -> None:
    """Save the final wordlist in multiple formats."""
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    # Save as plain text
    txt_path = output_dir / "wordlist_65536.txt"
    with open(txt_path, 'w') as f:
        f.write('\n'.join(words))
    print(f"\nSaved {len(words)} words to {txt_path}")
    
    # Save as JSON with metadata
    json_path = output_dir / "wordlist_65536.json"
    metadata = {
        "version": "1.0",
        "word_count": len(words),
        "includes_bip39": True,
        "words": words
    }
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {json_path}")


def main():
    """Generate the complete wordlist."""
    print("Easy Keys Wordlist Generator")
    print(f"Target: {TARGET_SIZE} words\n")
    
    wordlist = generate_wordlist()
    
    print(f"\nGenerated {len(wordlist)} words!")
    print(f"First 10 words: {wordlist[:10]}")
    print(f"Last 10 words: {wordlist[-10:]}")
    
    save_final_wordlist(wordlist)
    
    print("\nWordlist generation complete!")


if __name__ == "__main__":
    main()