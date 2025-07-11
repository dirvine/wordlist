#!/usr/bin/env python3
"""
Claude-optimized wordlist generator using linguistic knowledge.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python claude_optimized_generator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
#     "nltk>=3.8.1",
# ]
# ///

from pathlib import Path
from typing import List, Set, Dict, Tuple
import json
import re
from dataclasses import dataclass
from collections import defaultdict

from enhanced_generator import EnhancedWordFilter, TARGET_SIZE
from generate_wordlist import load_or_download_words, save_wordlist


@dataclass
class WordFeatures:
    """Features that make a word easy to read, speak, and hear."""
    word: str
    syllables: int
    has_clear_consonants: bool
    has_simple_vowels: bool
    is_common_pattern: bool
    phonetic_clarity: float
    semantic_clarity: float
    overall_score: float


class ClaudeOptimizedFilter:
    """Filter using Claude's linguistic knowledge."""
    
    def __init__(self):
        self.base_filter = EnhancedWordFilter()
        
        # Words that are exceptionally clear when spoken
        self.gold_standard_words = {
            # Single syllable with clear sounds
            "cat", "dog", "sun", "moon", "tree", "book", "desk", "lamp",
            "pen", "cup", "hat", "box", "key", "map", "net", "pot",
            
            # Two syllables with clear stress
            "table", "window", "pencil", "garden", "monkey", "rabbit",
            "sunset", "rainbow", "picture", "button", "pocket", "pillow",
            
            # Common actions
            "walk", "talk", "read", "write", "sing", "dance", "sleep",
            "drink", "think", "speak", "teach", "learn", "build", "clean",
            
            # Clear three-syllable words
            "elephant", "umbrella", "butterfly", "telephone", "computer",
            "newspaper", "hamburger", "basketball", "watermelon"
        }
        
        # Patterns that make words clear
        self.clear_patterns = [
            # Consonant-vowel alternation
            (r'^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz]$', 3.0),  # CVC
            (r'^[bcdfghjklmnpqrstvwxyz][aeiou][bcdfghjklmnpqrstvwxyz][aeiou]$', 2.5),  # CVCV
            (r'^[aeiou][bcdfghjklmnpqrstvwxyz][aeiou]$', 2.0),  # VCV
            
            # Clear endings
            (r'ing$', 1.2),  # Clear gerund
            (r'ly$', 1.2),   # Clear adverb
            (r'er$', 1.1),   # Clear comparative/agent
            (r'ed$', 1.1),   # Clear past tense
        ]
        
        # Avoid these problematic combinations
        self.avoid_patterns = [
            # Difficult consonant clusters
            (r'[bcdfghjklmnpqrstvwxyz]{4,}', 0.3),  # 4+ consonants
            (r'^[sz]c', 0.5),  # sc- at start (scene, science)
            (r'xc', 0.5),      # -xc- (excellent, except)
            (r'chs', 0.6),     # -chs- (yacht, ache)
            
            # Silent letters
            (r'^kn', 0.4),     # kn- (knife, know)
            (r'^wr', 0.4),     # wr- (write, wrong)
            (r'^ps', 0.4),     # ps- (psalm, pseudo)
            (r'mb$', 0.5),     # -mb (lamb, thumb)
            (r'mn$', 0.5),     # -mn (autumn, column)
            
            # Ambiguous vowel combinations
            (r'[aeiou]{3,}', 0.6),  # 3+ vowels
            (r'ea', 0.8),      # ea has many pronunciations
            (r'ie', 0.8),      # ie is often confusing
            (r'ei', 0.8),      # ei follows complex rules
        ]
        
        # Common semantic categories for clarity
        self.semantic_categories = {
            "concrete_objects": ["table", "chair", "door", "window", "wall"],
            "body_parts": ["hand", "foot", "head", "eye", "ear"],
            "nature": ["tree", "flower", "grass", "rock", "river"],
            "animals": ["cat", "dog", "bird", "fish", "horse"],
            "colors": ["red", "blue", "green", "yellow", "black"],
            "numbers": ["one", "two", "three", "four", "five"],
            "time": ["day", "night", "hour", "minute", "year"],
            "actions": ["go", "come", "take", "give", "make"],
        }
    
    def count_syllables(self, word: str) -> int:
        """Estimate syllable count using vowel groups."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1
        
        # Ensure at least 1 syllable
        return max(1, count)
    
    def analyze_phonetic_clarity(self, word: str) -> float:
        """Analyze how clear a word is phonetically."""
        score = 1.0
        
        # Apply positive patterns
        for pattern, multiplier in self.clear_patterns:
            if re.search(pattern, word, re.IGNORECASE):
                score *= multiplier
        
        # Apply negative patterns
        for pattern, multiplier in self.avoid_patterns:
            if re.search(pattern, word, re.IGNORECASE):
                score *= multiplier
        
        # Bonus for matching gold standard patterns
        if word in self.gold_standard_words:
            score *= 2.0
        
        # Length bonus (4-6 letters is ideal)
        if 4 <= len(word) <= 6:
            score *= 1.2
        elif 3 <= len(word) <= 7:
            score *= 1.1
        
        # Syllable bonus (1-2 syllables is ideal)
        syllables = self.count_syllables(word)
        if syllables == 1:
            score *= 1.3
        elif syllables == 2:
            score *= 1.2
        elif syllables >= 4:
            score *= 0.7
        
        return min(score, 5.0)  # Cap at 5.0
    
    def analyze_semantic_clarity(self, word: str) -> float:
        """Analyze semantic clarity and concreteness."""
        score = 1.0
        
        # Check if word appears in semantic categories
        for category, words in self.semantic_categories.items():
            if word in words:
                score *= 1.5  # Concrete, common words
                break
        
        # Common word bonus (based on position in frequency list)
        # This would need the word's position in the frequency list
        # For now, we'll use word length as a proxy
        if len(word) <= 5:
            score *= 1.1
        
        return min(score, 2.0)
    
    def analyze_word(self, word: str) -> WordFeatures:
        """Comprehensive word analysis."""
        word = word.lower().strip()
        
        syllables = self.count_syllables(word)
        
        # Check for clear consonants (no difficult clusters)
        has_clear_consonants = not bool(re.search(r'[bcdfghjklmnpqrstvwxyz]{3,}', word))
        
        # Check for simple vowels (no complex combinations)
        has_simple_vowels = not bool(re.search(r'[aeiou]{3,}|eau|ieu|oeu', word))
        
        # Check if it follows common English patterns
        is_common_pattern = bool(re.search(
            r'^[bcdfghjklmnpqrstvwxyz]?[aeiou][bcdfghjklmnpqrstvwxyz]+[aeiou]?[bcdfghjklmnpqrstvwxyz]?$',
            word
        ))
        
        phonetic_clarity = self.analyze_phonetic_clarity(word)
        semantic_clarity = self.analyze_semantic_clarity(word)
        
        # Calculate overall score
        base_score = self.base_filter.scorer.score_word(word).total_score
        overall_score = (
            base_score * 0.3 +
            phonetic_clarity * 0.4 +
            semantic_clarity * 0.3
        )
        
        return WordFeatures(
            word=word,
            syllables=syllables,
            has_clear_consonants=has_clear_consonants,
            has_simple_vowels=has_simple_vowels,
            is_common_pattern=is_common_pattern,
            phonetic_clarity=phonetic_clarity,
            semantic_clarity=semantic_clarity,
            overall_score=overall_score
        )
    
    def get_word_tier(self, features: WordFeatures) -> str:
        """Categorize word into quality tier."""
        if features.overall_score >= 1.5:
            return "premium"
        elif features.overall_score >= 1.2:
            return "excellent"
        elif features.overall_score >= 0.9:
            return "very_good"
        elif features.overall_score >= 0.7:
            return "good"
        else:
            return "acceptable"


def generate_claude_optimized_wordlist() -> List[str]:
    """Generate wordlist optimized with Claude's linguistic knowledge."""
    optimizer = ClaudeOptimizedFilter()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Start with BIP39 words
    final_words = set(bip39_words)
    print(f"Starting with {len(final_words)} BIP39 words")
    
    # Analyze and categorize words
    print("\nAnalyzing words with linguistic features...")
    word_tiers = defaultdict(list)
    
    # First, add all gold standard words that aren't in BIP39
    for word in optimizer.gold_standard_words:
        if word not in final_words:
            features = optimizer.analyze_word(word)
            word_tiers["premium"].append((word, features))
    
    # Process top English words
    processed = 0
    for word in top_english[:100000]:
        word = word.lower().strip()
        
        if word in final_words or word in optimizer.gold_standard_words:
            continue
        
        # Basic validity
        if not optimizer.base_filter.is_valid_word(word):
            continue
        
        # Phonetic filtering
        if not optimizer.base_filter.filter_by_phonetics(word):
            continue
        
        # Analyze word
        features = optimizer.analyze_word(word)
        tier = optimizer.get_word_tier(features)
        
        if tier in ["premium", "excellent", "very_good", "good"]:
            word_tiers[tier].append((word, features))
        
        processed += 1
        if processed % 10000 == 0:
            print(f"Processed {processed} words...")
    
    # Sort each tier by score
    for tier in word_tiers:
        word_tiers[tier].sort(key=lambda x: x[1].overall_score, reverse=True)
    
    # Add words in order of quality
    print("\nBuilding final wordlist by tier...")
    tier_order = ["premium", "excellent", "very_good", "good", "acceptable"]
    
    for tier in tier_order:
        if tier not in word_tiers:
            continue
            
        print(f"\nAdding {tier} words...")
        added = 0
        
        for word, features in word_tiers[tier]:
            if len(final_words) >= TARGET_SIZE:
                break
            
            # Final homophone check
            if optimizer.base_filter.filter_homophones(word, final_words):
                final_words.add(word)
                added += 1
                
                # Show some examples
                if added <= 5:
                    print(f"  {word}: score={features.overall_score:.2f}, "
                          f"syllables={features.syllables}, "
                          f"phonetic={features.phonetic_clarity:.2f}")
        
        print(f"Added {added} {tier} words (total: {len(final_words)})")
        
        if len(final_words) >= TARGET_SIZE:
            break
    
    # Convert to sorted list
    wordlist = sorted(list(final_words))[:TARGET_SIZE]
    
    return wordlist


def create_detailed_analysis(wordlist: List[str]) -> Dict:
    """Create detailed analysis of the wordlist."""
    optimizer = ClaudeOptimizedFilter()
    
    analysis = {
        "total_words": len(wordlist),
        "tier_distribution": defaultdict(int),
        "syllable_distribution": defaultdict(int),
        "length_distribution": defaultdict(int),
        "pattern_matches": defaultdict(int),
        "top_scored_words": [],
        "sample_by_tier": defaultdict(list)
    }
    
    # Analyze each word
    all_features = []
    for word in wordlist:
        features = optimizer.analyze_word(word)
        all_features.append(features)
        
        tier = optimizer.get_word_tier(features)
        analysis["tier_distribution"][tier] += 1
        analysis["syllable_distribution"][features.syllables] += 1
        analysis["length_distribution"][len(word)] += 1
        
        # Track pattern matches
        if features.has_clear_consonants:
            analysis["pattern_matches"]["clear_consonants"] += 1
        if features.has_simple_vowels:
            analysis["pattern_matches"]["simple_vowels"] += 1
        if features.is_common_pattern:
            analysis["pattern_matches"]["common_pattern"] += 1
        
        # Collect samples by tier
        if len(analysis["sample_by_tier"][tier]) < 10:
            analysis["sample_by_tier"][tier].append(word)
    
    # Get top scored words
    all_features.sort(key=lambda x: x.overall_score, reverse=True)
    analysis["top_scored_words"] = [
        {"word": f.word, "score": f.overall_score, "syllables": f.syllables}
        for f in all_features[:20]
    ]
    
    return dict(analysis)


def main():
    """Generate Claude-optimized wordlist."""
    print("Claude-Optimized Wordlist Generator")
    print(f"Target: {TARGET_SIZE} words\n")
    
    wordlist = generate_claude_optimized_wordlist()
    
    print(f"\n✓ Generated {len(wordlist)} words!")
    
    # Create detailed analysis
    print("\nCreating detailed analysis...")
    analysis = create_detailed_analysis(wordlist)
    
    # Display analysis
    print("\nQuality Tier Distribution:")
    for tier in ["premium", "excellent", "very_good", "good", "acceptable"]:
        if tier in analysis["tier_distribution"]:
            count = analysis["tier_distribution"][tier]
            percentage = (count / analysis["total_words"]) * 100
            print(f"  {tier}: {count} ({percentage:.1f}%)")
    
    print("\nTop 20 Scored Words:")
    for item in analysis["top_scored_words"]:
        print(f"  {item['word']:12} (score: {item['score']:.2f}, syllables: {item['syllables']})")
    
    print("\nPattern Analysis:")
    total = analysis["total_words"]
    for pattern, count in analysis["pattern_matches"].items():
        percentage = (count / total) * 100
        print(f"  {pattern}: {count} ({percentage:.1f}%)")
    
    # Save outputs
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save wordlist
    save_wordlist(wordlist, "../output/claude_optimized_65536.txt")
    
    # Save with metadata and analysis
    metadata = {
        "version": "3.0",
        "word_count": len(wordlist),
        "includes_bip39": True,
        "optimization": "claude_linguistic_knowledge",
        "analysis": analysis,
        "words": wordlist
    }
    
    with open(output_dir / "claude_optimized_65536.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved optimized wordlist to output/claude_optimized_65536.txt")
    print("✓ Saved detailed analysis to output/claude_optimized_65536.json")


if __name__ == "__main__":
    main()