#!/usr/bin/env python3
"""
Migration Validator for Central Package Management

This script validates the completeness and correctness of CPM migration.
Developed during the Axis platform migration to ensure migration quality.

Usage:
    python migration-validator.py [options]

Validation Checks:
- Directory.Packages.props exists and is valid
- All PackageReference elements lack Version attributes
- All packages have corresponding PackageVersion entries
- No duplicate PackageVersion entries
- Build validation (optional)
"""

import os
import re
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter
import subprocess

class MigrationValidator:
    def __init__(self):
        self.validation_results = {
            'directory_packages_props': {'status': 'UNKNOWN', 'details': []},
            'project_files': {'status': 'UNKNOWN', 'details': []},
            'package_consistency': {'status': 'UNKNOWN', 'details': []},
            'build_validation': {'status': 'UNKNOWN', 'details': []},
            'overall': {'status': 'UNKNOWN', 'score': 0}
        }
        
        self.packages_in_props = set()
        self.packages_in_projects = set()
        self.project_files = []
        
    def validate_directory_packages_props(self, solution_dir="."):
        """Validate Directory.Packages.props file"""
        props_file = Path(solution_dir) / "Directory.Packages.props"
        
        if not props_file.exists():
            self.validation_results['directory_packages_props'] = {
                'status': 'FAIL',
                'details': ['Directory.Packages.props file not found']
            }
            return False
        
        try:
            tree = ET.parse(props_file)
            root = tree.getroot()
            
            details = []
            
            # Check for ManagePackageVersionsCentrally property
            manage_centrally = False
            for prop_group in root.findall('.//PropertyGroup'):
                for prop in prop_group:
                    if prop.tag == 'ManagePackageVersionsCentrally' and prop.text == 'true':
                        manage_centrally = True
                        break
            
            if not manage_centrally:
                details.append('ManagePackageVersionsCentrally property not set to true')
            
            # Extract PackageVersion entries
            package_versions = {}
            duplicates = []
            
            for item_group in root.findall('.//ItemGroup'):
                for package_version in item_group.findall('PackageVersion'):
                    include = package_version.get('Include')
                    version = package_version.get('Version')
                    
                    if include and version:
                        if include in package_versions:
                            duplicates.append(include)
                        else:
                            package_versions[include] = version
                            self.packages_in_props.add(include)
            
            if duplicates:
                details.append(f'Duplicate PackageVersion entries: {", ".join(duplicates)}')
            
            details.append(f'Found {len(package_versions)} PackageVersion entries')
            
            if duplicates or not manage_centrally:
                status = 'WARN' if not duplicates else 'FAIL'
            else:
                status = 'PASS'
            
            self.validation_results['directory_packages_props'] = {
                'status': status,
                'details': details
            }
            
            return status != 'FAIL'
            
        except Exception as e:
            self.validation_results['directory_packages_props'] = {
                'status': 'FAIL',
                'details': [f'Error parsing Directory.Packages.props: {e}']
            }
            return False
    
    def validate_project_files(self, solution_dir="."):
        """Validate .csproj files for CPM compliance"""
        solution_path = Path(solution_dir)
        self.project_files = list(solution_path.rglob("*.csproj"))
        
        details = []
        issues = []
        
        for project_file in self.project_files:
            try:
                tree = ET.parse(project_file)
                root = tree.getroot()
                
                # Check for PackageReference elements with Version attributes
                package_refs_with_version = []
                package_refs_without_version = []
                
                for package_ref in root.findall('.//PackageReference'):
                    include = package_ref.get('Include')
                    version = package_ref.get('Version')
                    
                    if include:
                        if version:
                            package_refs_with_version.append((include, version))
                        else:
                            package_refs_without_version.append(include)
                            self.packages_in_projects.add(include)
                
                if package_refs_with_version:
                    issues.append(f'{project_file.name}: {len(package_refs_with_version)} PackageReference elements still have Version attributes')
                
                # Check for packages.config (should be removed)
                packages_config = project_file.parent / "packages.config"
                if packages_config.exists():
                    issues.append(f'{project_file.name}: packages.config still exists')
                
            except Exception as e:
                issues.append(f'{project_file.name}: Error parsing - {e}')
        
        details.append(f'Validated {len(self.project_files)} project files')
        
        if issues:
            details.extend(issues)
            status = 'FAIL'
        else:
            details.append('All project files are CPM compliant')
            status = 'PASS'
        
        self.validation_results['project_files'] = {
            'status': status,
            'details': details
        }
        
        return status == 'PASS'
    
    def validate_package_consistency(self):
        """Validate consistency between Directory.Packages.props and project files"""
        details = []
        issues = []
        
        # Find packages in projects but not in Directory.Packages.props
        missing_in_props = self.packages_in_projects - self.packages_in_props
        if missing_in_props:
            issues.append(f'Packages in projects but missing from Directory.Packages.props: {", ".join(sorted(missing_in_props))}')
        
        # Find packages in Directory.Packages.props but not used in projects
        unused_in_props = self.packages_in_props - self.packages_in_projects
        if unused_in_props:
            details.append(f'Packages defined in Directory.Packages.props but not used: {", ".join(sorted(unused_in_props))}')
        
        details.append(f'Packages in Directory.Packages.props: {len(self.packages_in_props)}')
        details.append(f'Packages referenced in projects: {len(self.packages_in_projects)}')
        
        if missing_in_props:
            status = 'FAIL'
            details.extend(issues)
        elif unused_in_props:
            status = 'WARN'
        else:
            status = 'PASS'
            details.append('Package consistency validated successfully')
        
        self.validation_results['package_consistency'] = {
            'status': status,
            'details': details
        }
        
        return status != 'FAIL'
    
    def validate_build(self, solution_dir=".", skip_build=False):
        """Validate that solution builds successfully"""
        if skip_build:
            self.validation_results['build_validation'] = {
                'status': 'SKIP',
                'details': ['Build validation skipped']
            }
            return True
        
        try:
            # Try dotnet restore
            restore_result = subprocess.run(
                ['dotnet', 'restore'],
                cwd=solution_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            details = []
            
            if restore_result.returncode != 0:
                details.append('dotnet restore failed')
                details.append(f'Error: {restore_result.stderr}')
                status = 'FAIL'
            else:
                details.append('dotnet restore succeeded')
                
                # Try dotnet build
                build_result = subprocess.run(
                    ['dotnet', 'build', '--no-restore'],
                    cwd=solution_dir,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if build_result.returncode != 0:
                    details.append('dotnet build failed')
                    details.append(f'Error: {build_result.stderr}')
                    status = 'FAIL'
                else:
                    details.append('dotnet build succeeded')
                    status = 'PASS'
            
            self.validation_results['build_validation'] = {
                'status': status,
                'details': details
            }
            
            return status == 'PASS'
            
        except subprocess.TimeoutExpired:
            self.validation_results['build_validation'] = {
                'status': 'FAIL',
                'details': ['Build validation timed out']
            }
            return False
        except Exception as e:
            self.validation_results['build_validation'] = {
                'status': 'FAIL',
                'details': [f'Build validation error: {e}']
            }
            return False
    
    def calculate_overall_score(self):
        """Calculate overall migration score"""
        weights = {
            'directory_packages_props': 25,
            'project_files': 30,
            'package_consistency': 25,
            'build_validation': 20
        }
        
        status_scores = {'PASS': 100, 'WARN': 75, 'FAIL': 0, 'SKIP': 0, 'UNKNOWN': 0}
        
        total_score = 0
        total_weight = 0
        
        for category, weight in weights.items():
            if category in self.validation_results:
                status = self.validation_results[category]['status']
                score = status_scores.get(status, 0)
                total_score += score * weight
                total_weight += weight
        
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        if overall_score >= 90:
            overall_status = 'EXCELLENT'
        elif overall_score >= 75:
            overall_status = 'GOOD'
        elif overall_score >= 50:
            overall_status = 'NEEDS_WORK'
        else:
            overall_status = 'POOR'
        
        self.validation_results['overall'] = {
            'status': overall_status,
            'score': round(overall_score, 1)
        }
    
    def generate_report(self):
        """Generate validation report"""
        self.calculate_overall_score()
        
        report = []
        report.append("=" * 60)
        report.append("CENTRAL PACKAGE MANAGEMENT MIGRATION VALIDATION REPORT")
        report.append("=" * 60)
        
        overall = self.validation_results['overall']
        report.append(f"Overall Status: {overall['status']} ({overall['score']}%)")
        report.append("")
        
        # Status indicators
        status_indicators = {
            'PASS': '✓ PASS',
            'WARN': '⚠ WARN',
            'FAIL': '✗ FAIL',
            'SKIP': '- SKIP',
            'UNKNOWN': '? UNKNOWN'
        }
        
        categories = [
            ('Directory.Packages.props Validation', 'directory_packages_props'),
            ('Project Files Validation', 'project_files'),
            ('Package Consistency Validation', 'package_consistency'),
            ('Build Validation', 'build_validation')
        ]
        
        for category_name, category_key in categories:
            if category_key in self.validation_results:
                result = self.validation_results[category_key]
                status_text = status_indicators.get(result['status'], result['status'])
                report.append(f"{category_name}: {status_text}")
                
                for detail in result['details']:
                    report.append(f"  {detail}")
                report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 15)
        
        recommendations = []
        
        if self.validation_results['directory_packages_props']['status'] == 'FAIL':
            recommendations.append("• Fix Directory.Packages.props issues before proceeding")
        
        if self.validation_results['project_files']['status'] == 'FAIL':
            recommendations.append("• Remove Version attributes from PackageReference elements")
            recommendations.append("• Delete remaining packages.config files")
        
        if self.validation_results['package_consistency']['status'] == 'FAIL':
            recommendations.append("• Add missing PackageVersion entries to Directory.Packages.props")
        
        if self.validation_results['build_validation']['status'] == 'FAIL':
            recommendations.append("• Resolve build errors before completing migration")
        
        if overall['score'] >= 90:
            recommendations.append("• Migration is complete and successful!")
            recommendations.append("• Consider cleanup of unused PackageVersion entries")
        elif overall['score'] >= 75:
            recommendations.append("• Migration is mostly complete - address remaining warnings")
        else:
            recommendations.append("• Migration requires additional work - focus on failed validations")
        
        for rec in recommendations:
            report.append(rec)
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Validate CPM migration completeness')
    parser.add_argument('--directory', default='.', help='Solution directory to validate')
    parser.add_argument('--skip-build', action='store_true', help='Skip build validation')
    parser.add_argument('--output', help='Output file for validation report')
    
    args = parser.parse_args()
    
    validator = MigrationValidator()
    
    print("Validating Central Package Management migration...")
    print(f"Solution directory: {os.path.abspath(args.directory)}")
    print()
    
    # Run validations
    print("1. Validating Directory.Packages.props...")
    validator.validate_directory_packages_props(args.directory)
    
    print("2. Validating project files...")
    validator.validate_project_files(args.directory)
    
    print("3. Validating package consistency...")
    validator.validate_package_consistency()
    
    print("4. Validating build...")
    validator.validate_build(args.directory, args.skip_build)
    
    # Generate report
    report = validator.generate_report()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nValidation report written to {args.output}")
    
    print("\n" + report)
    
    # Exit with appropriate code
    overall_status = validator.validation_results['overall']['status']
    if overall_status in ['EXCELLENT', 'GOOD']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
