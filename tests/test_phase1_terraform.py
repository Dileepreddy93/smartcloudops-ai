from pathlib import Path


def read_tf() -> str:
    tf_path = Path("terraform/main.tf")
    assert tf_path.exists(), "terraform/main.tf not found"
    return tf_path.read_text(encoding="utf-8")


def test_vpc_and_subnets_defined():
    content = read_tf()
    assert 'resource "aws_vpc" "main"' in content
    assert 'cidr_block           = "10.0.0.0/16"' in content
    assert 'resource "aws_subnet" "public_1"' in content
    assert 'cidr_block              = "10.0.1.0/24"' in content
    assert 'resource "aws_subnet" "public_2"' in content
    assert 'cidr_block              = "10.0.2.0/24"' in content


def test_security_groups_hardened_ports():
    content = read_tf()
    # Prometheus 9090 restricted
    assert 'from_port   = 9090' in content
    # Grafana 3000 restricted
    assert 'from_port   = 3000' in content
    # Node Exporter internal 9100
    assert 'from_port   = 9100' in content


