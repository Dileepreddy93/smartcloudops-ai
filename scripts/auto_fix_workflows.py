#!/usr/bin/env python3
"""
SmartCloudOps AI - Automatic Workflow Fixer
==========================================

This script automatically identifies and fixes common GitHub workflow issues.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


class WorkflowFixer:
    """Automatic workflow issue detector and fixer."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.fixes_applied = []
        self.issues_found = []

    def check_python_version_consistency(self) -> List[Dict[str, Any]]:
        """Check for Python version inconsistencies across workflows."""
        print("🔍 Checking Python version consistency...")
        
        issues = []
        python_versions = set()
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                # Find Python version specifications
                version_matches = re.findall(r"python-version:\s*['\"]?([^'\"]+)['\"]?", content)
                for version in version_matches:
                    python_versions.add(version)
                    
                # Check for hardcoded versions
                if "python-version: '3.12'" in content:
                    issues.append({
                        "file": str(workflow_file.relative_to(self.project_root)),
                        "issue": "Uses Python 3.12 instead of 3.11",
                        "severity": "MEDIUM"
                    })
                    
            except Exception as e:
                print(f"Warning: Could not read {workflow_file}: {e}")
        
        if len(python_versions) > 1:
            issues.append({
                "file": "Multiple workflows",
                "issue": f"Multiple Python versions found: {python_versions}",
                "severity": "HIGH"
            })
            
        return issues

    def check_node_version_consistency(self) -> List[Dict[str, Any]]:
        """Check for Node.js version inconsistencies across workflows."""
        print("🔍 Checking Node.js version consistency...")
        
        issues = []
        node_versions = set()
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                # Find Node version specifications
                version_matches = re.findall(r"node-version:\s*['\"]?([^'\"]+)['\"]?", content)
                for version in version_matches:
                    node_versions.add(version)
                    
            except Exception as e:
                print(f"Warning: Could not read {workflow_file}: {e}")
        
        if len(node_versions) > 1:
            issues.append({
                "file": "Multiple workflows",
                "issue": f"Multiple Node.js versions found: {node_versions}",
                "severity": "MEDIUM"
            })
            
        return issues

    def check_missing_dependencies(self) -> List[Dict[str, Any]]:
        """Check for missing dependencies in requirements files."""
        print("🔍 Checking for missing dependencies...")
        
        issues = []
        
        # Check if requirements.txt exists
        requirements_file = self.project_root / "app" / "requirements.txt"
        if not requirements_file.exists():
            issues.append({
                "file": "app/requirements.txt",
                "issue": "Requirements file not found",
                "severity": "CRITICAL"
            })
            return issues
            
        # Check for common missing dependencies
        try:
            content = requirements_file.read_text()
            required_deps = [
                "pytest",
                "pytest-cov",
                "black",
                "ruff",
                "mypy",
                "bandit",
                "safety"
            ]
            
            for dep in required_deps:
                if not any(dep in line for line in content.split('\n')):
                    issues.append({
                        "file": "app/requirements.txt",
                        "issue": f"Missing dependency: {dep}",
                        "severity": "HIGH"
                    })
                    
        except Exception as e:
            issues.append({
                "file": "app/requirements.txt",
                "issue": f"Could not read requirements file: {e}",
                "severity": "HIGH"
            })
            
        return issues

    def check_frontend_dependencies(self) -> List[Dict[str, Any]]:
        """Check for frontend dependency issues."""
        print("🔍 Checking frontend dependencies...")
        
        issues = []
        package_json = self.project_root / "frontend" / "package.json"
        
        if not package_json.exists():
            issues.append({
                "file": "frontend/package.json",
                "issue": "Frontend package.json not found",
                "severity": "CRITICAL"
            })
            return issues
            
        try:
            with open(package_json) as f:
                package_data = json.load(f)
                
            # Check for required scripts
            required_scripts = ["test", "build", "lint", "type-check"]
            scripts = package_data.get("scripts", {})
            
            for script in required_scripts:
                if script not in scripts:
                    issues.append({
                        "file": "frontend/package.json",
                        "issue": f"Missing script: {script}",
                        "severity": "HIGH"
                    })
                    
        except Exception as e:
            issues.append({
                "file": "frontend/package.json",
                "issue": f"Could not read package.json: {e}",
                "severity": "HIGH"
            })
            
        return issues

    def check_workflow_syntax(self) -> List[Dict[str, Any]]:
        """Check for YAML syntax issues in workflows."""
        print("🔍 Checking workflow syntax...")
        
        issues = []
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                
                # Check for common YAML issues
                if "python-version: '3.12'" in content:
                    issues.append({
                        "file": str(workflow_file.relative_to(self.project_root)),
                        "issue": "Uses Python 3.12 instead of 3.11",
                        "severity": "MEDIUM"
                    })
                    
                # Check for missing permissions
                if "permissions:" not in content:
                    issues.append({
                        "file": str(workflow_file.relative_to(self.project_root)),
                        "issue": "Missing permissions section",
                        "severity": "LOW"
                    })
                    
                # Check for hardcoded secrets
                if "password" in content.lower() and "secrets." not in content:
                    issues.append({
                        "file": str(workflow_file.relative_to(self.project_root)),
                        "issue": "Potential hardcoded password",
                        "severity": "HIGH"
                    })
                    
            except Exception as e:
                issues.append({
                    "file": str(workflow_file.relative_to(self.project_root)),
                    "issue": f"Could not read workflow file: {e}",
                    "severity": "HIGH"
                })
                
        return issues

    def fix_python_version_issues(self) -> None:
        """Fix Python version inconsistencies."""
        print("🔧 Fixing Python version issues...")
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                original_content = content
                
                # Replace Python 3.12 with 3.11
                content = re.sub(r"python-version:\s*['\"]?3\.12['\"]?", "python-version: '3.11'", content)
                
                if content != original_content:
                    workflow_file.write_text(content)
                    self.fixes_applied.append(f"Updated Python version in {workflow_file.name}")
                    print(f"✅ Fixed Python version in {workflow_file.name}")
                    
            except Exception as e:
                print(f"Warning: Could not fix {workflow_file}: {e}")

    def fix_node_version_issues(self) -> None:
        """Fix Node.js version inconsistencies."""
        print("🔧 Fixing Node.js version issues...")
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                original_content = content
                
                # Standardize on Node 18
                content = re.sub(r"node-version:\s*['\"]?20['\"]?", "node-version: '18'", content)
                
                if content != original_content:
                    workflow_file.write_text(content)
                    self.fixes_applied.append(f"Updated Node.js version in {workflow_file.name}")
                    print(f"✅ Fixed Node.js version in {workflow_file.name}")
                    
            except Exception as e:
                print(f"Warning: Could not fix {workflow_file}: {e}")

    def fix_missing_dependencies(self) -> None:
        """Fix missing dependencies in requirements.txt."""
        print("🔧 Fixing missing dependencies...")
        
        requirements_file = self.project_root / "app" / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ Requirements file not found, cannot fix dependencies")
            return
            
        try:
            content = requirements_file.read_text()
            missing_deps = []
            
            # Check for missing dependencies
            required_deps = {
                "pytest": "pytest==7.4.3",
                "pytest-cov": "pytest-cov==4.1.0",
                "black": "black==24.8.0",
                "ruff": "ruff==0.1.0",
                "mypy": "mypy==1.10.0",
                "bandit": "bandit==1.7.7",
                "safety": "safety>=2.4.0"
            }
            
            for dep, full_dep in required_deps.items():
                if not any(dep in line for line in content.split('\n')):
                    missing_deps.append(full_dep)
                    
            if missing_deps:
                # Add missing dependencies
                content += "\n# Additional dependencies for CI/CD\n"
                for dep in missing_deps:
                    content += f"{dep}\n"
                    
                requirements_file.write_text(content)
                self.fixes_applied.append(f"Added missing dependencies: {', '.join(missing_deps)}")
                print(f"✅ Added missing dependencies: {', '.join(missing_deps)}")
                
        except Exception as e:
            print(f"Warning: Could not fix dependencies: {e}")

    def fix_frontend_scripts(self) -> None:
        """Fix missing frontend scripts."""
        print("🔧 Fixing frontend scripts...")
        
        package_json = self.project_root / "frontend" / "package.json"
        
        if not package_json.exists():
            print("❌ Frontend package.json not found, cannot fix scripts")
            return
            
        try:
            with open(package_json) as f:
                package_data = json.load(f)
                
            scripts = package_data.get("scripts", {})
            missing_scripts = []
            
            # Add missing scripts
            if "type-check" not in scripts:
                scripts["type-check"] = "tsc --noEmit"
                missing_scripts.append("type-check")
                
            if missing_scripts:
                package_data["scripts"] = scripts
                
                with open(package_json, 'w') as f:
                    json.dump(package_data, f, indent=2)
                    
                self.fixes_applied.append(f"Added missing frontend scripts: {', '.join(missing_scripts)}")
                print(f"✅ Added missing frontend scripts: {', '.join(missing_scripts)}")
                
        except Exception as e:
            print(f"Warning: Could not fix frontend scripts: {e}")

    def fix_workflow_permissions(self) -> None:
        """Add missing permissions to workflows."""
        print("🔧 Fixing workflow permissions...")
        
        for workflow_file in self.workflows_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text()
                original_content = content
                
                # Add permissions if missing
                if "permissions:" not in content:
                    # Find where to insert permissions (after env: or at the beginning)
                    if "env:" in content:
                        content = content.replace("env:", "permissions:\n  contents: read\n  pull-requests: write\n  issues: write\n\nenv:")
                    else:
                        # Insert at the beginning after the trigger
                        lines = content.split('\n')
                        insert_index = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('jobs:'):
                                insert_index = i
                                break
                        
                        permissions = [
                            "permissions:",
                            "  contents: read",
                            "  pull-requests: write", 
                            "  issues: write",
                            ""
                        ]
                        
                        lines[insert_index:insert_index] = permissions
                        content = '\n'.join(lines)
                        
                if content != original_content:
                    workflow_file.write_text(content)
                    self.fixes_applied.append(f"Added permissions to {workflow_file.name}")
                    print(f"✅ Added permissions to {workflow_file.name}")
                    
            except Exception as e:
                print(f"Warning: Could not fix permissions in {workflow_file}: {e}")

    def create_missing_test_files(self) -> None:
        """Create missing test files if needed."""
        print("🔧 Creating missing test files...")
        
        # Check if basic test files exist
        test_files = [
            "tests/__init__.py",
            "tests/conftest.py",
            "tests/phase_1/__init__.py",
            "tests/phase_2/__init__.py",
            "tests/phase_3/__init__.py"
        ]
        
        for test_file in test_files:
            file_path = self.project_root / test_file
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text('"""Test module."""\n')
                self.fixes_applied.append(f"Created missing test file: {test_file}")
                print(f"✅ Created missing test file: {test_file}")

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all workflow checks."""
        print("🚀 Running comprehensive workflow checks...")
        
        all_issues = []
        all_issues.extend(self.check_python_version_consistency())
        all_issues.extend(self.check_node_version_consistency())
        all_issues.extend(self.check_missing_dependencies())
        all_issues.extend(self.check_frontend_dependencies())
        all_issues.extend(self.check_workflow_syntax())
        
        self.issues_found = all_issues
        
        return {
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i["severity"] == "CRITICAL"]),
            "high_issues": len([i for i in all_issues if i["severity"] == "HIGH"]),
            "medium_issues": len([i for i in all_issues if i["severity"] == "MEDIUM"]),
            "low_issues": len([i for i in all_issues if i["severity"] == "LOW"]),
            "issues": all_issues
        }

    def apply_all_fixes(self) -> None:
        """Apply all available fixes."""
        print("🔧 Applying all available fixes...")
        
        self.fix_python_version_issues()
        self.fix_node_version_issues()
        self.fix_missing_dependencies()
        self.fix_frontend_scripts()
        self.fix_workflow_permissions()
        self.create_missing_test_files()

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate a comprehensive report."""
        print("\n" + "=" * 60)
        print("WORKFLOW FIXER REPORT")
        print("=" * 60)
        
        print(f"Total Issues Found: {results['total_issues']}")
        print(f"Critical Issues: {results['critical_issues']}")
        print(f"High Issues: {results['high_issues']}")
        print(f"Medium Issues: {results['medium_issues']}")
        print(f"Low Issues: {results['low_issues']}")
        
        if self.fixes_applied:
            print(f"\nFixes Applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
        
        if self.issues_found:
            print(f"\nRemaining Issues:")
            for issue in self.issues_found:
                print(f"  {issue['severity']}: {issue['file']} - {issue['issue']}")
        
        print("=" * 60)

    def run_workflow_validation(self) -> bool:
        """Run basic workflow validation."""
        print("🧪 Running workflow validation...")
        
        try:
            # Check if we can import required modules
            import yaml
            
            for workflow_file in self.workflows_dir.glob("*.yml"):
                try:
                    with open(workflow_file) as f:
                        yaml.safe_load(f)
                    print(f"✅ {workflow_file.name} - Valid YAML")
                except yaml.YAMLError as e:
                    print(f"❌ {workflow_file.name} - Invalid YAML: {e}")
                    return False
                    
            return True
            
        except ImportError:
            print("⚠️ PyYAML not available, skipping YAML validation")
            return True


def main():
    """Main function to run workflow fixer."""
    fixer = WorkflowFixer()
    
    # Run all checks
    results = fixer.run_all_checks()
    
    # Apply fixes
    fixer.apply_all_fixes()
    
    # Generate report
    fixer.generate_report(results)
    
    # Run validation
    validation_passed = fixer.run_workflow_validation()
    
    if validation_passed and results['total_issues'] == 0:
        print("\n🎉 All workflows are now properly configured!")
        return 0
    else:
        print(f"\n⚠️ {results['total_issues']} issues remain to be fixed manually")
        return 1


if __name__ == "__main__":
    sys.exit(main())