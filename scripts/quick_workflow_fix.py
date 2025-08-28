#!/usr/bin/env python3
"""
SmartCloudOps AI - Quick Workflow Fixer
======================================

This script immediately fixes common workflow issues without requiring
external dependencies. It's designed to work in any environment.
"""

import os
import sys
import json
import subprocess
import re
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

def run_command(command, timeout=60):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_workflow_files():
    """Check and fix workflow files."""
    print_info("Checking workflow files...")
    
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print_error("No .github/workflows directory found")
        return False
    
    workflow_files = list(workflow_dir.glob("*.yml"))
    if not workflow_files:
        print_error("No workflow files found")
        return False
    
    print_info(f"Found {len(workflow_files)} workflow files")
    
    fixes_applied = []
    
    for workflow_file in workflow_files:
        print(f"🔧 Checking {workflow_file}...")
        
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            original_content = content
            file_fixes = []
            
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
                    file_fixes.append(f"Updated {old_action} to {new_action}")
            
            # Fix 2: Add missing permissions
            if "permissions:" not in content:
                lines = content.split('\n')
                new_lines = []
                permissions_added = False
                
                for line in lines:
                    new_lines.append(line)
                    if line.strip().startswith('on:') and not permissions_added:
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
                    file_fixes.append("Added permissions configuration")
            
            # Fix 3: Add cache configuration
            if "actions/setup-python" in content and "actions/cache" not in content:
                lines = content.split('\n')
                new_lines = []
                cache_added = False
                
                for line in lines:
                    new_lines.append(line)
                    if "uses: actions/setup-python" in line and not cache_added:
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
                    file_fixes.append("Added pip cache configuration")
            
            # Fix 4: Add npm cache
            if "actions/setup-node" in content and "actions/cache" not in content:
                lines = content.split('\n')
                new_lines = []
                cache_added = False
                
                for line in lines:
                    new_lines.append(line)
                    if "uses: actions/setup-node" in line and not cache_added:
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
                    file_fixes.append("Added npm cache configuration")
            
            # Write changes if any
            if content != original_content:
                with open(workflow_file, 'w') as f:
                    f.write(content)
                
                print_success(f"Fixed {len(file_fixes)} issues in {workflow_file}")
                for fix in file_fixes:
                    print(f"  • {fix}")
                fixes_applied.extend(file_fixes)
            else:
                print_info(f"No fixes needed for {workflow_file}")
                
        except Exception as e:
            print_error(f"Failed to fix {workflow_file}: {e}")
    
    return len(fixes_applied) > 0, fixes_applied

def check_dependencies():
    """Check and fix dependency issues."""
    print_info("Checking dependencies...")
    
    fixes_applied = []
    
    # Check Python requirements
    if Path("app/requirements.txt").exists():
        print_info("Found Python requirements.txt")
        
        # Try to install dependencies
        success, stdout, stderr = run_command("pip install -r app/requirements.txt", timeout=300)
        if success:
            print_success("Python dependencies installed successfully")
        else:
            print_warning(f"Failed to install Python dependencies: {stderr}")
            fixes_applied.append("Python dependency installation failed")
    
    # Check Node.js dependencies
    if Path("frontend/package.json").exists():
        print_info("Found Node.js package.json")
        
        # Try to install dependencies
        success, stdout, stderr = run_command("cd frontend && npm ci", timeout=300)
        if success:
            print_success("Node.js dependencies installed successfully")
        else:
            print_warning(f"Failed to install Node.js dependencies: {stderr}")
            fixes_applied.append("Node.js dependency installation failed")
    
    return len(fixes_applied) == 0, fixes_applied

def check_environment():
    """Check environment setup."""
    print_info("Checking environment...")
    
    issues = []
    
    # Check Python
    success, stdout, stderr = run_command("python3 --version")
    if success:
        print_success(f"Python: {stdout.strip()}")
    else:
        print_warning("Python not found or not working")
        issues.append("Python environment issue")
    
    # Check Node.js
    success, stdout, stderr = run_command("node --version")
    if success:
        print_success(f"Node.js: {stdout.strip()}")
    else:
        print_warning("Node.js not found or not working")
        issues.append("Node.js environment issue")
    
    # Check Git
    success, stdout, stderr = run_command("git --version")
    if success:
        print_success(f"Git: {stdout.strip()}")
    else:
        print_warning("Git not found or not working")
        issues.append("Git environment issue")
    
    return len(issues) == 0, issues

def commit_and_push():
    """Commit and push changes."""
    print_info("Committing and pushing changes...")
    
    # Check if there are changes
    success, stdout, stderr = run_command("git status --porcelain")
    if not success or not stdout.strip():
        print_info("No changes to commit")
        return True
    
    # Add changes
    success, stdout, stderr = run_command("git add .")
    if not success:
        print_error(f"Failed to add changes: {stderr}")
        return False
    
    # Commit changes
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"🔧 Auto-fix workflow issues - {timestamp}"
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success:
        print_error(f"Failed to commit changes: {stderr}")
        return False
    
    # Push changes
    success, stdout, stderr = run_command("git push")
    if not success:
        print_error(f"Failed to push changes: {stderr}")
        return False
    
    print_success("Changes committed and pushed successfully")
    return True

def main():
    """Main function."""
    print("🚀 SmartCloudOps AI - Quick Workflow Fixer")
    print("=" * 50)
    
    all_fixes = []
    success = True
    
    # Step 1: Check environment
    env_ok, env_issues = check_environment()
    if not env_ok:
        print_warning("Environment issues detected:")
        for issue in env_issues:
            print(f"  • {issue}")
    
    # Step 2: Check and fix workflow files
    workflow_fixed, workflow_fixes = check_workflow_files()
    if workflow_fixed:
        all_fixes.extend(workflow_fixes)
    
    # Step 3: Check dependencies
    deps_ok, dep_issues = check_dependencies()
    if not deps_ok:
        all_fixes.extend(dep_issues)
    
    # Step 4: Commit and push if there are fixes
    if all_fixes:
        print_info(f"Applying {len(all_fixes)} fixes...")
        if commit_and_push():
            print_success("All fixes applied and pushed!")
        else:
            print_error("Failed to commit and push fixes")
            success = False
    else:
        print_info("No fixes needed")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Environment OK: {'✅' if env_ok else '❌'}")
    print(f"Workflow fixes applied: {len(workflow_fixes)}")
    print(f"Dependency issues: {len(dep_issues)}")
    print(f"Total fixes: {len(all_fixes)}")
    
    if all_fixes:
        print("\n🔧 Fixes Applied:")
        for fix in all_fixes:
            print(f"  • {fix}")
    
    if success:
        print_success("🎉 Workflow fix process completed!")
        return 0
    else:
        print_error("❌ Some issues could not be resolved")
        return 1

if __name__ == "__main__":
    sys.exit(main())