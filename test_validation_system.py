#!/usr/bin/env python3
"""
Test script for the Claude validation system.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python test_validation_system.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import json
from pathlib import Path
from typing import List, Set

from claude_validator import ClaudeValidator
from claude_validated_generator import ClaudeValidatedGenerator
from validation_analysis import ValidationAnalyzer


def test_bip39_loading():
    """Test BIP39 wordlist loading."""
    
    print("Testing BIP39 loading...")
    
    generator = ClaudeValidatedGenerator()
    
    try:
        bip39_words = generator.load_bip39_words()
        print(f"✓ Loaded {len(bip39_words)} BIP39 words")
        
        # Show some examples
        sample_words = sorted(list(bip39_words))[:10]
        print(f"  Sample words: {sample_words}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading BIP39: {e}")
        return False


def test_candidate_preparation():
    """Test candidate word preparation."""
    
    print("\nTesting candidate preparation...")
    
    generator = ClaudeValidatedGenerator()
    
    try:
        bip39_words = generator.load_bip39_words()
        candidates = generator.prepare_candidate_words(bip39_words)
        
        print(f"✓ Prepared {len(candidates)} candidate words")
        print(f"  First 10 candidates: {candidates[:10]}")
        print(f"  Last 10 candidates: {candidates[-10:]}")
        
        # Check for no BIP39 overlap
        overlap = set(candidates) & bip39_words
        if overlap:
            print(f"✗ Found BIP39 overlap: {list(overlap)[:5]}")
            return False
        else:
            print("✓ No BIP39 overlap detected")
        
        return True
        
    except Exception as e:
        print(f"✗ Error preparing candidates: {e}")
        return False


def test_validator_prompt_generation():
    """Test validator prompt generation."""
    
    print("\nTesting validator prompt generation...")
    
    validator = ClaudeValidator()
    
    test_words = [
        "beautiful", "mountain", "aachen", "xyz", "computer",
        "happiness", "london", "strength", "abbreviation", "the"
    ]
    
    try:
        prompt = validator.create_validation_prompt(test_words, "TEST")
        print(f"✓ Generated prompt ({len(prompt)} characters)")
        
        # Check prompt contains all expected elements
        required_elements = [
            "Word Validation Task",
            "Validation Criteria",
            "ACCEPT:",
            "REJECT:",
            str(len(test_words))
        ]
        
        for element in required_elements:
            if element not in prompt:
                print(f"✗ Missing required element: {element}")
                return False
        
        print("✓ Prompt contains all required elements")
        
        # Show a snippet
        print(f"  Prompt snippet: {prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating prompt: {e}")
        return False


def test_response_parsing():
    """Test parsing of Claude responses."""
    
    print("\nTesting response parsing...")
    
    validator = ClaudeValidator()
    
    # Simulate Claude response
    test_response = """
ACCEPT: beautiful - common adjective, easily readable and pronounceable
REJECT: aachen - proper noun (German city name)
ACCEPT: mountain - common noun, universally understood  
REJECT: xyz - not a real English word
ACCEPT: computer - common noun, universally understood
ACCEPT: happiness - common abstract noun, easily understood
REJECT: london - proper noun (city name)
ACCEPT: strength - common noun, easily understood
REJECT: abbreviation - too technical/long for this context
ACCEPT: the - most common English word
"""
    
    original_words = [
        "beautiful", "aachen", "mountain", "xyz", "computer",
        "happiness", "london", "strength", "abbreviation", "the"
    ]
    
    try:
        result = validator.parse_validation_response(test_response, original_words)
        
        print(f"✓ Parsed response successfully")
        print(f"  Accepted: {len(result.valid_words)} words")
        print(f"  Rejected: {len(result.rejected_words)} words")
        print(f"  Valid words: {result.valid_words}")
        print(f"  Rejected words: {result.rejected_words}")
        
        # Verify correct parsing
        expected_valid = {"beautiful", "mountain", "computer", "happiness", "strength", "the"}
        expected_rejected = {"aachen", "xyz", "london", "abbreviation"}
        
        if set(result.valid_words) == expected_valid and set(result.rejected_words) == expected_rejected:
            print("✓ Parsing results match expected")
            return True
        else:
            print(f"✗ Parsing mismatch")
            print(f"  Expected valid: {expected_valid}")
            print(f"  Got valid: {set(result.valid_words)}")
            return False
        
    except Exception as e:
        print(f"✗ Error parsing response: {e}")
        return False


def test_state_management():
    """Test generation state save/load."""
    
    print("\nTesting state management...")
    
    generator = ClaudeValidatedGenerator()
    
    try:
        # Create test state
        from claude_validated_generator import GenerationState
        import time
        
        test_state = GenerationState(
            bip39_words={"test1", "test2"},
            validated_words={"test1", "test2", "validated1"},
            remaining_candidates=["candidate1", "candidate2", "candidate3"],
            current_batch=1,
            total_batches=5,
            start_time=time.time()
        )
        
        # Save state
        generator.state = test_state
        generator.save_generation_state(test_state)
        print("✓ Saved generation state")
        
        # Load state
        loaded_state = generator.load_generation_state()
        
        if loaded_state:
            print("✓ Loaded generation state")
            print(f"  Batch: {loaded_state.current_batch}/{loaded_state.total_batches}")
            print(f"  Validated: {len(loaded_state.validated_words)}")
            print(f"  Remaining: {len(loaded_state.remaining_candidates)}")
            
            # Clean up test file
            if generator.state_file.exists():
                generator.state_file.unlink()
                
            return True
        else:
            print("✗ Failed to load state")
            return False
            
    except Exception as e:
        print(f"✗ Error with state management: {e}")
        return False


def test_validation_analysis():
    """Test validation analysis functionality."""
    
    print("\nTesting validation analysis...")
    
    # Create test validation logs
    log_dir = Path("test_validation_logs")
    log_dir.mkdir(exist_ok=True)
    
    test_log_data = [
        {
            "timestamp": 1234567890,
            "batch_id": "TEST_01",
            "original_count": 10,
            "accepted_count": 6,
            "rejected_count": 4,
            "acceptance_rate": 0.6,
            "processing_time": 30.0,
            "accepted_words": ["word1", "word2", "word3", "word4", "word5", "word6"],
            "rejected_words": ["bad1", "bad2", "bad3", "bad4"],
            "rejection_reasons": {
                "bad1": "proper noun (place name)",
                "bad2": "not a real English word",
                "bad3": "abbreviation", 
                "bad4": "technical term"
            }
        }
    ]
    
    try:
        # Save test log
        test_log_file = log_dir / "validation_session_test.json"
        with open(test_log_file, 'w') as f:
            json.dump(test_log_data, f)
        
        # Test analyzer
        analyzer = ValidationAnalyzer(str(log_dir))
        logs = analyzer.load_all_validation_logs()
        
        print(f"✓ Loaded {len(logs)} validation entries")
        
        # Test analysis functions
        rejection_analysis = analyzer.analyze_rejection_patterns(logs)
        acceptance_analysis = analyzer.analyze_acceptance_patterns(logs)
        efficiency = analyzer.calculate_validation_efficiency(logs)
        
        print("✓ Generated rejection analysis")
        print("✓ Generated acceptance analysis") 
        print("✓ Generated efficiency metrics")
        
        print(f"  Sample rejection categories: {dict(rejection_analysis['by_category'])}")
        print(f"  Acceptance rate: {efficiency['overall_acceptance_rate']:.1%}")
        
        # Clean up test files
        if test_log_file.exists():
            test_log_file.unlink()
        if log_dir.exists():
            log_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"✗ Error with validation analysis: {e}")
        
        # Clean up on error
        if log_dir.exists():
            import shutil
            shutil.rmtree(log_dir)
        
        return False


def run_full_system_test():
    """Run comprehensive system test."""
    
    print("="*60)
    print("CLAUDE VALIDATION SYSTEM TEST")
    print("="*60)
    
    tests = [
        ("BIP39 Loading", test_bip39_loading),
        ("Candidate Preparation", test_candidate_preparation),
        ("Validator Prompt Generation", test_validator_prompt_generation),
        ("Response Parsing", test_response_parsing),
        ("State Management", test_state_management),
        ("Validation Analysis", test_validation_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! System is ready for production use.")
        return True
    else:
        print(f"\n⚠️  {len(tests) - passed} test(s) failed. Please review before proceeding.")
        return False


def main():
    """Run the test suite."""
    
    success = run_full_system_test()
    
    if success:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Run: uv run python claude_validated_generator.py")
        print("2. Follow the interactive prompts to validate word batches")
        print("3. The system will process words until reaching 65,536 total")
        print("4. Use Ctrl+C to interrupt and resume later if needed")
        print("5. Run: uv run python validation_analysis.py for quality reports")
    else:
        print("\nPlease fix the failing tests before proceeding with generation.")


if __name__ == "__main__":
    main()