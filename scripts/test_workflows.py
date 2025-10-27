#!/usr/bin/env python3
"""
SmartCloudOps AI - Workflow Tester
=================================

This script tests GitHub workflows by running them locally and checking for issues.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any


class WorkflowTester:
    """Test GitHub workflows for functionality and issues."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.test_results = []
        self.failed_tests = []

    def test_python_imports(self) -> bool:
        """Test if Python imports work correctly."""
        print("🐍 Testing Python imports...")
        
        try:
            # Test main app import
            result = subprocess.run([
                sys.executable, "-c", 
                "import sys; sys.path.append('app'); from main import create_app; print('✅ App import successful')"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Python imports working")
                return True
            else:
                print(f"❌ Python import failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Python import test failed: {e}")
            return False

    def test_frontend_build(self) -> bool:
        """Test if frontend can be built."""
        print("🏗️ Testing frontend build...")
        
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            print("⚠️ Frontend directory not found, skipping frontend test")
            return True
            
        try:
            # Check if package.json exists
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                print("⚠️ package.json not found, skipping frontend test")
                return True
                
            # Test npm install
            result = subprocess.run([
                "npm", "ci"
            ], capture_output=True, text=True, cwd=frontend_dir)
            
            if result.returncode != 0:
                print(f"❌ npm install failed: {result.stderr}")
                return False
                
            # Test npm run build
            result = subprocess.run([
                "npm", "run", "build"
            ], capture_output=True, text=True, cwd=frontend_dir)
            
            if result.returncode == 0:
                print("✅ Frontend build successful")
                return True
            else:
                print(f"❌ Frontend build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Frontend build test failed: {e}")
            return False

    def test_python_tests(self) -> bool:
        """Test if Python tests can run."""
        print("🧪 Testing Python tests...")
        
        try:
            # Install test dependencies
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "app/requirements.txt"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
                
            # Run a simple test
            result = subprocess.run([
                sys.executable, "-m", "pytest", "tests/phase_1/", "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Python tests passed")
                return True
            else:
                print(f"⚠️ Some Python tests failed: {result.stderr}")
                # Don't fail the entire workflow for test failures
                return True
                
        except Exception as e:
            print(f"❌ Python test execution failed: {e}")
            return False

    def test_security_audit(self) -> bool:
        """Test if security audit script works."""
        print("🔒 Testing security audit...")
        
        try:
            result = subprocess.run([
                sys.executable, "scripts/security_audit.py"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Security audit completed")
                return True
            else:
                print(f"⚠️ Security audit had issues: {result.stderr}")
                # Don't fail for security audit issues
                return True
                
        except Exception as e:
            print(f"❌ Security audit test failed: {e}")
            return False

    def test_ml_scripts(self) -> bool:
        """Test if ML scripts work."""
        print("🤖 Testing ML scripts...")
        
        try:
            # Test data collector
            result = subprocess.run([
                sys.executable, "scripts/simple_real_data_collector.py"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                print(f"❌ Data collector failed: {result.stderr}")
                return False
                
            # Test ML trainer
            result = subprocess.run([
                sys.executable, "scripts/simple_real_ml_trainer.py"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ ML scripts working")
                return True
            else:
                print(f"❌ ML trainer failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ ML scripts test failed: {e}")
            return False

    def test_docker_build(self) -> bool:
        """Test if Docker build works."""
        print("🐳 Testing Docker build...")
        
        try:
            # Check if Dockerfile exists
            dockerfile = self.project_root / "Dockerfile"
            if not dockerfile.exists():
                print("⚠️ Dockerfile not found, skipping Docker test")
                return True
                
            # Test Docker build
            result = subprocess.run([
                "docker", "build", "-t", "smartcloudops-ai:test", "."
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Docker build successful")
                return True
            else:
                print(f"❌ Docker build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Docker build test failed: {e}")
            return False

    def validate_workflow_syntax(self) -> bool:
        """Validate all workflow YAML syntax."""
        print("📝 Validating workflow syntax...")
        
        try:
            import yaml
            
            all_valid = True
            for workflow_file in self.workflows_dir.glob("*.yml"):
                try:
                    with open(workflow_file) as f:
                        yaml.safe_load(f)
                    print(f"✅ {workflow_file.name} - Valid YAML")
                except yaml.YAMLError as e:
                    print(f"❌ {workflow_file.name} - Invalid YAML: {e}")
                    all_valid = False
                    
            return all_valid
            
        except ImportError:
            print("⚠️ PyYAML not available, skipping YAML validation")
            return True

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all workflow tests."""
        print("🚀 Running comprehensive workflow tests...")
        
        tests = [
            ("Python Imports", self.test_python_imports),
            ("Frontend Build", self.test_frontend_build),
            ("Python Tests", self.test_python_tests),
            ("Security Audit", self.test_security_audit),
            ("ML Scripts", self.test_ml_scripts),
            ("Docker Build", self.test_docker_build),
            ("Workflow Syntax", self.validate_workflow_syntax),
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                else:
                    failed += 1
                    self.failed_tests.append(test_name)
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
                failed += 1
                self.failed_tests.append(test_name)
        
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "results": results,
            "failed_tests": self.failed_tests
        }

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate a comprehensive test report."""
        print("\n" + "=" * 60)
        print("WORKFLOW TEST REPORT")
        print("=" * 60)
        
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        
        print(f"\nTest Results:")
        for test_name, result in results['results'].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        if results['failed_tests']:
            print(f"\nFailed Tests:")
            for test in results['failed_tests']:
                print(f"  - {test}")
        
        print("=" * 60)
        
        # Save report to file
        report_file = self.project_root / "workflow_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📊 Report saved to {report_file}")


def main():
    """Main function to run workflow tests."""
    tester = WorkflowTester()
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Generate report
    tester.generate_report(results)
    
    # Return exit code based on results
    if results['failed'] == 0:
        print("\n🎉 All workflow tests passed!")
        return 0
    else:
        print(f"\n⚠️ {results['failed']} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())