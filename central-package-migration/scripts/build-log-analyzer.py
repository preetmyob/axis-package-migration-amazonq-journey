#!/usr/bin/env python3
"""
Build Log Analyzer for Central Package Management Migration

This script analyzes TeamCity build logs to extract and categorize NuGet and MSBuild errors.
Developed during the Axis platform migration from packages.config to Central Package Management.

Usage:
    python build-log-analyzer.py <path-to-build-log>
    python build-log-analyzer.py --directory <path-to-logs-directory>

Features:
- Extracts specific error codes (NU1103, NU1605, NU1202, NU1010, NU1008, NU1506, MSB4062)
- Categorizes errors by type and severity
- Generates summary reports
- Identifies most common issues for prioritization
"""

import re
import sys
import os
import json
from collections import defaultdict, Counter
from pathlib import Path

class BuildLogAnalyzer:
    def __init__(self):
        self.error_patterns = {
            'NU1103': r'NU1103.*Unable to find package.*?\'([^\']+)\'.*?version.*?\'([^\']+)\'',
            'NU1605': r'NU1605.*Detected package downgrade.*?\'([^\']+)\'.*?from.*?\'([^\']+)\'.*?to.*?\'([^\']+)\'',
            'NU1202': r'NU1202.*Package.*?\'([^\']+)\'.*?version.*?\'([^\']+)\'.*?is not compatible.*?\'([^\']+)\'',
            'NU1010': r'NU1010.*Package reference.*?\'([^\']+)\'.*?does not contain a version',
            'NU1008': r'NU1008.*Package.*?\'([^\']+)\'.*?version.*?\'([^\']+)\'.*?has a known.*?vulnerability',
            'NU1506': r'NU1506.*There are.*?duplicate.*?\'([^\']+)\'.*?package version',
            'MSB4062': r'MSB4062.*The.*?\'([^\']+)\'.*?task.*?could not be loaded.*?duplicate.*?attribute'
        }
        
        self.error_descriptions = {
            'NU1103': 'Unable to find package',
            'NU1605': 'Detected package downgrade',
            'NU1202': 'Package not compatible with framework',
            'NU1010': 'Package reference without version',
            'NU1008': 'Package has known vulnerability',
            'NU1506': 'Duplicate package version',
            'MSB4062': 'Duplicate assembly attributes'
        }
        
        self.error_priorities = {
            'NU1103': 1,  # Blocking
            'NU1605': 1,  # Blocking
            'NU1202': 1,  # Blocking
            'NU1010': 1,  # Blocking
            'MSB4062': 2, # Build issue
            'NU1506': 3,  # Warning
            'NU1008': 3   # Warning
        }

    def analyze_log(self, log_path):
        """Analyze a single build log file"""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {log_path}: {e}")
            return None
            
        results = {
            'file': log_path,
            'errors': defaultdict(list),
            'summary': defaultdict(int),
            'packages_affected': set(),
            'total_errors': 0
        }
        
        for error_code, pattern in self.error_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                error_info = {
                    'code': error_code,
                    'description': self.error_descriptions[error_code],
                    'priority': self.error_priorities[error_code],
                    'details': match
                }
                
                results['errors'][error_code].append(error_info)
                results['summary'][error_code] += 1
                results['total_errors'] += 1
                
                # Extract package name (usually first capture group)
                if match and isinstance(match, tuple) and len(match) > 0:
                    results['packages_affected'].add(match[0])
        
        results['packages_affected'] = list(results['packages_affected'])
        return results

    def analyze_directory(self, directory_path):
        """Analyze all log files in a directory"""
        directory = Path(directory_path)
        log_files = list(directory.glob('*.log')) + list(directory.glob('*.txt'))
        
        if not log_files:
            print(f"No log files found in {directory_path}")
            return []
        
        results = []
        for log_file in log_files:
            print(f"Analyzing {log_file.name}...")
            result = self.analyze_log(log_file)
            if result:
                results.append(result)
        
        return results

    def generate_summary_report(self, results):
        """Generate a summary report from analysis results"""
        if isinstance(results, dict):
            results = [results]
        
        # Aggregate results
        total_errors = sum(r['total_errors'] for r in results)
        error_counts = Counter()
        package_issues = Counter()
        
        for result in results:
            for error_code, count in result['summary'].items():
                error_counts[error_code] += count
            for package in result['packages_affected']:
                package_issues[package] += 1
        
        # Generate report
        report = []
        report.append("=" * 60)
        report.append("CENTRAL PACKAGE MANAGEMENT MIGRATION - BUILD LOG ANALYSIS")
        report.append("=" * 60)
        report.append(f"Total files analyzed: {len(results)}")
        report.append(f"Total errors found: {total_errors}")
        report.append("")
        
        # Error summary by priority
        report.append("ERROR SUMMARY BY PRIORITY:")
        report.append("-" * 30)
        
        priority_groups = defaultdict(list)
        for error_code, count in error_counts.items():
            priority = self.error_priorities[error_code]
            priority_groups[priority].append((error_code, count))
        
        priority_names = {1: "BLOCKING ERRORS", 2: "BUILD ISSUES", 3: "WARNINGS"}
        
        for priority in sorted(priority_groups.keys()):
            report.append(f"\n{priority_names[priority]}:")
            for error_code, count in sorted(priority_groups[priority], key=lambda x: x[1], reverse=True):
                description = self.error_descriptions[error_code]
                report.append(f"  {error_code}: {count:3d} - {description}")
        
        # Most problematic packages
        if package_issues:
            report.append("\nMOST PROBLEMATIC PACKAGES:")
            report.append("-" * 30)
            for package, count in package_issues.most_common(10):
                report.append(f"  {package}: {count} issues")
        
        # Recommendations
        report.append("\nRECOMMENDATIONS:")
        report.append("-" * 15)
        
        if error_counts.get('NU1103', 0) > 0:
            report.append("• NU1103 errors: Consider direct assembly references for problematic packages")
        if error_counts.get('NU1605', 0) > 0:
            report.append("• NU1605 errors: Update package versions to resolve conflicts")
        if error_counts.get('NU1202', 0) > 0:
            report.append("• NU1202 errors: Use framework-compatible package versions")
        if error_counts.get('NU1010', 0) > 0:
            report.append("• NU1010 errors: Add missing PackageVersion entries to Directory.Packages.props")
        if error_counts.get('MSB4062', 0) > 0:
            report.append("• MSB4062 errors: Add <GenerateAssemblyInfo>false</GenerateAssemblyInfo> to projects")
        if error_counts.get('NU1506', 0) > 0:
            report.append("• NU1506 warnings: Remove duplicate PackageVersion entries")
        
        return "\n".join(report)

    def export_detailed_results(self, results, output_path):
        """Export detailed results to JSON for further analysis"""
        # Convert sets to lists for JSON serialization
        serializable_results = []
        for result in results if isinstance(results, list) else [results]:
            serializable_result = dict(result)
            serializable_result['packages_affected'] = list(result['packages_affected'])
            serializable_results.append(serializable_result)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        print(f"Detailed results exported to {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python build-log-analyzer.py <path-to-build-log>")
        print("  python build-log-analyzer.py --directory <path-to-logs-directory>")
        sys.exit(1)
    
    analyzer = BuildLogAnalyzer()
    
    if sys.argv[1] == '--directory':
        if len(sys.argv) < 3:
            print("Please specify directory path")
            sys.exit(1)
        results = analyzer.analyze_directory(sys.argv[2])
    else:
        results = analyzer.analyze_log(sys.argv[1])
    
    if not results:
        print("No results to display")
        sys.exit(1)
    
    # Generate and display summary report
    summary = analyzer.generate_summary_report(results)
    print(summary)
    
    # Export detailed results
    output_file = "build-analysis-results.json"
    analyzer.export_detailed_results(results, output_file)
    
    # Save summary report
    summary_file = "build-analysis-summary.txt"
    with open(summary_file, 'w') as f:
        f.write(summary)
    print(f"\nSummary report saved to {summary_file}")

if __name__ == "__main__":
    main()
