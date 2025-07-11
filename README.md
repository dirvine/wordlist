# Wordlist Generator

Generate a wordlist of 65,536 easy-to-read, easy-to-speak, and easy-to-hear words for cryptographic applications.

## Overview

This project creates a comprehensive wordlist by:
1. Starting with the BIP39 wordlist (2048 words)
2. Adding carefully selected words from a 100,000 word English corpus
3. Filtering for readability, speakability, and distinctiveness
4. Producing exactly 65,536 words (2^16) for use in cryptographic systems

## Quick Start

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Generate the wordlist
uv run python generate_wordlist.py

# Analyze word characteristics
uv run python analyze_words.py
```

## Selection Criteria

Words are selected based on:
- **Phonetic simplicity**: Easy to pronounce across accents
- **Auditory distinctiveness**: Hard to confuse when spoken
- **Common usage**: Familiar to most English speakers
- **Length**: Preferably 3-8 characters
- **No ambiguity**: Avoiding homophones and similar-sounding words

## License

MIT