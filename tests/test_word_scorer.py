"""Tests for word scoring functionality."""

import pytest
from word_scorer import WordScorer, WordScore


class TestWordScorer:
    """Test the WordScorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = WordScorer()
    
    def test_simple_words_score_high(self):
        """Test that simple, readable words score high."""
        good_words = ["cat", "dog", "happy", "run", "blue", "green"]
        
        for word in good_words:
            score = self.scorer.score_word(word)
            assert score.total_score >= 0.7, f"{word} should score high"
    
    def test_difficult_words_score_low(self):
        """Test that difficult words score low."""
        difficult_words = ["rhythm", "strength", "through", "xylophone"]
        
        for word in difficult_words:
            score = self.scorer.score_word(word)
            assert score.total_score < 0.7, f"{word} should score low"
    
    def test_length_scoring(self):
        """Test length-based scoring."""
        # Too short
        assert self.scorer.score_word("a").length_score < 0.5
        assert self.scorer.score_word("at").length_score < 1.0
        
        # Ideal length
        assert self.scorer.score_word("word").length_score == 1.0
        assert self.scorer.score_word("hello").length_score == 1.0
        
        # Too long
        assert self.scorer.score_word("extraordinary").length_score < 0.5
    
    def test_phonetic_patterns(self):
        """Test phonetic pattern detection."""
        # Words with difficult consonant clusters
        score = self.scorer.score_word("strengths")
        assert "difficult pattern" in str(score.reasons)
        
        # Words with good patterns
        score = self.scorer.score_word("banana")
        assert score.phonetic_score > 0.8
    
    def test_is_good_word(self):
        """Test the is_good_word method."""
        assert self.scorer.is_good_word("hello", threshold=0.7)
        assert not self.scorer.is_good_word("xyzzy", threshold=0.7)
        
        # Test with different thresholds
        assert self.scorer.is_good_word("through", threshold=0.5)
        assert not self.scorer.is_good_word("through", threshold=0.8)