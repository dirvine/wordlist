#!/usr/bin/env python3
"""
Premium wordlist generator with strict quality controls for real English words only.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python premium_generator.py
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
from collections import Counter
from dataclasses import dataclass

from word_scorer import WordScorer
from generate_wordlist import load_or_download_words, save_wordlist


TARGET_SIZE = 65536  # 2^16


@dataclass
class WordValidation:
    """Comprehensive word validation results."""
    word: str
    is_real_word: bool
    is_pronounceable: bool
    is_memorable: bool
    phonetic_score: float
    reason: str


class PremiumWordFilter:
    """Ultra-strict filtering for premium English words only."""
    
    def __init__(self):
        self.scorer = WordScorer()
        
        # Curated list of high-quality English words by category
        self.premium_words = self._build_premium_vocabulary()
        
        # Patterns that indicate real English words
        self.valid_patterns = [
            # Common English morphology
            r'^[a-z]+(ing|ed|er|est|ly|ness|ment|tion|sion)$',  # Common suffixes
            r'^(un|re|pre|dis|mis|over|under|out|up|down)[a-z]+$',  # Common prefixes
            
            # Common word structures
            r'^[bcdfghjklmnpqrstvwxz][aeiou][bcdfghjklmnpqrstvwxz]$',  # CVC
            r'^[bcdfghjklmnpqrstvwxz][aeiou][bcdfghjklmnpqrstvwxz][aeiou]$',  # CVCV
            r'^[aeiou][bcdfghjklmnpqrstvwxz][aeiou]$',  # VCV
            r'^[bcdfghjklmnpqrstvwxz][aeiou][bcdfghjklmnpqrstvwxz][aeiou][bcdfghjklmnpqrstvwxz]$',  # CVCVC
        ]
        
        # Patterns that indicate low-quality or non-English words
        self.invalid_patterns = [
            r'^[aeiou]{2,}$',  # Just vowels (aa, aaa, etc.)
            r'^[bcdfghjklmnpqrstvwxz]{2,}$',  # Just consonants
            r'^[aeiou][aeiou][bcdfghjklmnpqrstvwxz]$',  # aab, aac pattern
            r'^[bcdfghjklmnpqrstvwxz][bcdfghjklmnpqrstvwxz][aeiou]$',  # bba, cca pattern
            r'^[aeiou]{3,}',  # Starting with 3+ vowels
            r'[aeiou]{4,}',  # 4+ vowels anywhere
            r'[bcdfghjklmnpqrstvwxz]{4,}',  # 4+ consonants
            r'^[qx]',  # Starting with q or x (very rare)
            r'[0-9]',  # Contains numbers
            r'[^a-z]',  # Contains non-lowercase letters
            r'^.{1,2}$',  # Too short (1-2 letters)
            r'^.{11,}$',  # Too long (11+ letters)
        ]
        
        # Words that should definitely be excluded
        self.excluded_words = {
            # Abbreviations and acronyms
            'aaa', 'aab', 'aac', 'aad', 'aaf', 'aag', 'aah', 'aal', 'aam', 'aan', 'aap', 'aar', 'aas', 'aat', 'aau', 'aav',
            'bbb', 'ccc', 'ddd', 'eee', 'fff', 'ggg', 'hhh', 'iii', 'jjj', 'kkk', 'lll', 'mmm', 'nnn', 'ooo', 'ppp',
            'qqq', 'rrr', 'sss', 'ttt', 'uuu', 'vvv', 'www', 'xxx', 'yyy', 'zzz',
            
            # Place names (proper nouns)
            'aalborg', 'aalto', 'aachen', 'aarhus', 'aaron', 'aba', 'abadan', 'abaft', 'abajo',
            
            # Technical terms and foreign words
            'abacus', 'abased', 'abashed', 'abate', 'abated', 'abatement', 'abates', 'abating',
            
            # Very obscure or archaic words
            'abattoir', 'abba', 'abbas', 'abbasid', 'abbaye', 'abbe', 'abbess', 'abbot',
        }
    
    def _build_premium_vocabulary(self) -> Set[str]:
        """Build a curated set of high-quality English words."""
        premium = set()
        
        # Core vocabulary categories
        categories = {
            # Basic objects (household, everyday items)
            'objects': [
                'table', 'chair', 'bed', 'door', 'window', 'wall', 'floor', 'roof', 'house', 'room',
                'book', 'pen', 'paper', 'phone', 'clock', 'lamp', 'mirror', 'picture', 'bottle', 'cup',
                'plate', 'spoon', 'fork', 'knife', 'bowl', 'glass', 'box', 'bag', 'key', 'lock',
                'car', 'bike', 'bus', 'train', 'plane', 'boat', 'road', 'bridge', 'tree', 'flower',
                'stone', 'rock', 'hill', 'mountain', 'river', 'lake', 'beach', 'forest', 'field', 'garden'
            ],
            
            # Body parts
            'body': [
                'head', 'face', 'eye', 'ear', 'nose', 'mouth', 'tooth', 'tongue', 'lip', 'chin',
                'neck', 'shoulder', 'arm', 'hand', 'finger', 'thumb', 'chest', 'back', 'stomach', 'leg',
                'knee', 'foot', 'toe', 'skin', 'hair', 'bone', 'muscle', 'heart', 'brain', 'blood'
            ],
            
            # Animals
            'animals': [
                'cat', 'dog', 'bird', 'fish', 'horse', 'cow', 'pig', 'sheep', 'goat', 'chicken',
                'duck', 'rabbit', 'mouse', 'bear', 'lion', 'tiger', 'elephant', 'monkey', 'snake', 'frog',
                'bee', 'ant', 'spider', 'fly', 'worm', 'whale', 'shark', 'eagle', 'owl', 'deer'
            ],
            
            # Colors
            'colors': [
                'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white',
                'gray', 'grey', 'gold', 'silver', 'dark', 'light', 'bright', 'pale', 'deep', 'clear'
            ],
            
            # Common actions
            'actions': [
                'go', 'come', 'walk', 'run', 'jump', 'sit', 'stand', 'lie', 'sleep', 'wake',
                'eat', 'drink', 'cook', 'clean', 'wash', 'dry', 'open', 'close', 'push', 'pull',
                'take', 'give', 'put', 'get', 'make', 'break', 'fix', 'build', 'cut', 'fold',
                'read', 'write', 'speak', 'listen', 'look', 'see', 'watch', 'think', 'know', 'learn',
                'teach', 'help', 'work', 'play', 'sing', 'dance', 'laugh', 'cry', 'smile', 'love'
            ],
            
            # Time and weather
            'time_weather': [
                'day', 'night', 'morning', 'evening', 'week', 'month', 'year', 'time', 'hour', 'minute',
                'today', 'tomorrow', 'yesterday', 'now', 'then', 'early', 'late', 'quick', 'slow', 'fast',
                'sun', 'moon', 'star', 'sky', 'cloud', 'rain', 'snow', 'wind', 'hot', 'cold',
                'warm', 'cool', 'wet', 'dry', 'storm', 'fog', 'ice', 'fire', 'light', 'dark'
            ],
            
            # Emotions and qualities
            'emotions': [
                'happy', 'sad', 'angry', 'calm', 'excited', 'tired', 'strong', 'weak', 'brave', 'afraid',
                'kind', 'mean', 'nice', 'good', 'bad', 'right', 'wrong', 'true', 'false', 'real',
                'big', 'small', 'large', 'little', 'tall', 'short', 'long', 'wide', 'narrow', 'thick',
                'thin', 'heavy', 'light', 'hard', 'soft', 'rough', 'smooth', 'sharp', 'dull', 'clean'
            ],
            
            # Food and drink
            'food': [
                'bread', 'meat', 'fish', 'egg', 'milk', 'cheese', 'butter', 'sugar', 'salt', 'pepper',
                'rice', 'pasta', 'soup', 'salad', 'fruit', 'apple', 'orange', 'banana', 'grape', 'berry',
                'cake', 'cookie', 'tea', 'coffee', 'water', 'juice', 'wine', 'beer', 'ice', 'honey'
            ],
            
            # Common adjectives
            'adjectives': [
                'new', 'old', 'young', 'fresh', 'clean', 'dirty', 'empty', 'full', 'open', 'closed',
                'free', 'busy', 'easy', 'hard', 'simple', 'complex', 'clear', 'cloudy', 'quiet', 'loud',
                'safe', 'dangerous', 'cheap', 'expensive', 'rich', 'poor', 'healthy', 'sick', 'alive', 'dead'
            ],
            
            # Common verbs
            'verbs': [
                'be', 'have', 'do', 'say', 'get', 'make', 'know', 'think', 'take', 'see',
                'come', 'want', 'use', 'find', 'give', 'tell', 'ask', 'work', 'seem', 'feel',
                'try', 'leave', 'call', 'move', 'live', 'show', 'hear', 'play', 'turn', 'bring'
            ]
        }
        
        # Add all words from categories
        for category, words in categories.items():
            premium.update(words)
        
        return premium
    
    def validate_word(self, word: str) -> WordValidation:
        """Comprehensive validation of a word."""
        word = word.lower().strip()
        
        # Check if it's in our excluded list
        if word in self.excluded_words:
            return WordValidation(
                word=word,
                is_real_word=False,
                is_pronounceable=False,
                is_memorable=False,
                phonetic_score=0.0,
                reason="Excluded word (abbreviation, proper noun, or low quality)"
            )
        
        # Check against invalid patterns
        for pattern in self.invalid_patterns:
            if re.search(pattern, word):
                return WordValidation(
                    word=word,
                    is_real_word=False,
                    is_pronounceable=False,
                    is_memorable=False,
                    phonetic_score=0.0,
                    reason=f"Invalid pattern: {pattern}"
                )
        
        # Check if it's in our premium vocabulary
        if word in self.premium_words:
            return WordValidation(
                word=word,
                is_real_word=True,
                is_pronounceable=True,
                is_memorable=True,
                phonetic_score=1.0,
                reason="Premium vocabulary word"
            )
        
        # Check if it looks like a real English word
        is_real_word = self._looks_like_english_word(word)
        is_pronounceable = self._is_pronounceable(word)
        is_memorable = self._is_memorable(word)
        phonetic_score = self.scorer.score_word(word).total_score
        
        # Must pass all checks
        if is_real_word and is_pronounceable and is_memorable and phonetic_score >= 0.8:
            return WordValidation(
                word=word,
                is_real_word=True,
                is_pronounceable=True,
                is_memorable=True,
                phonetic_score=phonetic_score,
                reason="Passes all validation checks"
            )
        else:
            reasons = []
            if not is_real_word:
                reasons.append("doesn't look like English")
            if not is_pronounceable:
                reasons.append("hard to pronounce")
            if not is_memorable:
                reasons.append("not memorable")
            if phonetic_score < 0.8:
                reasons.append(f"low phonetic score ({phonetic_score:.2f})")
            
            return WordValidation(
                word=word,
                is_real_word=False,
                is_pronounceable=False,
                is_memorable=False,
                phonetic_score=phonetic_score,
                reason=f"Failed checks: {', '.join(reasons)}"
            )
    
    def _looks_like_english_word(self, word: str) -> bool:
        """Check if word looks like a real English word."""
        # Must be 3-10 characters
        if len(word) < 3 or len(word) > 10:
            return False
        
        # Must be alphabetic
        if not word.isalpha():
            return False
        
        # Check for reasonable vowel/consonant distribution
        vowels = sum(1 for c in word if c in 'aeiou')
        consonants = len(word) - vowels
        
        # Should have at least one vowel
        if vowels == 0:
            return False
        
        # Should have reasonable vowel-consonant ratio
        if vowels / len(word) < 0.2 or vowels / len(word) > 0.8:
            return False
        
        # Check for valid English patterns
        has_valid_pattern = False
        for pattern in self.valid_patterns:
            if re.search(pattern, word):
                has_valid_pattern = True
                break
        
        # If no valid pattern, check for basic structure
        if not has_valid_pattern:
            # Must have alternating vowels and consonants or common structures
            vowel_positions = [i for i, c in enumerate(word) if c in 'aeiou']
            if len(vowel_positions) >= 2:
                # Check if vowels are reasonably spaced
                min_spacing = min(vowel_positions[i+1] - vowel_positions[i] for i in range(len(vowel_positions)-1))
                if min_spacing >= 1:  # At least one consonant between vowels
                    has_valid_pattern = True
        
        return has_valid_pattern
    
    def _is_pronounceable(self, word: str) -> bool:
        """Check if word is easily pronounceable."""
        # No more than 2 consonants in a row
        if re.search(r'[bcdfghjklmnpqrstvwxz]{3,}', word):
            return False
        
        # No more than 2 vowels in a row (except common diphthongs)
        if re.search(r'[aeiou]{3,}', word):
            return False
        
        # Check for difficult consonant clusters
        difficult_clusters = ['tch', 'dge', 'ght', 'ngh', 'rgh', 'sht', 'xth']
        for cluster in difficult_clusters:
            if cluster in word:
                return False
        
        # Check for silent letter combinations
        silent_patterns = [r'^gn', r'^kn', r'^pn', r'^ps', r'^pt', r'^wr', r'mb$', r'mn$']
        for pattern in silent_patterns:
            if re.search(pattern, word):
                return False
        
        return True
    
    def _is_memorable(self, word: str) -> bool:
        """Check if word is memorable and distinct."""
        # Not too repetitive
        char_counts = Counter(word)
        if max(char_counts.values()) > len(word) * 0.6:  # No character more than 60%
            return False
        
        # Should have some variety in characters
        if len(set(word)) < len(word) * 0.5:  # At least 50% unique characters
            return False
        
        # Common English letter frequency patterns
        common_letters = 'etaoinshrdlcumwfgypbvkjxqz'
        uncommon_count = sum(1 for c in word if c in 'qxzj')
        if uncommon_count > 1:  # No more than one uncommon letter
            return False
        
        return True


def generate_premium_wordlist() -> List[str]:
    """Generate premium quality wordlist with strict validation."""
    filter = PremiumWordFilter()
    
    # Load source wordlists
    print("Loading source wordlists...")
    bip39_words, top_english = load_or_download_words()
    
    # Start with BIP39 words (validate them too)
    print("Validating BIP39 words...")
    validated_words = set()
    
    for word in bip39_words:
        validation = filter.validate_word(word)
        if validation.is_real_word:
            validated_words.add(word)
        else:
            print(f"Excluding BIP39 word '{word}': {validation.reason}")
    
    print(f"Kept {len(validated_words)} BIP39 words after validation")
    
    # Process top English words with strict validation
    print("\nValidating top English words...")
    candidates = []
    processed = 0
    
    for word in top_english:
        word = word.lower().strip()
        
        if word in validated_words:
            continue
        
        validation = filter.validate_word(word)
        if validation.is_real_word:
            candidates.append((word, validation.phonetic_score))
        
        processed += 1
        if processed % 10000 == 0:
            print(f"Processed {processed} words, found {len(candidates)} valid candidates...")
    
    # Sort by quality
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Add best candidates
    print(f"\nAdding {TARGET_SIZE - len(validated_words)} more words...")
    for word, score in candidates:
        if len(validated_words) >= TARGET_SIZE:
            break
        validated_words.add(word)
    
    # Convert to sorted list
    wordlist = sorted(list(validated_words))[:TARGET_SIZE]
    
    print(f"\nGenerated {len(wordlist)} premium words")
    return wordlist


def analyze_premium_quality(words: List[str]) -> Dict:
    """Analyze the quality of the premium wordlist."""
    filter = PremiumWordFilter()
    
    analysis = {
        'total_words': len(words),
        'validation_results': {},
        'length_distribution': Counter(len(word) for word in words),
        'first_letter_distribution': Counter(word[0] for word in words),
        'sample_words': {
            'excellent': [],
            'good': [],
            'concerning': []
        }
    }
    
    # Validate each word
    for word in words:
        validation = filter.validate_word(word)
        category = 'excellent' if validation.phonetic_score >= 0.9 else 'good' if validation.phonetic_score >= 0.8 else 'concerning'
        
        if len(analysis['sample_words'][category]) < 20:
            analysis['sample_words'][category].append({
                'word': word,
                'score': validation.phonetic_score,
                'reason': validation.reason
            })
    
    return analysis


def main():
    """Generate premium wordlist."""
    print("Premium Wordlist Generator")
    print("Strict validation for real English words only")
    print("=" * 50)
    
    wordlist = generate_premium_wordlist()
    
    # Analyze quality
    analysis = analyze_premium_quality(wordlist)
    
    print(f"\nFirst 50 words: {wordlist[:50]}")
    print(f"Length distribution: {dict(analysis['length_distribution'])}")
    
    # Show samples
    print("\nSample excellent words:")
    for item in analysis['sample_words']['excellent'][:10]:
        print(f"  {item['word']}: {item['score']:.3f} - {item['reason']}")
    
    if analysis['sample_words']['concerning']:
        print("\nConcerning words found:")
        for item in analysis['sample_words']['concerning'][:5]:
            print(f"  {item['word']}: {item['score']:.3f} - {item['reason']}")
    
    # Save results
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    # Save wordlist
    save_wordlist(wordlist, "../wordlists/premium_wordlist_65536.txt")
    
    # Save with analysis
    metadata = {
        "version": "4.0",
        "word_count": len(wordlist),
        "generation_method": "premium_strict_validation",
        "includes_bip39": True,
        "quality_analysis": analysis,
        "description": "Premium quality wordlist with strict validation for real English words only",
        "words": wordlist
    }
    
    with open(output_dir / "premium_wordlist_65536.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Saved premium wordlist to wordlists/premium_wordlist_65536.txt")
    print("✓ Saved analysis to wordlists/premium_wordlist_65536.json")


if __name__ == "__main__":
    main()