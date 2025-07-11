# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Gold standard wordlist generation with automated Claude validation criteria
- Automated wordlist cleaning system to remove non-English words
- Comprehensive validation report with detailed statistics and quality metrics
- Multiple validator implementations (automated, interactive, self-validated)
- Automated replacement of foreign words with proper English alternatives
- Comprehensive proper noun database (347 first names, 800+ places, 200+ brands)
- Foreign word detection for German, French, Spanish, and other languages
- Archaic word filtering (thou, thee, hath, etc.)
- Technical/medical term filtering to maintain general readability
- Pattern validation for consecutive consonants, vowels, and letter patterns
- Resumable processing with state management for large batch operations
- Detailed logging and audit trail for all validation decisions

### Changed
- README now highlights gold wordlist as the primary recommended option
- Updated documentation to emphasize automated gold standard generation
- Improved validation criteria with 7 comprehensive filtering rules
- Enhanced user interface with clear recommendations and quality indicators

### Fixed
- Removed 198 non-English words (French, German, Spanish) from final wordlist
- Eliminated proper nouns, abbreviations, and foreign words comprehensively
- Ensured all 65,536 words are proper English words with ASCII characters only
- Fixed acceptance rate calculation and quality reporting
- Resolved inconsistent foreign word filtering across different generators

### Performance
- Achieved 95.9% acceptance rate with gold standard validation
- Reduced processing time to 1.0 second for complete wordlist generation
- Automated cleaning process for efficient non-English word removal
- Optimized batch processing with 1,000-word chunks for memory efficiency

## [1.0.0] - 2024-07-11

### Added
- Comprehensive wordlist generation system targeting 65,536 words
- BIP39 wordlist integration as foundation (2,048 words)
- Top English words corpus integration (100,000 words)
- Word scoring algorithm based on phonetic clarity and readability
- Enhanced word filtering with quality tier system (excellent, very good, good, acceptable)
- Claude-optimized generator using linguistic knowledge for premium word selection
- Phonetic distinctiveness analysis to avoid confusable words
- Homophone detection and filtering system
- Typing ease analysis for keyboard patterns
- Pattern recognition for common English structures (CVC, CVCV, prefixes, suffixes)
- Comprehensive word comparison tools across different generation approaches
- Readability evaluation with multiple metrics
- Semantic clarity analysis for word concreteness
- Syllable counting and stress pattern analysis
- Silent letter detection and penalization
- Consonant cluster difficulty assessment
- UV-based Python project structure with embedded dependencies
- Comprehensive test suite for word scoring functionality
- JSON output format with detailed metadata and analysis
- Multiple output formats (plain text, JSON with metadata)

### Changed
- Improved word selection criteria from basic filtering to linguistic analysis
- Enhanced phonetic scoring from simple patterns to comprehensive clarity metrics
- Upgraded from single-tier to multi-tier quality classification system

### Technical Details
- Python 3.11+ requirement with UV package manager
- Requests library for downloading source wordlists
- NLTK integration for advanced linguistic analysis
- Comprehensive error handling and validation
- Memory-efficient processing of large wordlists
- Configurable quality thresholds and filtering parameters

### Quality Metrics Achieved
- 54.3% excellent quality words in Claude-optimized wordlist
- 99.9% phonetic distinctiveness across all approaches
- 5.0% premium tier words with exceptional clarity
- 26.1% excellent tier words with high readability
- 68.8% very good tier words meeting strict criteria
- Strong pattern recognition for common English structures
- Comprehensive coverage of semantic categories (objects, actions, nature, etc.)

### Documentation
- Complete README.md with installation and usage instructions
- CLAUDE.md for Claude Code development assistance
- Comprehensive docstrings for all functions and classes
- Example usage and command-line interface documentation
- Detailed analysis output explanations

### Testing
- Unit tests for word scoring functionality
- Integration tests for wordlist generation
- Pattern recognition validation
- Quality tier classification verification
- Phonetic analysis accuracy testing