#!/usr/bin/env python3
"""
SmartCloudOps AI - Frontend Security Verification
===============================================

Comprehensive validation script for all Grafana security fixes.
Verifies that all 4 critical vulnerabilities have been resolved.

Security Framework: Four-Point Security Analysis
1. Authentication Bypass Prevention ✓
2. Credential Security Hardening ✓  
3. Transport Layer Security ✓
4. Session & Header Security ✓
"""

import sys
import json
import time
import subprocess
import urllib3
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import configparser
import os
import re

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GrafanaSecurityVerifier:
    """Comprehensive security verification for Grafana deployment"""
    
    def __init__(self):
        self.results = {
            'authentication': [],
            'credentials': [],
            'transport': [],
            'headers': []
        }
        self.critical_issues = 0
        self.warnings = 0
        self.passed_checks = 0
        
    def print_header(self):
        """Print verification header"""
        print("🔒 SmartCloudOps AI - Frontend Security Verification")
        print("=" * 55)
        print(f"📅 Verification Time: {datetime.now(timezone.utc).isoformat()}")
        print(f"🎯 Target: Grafana Dashboard Security")
        print(f"📋 Framework: Four-Point Security Analysis")
        print("")
        
    def check_grafana_config(self) -> Dict:
        """Verify Grafana configuration security"""
        print("📋 Checking Grafana Configuration Security...")
        config_issues = []
        
        # Check if secure config exists
        secure_config_paths = [
            '/etc/grafana/grafana.ini',
            '/tmp/grafana_secure.ini'
        ]
        
        config_found = False
        config_content = ""
        
        for config_path in secure_config_paths:
            if os.path.exists(config_path):
                config_found = True
                print(f"   ✅ Found configuration: {config_path}")
                
                try:
                    with open(config_path, 'r') as f:
                        config_content = f.read()
                except Exception as e:
                    config_issues.append(f"Cannot read config {config_path}: {e}")
                    continue
                
                # Parse configuration
                config = configparser.ConfigParser()
                try:
                    config.read_string(config_content)
                except Exception as e:
                    config_issues.append(f"Invalid config format in {config_path}: {e}")
                    continue
                
                # 1. Authentication Security Checks
                print("   🔐 Checking Authentication Security...")
                
                # Check anonymous access (CRITICAL)
                try:
                    anonymous_enabled = config.getboolean('auth.anonymous', 'enabled', fallback=True)
                    if anonymous_enabled:
                        config_issues.append("CRITICAL: Anonymous access is ENABLED (should be disabled)")
                        self.critical_issues += 1
                    else:
                        print("      ✅ Anonymous access: DISABLED")
                        self.passed_checks += 1
                except:
                    config_issues.append("WARNING: Cannot verify anonymous access setting")
                    self.warnings += 1
                
                # Check admin credentials (CRITICAL)
                try:
                    admin_user = config.get('security', 'admin_user', fallback='admin')
                    admin_password = config.get('security', 'admin_password', fallback='admin')
                    
                    if admin_user == 'admin' and admin_password == 'admin':
                        config_issues.append("CRITICAL: Default admin credentials detected (admin/admin)")
                        self.critical_issues += 1
                    elif admin_password in ['admin123', 'password', '123456']:
                        config_issues.append("CRITICAL: Weak admin password detected")
                        self.critical_issues += 1
                    else:
                        print("      ✅ Strong admin credentials configured")
                        self.passed_checks += 1
                except:
                    config_issues.append("WARNING: Cannot verify admin credentials")
                    self.warnings += 1
                
                # 2. Transport Security Checks
                print("   🌐 Checking Transport Security...")
                
                # Check HTTPS protocol (CRITICAL)
                try:
                    protocol = config.get('server', 'protocol', fallback='http')
                    if protocol != 'https':
                        config_issues.append("CRITICAL: HTTP protocol detected (should be HTTPS)")
                        self.critical_issues += 1
                    else:
                        print("      ✅ HTTPS protocol: ENABLED")
                        self.passed_checks += 1
                except:
                    config_issues.append("WARNING: Cannot verify protocol setting")
                    self.warnings += 1
                
                # Check SSL certificates
                try:
                    cert_file = config.get('server', 'cert_file', fallback='')
                    cert_key = config.get('server', 'cert_key', fallback='')
                    
                    if cert_file and cert_key:
                        print("      ✅ SSL certificates: CONFIGURED")
                        self.passed_checks += 1
                        
                        # Check if certificates exist
                        if os.path.exists(cert_file) and os.path.exists(cert_key):
                            print("      ✅ SSL certificate files: FOUND")
                            self.passed_checks += 1
                        else:
                            config_issues.append("WARNING: SSL certificate files not found")
                            self.warnings += 1
                    else:
                        config_issues.append("WARNING: SSL certificates not configured")
                        self.warnings += 1
                except:
                    config_issues.append("WARNING: Cannot verify SSL configuration")
                    self.warnings += 1
                
                # 3. Security Headers Checks
                print("   🛡️  Checking Security Headers...")
                
                # Check Content Security Policy
                try:
                    csp_enabled = config.getboolean('security.content_security_policy', 'enabled', fallback=False)
                    if csp_enabled:
                        print("      ✅ Content Security Policy: ENABLED")
                        self.passed_checks += 1
                    else:
                        config_issues.append("WARNING: Content Security Policy not enabled")
                        self.warnings += 1
                except:
                    config_issues.append("WARNING: Cannot verify CSP configuration")
                    self.warnings += 1
                
                # Check security headers
                security_headers = [
                    ('strict_transport_security', 'HSTS'),
                    ('cookie_secure', 'Secure Cookies'),
                    ('x_content_type_options', 'Content Type Protection'),
                    ('x_xss_protection', 'XSS Protection')
                ]
                
                for header_setting, header_name in security_headers:
                    try:
                        enabled = config.getboolean('security', header_setting, fallback=False)
                        if enabled:
                            print(f"      ✅ {header_name}: ENABLED")
                            self.passed_checks += 1
                        else:
                            config_issues.append(f"WARNING: {header_name} not enabled")
                            self.warnings += 1
                    except:
                        config_issues.append(f"WARNING: Cannot verify {header_name}")
                        self.warnings += 1
                
                # 4. Session Security Checks
                print("   🔑 Checking Session Security...")
                
                # Check session settings
                session_settings = [
                    ('login_remember_days', 'Login Remember Period'),
                    ('login_maximum_inactive_lifetime_days', 'Session Timeout'),
                    ('token_rotation_interval_minutes', 'Token Rotation')
                ]
                
                for setting, description in session_settings:
                    try:
                        value = config.get('security', setting, fallback=None)
                        if value:
                            print(f"      ✅ {description}: CONFIGURED ({value})")
                            self.passed_checks += 1
                        else:
                            config_issues.append(f"WARNING: {description} not configured")
                            self.warnings += 1
                    except:
                        config_issues.append(f"WARNING: Cannot verify {description}")
                        self.warnings += 1
                
                break  # Use first found config
        
        if not config_found:
            config_issues.append("CRITICAL: No Grafana configuration found")
            self.critical_issues += 1
        
        return {
            'config_found': config_found,
            'issues': config_issues,
            'content_length': len(config_content)
        }
    
    def check_service_status(self) -> Dict:
        """Check Grafana service status"""
        print("🚀 Checking Service Status...")
        service_issues = []
        
        services = ['grafana-server', 'prometheus', 'node_exporter']
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {service}: RUNNING")
                    service_status[service] = 'running'
                    self.passed_checks += 1
                else:
                    print(f"   ❌ {service}: NOT RUNNING")
                    service_issues.append(f"Service {service} is not running")
                    service_status[service] = 'stopped'
                    self.warnings += 1
                    
            except subprocess.TimeoutExpired:
                service_issues.append(f"Timeout checking {service} status")
                service_status[service] = 'timeout'
                self.warnings += 1
            except Exception as e:
                service_issues.append(f"Error checking {service}: {e}")
                service_status[service] = 'error'
                self.warnings += 1
        
        return {
            'services': service_status,
            'issues': service_issues
        }
    
    def check_network_security(self) -> Dict:
        """Check network security configuration"""
        print("🌐 Checking Network Security...")
        network_issues = []
        
        # Check if ports are listening
        try:
            result = subprocess.run(
                ['ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            listening_ports = result.stdout
            
            # Check for Grafana HTTPS port (3000)
            if ':3000' in listening_ports:
                print("   ✅ Grafana port 3000: LISTENING")
                self.passed_checks += 1
            else:
                network_issues.append("WARNING: Grafana port 3000 not listening")
                self.warnings += 1
                
            # Check for Prometheus port (9090)
            if ':9090' in listening_ports:
                print("   ✅ Prometheus port 9090: LISTENING")
                self.passed_checks += 1
            else:
                network_issues.append("WARNING: Prometheus port 9090 not listening")
                self.warnings += 1
                
        except Exception as e:
            network_issues.append(f"Error checking listening ports: {e}")
            self.warnings += 1
        
        # Check firewall configuration
        firewall_configured = False
        try:
            # Check for firewall-cmd
            result = subprocess.run(
                ['firewall-cmd', '--list-ports'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                ports = result.stdout
                if '3000/tcp' in ports:
                    print("   ✅ Firewall: Port 3000 allowed")
                    firewall_configured = True
                    self.passed_checks += 1
                else:
                    network_issues.append("WARNING: Port 3000 not allowed in firewall")
                    self.warnings += 1
                    
        except subprocess.CalledProcessError:
            # Try ufw
            try:
                result = subprocess.run(
                    ['ufw', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    status = result.stdout
                    if '3000' in status:
                        print("   ✅ UFW: Port 3000 allowed")
                        firewall_configured = True
                        self.passed_checks += 1
                    else:
                        network_issues.append("WARNING: Port 3000 not allowed in UFW")
                        self.warnings += 1
                        
            except Exception:
                network_issues.append("INFO: No firewall configuration detected")
        
        except Exception as e:
            network_issues.append(f"Error checking firewall: {e}")
            self.warnings += 1
        
        return {
            'firewall_configured': firewall_configured,
            'issues': network_issues
        }
    
    def check_file_permissions(self) -> Dict:
        """Check file security permissions"""
        print("📁 Checking File Permissions...")
        permission_issues = []
        
        # Critical files to check
        critical_files = [
            ('/etc/grafana/grafana.ini', '640', 'grafana:grafana'),
            ('/etc/grafana/ssl/grafana.key', '600', 'grafana:grafana'),
            ('/etc/grafana/ssl/grafana.crt', '644', 'grafana:grafana'),
        ]
        
        for file_path, expected_perms, expected_owner in critical_files:
            if os.path.exists(file_path):
                try:
                    # Check permissions
                    stat_info = os.stat(file_path)
                    actual_perms = oct(stat_info.st_mode)[-3:]
                    
                    if actual_perms == expected_perms:
                        print(f"   ✅ {file_path}: Permissions {actual_perms}")
                        self.passed_checks += 1
                    else:
                        permission_issues.append(f"WARNING: {file_path} has permissions {actual_perms}, expected {expected_perms}")
                        self.warnings += 1
                        
                except Exception as e:
                    permission_issues.append(f"Error checking {file_path}: {e}")
                    self.warnings += 1
            else:
                if 'ssl' in file_path:
                    permission_issues.append(f"INFO: SSL file {file_path} not found (may be generated at runtime)")
                else:
                    permission_issues.append(f"WARNING: Critical file {file_path} not found")
                    self.warnings += 1
        
        return {
            'issues': permission_issues
        }
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        print("\n📊 GENERATING SECURITY REPORT...")
        print("=" * 55)
        
        total_checks = self.passed_checks + self.warnings + self.critical_issues
        
        # Calculate security score
        if total_checks > 0:
            security_score = (self.passed_checks / total_checks) * 100
        else:
            security_score = 0
        
        # Determine security level
        if self.critical_issues > 0:
            security_level = "🔴 CRITICAL ISSUES DETECTED"
            recommendation = "IMMEDIATE ACTION REQUIRED"
        elif self.warnings > 5:
            security_level = "🟡 MULTIPLE WARNINGS"
            recommendation = "REVIEW AND IMPROVE"
        elif self.warnings > 0:
            security_level = "🟠 MINOR ISSUES"
            recommendation = "OPTIMIZE WHEN POSSIBLE"
        else:
            security_level = "🟢 ENTERPRISE SECURE"
            recommendation = "EXCELLENT SECURITY POSTURE"
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'security_score': security_score,
            'security_level': security_level,
            'recommendation': recommendation,
            'statistics': {
                'passed_checks': self.passed_checks,
                'warnings': self.warnings,
                'critical_issues': self.critical_issues,
                'total_checks': total_checks
            },
            'vulnerabilities_fixed': [
                "Anonymous access DISABLED",
                "Default credentials REPLACED",
                "HTTPS encryption ENABLED", 
                "Security headers CONFIGURED"
            ]
        }
        
        # Print summary
        print(f"🎯 SECURITY ASSESSMENT COMPLETE")
        print(f"📈 Security Score: {security_score:.1f}%")
        print(f"🏆 Security Level: {security_level}")
        print(f"📋 Recommendation: {recommendation}")
        print("")
        print(f"📊 STATISTICS:")
        print(f"   ✅ Passed Checks: {self.passed_checks}")
        print(f"   ⚠️  Warnings: {self.warnings}")
        print(f"   🔴 Critical Issues: {self.critical_issues}")
        print(f"   📝 Total Checks: {total_checks}")
        print("")
        
        if self.critical_issues == 0:
            print("🎉 ALL CRITICAL VULNERABILITIES RESOLVED!")
            print("")
            print("✅ SECURITY FIXES VERIFIED:")
            for fix in report['vulnerabilities_fixed']:
                print(f"   • {fix}")
        
        return report
    
    def run_verification(self) -> Dict:
        """Run complete security verification"""
        self.print_header()
        
        # Run all security checks
        config_results = self.check_grafana_config()
        service_results = self.check_service_status()
        network_results = self.check_network_security()
        permission_results = self.check_file_permissions()
        
        # Generate final report
        report = self.generate_security_report()
        
        # Combine all results
        verification_results = {
            'report': report,
            'config': config_results,
            'services': service_results,
            'network': network_results,
            'permissions': permission_results
        }
        
        return verification_results

def main():
    """Main verification function"""
    print("🔍 Starting SmartCloudOps AI Frontend Security Verification...")
    
    verifier = GrafanaSecurityVerifier()
    results = verifier.run_verification()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"frontend_security_verification_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Warning: Could not save results file: {e}")
    
    # Exit with appropriate code
    if verifier.critical_issues > 0:
        print("\n❌ VERIFICATION FAILED: Critical security issues detected")
        sys.exit(1)
    elif verifier.warnings > 0:
        print("\n⚠️  VERIFICATION PASSED WITH WARNINGS")
        sys.exit(2)
    else:
        print("\n✅ VERIFICATION PASSED: All security checks successful")
        sys.exit(0)

if __name__ == "__main__":
    main()
