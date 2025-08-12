#!/usr/bin/env python3
"""
SmartCloudOps AI - Comprehensive Security Audit Tool
===================================================

This script performs a comprehensive security audit of the application
to ensure all critical security fixes have been properly implemented.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    """Comprehensive security auditor for SmartCloudOps AI"""
    
    def __init__(self):
        self.root_path = Path.cwd()
        self.issues = []
        self.warnings = []
        self.passed_checks = []
    
    def audit_configuration_security(self):
        """Audit configuration and secret management"""
        print("🔍 Auditing Configuration Security...")
        
        # Check 1: No .env files in git
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        git_files = result.stdout.splitlines()
        
        sensitive_files = [f for f in git_files if re.match(r'\.env(\.|$)', f) and f != '.env.example']
        if sensitive_files:
            self.issues.append(f"CRITICAL: Sensitive .env files in git: {sensitive_files}")
        else:
            self.passed_checks.append("✅ No sensitive .env files in git")
        
        # Check 2: Hardcoded secrets detection
        secret_patterns = [
            r'SECRET_KEY\s*=\s*["\'][^"\']{10,}["\']',
            r'API_KEY\s*=\s*["\'][^"\']{10,}["\']',
            r'PASSWORD\s*=\s*["\'][^"\']{5,}["\']',
            r'TOKEN\s*=\s*["\'][^"\']{10,}["\']'
        ]
        
        hardcoded_secrets = []
        for py_file in self.root_path.glob('**/*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        hardcoded_secrets.append(str(py_file))
                        break
            except Exception:
                continue
        
        if hardcoded_secrets:
            self.issues.append(f"CRITICAL: Potential hardcoded secrets in: {hardcoded_secrets}")
        else:
            self.passed_checks.append("✅ No hardcoded secrets detected")
        
        # Check 3: Configuration loading test
        try:
            sys.path.append('app')
            from config import config
            if hasattr(config, 'environment'):
                self.passed_checks.append(f"✅ Secure configuration loads successfully ({config.environment})")
                
                # Check debug mode in production
                if config.environment == 'production' and getattr(config, 'debug', False):
                    self.issues.append("CRITICAL: Debug mode enabled in production")
                else:
                    self.passed_checks.append("✅ Debug mode properly configured")
                
            else:
                self.issues.append("CRITICAL: Configuration object missing environment attribute")
                
        except Exception as e:
            self.issues.append(f"CRITICAL: Configuration loading failed: {e}")
    
    def audit_dependency_security(self):
        """Audit dependencies for known vulnerabilities"""
        print("🔍 Auditing Dependency Security...")
        
        requirements_file = self.root_path / 'app' / 'requirements.txt'
        if requirements_file.exists():
            try:
                # Check for known vulnerable packages
                content = requirements_file.read_text()
                
                # Common vulnerable patterns
                vulnerable_patterns = [
                    r'flask==0\.',  # Very old Flask versions
                    r'requests==2\.1[0-8]',  # Old requests with SSL issues
                    r'urllib3==1\.[1-2][0-5]',  # Old urllib3
                ]
                
                for pattern in vulnerable_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.warnings.append(f"WARNING: Potentially vulnerable dependency pattern: {pattern}")
                
                self.passed_checks.append("✅ Requirements file analyzed for known vulnerabilities")
                
            except Exception as e:
                self.warnings.append(f"WARNING: Could not analyze requirements.txt: {e}")
        else:
            self.warnings.append("WARNING: No requirements.txt found")
    
    def audit_file_permissions(self):
        """Audit file permissions for security"""
        print("🔍 Auditing File Permissions...")
        
        # Check sensitive files
        sensitive_files = ['.env', '.dev-secret', 'app/config.py']
        
        for file_path in sensitive_files:
            full_path = self.root_path / file_path
            if full_path.exists():
                stat = full_path.stat()
                mode = oct(stat.st_mode)[-3:]
                
                if file_path.endswith(('.env', '.dev-secret')):
                    if mode != '600':
                        self.warnings.append(f"WARNING: {file_path} permissions should be 600, found {mode}")
                    else:
                        self.passed_checks.append(f"✅ {file_path} has secure permissions (600)")
        
        # Check executable scripts
        for script in self.root_path.glob('*.sh'):
            stat = script.stat()
            if not (stat.st_mode & 0o100):  # Not executable
                self.warnings.append(f"WARNING: Script {script.name} is not executable")
    
    def audit_aws_configuration(self):
        """Audit AWS configuration and secrets"""
        print("🔍 Auditing AWS Configuration...")
        
        try:
            # Check if AWS CLI is configured
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.passed_checks.append("✅ AWS credentials configured")
                
                # Parse the output to check account
                try:
                    aws_info = json.loads(result.stdout)
                    account_id = aws_info.get('Account', 'unknown')
                    self.passed_checks.append(f"✅ AWS Account: {account_id}")
                except:
                    pass
            else:
                self.warnings.append("WARNING: AWS credentials not configured or invalid")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.warnings.append("WARNING: AWS CLI not available or not responding")
    
    def audit_network_security(self):
        """Audit network and URL security"""
        print("🔍 Auditing Network Security...")
        
        # Check for insecure URLs in configuration
        insecure_patterns = [
            r'http://[^/\s]+',  # HTTP URLs
            r'localhost:\d+',   # Localhost URLs (might be OK for dev)
            r'\d+\.\d+\.\d+\.\d+:\d+',  # IP addresses with ports
        ]
        
        for py_file in self.root_path.glob('**/*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for pattern in insecure_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Filter out comments and obvious dev/test cases
                        filtered_matches = [m for m in matches if 'localhost' in m or 'example.com' in m]
                        if filtered_matches and 'config' in str(py_file):
                            self.warnings.append(f"WARNING: Insecure URLs in {py_file}: {filtered_matches}")
            except Exception:
                continue
    
    def audit_logging_security(self):
        """Audit logging configuration for security"""
        print("🔍 Auditing Logging Security...")
        
        # Check for potential log injection vulnerabilities
        log_files = list(self.root_path.glob('**/*.py'))
        
        for py_file in log_files:
            if '.venv' in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Look for potentially unsafe logging patterns
                unsafe_patterns = [
                    r'logger\.\w+\([^)]*\%[^)]*\)',  # String formatting in logging
                    r'print\([^)]*input\([^)]*\)',  # Printing user input
                ]
                
                for pattern in unsafe_patterns:
                    if re.search(pattern, content):
                        self.warnings.append(f"WARNING: Potentially unsafe logging in {py_file}")
                        break
                        
            except Exception:
                continue
        
        self.passed_checks.append("✅ Logging patterns analyzed")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        
        total_checks = len(self.passed_checks) + len(self.warnings) + len(self.issues)
        
        report = {
            'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
            'environment': os.getenv('ENVIRONMENT', 'unknown'),
            'summary': {
                'total_checks': total_checks,
                'passed': len(self.passed_checks),
                'warnings': len(self.warnings),
                'critical_issues': len(self.issues),
                'security_score': f"{(len(self.passed_checks) / max(total_checks, 1)) * 100:.1f}%"
            },
            'passed_checks': self.passed_checks,
            'warnings': self.warnings,
            'critical_issues': self.issues,
            'recommendations': self._get_recommendations()
        }
        
        return report
    
    def _get_recommendations(self) -> List[str]:
        """Get security recommendations based on audit results"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🚨 URGENT: Fix all critical issues before deployment")
            recommendations.append("🔒 Review all configuration files for hardcoded secrets")
            recommendations.append("🔐 Implement proper secret management (AWS Secrets Manager)")
        
        if self.warnings:
            recommendations.append("⚠️ Address security warnings for production readiness")
            recommendations.append("🛡️ Review file permissions and access controls")
        
        if not self.issues and not self.warnings:
            recommendations.append("✅ Security posture is good - maintain current practices")
            recommendations.append("🔄 Schedule regular security audits")
        
        recommendations.extend([
            "📚 Train team on secure coding practices",
            "🔍 Implement automated security scanning in CI/CD",
            "📖 Document security procedures and incident response",
            "🔄 Regularly update dependencies and security patches"
        ])
        
        return recommendations

def main():
    """Run comprehensive security audit"""
    print("🛡️ SmartCloudOps AI - Comprehensive Security Audit")
    print("=" * 50)
    
    auditor = SecurityAuditor()
    
    # Run all audit checks
    auditor.audit_configuration_security()
    auditor.audit_dependency_security()
    auditor.audit_file_permissions()
    auditor.audit_aws_configuration()
    auditor.audit_network_security()
    auditor.audit_logging_security()
    
    # Generate and display report
    report = auditor.generate_report()
    
    print("\n📊 SECURITY AUDIT REPORT")
    print("=" * 30)
    print(f"Environment: {report['summary']['security_score']}")
    print(f"Security Score: {report['summary']['security_score']}")
    print(f"Checks Passed: {report['summary']['passed']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Critical Issues: {report['summary']['critical_issues']}")
    
    if report['passed_checks']:
        print(f"\n✅ PASSED CHECKS ({len(report['passed_checks'])})")
        for check in report['passed_checks']:
            print(f"   {check}")
    
    if report['warnings']:
        print(f"\n⚠️ WARNINGS ({len(report['warnings'])})")
        for warning in report['warnings']:
            print(f"   {warning}")
    
    if report['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES ({len(report['critical_issues'])})")
        for issue in report['critical_issues']:
            print(f"   {issue}")
    
    print(f"\n💡 RECOMMENDATIONS")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    # Save report to file
    report_file = f"security-audit-{report['timestamp'].replace(' ', '-').replace(':', '')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Report saved to: {report_file}")
    
    # Exit with error code if critical issues found
    if report['critical_issues']:
        print(f"\n🚨 AUDIT FAILED - {len(report['critical_issues'])} critical issues found")
        sys.exit(1)
    else:
        print(f"\n✅ AUDIT PASSED - Security posture is acceptable")
        sys.exit(0)

if __name__ == "__main__":
    main()
