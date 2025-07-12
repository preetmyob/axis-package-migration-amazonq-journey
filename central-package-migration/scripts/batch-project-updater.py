#!/usr/bin/env python3
"""
Batch Project Updater for Central Package Management Migration

This script applies bulk modifications to .csproj files during CPM migration.
Developed during the Axis platform migration to automate repetitive project file changes.

Usage:
    python batch-project-updater.py --operation <operation> [options]

Operations:
    remove-package-versions    Remove Version attributes from PackageReference elements
    add-generate-assembly-info Add GenerateAssemblyInfo=false to projects with SharedAssemblyInfo
    remove-package            Remove specific PackageReference entries
    add-property              Add PropertyGroup properties to projects

Examples:
    python batch-project-updater.py --operation remove-package-versions --directory ./src
    python batch-project-updater.py --operation add-generate-assembly-info --pattern "**/*.csproj"
    python batch-project-updater.py --operation remove-package --package-name "Microsoft.Bcl.Build"
"""

import os
import re
import sys
import argparse
import glob
from pathlib import Path
import xml.etree.ElementTree as ET

class BatchProjectUpdater:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.changes_made = []
        
    def find_project_files(self, directory=None, pattern=None):
        """Find all .csproj files in directory or matching pattern"""
        if pattern:
            return glob.glob(pattern, recursive=True)
        elif directory:
            directory = Path(directory)
            return list(directory.rglob("*.csproj"))
        else:
            return list(Path(".").rglob("*.csproj"))
    
    def backup_file(self, file_path):
        """Create backup of file before modification"""
        backup_path = f"{file_path}.backup"
        if not os.path.exists(backup_path):
            with open(file_path, 'r', encoding='utf-8') as original:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())
            print(f"  Created backup: {backup_path}")
    
    def remove_package_versions(self, project_files):
        """Remove Version attributes from PackageReference elements"""
        print("Removing Version attributes from PackageReference elements...")
        
        for project_file in project_files:
            print(f"\nProcessing: {project_file}")
            
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Pattern to match PackageReference with Version attribute
                pattern = r'(<PackageReference\s+Include="[^"]+")(\s+Version="[^"]+")(\s*/?)'
                
                # Replace with PackageReference without Version
                modified_content = re.sub(pattern, r'\1\3', content)
                
                if modified_content != original_content:
                    if not self.dry_run:
                        self.backup_file(project_file)
                        with open(project_file, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                    
                    # Count changes
                    changes = len(re.findall(pattern, content))
                    print(f"  Removed {changes} Version attributes")
                    self.changes_made.append(f"{project_file}: Removed {changes} Version attributes")
                else:
                    print("  No changes needed")
                    
            except Exception as e:
                print(f"  Error processing {project_file}: {e}")
    
    def add_generate_assembly_info(self, project_files):
        """Add GenerateAssemblyInfo=false to projects that reference SharedAssemblyInfo"""
        print("Adding GenerateAssemblyInfo=false to projects with SharedAssemblyInfo...")
        
        for project_file in project_files:
            print(f"\nProcessing: {project_file}")
            
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if project references SharedAssemblyInfo
                if 'SharedAssemblyInfo' not in content:
                    print("  No SharedAssemblyInfo reference found, skipping")
                    continue
                
                # Check if GenerateAssemblyInfo already exists
                if 'GenerateAssemblyInfo' in content:
                    print("  GenerateAssemblyInfo already present")
                    continue
                
                # Find first PropertyGroup and add GenerateAssemblyInfo
                pattern = r'(<PropertyGroup>)'
                replacement = r'\1\n    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>'
                
                modified_content = re.sub(pattern, replacement, content, count=1)
                
                if modified_content != content:
                    if not self.dry_run:
                        self.backup_file(project_file)
                        with open(project_file, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                    
                    print("  Added GenerateAssemblyInfo=false")
                    self.changes_made.append(f"{project_file}: Added GenerateAssemblyInfo=false")
                else:
                    print("  No changes made")
                    
            except Exception as e:
                print(f"  Error processing {project_file}: {e}")
    
    def remove_package_reference(self, project_files, package_name):
        """Remove specific PackageReference entries"""
        print(f"Removing PackageReference for {package_name}...")
        
        for project_file in project_files:
            print(f"\nProcessing: {project_file}")
            
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Pattern to match PackageReference for specific package
                pattern = rf'<PackageReference\s+Include="{re.escape(package_name)}"[^>]*/?>\s*\n?'
                
                modified_content = re.sub(pattern, '', content, flags=re.MULTILINE)
                
                if modified_content != original_content:
                    if not self.dry_run:
                        self.backup_file(project_file)
                        with open(project_file, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                    
                    print(f"  Removed PackageReference for {package_name}")
                    self.changes_made.append(f"{project_file}: Removed {package_name}")
                else:
                    print("  Package not found")
                    
            except Exception as e:
                print(f"  Error processing {project_file}: {e}")
    
    def add_property(self, project_files, property_name, property_value):
        """Add a property to the first PropertyGroup in projects"""
        print(f"Adding {property_name}={property_value} to projects...")
        
        for project_file in project_files:
            print(f"\nProcessing: {project_file}")
            
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if property already exists
                if f'<{property_name}>' in content:
                    print(f"  {property_name} already present")
                    continue
                
                # Find first PropertyGroup and add property
                pattern = r'(<PropertyGroup>)'
                replacement = rf'\1\n    <{property_name}>{property_value}</{property_name}>'
                
                modified_content = re.sub(pattern, replacement, content, count=1)
                
                if modified_content != content:
                    if not self.dry_run:
                        self.backup_file(project_file)
                        with open(project_file, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                    
                    print(f"  Added {property_name}={property_value}")
                    self.changes_made.append(f"{project_file}: Added {property_name}={property_value}")
                else:
                    print("  No changes made")
                    
            except Exception as e:
                print(f"  Error processing {project_file}: {e}")
    
    def generate_summary(self):
        """Generate summary of all changes made"""
        print("\n" + "="*60)
        print("BATCH PROJECT UPDATE SUMMARY")
        print("="*60)
        print(f"Total files processed: {len(self.changes_made)}")
        
        if self.dry_run:
            print("DRY RUN MODE - No actual changes were made")
        
        print("\nChanges made:")
        for change in self.changes_made:
            print(f"  {change}")
        
        if not self.dry_run and self.changes_made:
            print(f"\nBackup files created with .backup extension")
            print("To restore original files: find . -name '*.backup' -exec sh -c 'mv \"$1\" \"${1%.backup}\"' _ {} \\;")

def main():
    parser = argparse.ArgumentParser(description='Batch update .csproj files for CPM migration')
    parser.add_argument('--operation', required=True, 
                       choices=['remove-package-versions', 'add-generate-assembly-info', 
                               'remove-package', 'add-property'],
                       help='Operation to perform')
    parser.add_argument('--directory', help='Directory to search for .csproj files')
    parser.add_argument('--pattern', help='Glob pattern for .csproj files')
    parser.add_argument('--package-name', help='Package name for remove-package operation')
    parser.add_argument('--property-name', help='Property name for add-property operation')
    parser.add_argument('--property-value', help='Property value for add-property operation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    
    args = parser.parse_args()
    
    # Validate operation-specific arguments
    if args.operation == 'remove-package' and not args.package_name:
        print("Error: --package-name is required for remove-package operation")
        sys.exit(1)
    
    if args.operation == 'add-property' and (not args.property_name or not args.property_value):
        print("Error: --property-name and --property-value are required for add-property operation")
        sys.exit(1)
    
    updater = BatchProjectUpdater(dry_run=args.dry_run)
    
    # Find project files
    project_files = updater.find_project_files(args.directory, args.pattern)
    
    if not project_files:
        print("No .csproj files found")
        sys.exit(1)
    
    print(f"Found {len(project_files)} .csproj files")
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    
    # Perform requested operation
    if args.operation == 'remove-package-versions':
        updater.remove_package_versions(project_files)
    elif args.operation == 'add-generate-assembly-info':
        updater.add_generate_assembly_info(project_files)
    elif args.operation == 'remove-package':
        updater.remove_package_reference(project_files, args.package_name)
    elif args.operation == 'add-property':
        updater.add_property(project_files, args.property_name, args.property_value)
    
    # Generate summary
    updater.generate_summary()

if __name__ == "__main__":
    main()
