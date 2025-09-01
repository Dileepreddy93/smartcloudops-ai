#!/usr/bin/env python3
"""
Generate IAM policies required for this repository with least privilege.

Outputs JSON documents for:
- Terraform backend access (S3 state bucket + DynamoDB lock table)
- Developer profile: minimal set to run terraform plan/apply for resources in this repo

Usage:
  python scripts/generate_iam_policies.py \
    --state-bucket smartcloudops-terraform-state \
    --lock-table terraform-locks \
    --region us-east-1

The script prints JSON to stdout. Use --out-dir to write files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def build_backend_policy(state_bucket: str, lock_table: str, region: str, account_id: str | None) -> dict:
    bucket_arn = f"arn:aws:s3:::{state_bucket}"
    bucket_objects_arn = f"{bucket_arn}/*"
    table_arn = f"arn:aws:dynamodb:{region}:{account_id or '*'}:table/{lock_table}"

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TerraformStateBucketList",
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": bucket_arn,
            },
            {
                "Sid": "TerraformStateObjectRW",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                    "s3:ListBucketMultipartUploads",
                ],
                "Resource": bucket_objects_arn,
            },
            {
                "Sid": "TerraformDynamoDBLock",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:DescribeTable",
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Scan",
                ],
                "Resource": table_arn,
            },
        ],
    }


def build_dev_policy(region: str, account_id: str | None) -> dict:
    # Minimal permissions commonly required by Terraform to manage resources here.
    # Scope by account and region where possible.
    account_scope = account_id or "*"
    region_scope = region or "*"
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ReadIdentity",
                "Effect": "Allow",
                "Action": ["sts:GetCallerIdentity"],
                "Resource": "*",
            },
            {
                "Sid": "S3Describe",
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets",
                    "s3:GetAccountPublicAccessBlock",
                ],
                "Resource": "*",
            },
            {
                "Sid": "EC2Describe",
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                ],
                "Resource": "*",
            },
            {
                "Sid": "AllowResourceManagement",
                "Effect": "Allow",
                "Action": [
                    "ec2:*",
                    "elasticloadbalancing:*",
                    "iam:PassRole",
                    "iam:GetRole",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:CreateInstanceProfile",
                    "iam:DeleteInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:RemoveRoleFromInstanceProfile",
                    "s3:*",
                    "cloudwatch:*",
                    "logs:*",
                    "dynamodb:*",
                    "rds:*",
                    "elasticache:*",
                    "acm:*",
                    "guardduty:*",
                ],
                "Resource": f"arn:aws:*:{account_scope}:*/*",
                "Condition": {
                    "StringEquals": {
                        "aws:RequestedRegion": region_scope,
                    }
                },
            },
        ],
    }


def load_account_id_from_env() -> str | None:
    return os.environ.get("AWS_ACCOUNT_ID") or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate IAM policies JSON for SmartCloudOps")
    parser.add_argument("--state-bucket", required=True, help="Terraform S3 state bucket name")
    parser.add_argument("--lock-table", required=True, help="DynamoDB table for Terraform locks")
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--account-id", default=load_account_id_from_env(), help="AWS Account ID")
    parser.add_argument("--out-dir", default=None, help="Directory to write JSON files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend = build_backend_policy(args.state_bucket, args.lock_table, args.region, args.account_id)
    dev = build_dev_policy(args.region, args.account_id)

    if args.out_dir:
        out_path = Path(args.out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "terraform_backend_policy.json").write_text(json.dumps(backend, indent=2))
        (out_path / "smartcloudops_dev_policy.json").write_text(json.dumps(dev, indent=2))
        print(f"Wrote policies to {out_path}")
    else:
        print(json.dumps({
            "terraform_backend_policy": backend,
            "developer_policy": dev,
        }, indent=2))


if __name__ == "__main__":
    main()


