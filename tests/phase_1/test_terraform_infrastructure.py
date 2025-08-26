"""
Phase 1: Terraform Infrastructure Tests
Tests for VPC, subnets, security groups, and core infrastructure components.
"""

import pytest
from pathlib import Path


class TestTerraformInfrastructure:
    """Test suite for Terraform infrastructure configuration."""

    @pytest.fixture(scope="class")
    def terraform_content(self):
        """Arrange: Load Terraform main.tf content."""
        tf_path = Path("terraform/main.tf")
        assert tf_path.exists(), "terraform/main.tf not found"
        return tf_path.read_text(encoding="utf-8")

    def test_vpc_configuration(self, terraform_content):
        """Test VPC configuration and CIDR block."""
        # Arrange: Define expected VPC configuration
        expected_cidr = "10.0.0.0/16"

        # Act: Check VPC resource definition
        assert 'resource "aws_vpc" "main"' in terraform_content
        assert f'cidr_block           = "{expected_cidr}"' in terraform_content
        assert "enable_dns_hostnames = true" in terraform_content
        assert "enable_dns_support   = true" in terraform_content

    def test_public_subnets_configuration(self, terraform_content):
        """Test public subnets configuration."""
        # Arrange: Define expected subnet configurations
        expected_subnets = [("public_1", "10.0.1.0/24"), ("public_2", "10.0.2.0/24")]

        # Act & Assert: Check each subnet
        for subnet_name, cidr in expected_subnets:
            assert f'resource "aws_subnet" "{subnet_name}"' in terraform_content
            assert f'cidr_block              = "{cidr}"' in terraform_content
            assert "map_public_ip_on_launch = true" in terraform_content

    def test_security_groups_hardened_ports(self, terraform_content):
        """Test security group port configurations."""
        # Arrange: Define expected port configurations
        expected_ports = {
            "9090": "Prometheus",
            "3000": "Grafana",
            "9100": "Node Exporter",
            "5000": "Flask Application",
            "80": "HTTP",
            "443": "HTTPS",
        }

        # Act & Assert: Check each port is properly configured
        for port, service in expected_ports.items():
            assert (
                f"from_port   = {port}" in terraform_content
            ), f"Port {port} ({service}) not found"

    def test_internet_gateway_configuration(self, terraform_content):
        """Test Internet Gateway configuration."""
        # Act & Assert: Check IGW resource
        assert 'resource "aws_internet_gateway" "main"' in terraform_content
        assert "vpc_id = aws_vpc.main.id" in terraform_content

    def test_route_table_configuration(self, terraform_content):
        """Test route table configuration."""
        # Act & Assert: Check route table
        assert 'resource "aws_route_table" "public"' in terraform_content
        assert 'cidr_block = "0.0.0.0/0"' in terraform_content
        assert "gateway_id = aws_internet_gateway.main.id" in terraform_content

    def test_ec2_instances_configuration(self, terraform_content):
        """Test EC2 instances are configured correctly."""
        # Check for production-ready instance types (not free tier)
        assert 'instance_type          = var.monitoring_instance_type' in terraform_content
        assert 'instance_type          = var.application_instance_type' in terraform_content
        
        # Check for proper variable definitions
        assert 'monitoring_instance_type' in terraform_content
        assert 'application_instance_type' in terraform_content

    def test_s3_buckets_configuration(self, terraform_content):
        """Test S3 buckets configuration."""
        # Act & Assert: Check ML models and logs buckets
        assert 'resource "aws_s3_bucket" "ml_models"' in terraform_content
        assert 'resource "aws_s3_bucket" "logs"' in terraform_content
        assert 'resource "aws_s3_bucket_versioning"' in terraform_content
        assert (
            'resource "aws_s3_bucket_server_side_encryption_configuration"'
            in terraform_content
        )

    def test_iam_roles_and_policies(self, terraform_content):
        """Test IAM roles and policies configuration."""
        # Act & Assert: Check IAM resources
        assert 'resource "aws_iam_role" "ec2_role"' in terraform_content
        assert 'resource "aws_iam_policy" "ec2_policy"' in terraform_content
        assert 'resource "aws_iam_instance_profile" "ec2_profile"' in terraform_content

    def test_cloudwatch_log_groups(self, terraform_content):
        """Test CloudWatch log groups configuration."""
        # Act & Assert: Check log groups
        assert 'resource "aws_cloudwatch_log_group" "application"' in terraform_content
        assert 'resource "aws_cloudwatch_log_group" "monitoring"' in terraform_content
        assert "retention_in_days = 7" in terraform_content  # Free tier optimization

    def test_terraform_version_and_providers(self, terraform_content):
        """Test Terraform version and provider configuration."""
        # Act & Assert: Check Terraform configuration
        assert 'required_version = ">= 1.0"' in terraform_content
        assert 'source  = "hashicorp/aws"' in terraform_content
        assert 'version = "~> 5.0"' in terraform_content

    def test_security_hardening_features(self, terraform_content):
        """Test security hardening features."""
        # Act & Assert: Check security features
        assert 'dynamic "ingress"' in terraform_content  # Dynamic security groups
        assert "allowed_ssh_cidrs" in terraform_content  # Restricted SSH access
        assert "admin_ip_cidr" in terraform_content  # Admin access control
        assert (
            'description = "SSH access from authorized networks only"'
            in terraform_content
        )
