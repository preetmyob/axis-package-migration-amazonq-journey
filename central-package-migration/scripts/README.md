# Reusable Migration Scripts

This directory contains automation scripts developed during the Axis Central Package Management migration. These scripts can be adapted for future migrations or similar projects.

## Script Categories

### Analysis Scripts
- **build-log-analyzer.py** - Extract and categorize errors from build logs
- **package-inventory.py** - Generate inventory of current packages across projects
- **dependency-analyzer.py** - Analyze package dependencies and conflicts

### Automation Scripts
- **batch-project-updater.py** - Apply bulk changes to project files
- **package-version-extractor.py** - Extract versions from packages.config files
- **duplicate-finder.py** - Find and report duplicate package versions

### Validation Scripts
- **migration-validator.py** - Validate migration completeness
- **error-tracker.py** - Track error reduction progress
- **build-tester.py** - Automated build testing

## Usage Guidelines

1. **Review and Adapt:** These scripts were created for specific scenarios - review and modify for your use case
2. **Test First:** Always test scripts on a small subset before bulk operations
3. **Backup:** Ensure you have backups or version control before running modification scripts
4. **Incremental:** Use scripts incrementally rather than all at once

## Script Dependencies

Most scripts require:
- Python 3.7+
- Standard libraries (os, re, json, subprocess)
- Git (for some automation scripts)
