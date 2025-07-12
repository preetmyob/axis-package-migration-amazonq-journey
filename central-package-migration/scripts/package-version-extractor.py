#!/usr/bin/env python3
"""
Package Version Extractor for Central Package Management Migration

This script extracts package versions from packages.config and .csproj files
to generate Directory.Packages.props entries for CPM migration.

Usage:
    python package-version-extractor.py [options]

Features:
- Extracts from packages.config files
- Extracts from PackageReference elements in .csproj files
- Consolidates versions and identifies conflicts
- Generates Directory.Packages.props content
- Groups packages by category for better organization
"""

import os
import re
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter
import json

class PackageVersionExtractor:
    def __init__(self):
        self.packages = defaultdict(set)  # package_name -> set of versions
        self.package_sources = defaultdict(list)  # package_name -> list of source files
        
        # Package categorization for better organization
        self.package_categories = {
            'AWS SDK': ['AWSSDK.', 'Amazon.'],
            'Microsoft Extensions': ['Microsoft.Extensions.'],
            'Microsoft Core': ['Microsoft.NETFramework', 'Microsoft.Bcl', 'System.'],
            'Testing': ['FluentAssertions', 'Castle.Core', 'Moq', 'NUnit', 'xunit'],
            'Logging': ['Common.Logging', 'log4net', 'NLog', 'Serilog'],
            'JSON': ['Newtonsoft.Json', 'System.Text.Json'],
            'Utilities': ['ZstdSharp', 'Fare', 'AutoMapper']
        }
    
    def extract_from_packages_config(self, config_file):
        """Extract package versions from packages.config file"""
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            for package in root.findall('package'):
                package_id = package.get('id')
                version = package.get('version')
                
                if package_id and version:
                    self.packages[package_id].add(version)
                    self.package_sources[package_id].append(str(config_file))
                    
        except Exception as e:
            print(f"Error parsing {config_file}: {e}")
    
    def extract_from_csproj(self, csproj_file):
        """Extract package versions from .csproj PackageReference elements"""
        try:
            tree = ET.parse(csproj_file)
            root = tree.getroot()
            
            # Handle both old and new project file formats
            for package_ref in root.findall('.//PackageReference'):
                package_id = package_ref.get('Include')
                version = package_ref.get('Version')
                
                if package_id and version:
                    self.packages[package_id].add(version)
                    self.package_sources[package_id].append(str(csproj_file))
                    
        except Exception as e:
            print(f"Error parsing {csproj_file}: {e}")
    
    def find_and_extract(self, directory="."):
        """Find and extract from all packages.config and .csproj files"""
        directory = Path(directory)
        
        # Find packages.config files
        config_files = list(directory.rglob("packages.config"))
        print(f"Found {len(config_files)} packages.config files")
        
        for config_file in config_files:
            print(f"  Processing: {config_file}")
            self.extract_from_packages_config(config_file)
        
        # Find .csproj files
        csproj_files = list(directory.rglob("*.csproj"))
        print(f"Found {len(csproj_files)} .csproj files")
        
        for csproj_file in csproj_files:
            print(f"  Processing: {csproj_file}")
            self.extract_from_csproj(csproj_file)
    
    def categorize_package(self, package_name):
        """Categorize package based on name patterns"""
        for category, patterns in self.package_categories.items():
            for pattern in patterns:
                if package_name.startswith(pattern):
                    return category
        return 'Other'
    
    def resolve_version_conflicts(self):
        """Identify and suggest resolutions for version conflicts"""
        conflicts = {}
        resolutions = {}
        
        for package_name, versions in self.packages.items():
            if len(versions) > 1:
                conflicts[package_name] = list(versions)
                # Suggest highest version as resolution
                version_list = list(versions)
                version_list.sort(key=lambda v: [int(x) if x.isdigit() else x for x in re.split(r'[.-]', v)])
                resolutions[package_name] = version_list[-1]
            else:
                resolutions[package_name] = list(versions)[0]
        
        return conflicts, resolutions
    
    def generate_directory_packages_props(self, output_file=None):
        """Generate Directory.Packages.props content"""
        conflicts, resolutions = self.resolve_version_conflicts()
        
        # Group packages by category
        categorized_packages = defaultdict(list)
        for package_name, version in resolutions.items():
            category = self.categorize_package(package_name)
            categorized_packages[category].append((package_name, version))
        
        # Sort packages within each category
        for category in categorized_packages:
            categorized_packages[category].sort(key=lambda x: x[0])
        
        # Generate XML content
        lines = []
        lines.append('<Project>')
        lines.append('  <PropertyGroup>')
        lines.append('    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>')
        lines.append('  </PropertyGroup>')
        lines.append('')
        
        # Add packages by category
        for category in sorted(categorized_packages.keys()):
            if category != 'Other':  # Process 'Other' last
                lines.append(f'  <ItemGroup Label="{category}">')
                for package_name, version in categorized_packages[category]:
                    lines.append(f'    <PackageVersion Include="{package_name}" Version="{version}" />')
                lines.append('  </ItemGroup>')
                lines.append('')
        
        # Add 'Other' category if it exists
        if 'Other' in categorized_packages:
            lines.append('  <ItemGroup Label="Other">')
            for package_name, version in categorized_packages['Other']:
                lines.append(f'    <PackageVersion Include="{package_name}" Version="{version}" />')
            lines.append('  </ItemGroup>')
            lines.append('')
        
        lines.append('</Project>')
        
        content = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Directory.Packages.props written to {output_file}")
        
        return content, conflicts
    
    def generate_report(self):
        """Generate extraction and conflict report"""
        conflicts, resolutions = self.resolve_version_conflicts()
        
        report = []
        report.append("=" * 60)
        report.append("PACKAGE VERSION EXTRACTION REPORT")
        report.append("=" * 60)
        report.append(f"Total unique packages found: {len(self.packages)}")
        report.append(f"Packages with version conflicts: {len(conflicts)}")
        report.append("")
        
        if conflicts:
            report.append("VERSION CONFLICTS DETECTED:")
            report.append("-" * 30)
            for package_name, versions in conflicts.items():
                report.append(f"{package_name}:")
                for version in sorted(versions):
                    sources = [src for src in self.package_sources[package_name]]
                    report.append(f"  {version} (used in {len(sources)} files)")
                report.append(f"  RECOMMENDED: {resolutions[package_name]}")
                report.append("")
        
        # Package count by category
        categorized_packages = defaultdict(list)
        for package_name in self.packages.keys():
            category = self.categorize_package(package_name)
            categorized_packages[category].append(package_name)
        
        report.append("PACKAGES BY CATEGORY:")
        report.append("-" * 20)
        for category in sorted(categorized_packages.keys()):
            count = len(categorized_packages[category])
            report.append(f"{category}: {count} packages")
        
        return "\n".join(report)
    
    def export_detailed_data(self, output_file):
        """Export detailed extraction data to JSON"""
        data = {
            'packages': {name: list(versions) for name, versions in self.packages.items()},
            'sources': dict(self.package_sources),
            'categories': {name: self.categorize_package(name) for name in self.packages.keys()}
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Detailed data exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Extract package versions for CPM migration')
    parser.add_argument('--directory', default='.', help='Directory to search for package files')
    parser.add_argument('--output', default='Directory.Packages.props', 
                       help='Output file for Directory.Packages.props')
    parser.add_argument('--report', default='package-extraction-report.txt',
                       help='Output file for extraction report')
    parser.add_argument('--export-data', help='Export detailed data to JSON file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Generate content without writing files')
    
    args = parser.parse_args()
    
    extractor = PackageVersionExtractor()
    
    print("Extracting package versions...")
    extractor.find_and_extract(args.directory)
    
    if not extractor.packages:
        print("No packages found!")
        sys.exit(1)
    
    # Generate Directory.Packages.props
    if not args.dry_run:
        content, conflicts = extractor.generate_directory_packages_props(args.output)
    else:
        content, conflicts = extractor.generate_directory_packages_props()
        print("DRY RUN - Directory.Packages.props content:")
        print(content)
    
    # Generate report
    report = extractor.generate_report()
    
    if not args.dry_run:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Extraction report written to {args.report}")
    else:
        print("\nExtraction Report:")
        print(report)
    
    # Export detailed data if requested
    if args.export_data and not args.dry_run:
        extractor.export_detailed_data(args.export_data)
    
    # Summary
    print(f"\nSummary:")
    print(f"  Packages found: {len(extractor.packages)}")
    print(f"  Version conflicts: {len(conflicts) if conflicts else 0}")
    
    if conflicts:
        print(f"  Conflicts detected - review {args.report} for details")

if __name__ == "__main__":
    main()
