#!/usr/bin/env python3
"""
Claude-validated wordlist generator - main orchestration logic.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python claude_validated_generator.py
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
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
import re

from claude_validator import ClaudeValidator
from generate_wordlist import save_wordlist


TARGET_SIZE = 65536  # 2^16
BATCH_SIZE = 5000  # Words per Claude validation batch


@dataclass
class GenerationState:
    """Track the state of wordlist generation."""
    bip39_words: Set[str]
    validated_words: Set[str]
    remaining_candidates: List[str]
    current_batch: int
    total_batches: int
    start_time: float
    

class ClaudeValidatedGenerator:
    """Main orchestrator for Claude-validated wordlist generation."""
    
    def __init__(self, output_dir: str = "wordlists"):
        """Initialize the generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.state_file = self.output_dir / "generation_state.json"
        self.validator = ClaudeValidator()
        
        # Initialize state
        self.state: Optional[GenerationState] = None
        
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
            if not self.is_basic_valid_word(word):
                continue
            
            candidates.append(word)
        
        print(f"Prepared {len(candidates)} candidate words for validation")
        print(f"Excluded {len(all_words) - len(candidates)} words (duplicates or invalid)")
        
        return candidates
    
    def is_basic_valid_word(self, word: str) -> bool:
        """Apply basic filters before Claude validation."""
        
        # Length check
        if len(word) < 3 or len(word) > 12:
            return False
        
        # Must be alphabetic
        if not word.isalpha():
            return False
        
        # Must be lowercase
        if not word.islower():
            return False
        
        # Skip obvious abbreviations
        if len(word) <= 3 and word.isupper():
            return False
        
        # Skip words with obvious problematic patterns
        problematic_patterns = [
            r'^[aeiou]{2,}[bcdfghjklmnpqrstvwxyz]$',  # aab, eef, etc.
            r'^[bcdfghjklmnpqrstvwxyz][aeiou]{2,}$',  # baa, cee, etc.
            r'^[aeiou][bcdfghjklmnpqrstvwxyz]{2,}$',  # abb, ecc, etc.
            r'^(.)\1{2,}',  # aaa, bbb, etc.
            r'[bcdfghjklmnpqrstvwxyz]{5,}',  # 5+ consonants
            r'[aeiou]{4,}',  # 4+ vowels
        ]
        
        for pattern in problematic_patterns:
            if re.search(pattern, word):
                return False
        
        return True
    
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
            
            print(f"Loaded previous generation state:")
            print(f"  - Batch {state.current_batch}/{state.total_batches}")
            print(f"  - {len(state.validated_words)} validated words")
            print(f"  - {len(state.remaining_candidates)} candidates remaining")
            
            return state
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Could not load generation state: {e}")
            return None
    
    def calculate_batch_plan(self, total_candidates: int, validated_count: int) -> tuple[int, int]:
        """Calculate how many batches we need to reach target size."""
        
        words_needed = TARGET_SIZE - validated_count
        batches_needed = (words_needed + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
        
        # We might need more batches due to rejection rate
        # Estimate based on typical acceptance rates (assume ~60% acceptance)
        estimated_acceptance_rate = 0.6
        estimated_batches = int(batches_needed / estimated_acceptance_rate) + 1
        
        # Don't process more candidates than we have
        max_possible_batches = (total_candidates + BATCH_SIZE - 1) // BATCH_SIZE
        actual_batches = min(estimated_batches, max_possible_batches)
        
        return words_needed, actual_batches
    
    def generate_wordlist(self, resume: bool = True) -> List[str]:
        """Generate the complete validated wordlist."""
        
        print("Claude-Validated Wordlist Generation")
        print("=" * 50)
        
        # Try to resume previous session
        if resume:
            self.state = self.load_generation_state()
        
        # Initialize new generation if no previous state
        if self.state is None:
            print("Starting new generation session...")
            
            bip39_words = self.load_bip39_words()
            candidates = self.prepare_candidate_words(bip39_words)
            
            # Check if we have enough candidates
            max_possible = len(bip39_words) + len(candidates)
            if max_possible < TARGET_SIZE:
                raise ValueError(f"Insufficient candidates: {max_possible} < {TARGET_SIZE}")
            
            words_needed, total_batches = self.calculate_batch_plan(len(candidates), len(bip39_words))
            
            self.state = GenerationState(
                bip39_words=bip39_words,
                validated_words=bip39_words.copy(),  # Start with BIP39 as validated
                remaining_candidates=candidates,
                current_batch=0,
                total_batches=total_batches,
                start_time=time.time()
            )
            
            print(f"Generation plan:")
            print(f"  - Foundation: {len(bip39_words)} BIP39 words")
            print(f"  - Need: {words_needed} more words")
            print(f"  - Candidates: {len(candidates)} available")
            print(f"  - Planned batches: {total_batches}")
            print(f"  - Batch size: {BATCH_SIZE}")
        
        # Process batches until we have enough words
        while (len(self.state.validated_words) < TARGET_SIZE and 
               self.state.remaining_candidates and 
               self.state.current_batch < self.state.total_batches):
            
            self.process_next_batch()
            self.save_generation_state(self.state)
        
        # Generate final wordlist
        final_words = sorted(list(self.state.validated_words))[:TARGET_SIZE]
        
        print(f"\nGeneration complete!")
        print(f"Final wordlist size: {len(final_words)}")
        print(f"Total processing time: {time.time() - self.state.start_time:.1f} seconds")
        
        return final_words
    
    def process_next_batch(self) -> None:
        """Process the next batch of candidate words."""
        
        if not self.state or not self.state.remaining_candidates:
            return
        
        # Prepare batch
        batch_size = min(BATCH_SIZE, len(self.state.remaining_candidates))
        batch_words = self.state.remaining_candidates[:batch_size]
        self.state.remaining_candidates = self.state.remaining_candidates[batch_size:]
        self.state.current_batch += 1
        
        batch_id = f"B{self.state.current_batch:03d}"
        
        print(f"\n{'='*60}")
        print(f"Processing Batch {self.state.current_batch}/{self.state.total_batches}")
        print(f"Words in batch: {len(batch_words)}")
        print(f"Current validated total: {len(self.state.validated_words)}")
        print(f"Target: {TARGET_SIZE}")
        print(f"Remaining candidates: {len(self.state.remaining_candidates)}")
        print(f"{'='*60}")
        
        # Validate with Claude
        result = self.validator.validate_batch_interactive(batch_words, batch_id)
        
        # Add validated words to our collection
        new_validated = set(result.valid_words)
        self.state.validated_words.update(new_validated)
        
        print(f"\nBatch {batch_id} processed:")
        print(f"  - Accepted: {len(result.valid_words)}")
        print(f"  - Rejected: {len(result.rejected_words)}")
        print(f"  - Total validated: {len(self.state.validated_words)}")
        print(f"  - Progress: {len(self.state.validated_words)/TARGET_SIZE*100:.1f}%")
        
        # Show some examples of accepted/rejected words
        if result.valid_words:
            print(f"  - Sample accepted: {result.valid_words[:5]}")
        if result.rejected_words:
            print(f"  - Sample rejected: {result.rejected_words[:5]}")
    
    def save_final_wordlist(self, words: List[str]) -> None:
        """Save the final validated wordlist."""
        
        # Save plain text version
        txt_file = self.output_dir / "claude_validated_65536.txt"
        save_wordlist(words, f"../{txt_file}")
        
        # Create comprehensive metadata
        metadata = {
            "version": "6.0",
            "word_count": len(words),
            "generation_method": "claude_validated",
            "includes_bip39": True,
            "target_size": TARGET_SIZE,
            "batch_size": BATCH_SIZE,
            "validation_criteria": self.validator.validation_criteria,
            "generation_summary": self.validator.generate_summary_report(),
            "description": "Claude-validated wordlist with human-level quality assessment",
            "words": words
        }
        
        # Save JSON version
        json_file = self.output_dir / "claude_validated_65536.json"
        with open(json_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nSaved wordlist:")
        print(f"  - Text: {txt_file}")
        print(f"  - JSON: {json_file}")
    
    def cleanup_state(self) -> None:
        """Clean up temporary state files after successful completion."""
        
        if self.state_file.exists():
            self.state_file.unlink()
            print("Cleaned up generation state file")


def main():
    """Run the complete Claude-validated wordlist generation."""
    
    generator = ClaudeValidatedGenerator()
    
    try:
        # Generate the wordlist
        final_words = generator.generate_wordlist(resume=True)
        
        # Save the results
        generator.save_final_wordlist(final_words)
        
        # Show final statistics
        print("\nFinal Statistics:")
        print(f"  - Total words: {len(final_words)}")
        print(f"  - First 10: {final_words[:10]}")
        print(f"  - Last 10: {final_words[-10:]}")
        
        # Generate validation summary
        summary = generator.validator.generate_summary_report()
        print(f"\nValidation Summary:")
        print(f"  - Batches processed: {summary.get('total_batches', 0)}")
        print(f"  - Overall acceptance rate: {summary.get('overall_acceptance_rate', 0)*100:.1f}%")
        print(f"  - Words rejected: {summary.get('total_rejected', 0)}")
        
        # Clean up
        generator.cleanup_state()
        
        print("\n✓ Claude-validated wordlist generation complete!")
        
    except KeyboardInterrupt:
        print("\nGeneration interrupted. State saved for resumption.")
    except Exception as e:
        print(f"\nError during generation: {e}")
        print("State saved for debugging and resumption.")


if __name__ == "__main__":
    main()