# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project generates a wordlist of 65,536 easy-to-read, easy-to-speak, and easy-to-hear words for cryptographic applications. It combines the BIP39 wordlist with carefully selected words from a larger English corpus.

## Development Commands

### Setup and Running
```bash
# Install UV if not available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the main wordlist generator
uv run python generate_wordlist.py

# Run word analysis
uv run python analyze_words.py
```

### Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html

# Run specific test
uv run pytest tests/test_wordlist.py -v
```

### Linting and Formatting
```bash
# Format code
uv run black .

# Lint
uv run ruff .

# Type check
uv run mypy .
```

## Architecture Overview

### Core Components
- `generate_wordlist.py` - Main wordlist generation script
- `analyze_words.py` - Word analysis and filtering utilities
- `word_scorer.py` - Scoring algorithm for word readability
- `bip39_loader.py` - BIP39 wordlist loader
- `download_sources.py` - Download source wordlists

### Word Selection Criteria
1. **Phonetic simplicity** - Easy to pronounce
2. **Distinctive sounds** - Hard to confuse when spoken
3. **Common usage** - Familiar to most speakers
4. **Length constraints** - 3-8 characters preferred
5. **No ambiguity** - Avoid homophones and similar-sounding words

## Development Guidelines

### Python Standards
- Use type hints for all functions
- Include docstrings with examples
- Handle errors gracefully
- Use dataclasses for word metadata
- Follow UV script format

### Important Notes
1. Target exactly 65,536 words (2^16)
2. Maintain compatibility with BIP39 words
3. Document selection criteria for each word
4. Provide phonetic analysis where possible