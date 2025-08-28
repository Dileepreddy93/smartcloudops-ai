#!/usr/bin/env python3
"""
SmartCloudOps AI - Immediate Workflow Fixer
==========================================

This script immediately fixes common workflow issues without requiring
external dependencies. It directly addresses the issues found in the demo.
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def fix_workflow_file(file_path):
    """Fix a single workflow file."""
    print(f"🔧 Fixing {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix 1: Update deprecated actions
        deprecated_actions = {
            "actions/checkout@v1": "actions/checkout@v4",
            "actions/checkout@v2": "actions/checkout@v4",
            "actions/checkout@v3": "actions/checkout@v4",
            "actions/setup-python@v1": "actions/setup-python@v5",
            "actions/setup-python@v2": "actions/setup-python@v5",
            "actions/setup-python@v3": "actions/setup-python@v5",
            "actions/setup-python@v4": "actions/setup-python@v5",
            "actions/setup-node@v1": "actions/setup-node@v4",
            "actions/setup-node@v2": "actions/setup-node@v4",
            "actions/setup-node@v3": "actions/setup-node@v4",
            "actions/upload-artifact@v1": "actions/upload-artifact@v4",
            "actions/upload-artifact@v2": "actions/upload-artifact@v4",
            "actions/upload-artifact@v3": "actions/upload-artifact@v4",
            "actions/download-artifact@v1": "actions/download-artifact@v4",
            "actions/download-artifact@v2": "actions/download-artifact@v4",
            "actions/download-artifact@v3": "actions/download-artifact@v4"
        }
        
        for old_action, new_action in deprecated_actions.items():
            if old_action in content:
                content = content.replace(old_action, new_action)
                fixes_applied.append(f"Updated {old_action} to {new_action}")
        
        # Fix 2: Add missing permissions if not present
        if "permissions:" not in content:
            # Find the right place to insert permissions (after 'on:' section)
            lines = content.split('\n')
            new_lines = []
            permissions_added = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.strip().startswith('on:') and not permissions_added:
                    # Add permissions after the 'on:' section
                    indent = len(line) - len(line.lstrip())
                    permissions_indent = ' ' * (indent + 2)
                    new_lines.append(f'{permissions_indent}permissions:')
                    new_lines.append(f'{permissions_indent}  contents: read')
                    new_lines.append(f'{permissions_indent}  pull-requests: write')
                    new_lines.append(f'{permissions_indent}  issues: write')
                    new_lines.append('')
                    permissions_added = True
            
            if permissions_added:
                content = '\n'.join(new_lines)
                fixes_applied.append("Added permissions configuration")
        
        # Fix 3: Add pip cache for Python setup
        if "actions/setup-python" in content and "actions/cache" not in content:
            # Find setup-python steps and add cache after them
            lines = content.split('\n')
            new_lines = []
            cache_added = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if "uses: actions/setup-python" in line and not cache_added:
                    # Add cache step after setup-python
                    indent = len(line) - len(line.lstrip())
                    cache_indent = ' ' * indent
                    new_lines.append(f'{cache_indent}- name: Cache pip dependencies')
                    new_lines.append(f'{cache_indent}  uses: actions/cache@v4')
                    new_lines.append(f'{cache_indent}  with:')
                    new_lines.append(f'{cache_indent}    path: ~/.cache/pip')
                    new_lines.append(f'{cache_indent}    key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles("**/requirements.txt") }}}}')
                    new_lines.append(f'{cache_indent}    restore-keys: |')
                    new_lines.append(f'{cache_indent}      ${{{{ runner.os }}}}-pip-')
                    cache_added = True
            
            if cache_added:
                content = '\n'.join(new_lines)
                fixes_applied.append("Added pip cache configuration")
        
        # Fix 4: Add npm cache for Node.js setup
        if "actions/setup-node" in content and "actions/cache" not in content:
            # Find setup-node steps and add cache after them
            lines = content.split('\n')
            new_lines = []
            cache_added = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if "uses: actions/setup-node" in line and not cache_added:
                    # Add cache step after setup-node
                    indent = len(line) - len(line.lstrip())
                    cache_indent = ' ' * indent
                    new_lines.append(f'{cache_indent}- name: Cache npm dependencies')
                    new_lines.append(f'{cache_indent}  uses: actions/cache@v4')
                    new_lines.append(f'{cache_indent}  with:')
                    new_lines.append(f'{cache_indent}    path: ~/.npm')
                    new_lines.append(f'{cache_indent}    key: ${{{{ runner.os }}}}-node-${{{{ hashFiles("**/package-lock.json") }}}}')
                    new_lines.append(f'{cache_indent}    restore-keys: |')
                    new_lines.append(f'{cache_indent}      ${{{{ runner.os }}}}-node-')
                    cache_added = True
            
            if cache_added:
                content = '\n'.join(new_lines)
                fixes_applied.append("Added npm cache configuration")
        
        # Write the fixed content back to file
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            
            print_success(f"Fixed {len(fixes_applied)} issues in {file_path}")
            for fix in fixes_applied:
                print(f"  • {fix}")
            return fixes_applied
        else:
            print_info(f"No fixes needed for {file_path}")
            return []
            
    except Exception as e:
        print_error(f"Failed to fix {file_path}: {e}")
        return []

def validate_workflow_file(file_path):
    """Validate a workflow file for basic YAML structure."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic YAML validation - check for common issues
        issues = []
        
        # Check for basic structure
        if "on:" not in content:
            issues.append("Missing 'on:' triggers section")
        
        if "jobs:" not in content:
            issues.append("Missing 'jobs:' section")
        
        # Check for balanced braces in GitHub expressions
        if content.count("{{") != content.count("}}"):
            issues.append("Unbalanced GitHub expressions {{ }}")
        
        # Check for basic indentation
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith(' ') and not line.startswith('#'):
                # This should be a top-level key
                if not any(key in line for key in ['name:', 'on:', 'env:', 'jobs:', 'permissions:']):
                    issues.append(f"Line {i}: Unexpected top-level key: {line.strip()}")
        
        if issues:
            print_warning(f"Validation issues in {file_path}:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        else:
            print_success(f"✅ {file_path} is valid")
            return True
            
    except Exception as e:
        print_error(f"Failed to validate {file_path}: {e}")
        return False

def main():
    """Main function to fix all workflow files."""
    print("🚀 SmartCloudOps AI - Immediate Workflow Fixer")
    print("=" * 50)
    
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print_error("No .github/workflows directory found")
        return 1
    
    workflow_files = list(workflow_dir.glob("*.yml"))
    if not workflow_files:
        print_error("No workflow files found")
        return 1
    
    print_info(f"Found {len(workflow_files)} workflow files to fix")
    
    all_fixes = []
    valid_files = 0
    
    # Fix each workflow file
    for workflow_file in workflow_files:
        fixes = fix_workflow_file(workflow_file)
        all_fixes.extend(fixes)
        
        # Validate the file after fixing
        if validate_workflow_file(workflow_file):
            valid_files += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FIX SUMMARY")
    print("=" * 50)
    print(f"Files processed: {len(workflow_files)}")
    print(f"Files valid: {valid_files}")
    print(f"Total fixes applied: {len(all_fixes)}")
    
    if all_fixes:
        print("\n🔧 Fixes Applied:")
        for fix in all_fixes:
            print(f"  • {fix}")
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "files_processed": len(workflow_files),
        "files_valid": valid_files,
        "total_fixes": len(all_fixes),
        "fixes_applied": all_fixes,
        "status": "completed"
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"workflow_fix_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to {report_file}")
    
    if valid_files == len(workflow_files):
        print_success("🎉 All workflow files are now valid!")
        return 0
    else:
        print_warning(f"⚠️  {len(workflow_files) - valid_files} files still have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())