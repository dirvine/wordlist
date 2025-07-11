#!/usr/bin/env python3
"""
Download source wordlists for processing.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python download_sources.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import requests
from pathlib import Path
from typing import List


def download_bip39() -> List[str]:
    """Download BIP39 English wordlist."""
    url = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
    print(f"Downloading BIP39 wordlist from {url}...")
    
    response = requests.get(url)
    response.raise_for_status()
    
    words = [word.strip() for word in response.text.strip().split('\n')]
    print(f"Downloaded {len(words)} BIP39 words")
    return words


def download_top_english() -> List[str]:
    """Download top 100,000 English words."""
    url = "https://raw.githubusercontent.com/david47k/top-english-wordlists/master/top_english_words_lower_100000.txt"
    print(f"Downloading top English words from {url}...")
    
    response = requests.get(url)
    response.raise_for_status()
    
    words = [word.strip() for word in response.text.strip().split('\n')]
    print(f"Downloaded {len(words)} top English words")
    return words


def save_wordlist(words: List[str], filename: str) -> None:
    """Save wordlist to file."""
    output_dir = Path("wordlists")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    with open(output_path, 'w') as f:
        f.write('\n'.join(words))
    
    print(f"Saved {len(words)} words to {output_path}")


def main():
    """Download all source wordlists."""
    print("Downloading source wordlists...\n")
    
    # Download BIP39
    bip39_words = download_bip39()
    save_wordlist(bip39_words, "bip39_english.txt")
    
    # Download top English words
    top_english = download_top_english()
    save_wordlist(top_english, "top_english_100000.txt")
    
    print("\nAll wordlists downloaded successfully!")


if __name__ == "__main__":
    main()