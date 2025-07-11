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

### 🚀 Claude-Validated Generation (Recommended)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Download source wordlists
uv run python download_sources.py

# Test the validation system
uv run python test_validation_system.py

# Generate Claude-validated wordlist (interactive)
uv run python claude_validated_generator.py

# Analyze validation results
uv run python validation_analysis.py
```

### 📊 Algorithmic Generation (Research)

```bash
# Generate basic wordlist
uv run python generate_wordlist.py

# Generate enhanced wordlist with quality tiers
uv run python enhanced_generator.py

# Generate Claude-optimized wordlist
uv run python claude_optimized_generator.py

# Analyze word characteristics
uv run python analyze_words.py

# Compare different approaches
uv run python compare_wordlists.py

# Evaluate readability metrics
uv run python evaluate_readability.py
```

## Generation Approaches

### 🏆 Claude-Validated Generation (Interactive) - **ULTIMATE QUALITY**

The Claude validation system provides human-level word quality assessment through interactive validation sessions.

#### How It Works
1. **Foundation**: Starts with 2,048 validated BIP39 words
2. **Candidate Pool**: Filters 100,000 English words to create 88,155 candidates
3. **Batch Validation**: Processes 5,000 words at a time through Claude
4. **Interactive Process**: You provide Claude's validation responses for each batch
5. **Smart Resumption**: Automatically saves progress and can resume interrupted sessions

#### Validation Criteria
- ✅ Real English words in standard dictionaries
- ✅ Easily readable and pronounceable
- ✅ Commonly understood (not highly technical)
- ✅ Appropriate for general audiences
- ❌ No proper nouns (places, names, brands)
- ❌ No abbreviations, acronyms, or codes
- ❌ No foreign words unless fully adopted

#### Usage Example
```bash
# Run the generator
uv run python claude_validated_generator.py

# Follow prompts to validate each batch:
# 1. Copy the validation prompt to Claude
# 2. Paste Claude's response back
# 3. System automatically processes and continues
# 4. Use Ctrl+C to pause and resume later
```

#### Benefits
- **Zero non-words**: Every word validated by Claude's language understanding
- **Human-level quality**: Catches subtle issues algorithms miss
- **Complete audit trail**: Full logging of all validation decisions
- **Resumable process**: Can be interrupted and resumed without losing progress
- **Quality analytics**: Comprehensive reporting on validation patterns

### 📊 Algorithmic Generation Approaches

### 1. Basic Generator (`generate_wordlist.py`)
- Combines BIP39 with top English words
- Simple scoring algorithm
- Produces 65,536 words with basic quality filtering

### 2. Enhanced Generator (`enhanced_generator.py`)
- Adds quality tier classification
- Filters homophones and ambiguous words
- Improved phonetic pattern detection
- **Results**: 54.3% excellent quality, 38.5% very good

### 3. Claude-Optimized Generator (`claude_optimized_generator.py`)
- Uses linguistic knowledge for premium word selection
- Comprehensive phonetic clarity analysis
- Semantic concreteness evaluation
- **Results**: 5.0% premium, 26.1% excellent, 68.8% very good quality
- **⚠️ Note**: Contains some non-words due to algorithmic limitations

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

## Generated Wordlists

All generated wordlists are available in the [`wordlists/`](wordlists/) directory:

### Ready-to-Use Wordlists

**🏆 RECOMMENDED - Claude-Validated (Interactive Generation):**
- **[`claude_validated_65536.txt`](wordlists/claude_validated_65536.txt)** - **🚀 ULTIMATE QUALITY** - Every word validated by Claude
- Run `uv run python claude_validated_generator.py` to generate your own with human-level validation

**Production-Ready (Algorithmic):**
- **[`ultra_clean_65536.txt`](wordlists/ultra_clean_65536.txt)** - Common, recognizable English words only
- **[`refined_wordlist_65536.txt`](wordlists/refined_wordlist_65536.txt)** - Eliminates non-words while preserving real English
- **[`premium_wordlist_65536.txt`](wordlists/premium_wordlist_65536.txt)** - Premium quality with strict validation

**Research and Comparison:**
- **[`claude_optimized_65536.txt`](wordlists/claude_optimized_65536.txt)** - Linguistic optimization (contains some non-words)
- **[`enhanced_wordlist_65536.txt`](wordlists/enhanced_wordlist_65536.txt)** - Quality tiers with homophone filtering
- **[`wordlist_65536.txt`](wordlists/wordlist_65536.txt)** - Basic generation with simple filtering

**⚠️ Note:** The algorithmic wordlists may contain some problematic entries. For guaranteed quality, use the **Claude-validated** interactive generation system.

### JSON Format with Metadata
Each wordlist includes a JSON version with comprehensive metadata:
- **[`claude_optimized_65536.json`](wordlists/claude_optimized_65536.json)** - Includes quality analysis and generation details
- **[`enhanced_wordlist_65536.json`](wordlists/enhanced_wordlist_65536.json)** - Quality tier distribution data
- **[`wordlist_65536.json`](wordlists/wordlist_65536.json)** - Basic generation metadata

### Analysis Files
- **[`readability_evaluation.json`](wordlists/readability_evaluation.json)** - Comprehensive quality comparison
- **[`word_analysis.json`](wordlists/word_analysis.json)** - Linguistic feature analysis

See the [wordlists README](wordlists/README.md) for detailed information about each wordlist.

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