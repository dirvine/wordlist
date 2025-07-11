#!/usr/bin/env python3
"""
Validation analysis and quality reporting for Claude-validated wordlists.

UV Dependencies:
# Install UV if not available: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run this script: uv run python validation_analysis.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import time

from claude_validator import ClaudeValidator


class ValidationAnalyzer:
    """Analyze validation results and generate quality reports."""
    
    def __init__(self, log_dir: str = "validation_logs"):
        """Initialize the analyzer."""
        self.log_dir = Path(log_dir)
        self.validator = ClaudeValidator(str(log_dir))
    
    def load_all_validation_logs(self) -> List[Dict]:
        """Load all validation session logs."""
        
        log_files = list(self.log_dir.glob("validation_session_*.json"))
        all_logs = []
        
        for log_file in log_files:
            try:
                with open(log_file) as f:
                    session_data = json.load(f)
                all_logs.extend(session_data)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Could not load {log_file}")
        
        return all_logs
    
    def analyze_rejection_patterns(self, logs: List[Dict]) -> Dict:
        """Analyze patterns in word rejections."""
        
        rejection_analysis = {
            "by_category": Counter(),
            "by_length": Counter(),
            "by_starting_letter": Counter(),
            "common_reasons": Counter(),
            "examples": defaultdict(list)
        }
        
        for entry in logs:
            for word, reason in entry.get("rejection_reasons", {}).items():
                # Categorize rejection
                category = self.validator.categorize_rejection_reason(reason)
                rejection_analysis["by_category"][category] += 1
                rejection_analysis["examples"][category].append((word, reason))
                
                # Analyze by word characteristics
                rejection_analysis["by_length"][len(word)] += 1
                rejection_analysis["by_starting_letter"][word[0]] += 1
                rejection_analysis["common_reasons"][reason] += 1
        
        # Limit examples
        for category in rejection_analysis["examples"]:
            rejection_analysis["examples"][category] = rejection_analysis["examples"][category][:10]
        
        return rejection_analysis
    
    def analyze_acceptance_patterns(self, logs: List[Dict]) -> Dict:
        """Analyze patterns in word acceptances."""
        
        acceptance_analysis = {
            "by_length": Counter(),
            "by_starting_letter": Counter(),
            "by_batch": [],
            "quality_trends": []
        }
        
        for entry in logs:
            accepted_words = entry.get("accepted_words", [])
            batch_info = {
                "batch_id": entry.get("batch_id", ""),
                "acceptance_rate": entry.get("acceptance_rate", 0),
                "accepted_count": len(accepted_words),
                "timestamp": entry.get("timestamp", 0)
            }
            acceptance_analysis["by_batch"].append(batch_info)
            
            for word in accepted_words:
                acceptance_analysis["by_length"][len(word)] += 1
                acceptance_analysis["by_starting_letter"][word[0]] += 1
        
        return acceptance_analysis
    
    def calculate_validation_efficiency(self, logs: List[Dict]) -> Dict:
        """Calculate efficiency metrics for the validation process."""
        
        if not logs:
            return {"error": "No validation data"}
        
        total_processed = sum(entry.get("original_count", 0) for entry in logs)
        total_accepted = sum(entry.get("accepted_count", 0) for entry in logs)
        total_time = sum(entry.get("processing_time", 0) for entry in logs)
        
        # Calculate rates over time
        batch_rates = []
        for entry in logs:
            if entry.get("original_count", 0) > 0:
                rate = entry.get("accepted_count", 0) / entry.get("original_count", 1)
                batch_rates.append(rate)
        
        return {
            "total_words_processed": total_processed,
            "total_words_accepted": total_accepted,
            "overall_acceptance_rate": total_accepted / total_processed if total_processed > 0 else 0,
            "average_batch_acceptance": sum(batch_rates) / len(batch_rates) if batch_rates else 0,
            "acceptance_rate_variance": self.calculate_variance(batch_rates),
            "total_processing_time": total_time,
            "words_per_second": total_processed / total_time if total_time > 0 else 0,
            "batch_count": len(logs),
            "average_batch_size": total_processed / len(logs) if logs else 0
        }
    
    def calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def compare_with_previous_wordlists(self, validated_words: Set[str]) -> Dict:
        """Compare the validated wordlist with previous algorithmic versions."""
        
        wordlist_dir = Path("wordlists")
        comparison = {}
        
        # Files to compare against
        comparison_files = [
            ("claude_optimized_65536.txt", "Claude Optimized"),
            ("enhanced_wordlist_65536.txt", "Enhanced"),
            ("refined_wordlist_65536.txt", "Refined"),
            ("ultra_clean_65536.txt", "Ultra Clean")
        ]
        
        for filename, name in comparison_files:
            filepath = wordlist_dir / filename
            if filepath.exists():
                try:
                    with open(filepath) as f:
                        other_words = {line.strip().lower() for line in f if line.strip()}
                    
                    overlap = validated_words & other_words
                    unique_to_validated = validated_words - other_words
                    unique_to_other = other_words - validated_words
                    
                    comparison[name] = {
                        "total_words": len(other_words),
                        "overlap_count": len(overlap),
                        "overlap_percentage": len(overlap) / len(validated_words) * 100,
                        "unique_to_validated": len(unique_to_validated),
                        "unique_to_other": len(unique_to_other),
                        "unique_examples": list(unique_to_validated)[:10]
                    }
                    
                except Exception as e:
                    comparison[name] = {"error": str(e)}
        
        return comparison
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate a comprehensive analysis report."""
        
        print("Generating comprehensive validation analysis...")
        
        # Load all validation data
        logs = self.load_all_validation_logs()
        
        if not logs:
            return {"error": "No validation logs found"}
        
        # Get current validated words
        validated_words = self.validator.get_validated_words()
        rejected_words = self.validator.get_rejected_words()
        
        # Perform analyses
        rejection_patterns = self.analyze_rejection_patterns(logs)
        acceptance_patterns = self.analyze_acceptance_patterns(logs)
        efficiency_metrics = self.calculate_validation_efficiency(logs)
        comparison_data = self.compare_with_previous_wordlists(validated_words)
        
        # Summary statistics
        summary = {
            "validation_summary": {
                "total_validated_words": len(validated_words),
                "total_rejected_words": len(rejected_words),
                "unique_words_processed": len(validated_words) + len(rejected_words),
                "overall_acceptance_rate": len(validated_words) / (len(validated_words) + len(rejected_words)) * 100,
                "validation_sessions": len(set(entry.get("batch_id", "") for entry in logs)),
                "analysis_timestamp": time.time()
            },
            "efficiency_metrics": efficiency_metrics,
            "rejection_analysis": rejection_patterns,
            "acceptance_analysis": acceptance_patterns,
            "wordlist_comparisons": comparison_data
        }
        
        return summary
    
    def save_analysis_report(self, report: Dict, filename: str = "validation_analysis_report.json") -> None:
        """Save the analysis report to file."""
        
        output_file = self.log_dir / filename
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Analysis report saved to {output_file}")
    
    def print_summary_statistics(self, report: Dict) -> None:
        """Print key statistics to console."""
        
        summary = report.get("validation_summary", {})
        efficiency = report.get("efficiency_metrics", {})
        rejections = report.get("rejection_analysis", {})
        
        print("\n" + "="*60)
        print("VALIDATION ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\nOverall Statistics:")
        print(f"  Words validated: {summary.get('total_validated_words', 0):,}")
        print(f"  Words rejected: {summary.get('total_rejected_words', 0):,}")
        print(f"  Acceptance rate: {summary.get('overall_acceptance_rate', 0):.1f}%")
        print(f"  Validation sessions: {summary.get('validation_sessions', 0)}")
        
        print(f"\nEfficiency Metrics:")
        print(f"  Total processed: {efficiency.get('total_words_processed', 0):,}")
        print(f"  Processing rate: {efficiency.get('words_per_second', 0):.1f} words/sec")
        print(f"  Average batch size: {efficiency.get('average_batch_size', 0):.0f}")
        print(f"  Batch acceptance variance: {efficiency.get('acceptance_rate_variance', 0):.3f}")
        
        print(f"\nTop Rejection Categories:")
        rejection_cats = rejections.get("by_category", {})
        for category, count in rejection_cats.most_common(5):
            percentage = count / sum(rejection_cats.values()) * 100
            print(f"  {category}: {count} ({percentage:.1f}%)")
        
        print("\nWordlist Comparison:")
        comparisons = report.get("wordlist_comparisons", {})
        for name, data in comparisons.items():
            if "error" not in data:
                overlap = data.get("overlap_percentage", 0)
                print(f"  vs {name}: {overlap:.1f}% overlap")
    
    def generate_rejection_examples_report(self) -> None:
        """Generate a detailed report of rejection examples by category."""
        
        logs = self.load_all_validation_logs()
        rejection_examples = defaultdict(list)
        
        for entry in logs:
            for word, reason in entry.get("rejection_reasons", {}).items():
                category = self.validator.categorize_rejection_reason(reason)
                rejection_examples[category].append((word, reason))
        
        # Save detailed examples
        examples_file = self.log_dir / "rejection_examples.json"
        with open(examples_file, 'w') as f:
            json.dump(dict(rejection_examples), f, indent=2)
        
        print(f"Detailed rejection examples saved to {examples_file}")


def main():
    """Run validation analysis on existing logs."""
    
    analyzer = ValidationAnalyzer()
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    if "error" in report:
        print(f"Error: {report['error']}")
        return
    
    # Print summary
    analyzer.print_summary_statistics(report)
    
    # Save detailed report
    analyzer.save_analysis_report(report)
    
    # Generate rejection examples
    analyzer.generate_rejection_examples_report()
    
    print("\n✓ Validation analysis complete!")


if __name__ == "__main__":
    main()