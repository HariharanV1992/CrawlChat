#!/bin/bash
# Script to create the missing crawler Lambda function

set -e

# Configuration
REGION="ap-south-1"
FUNCTION_NAME="crawlchat-crawler-function"
ROLE_NAME="crawlchat-crawler-role"
ECR_REPO="crawlchat-crawler"

echo "🔧 Creating Crawler Lambda Function..."

# 1. Create IAM role for the crawler function
echo "📋 Creating IAM role..."
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }' 2>/dev/null || echo "Role already exists"

# 2. Attach basic Lambda execution policy
echo "🔐 Attaching execution policy..."
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 3. Create custom policy for crawler permissions
echo "📝 Creating custom policy..."
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name CrawlerPermissions \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::crawlchat-data",
          "arn:aws:s3:::crawlchat-data/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        "Resource": "*"
      }
    ]
  }'

# 4. Wait for role to be available
echo "⏳ Waiting for role to be available..."
sleep 10

# 5. Get the role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "🎯 Role ARN: $ROLE_ARN"

# 6. Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPO --region $REGION

# 7. Get ECR registry
ECR_REGISTRY=$(aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin 169164939839.dkr.ecr.$REGION.amazonaws.com 2>/dev/null && echo "169164939839.dkr.ecr.$REGION.amazonaws.com" || echo "Failed to get ECR registry")

# 8. Build and push crawler image
echo "🏗️ Building crawler Docker image..."
# Copy requirements file for Docker build
cp crawler-service/requirements.txt crawler-service/requirements-lambda.txt
docker build -f crawler-service/Dockerfile -t $ECR_REGISTRY/$ECR_REPO:latest .
docker push $ECR_REGISTRY/$ECR_REPO:latest

# 9. Create Lambda function
echo "🚀 Creating Lambda function..."
aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --package-type Image \
  --code ImageUri=$ECR_REGISTRY/$ECR_REPO:latest \
  --role $ROLE_ARN \
  --memory-size 1024 \
  --timeout 60 \
  --region $REGION

echo "✅ Crawler Lambda function created successfully!"
echo "📋 Function details:"
echo "   Name: $FUNCTION_NAME"
echo "   Memory: 1024MB"
echo "   Timeout: 60 seconds"
echo "   Role: $ROLE_NAME"
echo "   Image: $ECR_REGISTRY/$ECR_REPO:latest"

echo ""
echo "🎉 Your CrawlChat system now has all 3 services:"
echo "   1. ✅ API Service (crawlchat-api-function)"
echo "   2. ✅ Crawler Service (crawlchat-crawler-function)"
echo "   3. ✅ Preprocessor Service (crawlchat-preprocessor - ECR ready)" 