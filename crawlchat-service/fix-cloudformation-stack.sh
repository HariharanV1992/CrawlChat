#!/bin/bash

# Fix CloudFormation Stack in ROLLBACK_COMPLETE state
# This script deletes the failed stack and redeploys it

set -e

# Configuration
AWS_REGION="ap-south-1"
STACK_NAME="crawlchat-complete-stack"
S3_BUCKET="crawlchat-data"
DOMAIN_NAME="api.crawlchat.site"

echo "🔧 Fixing CloudFormation stack in ROLLBACK_COMPLETE state..."

# Check if stack exists and get its status
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "STACK_NOT_FOUND")

echo "📋 Current stack status: $STACK_STATUS"

if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "🗑️  Deleting failed stack..."
    aws cloudformation delete-stack \
        --stack-name $STACK_NAME \
        --region $AWS_REGION
    
    echo "⏳ Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name $STACK_NAME \
        --region $AWS_REGION
    
    echo "✅ Stack deleted successfully"
elif [ "$STACK_STATUS" = "STACK_NOT_FOUND" ]; then
    echo "ℹ️  Stack does not exist - will create new one"
else
    echo "⚠️  Stack is in state: $STACK_STATUS"
    echo "   This script only handles ROLLBACK_COMPLETE state"
    exit 1
fi

# Create S3 bucket for deployment (if it doesn't exist)
echo "🪣 Ensuring S3 bucket exists..."
aws s3api create-bucket \
    --bucket $S3_BUCKET \
    --region $AWS_REGION \
    --create-bucket-configuration LocationConstraint=$AWS_REGION \
    2>/dev/null || echo "Bucket already exists"

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $S3_BUCKET \
    --versioning-configuration Status=Enabled

echo "✅ S3 bucket ready"

# Get the latest Lambda image URI
echo "🔍 Getting latest Lambda image URI..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="crawlchat-api-function"
LATEST_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"

echo "📋 Using image: $LATEST_IMAGE_URI"

# Deploy the stack
echo "🏗️  Deploying new infrastructure stack..."
aws cloudformation deploy \
    --template-file infra/crawlchat-complete-infrastructure.yml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        LambdaImageUri=$LATEST_IMAGE_URI \
        DomainName=$DOMAIN_NAME \
        CertificateArn=$CERTIFICATE_ARN \
    --region $AWS_REGION

echo "✅ Infrastructure deployed successfully"

# Get deployment outputs
echo "📋 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

CUSTOM_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CustomDomainUrl`].OutputValue' \
    --output text)

echo "🎉 Deployment completed successfully!"
echo "📋 Summary:"
echo "   - Stack: $STACK_NAME"
echo "   - Region: $AWS_REGION"
echo "   - API Gateway URL: $API_URL"
echo "   - Custom Domain: $CUSTOM_URL"
echo "   - Lambda Image: $LATEST_IMAGE_URI" 