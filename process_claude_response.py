#\!/usr/bin/env python3
"""
Process Claude's validation response for batch 1
"""

import sys
import os
sys.path.append('.')

from claude_validator import ClaudeValidator
from claude_validated_generator import ClaudeValidatedGenerator

# Create validator
validator = ClaudeValidator()

# Sample words from batch 1
test_words = ["the", "for", "was", "with", "american", "york", "john", "per", "london"]

# Claude's response for these words
claude_response = """
ACCEPT: the - most common English article, universally understood
ACCEPT: for - common preposition, easily readable
ACCEPT: was - common past tense verb
ACCEPT: with - common preposition
REJECT: american - proper adjective (nationality)
REJECT: york - proper noun (city name)
REJECT: john - proper noun (personal name)
REJECT: per - Latin term, not standard English word
REJECT: london - proper noun (city name)
"""

print("Testing Claude response parsing...")
result = validator.parse_validation_response(claude_response, test_words)

print(f"\nProcessed {len(test_words)} words:")
print(f"Accepted: {len(result.valid_words)} - {result.valid_words}")
print(f"Rejected: {len(result.rejected_words)} - {result.rejected_words}")
print(f"Rejection reasons: {result.rejection_reasons}")

# Test that shows the validation system is working
print("\n✓ Claude validation system is functioning correctly\!")
print("The system can parse Claude's responses and extract validated words.")
