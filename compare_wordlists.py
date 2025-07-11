#!/usr/bin/env python3
"""
Compare and analyze the different wordlist generation approaches.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python compare_wordlists.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

from pathlib import Path
import json
from collections import Counter
from typing import Dict, List, Set


def load_wordlist(filename: str) -> List[str]:
    """Load a wordlist from file."""
    path = Path("output") / filename
    if not path.exists():
        return []
    
    with open(path) as f:
        if filename.endswith('.json'):
            data = json.load(f)
            return data.get("words", [])
        else:
            return [line.strip() for line in f if line.strip()]


def analyze_wordlist(words: List[str], name: str) -> Dict:
    """Analyze characteristics of a wordlist."""
    if not words:
        return {"name": name, "error": "No words found"}
    
    # Length distribution
    lengths = Counter(len(word) for word in words)
    
    # Character usage
    all_chars = ''.join(words)
    char_freq = Counter(all_chars)
    
    # Common patterns
    patterns = {
        "starts_with_vowel": sum(1 for w in words if w[0] in 'aeiou'),
        "ends_with_vowel": sum(1 for w in words if w[-1] in 'aeiou'),
        "contains_double": sum(1 for w in words if any(w[i] == w[i+1] for i in range(len(w)-1))),
        "all_lowercase": sum(1 for w in words if w.islower()),
    }
    
    # Sample words
    sample_start = words[:20] if len(words) >= 20 else words
    sample_middle = words[len(words)//2:len(words)//2+20] if len(words) >= 40 else []
    sample_end = words[-20:] if len(words) >= 20 else words
    
    return {
        "name": name,
        "total_words": len(words),
        "unique_words": len(set(words)),
        "avg_length": sum(len(w) for w in words) / len(words),
        "length_distribution": dict(lengths),
        "most_common_chars": char_freq.most_common(10),
        "patterns": patterns,
        "samples": {
            "start": sample_start,
            "middle": sample_middle,
            "end": sample_end
        }
    }


def compare_wordlists(wordlists: Dict[str, List[str]]) -> None:
    """Compare multiple wordlists."""
    print("Wordlist Comparison Analysis\n")
    print("=" * 80)
    
    # Basic statistics
    print("\nBasic Statistics:")
    print(f"{'Wordlist':<30} {'Words':<10} {'Unique':<10} {'Avg Length':<12}")
    print("-" * 62)
    
    analyses = {}
    for name, words in wordlists.items():
        analysis = analyze_wordlist(words, name)
        analyses[name] = analysis
        
        if "error" not in analysis:
            print(f"{name:<30} {analysis['total_words']:<10} "
                  f"{analysis['unique_words']:<10} {analysis['avg_length']:<12.2f}")
    
    # Length distribution comparison
    print("\n\nLength Distribution:")
    print(f"{'Length':<10}", end="")
    for name in wordlists:
        print(f"{name[:15]:>15}", end="")
    print()
    print("-" * (10 + 15 * len(wordlists)))
    
    for length in range(3, 11):
        print(f"{length:<10}", end="")
        for name in wordlists:
            if "error" not in analyses[name]:
                count = analyses[name]["length_distribution"].get(length, 0)
                print(f"{count:>15,}", end="")
        print()
    
    # Pattern comparison
    print("\n\nPattern Analysis:")
    print(f"{'Pattern':<25}", end="")
    for name in wordlists:
        print(f"{name[:15]:>15}", end="")
    print()
    print("-" * (25 + 15 * len(wordlists)))
    
    patterns = ["starts_with_vowel", "ends_with_vowel", "contains_double", "all_lowercase"]
    for pattern in patterns:
        print(f"{pattern.replace('_', ' ').title():<25}", end="")
        for name in wordlists:
            if "error" not in analyses[name]:
                count = analyses[name]["patterns"][pattern]
                total = analyses[name]["total_words"]
                pct = (count / total) * 100
                print(f"{count:>8,} ({pct:>4.1f}%)", end="")
        print()
    
    # Show unique words between lists
    print("\n\nUnique Words Analysis:")
    all_sets = {name: set(words) for name, words in wordlists.items() if words}
    
    for name1 in all_sets:
        for name2 in all_sets:
            if name1 < name2:  # Only compare each pair once
                unique_to_1 = len(all_sets[name1] - all_sets[name2])
                unique_to_2 = len(all_sets[name2] - all_sets[name1])
                common = len(all_sets[name1] & all_sets[name2])
                
                print(f"\n{name1} vs {name2}:")
                print(f"  Common words: {common:,}")
                print(f"  Unique to {name1}: {unique_to_1:,}")
                print(f"  Unique to {name2}: {unique_to_2:,}")


def main():
    """Run wordlist comparison."""
    # Load all wordlists
    wordlists = {
        "Basic": load_wordlist("wordlist_65536.txt"),
        "Enhanced": load_wordlist("enhanced_wordlist_65536.txt"),
        "Claude-Optimized": load_wordlist("claude_optimized_65536.txt"),
    }
    
    # Filter out empty wordlists
    wordlists = {k: v for k, v in wordlists.items() if v}
    
    if not wordlists:
        print("No wordlists found! Please run the generators first.")
        return
    
    # Run comparison
    compare_wordlists(wordlists)
    
    # Show sample high-quality words from Claude-optimized list
    if "Claude-Optimized" in wordlists:
        print("\n\nSample High-Quality Words from Claude-Optimized List:")
        claude_words = wordlists["Claude-Optimized"]
        
        # Show words that are likely to score highly
        quality_samples = []
        for word in claude_words[5000:5100]:  # Sample from a good section
            if (3 <= len(word) <= 6 and 
                word[0] not in 'xzq' and 
                not any(word[i] == word[i+1] for i in range(len(word)-1))):
                quality_samples.append(word)
                if len(quality_samples) >= 20:
                    break
        
        for i, word in enumerate(quality_samples):
            print(f"{word:<12}", end="")
            if (i + 1) % 5 == 0:
                print()
    
    print("\n\nAnalysis complete!")


if __name__ == "__main__":
    main()