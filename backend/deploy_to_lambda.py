#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartDocAI Backend Deployment Script
Tự động: Build Docker -> Push ECR -> Update Lambda

Usage:
  python deploy_to_lambda.py
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sys
import subprocess
import boto3
import time
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

FUNCTION_NAME = "smartdocai"
REPOSITORY_NAME = "smartdocai"
REGION = "us-east-1"
IMAGE_TAG = "latest"
BACKEND_DIR = Path(__file__).parent

# ============================================================================
# Main Deployment Script
# ============================================================================

def run_command(cmd, description=""):
    """Run shell command and return success status"""
    if description:
        print(f"\n[INFO] {description}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.stdout:
            for line in result.stdout.split('\n')[-10:]:
                if line.strip():
                    print(f"  {line}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("🚀 SmartDocAI Backend Deployment to AWS Lambda")
    print("=" * 80)
    print()
    
    # Step 1: Get AWS Account ID
    print("[STEP 1/5] Getting AWS Account ID...")
    try:
        sts = boto3.client('sts', region_name=REGION)
        account_id = sts.get_caller_identity()['Account']
        ECR_REGISTRY = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com"
        IMAGE_URI = f"{ECR_REGISTRY}/{REPOSITORY_NAME}:{IMAGE_TAG}"
        print(f"✓ Account: {account_id}")
        print(f"✓ Registry: {ECR_REGISTRY}")
        print(f"✓ Image URI: {IMAGE_URI}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    # Step 2: Check ECR Repository
    print("\n[STEP 2/5] Checking ECR Repository...")
    try:
        ecr = boto3.client('ecr', region_name=REGION)
        try:
            ecr.describe_repositories(repositoryNames=[REPOSITORY_NAME])
            print(f"✓ Repository '{REPOSITORY_NAME}' exists")
        except ecr.exceptions.RepositoryNotFoundException:
            print(f"  Creating repository '{REPOSITORY_NAME}'...")
            ecr.create_repository(repositoryName=REPOSITORY_NAME)
            print(f"✓ Repository created!")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    # Step 3: Build Docker image
    print("\n[STEP 3/5] Building Docker image...")
    # Disable BuildKit to use Docker format (not OCI) for Lambda compatibility
    build_env = os.environ.copy()
    build_env['DOCKER_BUILDKIT'] = '0'
    
    try:
        result = subprocess.run(
            f"docker build --platform linux/amd64 -t {IMAGE_URI} .",
            shell=True,
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=build_env
        )
        
        if result.returncode == 0:
            print("  [Building...] Please wait ~3 minutes for dependencies")
            print("✓ Docker image built!")
        else:
            print(f"✗ Docker build failed!")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"✗ Build error: {e}")
        sys.exit(1)
    
    # Step 4: Push to ECR
    print("\n[STEP 4/5] Pushing image to ECR...")
    
    # ECR login
    try:
        auth_response = ecr.get_authorization_token()
        auth_data = auth_response['authorizationData'][0]
        
        import base64
        credentials = base64.b64decode(auth_data['authorizationToken']).decode()
        username, password = credentials.split(':')
        
        cmd = f"docker login --username {username} --password {password} {ECR_REGISTRY}"
        if not run_command(cmd, "Logging in to ECR..."):
            print("✗ ECR login failed!")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    # Push image
    cmd = f"docker push {IMAGE_URI}"
    if not run_command(cmd, "Pushing image to ECR..."):
        print("✗ Docker push failed!")
        sys.exit(1)
    
    # Get image digest from ECR
    print("\n  Waiting for ECR to stabilize...")
    time.sleep(5)
    
    try:
        response = ecr.describe_images(repositoryName=REPOSITORY_NAME)
        if response['imageDetails']:
            # Get latest pushed image
            latest_image = max(
                response['imageDetails'],
                key=lambda x: x['imagePushedAt']
            )
            image_digest = latest_image['imageDigest']
            print(f"✓ Image pushed! Digest: {image_digest[:12]}...")
        else:
            print("✗ No images found in ECR!")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error getting digest: {e}")
        sys.exit(1)
    
    # Step 5: Update Lambda
    print("\n[STEP 5/5] Updating Lambda function...")
    try:
        # Use specific digest instead of :latest tag
        image_uri_with_digest = f"{ECR_REGISTRY}/{REPOSITORY_NAME}@{image_digest}"
        
        lambda_client = boto3.client('lambda', region_name=REGION)
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ImageUri=image_uri_with_digest
        )
        
        print(f"✓ Lambda function updated!")
        print(f"  Function: {response['FunctionName']}")
        print(f"  CodeSha256: {response['CodeSha256'][:16]}...")
        print(f"  State: {response['State']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    # Success
    print()
    print("=" * 80)
    print("✅ DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Backend deployed to AWS Lambda!")
    print()
    print("Next steps:")
    print("  1. Test your backend endpoints")
    print("  2. Update frontend API_BASE_URL if needed")
    print("  3. Redeploy frontend")
    print()


if __name__ == "__main__":
    main()
