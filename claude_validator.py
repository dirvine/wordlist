#!/usr/bin/env python3
"""
Claude-powered word validator for creating high-quality English wordlists.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python claude_validator.py
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
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of validating a batch of words."""
    valid_words: List[str]
    rejected_words: List[str]
    rejection_reasons: Dict[str, str]
    processing_time: float
    batch_id: str


class ClaudeValidator:
    """Interface for validating words using Claude's language understanding."""
    
    def __init__(self, log_dir: str = "validation_logs"):
        """Initialize the validator with logging."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = int(time.time())
        
        # Validation criteria
        self.validation_criteria = {
            "english_word": "Must be a real English word found in standard dictionaries",
            "readable": "Must be easily readable and pronounceable by average English speakers", 
            "common_usage": "Should be commonly understood, not highly technical or archaic",
            "appropriate": "Must be appropriate for general audiences (no offensive terms)",
            "not_proper_noun": "Should not be a proper noun (place names, personal names, brand names)",
            "not_abbreviation": "Should not be an abbreviation, acronym, or code",
            "not_foreign": "Should not be a foreign language word unless fully adopted into English"
        }
        
        # Initialize logging
        self.validation_log = []
        self.load_previous_validations()
    
    def create_validation_prompt(self, words: List[str], batch_id: str) -> str:
        """Create a detailed validation prompt for Claude."""
        
        prompt = f"""# Word Validation Task - Batch {batch_id}

I need you to validate each of the following words for inclusion in a high-quality English wordlist for cryptographic applications. This wordlist will be used by people worldwide, so words must be:

## Validation Criteria:
1. **Real English words** - Found in standard English dictionaries
2. **Easily readable** - Pronounceable by average English speakers
3. **Commonly understood** - Not highly technical, medical, or archaic terms
4. **Appropriate** - Suitable for general audiences
5. **Not proper nouns** - No place names, personal names, or brand names
6. **Not abbreviations** - No acronyms, codes, or abbreviated forms
7. **Not foreign words** - Unless fully adopted into common English usage

## Instructions:
For each word below, respond with either:
- **ACCEPT**: [word] - [brief reason why it's good]
- **REJECT**: [word] - [specific reason for rejection]

Please be strict in your evaluation. When in doubt, err on the side of rejection to ensure only the highest quality words are included.

## Words to Validate ({len(words)} total):

"""
        
        # Add numbered word list
        for i, word in enumerate(words, 1):
            prompt += f"{i:3d}. {word}\n"
        
        prompt += f"""

## Expected Response Format:
For each word, provide one line in this exact format:
ACCEPT: word - reason
OR
REJECT: word - reason

Example:
ACCEPT: beautiful - common adjective, easily readable and pronounceable
REJECT: aachen - proper noun (German city name)
ACCEPT: mountain - common noun, universally understood
REJECT: xyz - not a real English word

Please evaluate all {len(words)} words above."""
        
        return prompt
    
    def parse_validation_response(self, response: str, original_words: List[str]) -> ValidationResult:
        """Parse Claude's validation response into structured results."""
        
        valid_words = []
        rejected_words = []
        rejection_reasons = {}
        
        # Extract decision lines
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse ACCEPT/REJECT lines
            if line.startswith('ACCEPT:'):
                match = re.match(r'ACCEPT:\s*(\w+)\s*-\s*(.+)', line)
                if match:
                    word, reason = match.groups()
                    word = word.lower().strip()
                    if word in original_words:
                        valid_words.append(word)
                        
            elif line.startswith('REJECT:'):
                match = re.match(r'REJECT:\s*(\w+)\s*-\s*(.+)', line)
                if match:
                    word, reason = match.groups()
                    word = word.lower().strip()
                    if word in original_words:
                        rejected_words.append(word)
                        rejection_reasons[word] = reason.strip()
        
        # Find any words that weren't processed
        processed_words = set(valid_words + rejected_words)
        missing_words = [w for w in original_words if w not in processed_words]
        
        # Treat missing words as rejected
        for word in missing_words:
            rejected_words.append(word)
            rejection_reasons[word] = "Not processed in response"
        
        return ValidationResult(
            valid_words=valid_words,
            rejected_words=rejected_words,
            rejection_reasons=rejection_reasons,
            processing_time=0.0,
            batch_id=""
        )
    
    def validate_batch_interactive(self, words: List[str], batch_id: str) -> ValidationResult:
        """Validate a batch of words through interactive Claude session."""
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_id}: Validating {len(words)} words")
        print(f"{'='*60}")
        
        # Create the validation prompt
        prompt = self.create_validation_prompt(words, batch_id)
        
        # Save prompt to file for reference
        prompt_file = self.log_dir / f"batch_{batch_id}_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        # Display prompt for user
        print("\n" + "="*80)
        print("CLAUDE VALIDATION PROMPT")
        print("="*80)
        print(prompt)
        print("="*80)
        print("\nPlease copy the above prompt to Claude and paste the response below.")
        print("Press Enter when ready to input Claude's response...")
        input()
        
        # Get Claude's response
        print("\nPaste Claude's validation response (press Ctrl+D when done):")
        response_lines = []
        try:
            while True:
                line = input()
                response_lines.append(line)
        except EOFError:
            pass
        
        response = '\n'.join(response_lines)
        
        # Save response
        response_file = self.log_dir / f"batch_{batch_id}_response.txt"
        with open(response_file, 'w') as f:
            f.write(response)
        
        # Parse the response
        start_time = time.time()
        result = self.parse_validation_response(response, words)
        result.processing_time = time.time() - start_time
        result.batch_id = batch_id
        
        # Log the results
        self.log_validation_result(result, words)
        
        # Display summary
        print(f"\n{'='*60}")
        print(f"BATCH {batch_id} RESULTS:")
        print(f"  Accepted: {len(result.valid_words)} words")
        print(f"  Rejected: {len(result.rejected_words)} words")
        print(f"  Acceptance Rate: {len(result.valid_words)/len(words)*100:.1f}%")
        print(f"{'='*60}")
        
        return result
    
    def log_validation_result(self, result: ValidationResult, original_words: List[str]) -> None:
        """Log validation results for analysis."""
        
        log_entry = {
            "timestamp": time.time(),
            "batch_id": result.batch_id,
            "original_count": len(original_words),
            "accepted_count": len(result.valid_words),
            "rejected_count": len(result.rejected_words),
            "acceptance_rate": len(result.valid_words) / len(original_words),
            "processing_time": result.processing_time,
            "accepted_words": result.valid_words,
            "rejected_words": result.rejected_words,
            "rejection_reasons": result.rejection_reasons
        }
        
        self.validation_log.append(log_entry)
        
        # Save to file
        log_file = self.log_dir / f"validation_session_{self.session_id}.json"
        with open(log_file, 'w') as f:
            json.dump(self.validation_log, f, indent=2)
    
    def load_previous_validations(self) -> None:
        """Load previous validation results to avoid re-validating."""
        
        # Look for existing log files
        log_files = list(self.log_dir.glob("validation_session_*.json"))
        
        if log_files:
            # Load the most recent session
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            try:
                with open(latest_log) as f:
                    self.validation_log = json.load(f)
                print(f"Loaded {len(self.validation_log)} previous validation batches")
            except (json.JSONDecodeError, FileNotFoundError):
                print("Could not load previous validations, starting fresh")
    
    def get_validated_words(self) -> Set[str]:
        """Get all previously validated words."""
        
        validated = set()
        for entry in self.validation_log:
            validated.update(entry.get("accepted_words", []))
        
        return validated
    
    def get_rejected_words(self) -> Set[str]:
        """Get all previously rejected words."""
        
        rejected = set()
        for entry in self.validation_log:
            rejected.update(entry.get("rejected_words", []))
        
        return rejected
    
    def generate_summary_report(self) -> Dict:
        """Generate summary statistics from all validations."""
        
        if not self.validation_log:
            return {"error": "No validation data available"}
        
        total_processed = sum(entry["original_count"] for entry in self.validation_log)
        total_accepted = sum(entry["accepted_count"] for entry in self.validation_log)
        total_rejected = sum(entry["rejected_count"] for entry in self.validation_log)
        
        # Collect rejection reasons
        all_rejections = {}
        for entry in self.validation_log:
            for word, reason in entry.get("rejection_reasons", {}).items():
                all_rejections[word] = reason
        
        # Analyze rejection patterns
        rejection_categories = {}
        for reason in all_rejections.values():
            category = self.categorize_rejection_reason(reason)
            rejection_categories[category] = rejection_categories.get(category, 0) + 1
        
        return {
            "total_batches": len(self.validation_log),
            "total_words_processed": total_processed,
            "total_accepted": total_accepted,
            "total_rejected": total_rejected,
            "overall_acceptance_rate": total_accepted / total_processed if total_processed > 0 else 0,
            "rejection_categories": rejection_categories,
            "avg_batch_size": total_processed / len(self.validation_log) if self.validation_log else 0,
            "session_id": self.session_id
        }
    
    def categorize_rejection_reason(self, reason: str) -> str:
        """Categorize rejection reasons for analysis."""
        
        reason_lower = reason.lower()
        
        if any(term in reason_lower for term in ["proper noun", "place name", "person", "name"]):
            return "proper_noun"
        elif any(term in reason_lower for term in ["abbreviation", "acronym", "code"]):
            return "abbreviation"
        elif any(term in reason_lower for term in ["technical", "medical", "scientific"]):
            return "technical"
        elif any(term in reason_lower for term in ["foreign", "not english", "language"]):
            return "foreign"
        elif any(term in reason_lower for term in ["archaic", "obsolete", "old"]):
            return "archaic"
        elif any(term in reason_lower for term in ["not a word", "not real", "invalid"]):
            return "not_word"
        else:
            return "other"


def main():
    """Test the Claude validator with a small batch."""
    
    validator = ClaudeValidator()
    
    # Test with a small sample
    test_words = [
        "beautiful", "mountain", "aachen", "xyz", "computer", 
        "telephone", "happiness", "quick", "strength", "london"
    ]
    
    print("Testing Claude Validator")
    print("=" * 50)
    
    result = validator.validate_batch_interactive(test_words, "TEST_01")
    
    print("\nValidation Complete!")
    print(f"Accepted: {result.valid_words}")
    print(f"Rejected: {result.rejected_words}")
    
    # Generate summary
    summary = validator.generate_summary_report()
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()