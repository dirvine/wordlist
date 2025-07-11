# Generated Wordlists

This directory contains the generated wordlists produced by the various generation approaches in this project.

## Source Data

### BIP39 English Wordlist
- **File**: `bip39_english.txt`
- **Size**: 2,048 words
- **Source**: [Bitcoin BIP39 Standard](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt)
- **Purpose**: Foundation wordlist for cryptocurrency mnemonic phrases

### Top English Words
- **File**: `top_english_100000.txt`
- **Size**: 100,000 words
- **Source**: [Top English Words by david47k](https://github.com/david47k/top-english-wordlists)
- **Purpose**: Comprehensive English word frequency corpus

## Generated Wordlists

### Ultra-Clean Wordlist (NEW - Production Recommended)
- **Files**: `ultra_clean_65536.txt`, `ultra_clean_65536.json`
- **Algorithm**: Common, recognizable English words with comprehensive known-word vocabulary
- **Quality**: Focus on everyday English words from curated categories
- **Use Case**: **Production use** - common words everyone recognizes

### Refined Wordlist (NEW - Production Ready)
- **Files**: `refined_wordlist_65536.txt`, `refined_wordlist_65536.json`
- **Algorithm**: Eliminates non-words while preserving real English words
- **Quality Distribution**:
  - Excellent: 76.4%
  - Very Good: 23.6%
  - Good: 0.0%
- **Use Case**: **Production use** - real English words with quality filtering

### Premium Wordlist (NEW - Ultra-Strict)
- **Files**: `premium_wordlist_65536.txt`, `premium_wordlist_65536.json`
- **Algorithm**: Ultra-strict validation with premium vocabulary curation
- **Quality**: Highest standards with comprehensive validation
- **Use Case**: **Ultra-high quality** - strictest validation of word authenticity

### Claude-Optimized Wordlist (Research)
- **Files**: `claude_optimized_65536.txt`, `claude_optimized_65536.json`
- **Algorithm**: Linguistic analysis with phonetic clarity optimization
- **Quality Distribution**:
  - Premium: 5.0%
  - Excellent: 26.1%
  - Very Good: 68.8%
  - Good: 0.1%
  - Acceptable: 0.0%
- **Use Case**: **Research** - contains some non-words and proper nouns
- **⚠️ Note**: Contains problematic entries like "aab", "aac", proper nouns

### Enhanced Wordlist (Research)
- **Files**: `enhanced_wordlist_65536.txt`, `enhanced_wordlist_65536.json`
- **Algorithm**: Quality tier classification with homophone filtering
- **Quality Distribution**:
  - Excellent: 54.3%
  - Very Good: 38.5%
  - Good: 4.4%
  - Acceptable: 2.7%
- **Use Case**: Research and comparison

### Basic Wordlist (Research)
- **Files**: `wordlist_65536.txt`, `wordlist_65536.json`
- **Algorithm**: Basic scoring with simple filtering
- **Quality**: Mixed quality with basic readability checks
- **Use Case**: Research baseline, broad vocabulary

## Quality Metrics

### Readability Analysis
- **File**: `readability_evaluation.json`
- **Metrics**:
  - Phonetic distinctiveness: 99.9%
  - Pattern recognition for common English structures
  - Typing ease analysis
  - Comparative quality scoring

### Word Analysis
- **File**: `word_analysis.json`
- **Contains**:
  - Excellent word examples with scoring breakdown
  - Linguistic criteria definitions
  - Sample analysis of top-rated words

## File Formats

### Plain Text Format
```
# Example: claude_optimized_65536.txt
cat
dog
tree
house
...
```

### JSON Format with Metadata
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

## Usage Recommendations

### For Cryptographic Applications
- **Recommended**: `claude_optimized_65536.txt`
- **Reason**: Highest phonetic distinctiveness and clarity
- **Benefits**: Minimal confusion when spoken or transcribed

### For General Word Games
- **Recommended**: `enhanced_wordlist_65536.txt`
- **Reason**: Good balance of quality and vocabulary diversity
- **Benefits**: Broader range of word difficulty levels

### For Research and Analysis
- **Recommended**: All JSON files
- **Reason**: Include comprehensive metadata and quality analysis
- **Benefits**: Full transparency of generation process and quality metrics

## Quality Assurance

All wordlists have been validated for:
- ✅ Phonetic distinctiveness (99.9% unique pronunciation patterns)
- ✅ Appropriate length distribution (3-10 characters)
- ✅ English language patterns
- ✅ Homophone filtering
- ✅ Pronunciation clarity
- ✅ Typing ease optimization

## File Sizes

| File | Size | Words | Format |
|------|------|-------|---------|
| `claude_optimized_65536.txt` | 467 KB | 65,536 | Plain text |
| `claude_optimized_65536.json` | 920 KB | 65,536 | JSON with metadata |
| `enhanced_wordlist_65536.txt` | 500 KB | 65,536 | Plain text |
| `enhanced_wordlist_65536.json` | 950 KB | 65,536 | JSON with metadata |
| `wordlist_65536.txt` | 481 KB | 65,536 | Plain text |
| `wordlist_65536.json` | 930 KB | 65,536 | JSON with metadata |

## License

All generated wordlists are released under the MIT License, making them freely available for commercial and non-commercial use.