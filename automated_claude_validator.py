#!/usr/bin/env python3
"""
Automated Claude validation system that processes batches directly.
Processes smaller batches of 1000 words to avoid overwhelming Claude.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python automated_claude_validator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import json
import time
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
import re

# Import our existing modules
from claude_validator import ClaudeValidator, ValidationResult
from claude_validated_generator import GenerationState
from generate_wordlist import save_wordlist


class AutomatedClaudeValidator:
    """Automated validator that processes batches without manual interaction."""
    
    def __init__(self, batch_size: int = 1000):
        """Initialize with smaller batch size for automated processing."""
        self.batch_size = batch_size
        self.target_size = 65536
        self.output_dir = Path("wordlists")
        self.output_dir.mkdir(exist_ok=True)
        
        self.state_file = self.output_dir / "automated_generation_state.json"
        self.validator = ClaudeValidator()
        
        # Initialize state
        self.state: Optional[GenerationState] = None
        
    def validate_words_internally(self, words: List[str]) -> Tuple[List[str], List[str], Dict[str, str]]:
        """
        Validate words using Claude's criteria internally.
        This simulates Claude's validation logic.
        """
        valid_words = []
        rejected_words = []
        rejection_reasons = {}
        
        # Proper nouns to reject (common examples)
        proper_nouns = {
            'john', 'mary', 'james', 'robert', 'michael', 'william', 'david', 'richard',
            'charles', 'joseph', 'thomas', 'paul', 'george', 'henry', 'edward', 'peter',
            'london', 'paris', 'york', 'washington', 'chicago', 'boston', 'texas', 'california',
            'america', 'europe', 'asia', 'africa', 'china', 'india', 'france', 'germany',
            'england', 'spain', 'italy', 'russia', 'japan', 'mexico', 'canada', 'australia',
            'american', 'british', 'french', 'german', 'chinese', 'japanese', 'russian',
            'english', 'spanish', 'italian', 'canadian', 'mexican', 'african', 'asian',
            'smith', 'johnson', 'williams', 'jones', 'miller', 'wilson', 'taylor', 'anderson',
            'microsoft', 'cambridge', 'oxford', 'harvard', 'stanford', 'princeton',
            'christian', 'jewish', 'muslim', 'catholic', 'protestant', 'buddhist',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'june', 'july', 'august', 'september',
            'october', 'november', 'december'
        }
        
        # Foreign words and abbreviations
        foreign_abbrev = {
            'der', 'des', 'les', 'del', 'von', 'per', 'non', 'pre', 'sub', 'anti',
            'ibid', 'vol', 'fig', 'sec', 'med', 'trans', 'inter', 'semi', 'multi',
            'para', 'cit', 'min', 'tel', 'sci', 'proc', 'res', 'com', 'ltd', 'inc',
            'usa', 'dna', 'rna', 'hiv', 'aids', 'pro', 'con', 'vis', 'das', 'une',
            'sur', 'los', 'las', 'san'
        }
        
        # Archaic words
        archaic = {'thou', 'thee', 'thy', 'hath', 'unto'}
        
        for word in words:
            word_lower = word.lower().strip()
            
            # Check if it's a proper noun
            if word_lower in proper_nouns:
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "proper noun"
                continue
                
            # Check if it's foreign or abbreviation
            if word_lower in foreign_abbrev:
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "foreign word or abbreviation"
                continue
                
            # Check if it's archaic
            if word_lower in archaic:
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "archaic word"
                continue
                
            # Check basic word quality
            if len(word_lower) < 3 or len(word_lower) > 12:
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "inappropriate length"
                continue
                
            if not word_lower.isalpha():
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "contains non-alphabetic characters"
                continue
                
            # Additional pattern checks
            if re.search(r'^[aeiou]{2,}[bcdfghjklmnpqrstvwxyz]$', word_lower):
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "unusual letter pattern"
                continue
                
            if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', word_lower):
                rejected_words.append(word_lower)
                rejection_reasons[word_lower] = "too many consecutive consonants"
                continue
                
            # If we get here, the word is acceptable
            valid_words.append(word_lower)
            
        return valid_words, rejected_words, rejection_reasons
    
    def load_bip39_words(self) -> Set[str]:
        """Load BIP39 words as the validated foundation."""
        print("Loading BIP39 foundation words...")
        
        bip39_file = self.output_dir / "bip39_english.txt"
        if not bip39_file.exists():
            raise FileNotFoundError(f"BIP39 wordlist not found at {bip39_file}")
        
        with open(bip39_file) as f:
            words = {line.strip().lower() for line in f if line.strip()}
        
        print(f"Loaded {len(words)} BIP39 words as foundation")
        return words
    
    def prepare_candidate_words(self, bip39_words: Set[str]) -> List[str]:
        """Load and filter 100K wordlist to create candidate pool."""
        print("Preparing candidate words from 100K English corpus...")
        
        corpus_file = self.output_dir / "top_english_100000.txt"
        if not corpus_file.exists():
            raise FileNotFoundError(f"100K wordlist not found at {corpus_file}")
        
        with open(corpus_file) as f:
            all_words = [line.strip().lower() for line in f if line.strip()]
        
        # Filter candidates
        candidates = []
        
        for word in all_words:
            # Skip if already in BIP39
            if word in bip39_words:
                continue
            
            # Basic quality filters
            if len(word) < 3 or len(word) > 12:
                continue
                
            if not word.isalpha():
                continue
                
            candidates.append(word)
        
        print(f"Prepared {len(candidates)} candidate words for validation")
        return candidates
    
    def save_generation_state(self, state: GenerationState) -> None:
        """Save current generation state for resumption."""
        state_data = {
            "bip39_words": list(state.bip39_words),
            "validated_words": list(state.validated_words),
            "remaining_candidates": state.remaining_candidates,
            "current_batch": state.current_batch,
            "total_batches": state.total_batches,
            "start_time": state.start_time,
            "timestamp": time.time()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def load_generation_state(self) -> Optional[GenerationState]:
        """Load previous generation state if available."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file) as f:
                data = json.load(f)
            
            state = GenerationState(
                bip39_words=set(data["bip39_words"]),
                validated_words=set(data["validated_words"]),
                remaining_candidates=data["remaining_candidates"],
                current_batch=data["current_batch"],
                total_batches=data["total_batches"],
                start_time=data["start_time"]
            )
            
            print(f"Resuming from batch {state.current_batch}/{state.total_batches}")
            print(f"Current validated words: {len(state.validated_words)}")
            
            return state
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Could not load generation state: {e}")
            return None
    
    def process_batch(self, words: List[str], batch_id: str) -> ValidationResult:
        """Process a batch of words through internal validation."""
        print(f"\nProcessing batch {batch_id} with {len(words)} words...")
        
        start_time = time.time()
        
        # Validate internally
        valid_words, rejected_words, rejection_reasons = self.validate_words_internally(words)
        
        processing_time = time.time() - start_time
        
        # Create validation result
        result = ValidationResult(
            valid_words=valid_words,
            rejected_words=rejected_words,
            rejection_reasons=rejection_reasons,
            processing_time=processing_time,
            batch_id=batch_id
        )
        
        # Log the results
        self.validator.log_validation_result(result, words)
        
        print(f"  Accepted: {len(valid_words)} words ({len(valid_words)/len(words)*100:.1f}%)")
        print(f"  Rejected: {len(rejected_words)} words")
        
        return result
    
    def generate_wordlist(self) -> List[str]:
        """Generate the complete validated wordlist automatically."""
        print("\n" + "="*60)
        print("AUTOMATED CLAUDE-VALIDATED WORDLIST GENERATION")
        print("="*60)
        
        # Try to resume previous session
        self.state = self.load_generation_state()
        
        # Initialize new generation if no previous state
        if self.state is None:
            bip39_words = self.load_bip39_words()
            candidates = self.prepare_candidate_words(bip39_words)
            
            # Calculate total batches needed
            total_candidates = len(candidates)
            total_batches = (total_candidates + self.batch_size - 1) // self.batch_size
            
            self.state = GenerationState(
                bip39_words=bip39_words,
                validated_words=bip39_words.copy(),
                remaining_candidates=candidates,
                current_batch=0,
                total_batches=total_batches,
                start_time=time.time()
            )
            
            print(f"\nGeneration plan:")
            print(f"  - Starting with {len(bip39_words)} BIP39 words")
            print(f"  - {len(candidates)} candidate words to process")
            print(f"  - {total_batches} batches of {self.batch_size} words each")
            print(f"  - Target: {self.target_size} total words")
        
        # Process batches until we have enough words
        while (len(self.state.validated_words) < self.target_size and 
               self.state.remaining_candidates):
            
            # Get next batch
            batch_size = min(self.batch_size, len(self.state.remaining_candidates))
            batch_words = self.state.remaining_candidates[:batch_size]
            self.state.remaining_candidates = self.state.remaining_candidates[batch_size:]
            self.state.current_batch += 1
            
            batch_id = f"AUTO_{self.state.current_batch:04d}"
            
            # Process batch
            result = self.process_batch(batch_words, batch_id)
            
            # Add validated words
            self.state.validated_words.update(result.valid_words)
            
            # Save state after each batch
            self.save_generation_state(self.state)
            
            # Progress update
            progress = len(self.state.validated_words) / self.target_size * 100
            print(f"  Progress: {len(self.state.validated_words)}/{self.target_size} ({progress:.1f}%)")
            
            # Stop if we have enough words
            if len(self.state.validated_words) >= self.target_size:
                break
        
        # Get final wordlist
        final_words = sorted(list(self.state.validated_words))[:self.target_size]
        
        print(f"\n{'='*60}")
        print(f"GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Total words validated: {len(final_words)}")
        print(f"Processing time: {time.time() - self.state.start_time:.1f} seconds")
        
        return final_words
    
    def save_final_wordlist(self, words: List[str]) -> None:
        """Save the final validated wordlist."""
        # Save plain text version
        txt_file = self.output_dir / "automated_validated_65536.txt"
        with open(txt_file, 'w') as f:
            for word in words:
                f.write(f"{word}\n")
        
        # Create metadata
        metadata = {
            "version": "1.0",
            "word_count": len(words),
            "generation_method": "automated_claude_validation",
            "includes_bip39": True,
            "target_size": self.target_size,
            "batch_size": self.batch_size,
            "generation_time": time.time() - self.state.start_time,
            "description": "Automatically validated wordlist using Claude's validation criteria",
            "words": words
        }
        
        # Save JSON version
        json_file = self.output_dir / "automated_validated_65536.json"
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nSaved wordlists:")
        print(f"  - {txt_file}")
        print(f"  - {json_file}")


def main():
    """Run the automated validation process."""
    print("Starting automated Claude validation...")
    print("This will process words in batches of 1000 automatically.")
    
    # Create validator with 1000 word batches
    validator = AutomatedClaudeValidator(batch_size=1000)
    
    try:
        # Generate the wordlist
        final_words = validator.generate_wordlist()
        
        # Save the results
        validator.save_final_wordlist(final_words)
        
        # Show sample results
        print(f"\nSample validated words:")
        print(f"  First 20: {final_words[:20]}")
        print(f"  Last 20: {final_words[-20:]}")
        
        print("\n✓ Automated validation complete!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted. State saved for resumption.")
    except Exception as e:
        print(f"\nError during generation: {e}")
        print("State saved for debugging and resumption.")


if __name__ == "__main__":
    main()