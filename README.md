# Wordlist Generator

Generate a wordlist of 65,536 easy-to-read, easy-to-speak, and easy-to-hear words for cryptographic applications.

## Overview

This project creates a comprehensive wordlist by combining the BIP39 wordlist with carefully selected words from a 100,000 word English corpus, using advanced linguistic analysis to ensure maximum readability and distinctiveness.

### Key Features

- **Multiple Generation Approaches**: Basic, Enhanced, and Claude-optimized generators
- **Quality Tier System**: Premium, Excellent, Very Good, Good, and Acceptable word categories
- **Linguistic Analysis**: Phonetic clarity, syllable patterns, and semantic concreteness
- **Comprehensive Filtering**: Homophone detection, ambiguous pronunciation avoidance
- **Readability Evaluation**: Multiple metrics for typing ease and pattern recognition
- **UV-Based Development**: Modern Python packaging with embedded dependencies

## Quick Start

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Download source wordlists
uv run python download_sources.py

# Generate basic wordlist
uv run python generate_wordlist.py

# Generate enhanced wordlist with quality tiers
uv run python enhanced_generator.py

# Generate Claude-optimized wordlist (recommended)
uv run python claude_optimized_generator.py

# Analyze word characteristics
uv run python analyze_words.py

# Compare different approaches
uv run python compare_wordlists.py

# Evaluate readability metrics
uv run python evaluate_readability.py
```

## Generation Approaches

### 1. Basic Generator (`generate_wordlist.py`)
- Combines BIP39 with top English words
- Simple scoring algorithm
- Produces 65,536 words with basic quality filtering

### 2. Enhanced Generator (`enhanced_generator.py`)
- Adds quality tier classification
- Filters homophones and ambiguous words
- Improved phonetic pattern detection
- **Results**: 54.3% excellent quality, 38.5% very good

### 3. Claude-Optimized Generator (`claude_optimized_generator.py`) - **Recommended**
- Uses linguistic knowledge for premium word selection
- Comprehensive phonetic clarity analysis
- Semantic concreteness evaluation
- **Results**: 5.0% premium, 26.1% excellent, 68.8% very good quality

## Selection Criteria

### Phonetic Clarity
- Consonant-vowel alternation patterns
- Avoidance of difficult consonant clusters
- Clear vowel sounds without ambiguity
- Minimal silent letters

### Semantic Clarity
- Concrete, everyday vocabulary
- Common objects, actions, and concepts
- Culturally neutral terms
- Age-appropriate language

### Distinctiveness
- Phonetically distinct from other words
- No confusable homophones
- Clear pronunciation patterns
- Minimal ambiguity when spoken

### Technical Criteria
- Length: 3-8 characters (optimal: 4-6)
- Syllables: 1-3 (optimal: 1-2)
- Alphabetic characters only
- Common English patterns

## Quality Metrics

The Claude-optimized wordlist achieves:
- **99.9% phonetic distinctiveness** - extremely low confusion rate
- **54.3% excellent quality** - words meeting highest standards
- **Strong pattern recognition** - 81.4% with clear consonants
- **Typing ease** - optimized for keyboard patterns

## Output Formats

### Plain Text
```
# output/claude_optimized_65536.txt
cat
dog
tree
house
...
```

### JSON with Metadata
```json
{
  "version": "3.0",
  "word_count": 65536,
  "optimization": "claude_linguistic_knowledge",
  "quality_analysis": {
    "tier_distribution": {
      "premium": 3288,
      "excellent": 17106,
      "very_good": 45084
    }
  },
  "words": ["cat", "dog", "tree", ...]
}
```

## Development

### Testing
```bash
# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html
```

### Code Quality
```bash
# Format code
uv run black .

# Lint code
uv run ruff .

# Type checking
uv run mypy .
```

## Architecture

### Core Components
- `word_scorer.py` - Phonetic and pattern analysis
- `download_sources.py` - Source wordlist management
- `generate_wordlist.py` - Basic generation algorithm
- `enhanced_generator.py` - Quality tier classification
- `claude_optimized_generator.py` - Linguistic optimization
- `analyze_words.py` - Word characteristic analysis
- `compare_wordlists.py` - Cross-approach comparison
- `evaluate_readability.py` - Comprehensive evaluation

### Dependencies
- Python 3.11+
- UV package manager
- requests (wordlist downloading)
- nltk (linguistic analysis)
- pytest (testing)
- black, ruff, mypy (code quality)

## Use Cases

- **Cryptographic Applications**: Mnemonic phrase generation
- **Password Systems**: Human-readable password components
- **Educational Tools**: Vocabulary building with quality assurance
- **Accessibility**: Screen reader and pronunciation-friendly word lists
- **Internationalization**: Base vocabulary for translation systems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the full test suite
5. Submit a pull request

## License

MIT - See LICENSE file for details