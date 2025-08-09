#!/usr/bin/env python3
"""
SmartCloudOps AI - Phase 3 Security Assessment
Validates Phase 3 implementation and provides security score
"""

import subprocess
import json
import sys
import os
from datetime import datetime

class Phase3SecurityAssessment:
    """Comprehensive security assessment for Phase 3 implementation"""
    
    def __init__(self):
        self.score = 0
        self.max_score = 100
        self.findings = []
        self.recommendations = []
    
    def check_terraform_configuration(self):
        """Check Terraform configuration validity"""
        print("🔧 Checking Terraform Configuration...")
        
        try:
            result = subprocess.run(['terraform', 'validate'], 
                                  capture_output=True, text=True, cwd='/home/dileep-reddy/smartcloudops-ai/terraform')
            if result.returncode == 0:
                self.score += 10
                self.findings.append("✅ Terraform configuration is valid")
            else:
                self.findings.append("❌ Terraform validation failed")
                self.recommendations.append("Fix Terraform configuration errors")
        except Exception as e:
            self.findings.append(f"❌ Cannot run Terraform validation: {e}")
            self.recommendations.append("Install Terraform and ensure it's in PATH")
    
    def check_https_configuration(self):
        """Check HTTPS/TLS configuration"""
        print("🔒 Checking HTTPS/TLS Configuration...")
        
        # Check if HTTPS is configured in Terraform
        tfvars_file = '/home/dileep-reddy/smartcloudops-ai/terraform/terraform-phase3.tfvars'
        if os.path.exists(tfvars_file):
            with open(tfvars_file, 'r') as f:
                content = f.read()
                if 'enable_https = true' in content:
                    self.score += 15
                    self.findings.append("✅ HTTPS enabled in configuration")
                else:
                    self.findings.append("⚠️ HTTPS not enabled in configuration")
                    self.recommendations.append("Set enable_https = true in terraform-phase3.tfvars")
        else:
            self.findings.append("❌ Phase 3 configuration file not found")
            self.recommendations.append("Create terraform-phase3.tfvars with HTTPS configuration")
    
    def check_secrets_management(self):
        """Check secrets management configuration"""
        print("🔐 Checking Secrets Management...")
        
        # Check if secrets manager is configured
        tfvars_file = '/home/dileep-reddy/smartcloudops-ai/terraform/terraform-phase3.tfvars'
        if os.path.exists(tfvars_file):
            with open(tfvars_file, 'r') as f:
                content = f.read()
                if 'enable_secrets_manager = true' in content:
                    self.score += 15
                    self.findings.append("✅ Secrets Manager enabled in configuration")
                else:
                    self.findings.append("⚠️ Secrets Manager not enabled")
                    self.recommendations.append("Set enable_secrets_manager = true")
        
        # Check if secrets integration script exists
        secrets_script = '/home/dileep-reddy/smartcloudops-ai/app/secrets_manager.py'
        if os.path.exists(secrets_script):
            self.score += 5
            self.findings.append("✅ Secrets Manager integration script created")
        else:
            self.findings.append("❌ Secrets Manager integration script missing")
            self.recommendations.append("Create secrets_manager.py integration script")
    
    def check_advanced_monitoring(self):
        """Check advanced monitoring configuration"""
        print("📊 Checking Advanced Monitoring...")
        
        tfvars_file = '/home/dileep-reddy/smartcloudops-ai/terraform/terraform-phase3.tfvars'
        if os.path.exists(tfvars_file):
            with open(tfvars_file, 'r') as f:
                content = f.read()
                if 'enable_advanced_monitoring = true' in content:
                    self.score += 15
                    self.findings.append("✅ Advanced monitoring enabled")
                else:
                    self.findings.append("⚠️ Advanced monitoring not enabled")
                    self.recommendations.append("Set enable_advanced_monitoring = true")
                
                if 'enable_waf = true' in content:
                    self.score += 10
                    self.findings.append("✅ Web Application Firewall enabled")
                else:
                    self.findings.append("⚠️ WAF not enabled")
                    self.recommendations.append("Set enable_waf = true for enhanced security")
    
    def check_network_security(self):
        """Check network security configuration from Phase 2"""
        print("🛡️ Checking Network Security...")
        
        tfvars_file = '/home/dileep-reddy/smartcloudops-ai/terraform/terraform-phase3.tfvars'
        if os.path.exists(tfvars_file):
            with open(tfvars_file, 'r') as f:
                content = f.read()
                
                # Check if IP restrictions are configured
                if 'allowed_ssh_cidrs' in content and '203.0.113' not in content:
                    self.score += 10
                    self.findings.append("✅ SSH access restrictions configured")
                else:
                    self.findings.append("⚠️ Configure actual IP ranges for SSH access")
                    self.recommendations.append("Replace example IPs with actual authorized networks")
                
                if 'allowed_app_cidrs' in content:
                    self.score += 10
                    self.findings.append("✅ Application access restrictions configured")
                else:
                    self.findings.append("❌ Application access restrictions not configured")
                    self.recommendations.append("Configure allowed_app_cidrs with authorized networks")
    
    def check_authentication_system(self):
        """Check authentication system from Phase 2"""
        print("🔑 Checking Authentication System...")
        
        # Check if auth module exists
        auth_file = '/home/dileep-reddy/smartcloudops-ai/app/auth.py'
        if os.path.exists(auth_file):
            self.score += 10
            self.findings.append("✅ Authentication module exists")
            
            # Check if API keys are generated
            keys_file = '/home/dileep-reddy/smartcloudops-ai/api_keys_db.json'
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    try:
                        keys_data = json.load(f)
                        if len(keys_data) > 0:
                            self.score += 5
                            self.findings.append(f"✅ API keys database with {len(keys_data)} keys")
                        else:
                            self.findings.append("⚠️ API keys database is empty")
                            self.recommendations.append("Generate API keys using scripts/simple_key_generator.py")
                    except Exception:
                        self.findings.append("❌ Invalid API keys database format")
                        self.recommendations.append("Regenerate API keys database")
            else:
                self.findings.append("❌ API keys database not found")
                self.recommendations.append("Generate API keys using scripts/simple_key_generator.py")
        else:
            self.findings.append("❌ Authentication module missing")
            self.recommendations.append("Create authentication module (auth.py)")
    
    def check_documentation(self):
        """Check if proper documentation exists"""
        print("📚 Checking Documentation...")
        
        docs = [
            ('PHASE3_IMPLEMENTATION_GUIDE.md', 'Phase 3 implementation guide'),
            ('API_KEYS_SETUP.md', 'API keys setup guide'),
            ('NETWORK_SECURITY_GUIDE.md', 'Network security guide'),
            ('PHASE2_IMPLEMENTATION_COMPLETE.md', 'Phase 2 completion documentation')
        ]
        
        doc_score = 0
        for doc_file, desc in docs:
            if os.path.exists(f'/home/dileep-reddy/smartcloudops-ai/{doc_file}'):
                doc_score += 2
                self.findings.append(f"✅ {desc} exists")
            else:
                self.findings.append(f"❌ Missing {desc}")
                self.recommendations.append(f"Create {doc_file}")
        
        self.score += doc_score
    
    def check_deployment_readiness(self):
        """Check if deployment artifacts are ready"""
        print("🚀 Checking Deployment Readiness...")
        
        # Check Docker image
        try:
            result = subprocess.run(['docker', 'images', 'smartcloudops-ai:auth-v1.0'], 
                                  capture_output=True, text=True)
            if 'smartcloudops-ai' in result.stdout:
                self.score += 5
                self.findings.append("✅ Docker image with authentication built")
            else:
                self.findings.append("❌ Docker image not found")
                self.recommendations.append("Build Docker image: docker build -t smartcloudops-ai:auth-v1.0 .")
        except Exception:
            self.findings.append("❌ Cannot check Docker images")
            self.recommendations.append("Install Docker and build application image")
    
    def generate_security_score(self):
        """Generate final security score and recommendations"""
        percentage = (self.score / self.max_score) * 100
        
        if percentage >= 90:
            grade = "A+ (Enterprise Ready)"
            status = "🏆 EXCELLENT"
        elif percentage >= 80:
            grade = "A (Production Ready)"
            status = "🟢 GREAT"
        elif percentage >= 70:
            grade = "B (Good Progress)"
            status = "🟡 GOOD"
        elif percentage >= 60:
            grade = "C (Needs Improvement)"
            status = "🟠 FAIR"
        else:
            grade = "D (Significant Issues)"
            status = "🔴 POOR"
        
        return {
            'score': self.score,
            'max_score': self.max_score,
            'percentage': percentage,
            'grade': grade,
            'status': status
        }
    
    def run_assessment(self):
        """Run complete Phase 3 security assessment"""
        print("🔒 SMARTCLOUDOPS AI - PHASE 3 SECURITY ASSESSMENT")
        print("=" * 60)
        print(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all checks
        self.check_terraform_configuration()
        self.check_https_configuration()
        self.check_secrets_management()
        self.check_advanced_monitoring()
        self.check_network_security()
        self.check_authentication_system()
        self.check_documentation()
        self.check_deployment_readiness()
        
        # Generate final score
        score_data = self.generate_security_score()
        
        print("\n" + "=" * 60)
        print("📋 ASSESSMENT RESULTS")
        print("=" * 60)
        
        print(f"\n🎯 SECURITY SCORE: {score_data['score']}/{score_data['max_score']} ({score_data['percentage']:.1f}%)")
        print(f"🏅 GRADE: {score_data['grade']}")
        print(f"📊 STATUS: {score_data['status']}")
        
        print(f"\n✅ FINDINGS ({len(self.findings)}):")
        for finding in self.findings:
            print(f"   {finding}")
        
        if self.recommendations:
            print(f"\n🔧 RECOMMENDATIONS ({len(self.recommendations)}):")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "=" * 60)
        print("🚀 PHASE 3 IMPLEMENTATION STATUS")
        print("=" * 60)
        
        phase3_features = [
            ("HTTPS/TLS", "🔒", "End-to-end encryption"),
            ("Secrets Management", "🔐", "AWS Secrets Manager integration"),
            ("Advanced Monitoring", "📊", "CloudTrail, GuardDuty, VPC Flow Logs"),
            ("Web Application Firewall", "🛡️", "WAF protection"),
            ("Network Security", "🛡️", "IP whitelisting and access control"),
            ("API Authentication", "🔑", "Multi-tier API key system"),
            ("Documentation", "📚", "Complete implementation guides"),
            ("Deployment", "🚀", "Production-ready artifacts")
        ]
        
        for feature, icon, desc in phase3_features:
            # Simple check based on score components
            if "✅" in str([f for f in self.findings if feature.lower() in f.lower()]):
                status = "✅ IMPLEMENTED"
            elif "⚠️" in str([f for f in self.findings if feature.lower() in f.lower()]):
                status = "⚠️ PARTIAL"
            else:
                status = "❌ PENDING"
            
            print(f"   {icon} {feature:<20} {status:<15} {desc}")
        
        # Next steps based on score
        print("\n" + "=" * 60)
        print("🎯 NEXT STEPS")
        print("=" * 60)
        
        if score_data['percentage'] >= 90:
            print("🎉 Congratulations! Phase 3 implementation is excellent.")
            print("   Ready for production deployment and enterprise sales.")
            print("   Consider scheduling regular security assessments.")
        elif score_data['percentage'] >= 80:
            print("🟢 Great progress! Address remaining recommendations.")
            print("   Focus on any missing critical security features.")
            print("   Consider compliance audit preparation.")
        else:
            print("🔧 Complete the high-priority recommendations above.")
            print("   Focus on HTTPS, secrets management, and monitoring.")
            print("   Re-run assessment after implementing fixes.")
        
        return score_data

def main():
    """Main assessment function"""
    try:
        assessment = Phase3SecurityAssessment()
        result = assessment.run_assessment()
        
        # Exit with appropriate code
        if result['percentage'] >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Needs improvement
            
    except Exception as e:
        print(f"\n💥 Assessment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
