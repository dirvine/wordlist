#!/usr/bin/env python3
"""
Evaluate readability of wordlists using various metrics.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python evaluate_readability.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

from pathlib import Path
import random
from typing import List, Tuple
import json

from word_scorer import WordScorer
from claude_optimized_generator import ClaudeOptimizedFilter


def phonetic_similarity_test(words: List[str], sample_size: int = 100) -> float:
    """Test how distinct words are from each other phonetically."""
    # Sample random pairs
    sample_words = random.sample(words, min(sample_size, len(words)))
    
    similar_pairs = 0
    total_pairs = 0
    
    for i in range(len(sample_words)):
        for j in range(i + 1, len(sample_words)):
            word1, word2 = sample_words[i], sample_words[j]
            
            # Check for similar patterns that could cause confusion
            if (abs(len(word1) - len(word2)) <= 1 and
                sum(c1 == c2 for c1, c2 in zip(word1, word2)) >= len(word1) * 0.6):
                similar_pairs += 1
            
            total_pairs += 1
    
    # Return distinctiveness score (higher is better)
    return 1.0 - (similar_pairs / total_pairs) if total_pairs > 0 else 1.0


def common_pattern_test(words: List[str]) -> dict:
    """Test how many words follow common English patterns."""
    patterns = {
        "CVC": 0,  # consonant-vowel-consonant
        "CVCV": 0,  # alternating pattern
        "common_prefix": 0,  # un-, re-, in-, etc.
        "common_suffix": 0,  # -ing, -ed, -er, etc.
        "simple_plural": 0,  # -s, -es
    }
    
    vowels = set('aeiou')
    common_prefixes = ['un', 're', 'in', 'dis', 'pre', 'over', 'under', 'out']
    common_suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ment', 'ness']
    
    for word in words:
        # Check CVC pattern
        if (len(word) == 3 and 
            word[0] not in vowels and 
            word[1] in vowels and 
            word[2] not in vowels):
            patterns["CVC"] += 1
        
        # Check CVCV pattern
        if len(word) == 4:
            is_cvcv = True
            for i in range(4):
                if i % 2 == 0 and word[i] in vowels:
                    is_cvcv = False
                elif i % 2 == 1 and word[i] not in vowels:
                    is_cvcv = False
            if is_cvcv:
                patterns["CVCV"] += 1
        
        # Check prefixes
        for prefix in common_prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                patterns["common_prefix"] += 1
                break
        
        # Check suffixes
        for suffix in common_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                patterns["common_suffix"] += 1
                break
        
        # Check simple plurals
        if word.endswith('s') and not word.endswith('ss'):
            patterns["simple_plural"] += 1
    
    # Convert to percentages
    total = len(words)
    return {k: (v / total) * 100 for k, v in patterns.items()}


def typing_ease_test(words: List[str], sample_size: int = 1000) -> dict:
    """Test how easy words are to type on a QWERTY keyboard."""
    # Define keyboard rows
    top_row = set('qwertyuiop')
    middle_row = set('asdfghjkl')
    bottom_row = set('zxcvbnm')
    
    sample_words = random.sample(words, min(sample_size, len(words)))
    
    stats = {
        "single_row": 0,  # Words typed on a single row
        "alternating_hands": 0,  # Words that alternate between hands
        "repeated_letters": 0,  # Words with repeated letters
        "common_bigrams": 0,  # Words with common letter pairs
    }
    
    # Common bigrams in English
    common_bigrams = {'th', 'he', 'in', 'er', 'an', 're', 'ed', 'on', 'es', 'st',
                      'en', 'at', 'to', 'nt', 'ha', 'nd', 'ou', 'ea', 'ng', 'as'}
    
    # Left and right hand keys (simplified)
    left_hand = set('qwertasdfgzxcvb')
    right_hand = set('yuiophjklnm')
    
    for word in sample_words:
        word_lower = word.lower()
        
        # Check single row
        word_chars = set(word_lower)
        if word_chars.issubset(top_row) or word_chars.issubset(middle_row) or word_chars.issubset(bottom_row):
            stats["single_row"] += 1
        
        # Check alternating hands
        if len(word) >= 3:
            alternates = True
            for i in range(len(word) - 1):
                char1, char2 = word_lower[i], word_lower[i + 1]
                if ((char1 in left_hand and char2 in left_hand) or
                    (char1 in right_hand and char2 in right_hand)):
                    alternates = False
                    break
            if alternates:
                stats["alternating_hands"] += 1
        
        # Check repeated letters
        for i in range(len(word) - 1):
            if word[i] == word[i + 1]:
                stats["repeated_letters"] += 1
                break
        
        # Check common bigrams
        for i in range(len(word) - 1):
            if word_lower[i:i+2] in common_bigrams:
                stats["common_bigrams"] += 1
                break
    
    # Convert to percentages
    return {k: (v / sample_size) * 100 for k, v in stats.items()}


def evaluate_wordlist(words: List[str], name: str) -> dict:
    """Comprehensive evaluation of a wordlist."""
    print(f"\nEvaluating {name}...")
    
    scorer = WordScorer()
    optimizer = ClaudeOptimizedFilter()
    
    # Score distribution
    scores = []
    premium_count = 0
    
    sample = random.sample(words, min(1000, len(words)))
    for word in sample:
        score = scorer.score_word(word)
        scores.append(score.total_score)
        
        # Check if it would be premium in Claude's system
        features = optimizer.analyze_word(word)
        if features.overall_score >= 1.5:
            premium_count += 1
    
    avg_score = sum(scores) / len(scores)
    
    # Run tests
    distinctiveness = phonetic_similarity_test(words, 200)
    patterns = common_pattern_test(words)
    typing = typing_ease_test(words, 500)
    
    return {
        "name": name,
        "average_score": avg_score,
        "premium_percentage": (premium_count / len(sample)) * 100,
        "phonetic_distinctiveness": distinctiveness * 100,
        "pattern_analysis": patterns,
        "typing_ease": typing
    }


def main():
    """Run readability evaluation."""
    print("Wordlist Readability Evaluation")
    print("=" * 50)
    
    # Load wordlists
    wordlists = {}
    for filename, name in [
        ("wordlist_65536.txt", "Basic"),
        ("enhanced_wordlist_65536.txt", "Enhanced"),
        ("claude_optimized_65536.txt", "Claude-Optimized")
    ]:
        path = Path("output") / filename
        if path.exists():
            with open(path) as f:
                wordlists[name] = [line.strip() for line in f if line.strip()]
    
    if not wordlists:
        print("No wordlists found! Please run the generators first.")
        return
    
    # Evaluate each wordlist
    results = {}
    for name, words in wordlists.items():
        results[name] = evaluate_wordlist(words, name)
    
    # Display results
    print("\n\nEvaluation Results")
    print("=" * 50)
    
    print("\nOverall Quality Scores:")
    print(f"{'Wordlist':<20} {'Avg Score':<12} {'Premium %':<12} {'Distinct %':<12}")
    print("-" * 56)
    for name, result in results.items():
        print(f"{name:<20} {result['average_score']:<12.3f} "
              f"{result['premium_percentage']:<12.1f} "
              f"{result['phonetic_distinctiveness']:<12.1f}")
    
    print("\n\nPattern Analysis (% of words):")
    pattern_names = ["CVC", "CVCV", "common_prefix", "common_suffix", "simple_plural"]
    print(f"{'Pattern':<20}", end="")
    for name in results:
        print(f"{name:>15}", end="")
    print()
    print("-" * (20 + 15 * len(results)))
    
    for pattern in pattern_names:
        print(f"{pattern:<20}", end="")
        for name in results:
            value = results[name]["pattern_analysis"].get(pattern, 0)
            print(f"{value:>14.1f}%", end="")
        print()
    
    print("\n\nTyping Ease Analysis (% of sampled words):")
    typing_metrics = ["single_row", "alternating_hands", "repeated_letters", "common_bigrams"]
    print(f"{'Metric':<20}", end="")
    for name in results:
        print(f"{name:>15}", end="")
    print()
    print("-" * (20 + 15 * len(results)))
    
    for metric in typing_metrics:
        print(f"{metric.replace('_', ' ').title():<20}", end="")
        for name in results:
            value = results[name]["typing_ease"].get(metric, 0)
            print(f"{value:>14.1f}%", end="")
        print()
    
    # Save detailed results
    output_dir = Path("wordlists")
    with open(output_dir / "readability_evaluation.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nDetailed results saved to wordlists/readability_evaluation.json")
    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()