#!/bin/bash

# Fresh Deployment Script for CrawlChat
# This script completely removes the failed stack and redeploys everything

set -e

# Configuration
AWS_REGION="ap-south-1"
STACK_NAME="crawlchat-complete-stack"
FUNCTION_NAME="crawlchat-crawl-worker"
ECR_REPOSITORY="crawlchat-api-function"

echo "🚀 Starting Fresh CrawlChat Deployment"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Check and delete the failed stack
echo "🔍 Checking CloudFormation stack status..."
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "STACK_NOT_FOUND")

echo "📋 Current stack status: $STACK_STATUS"

if [ "$STACK_STATUS" != "STACK_NOT_FOUND" ]; then
    echo "🗑️  Deleting existing stack..."
    aws cloudformation delete-stack \
        --stack-name $STACK_NAME \
        --region $AWS_REGION
    
    echo "⏳ Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name $STACK_NAME \
        --region $AWS_REGION
    
    echo "✅ Stack deleted successfully"
else
    echo "ℹ️  No existing stack found"
fi

# Step 2: Build and push Docker image
echo "🐳 Building Docker image..."
cd crawler-service
docker build -t $ECR_REPOSITORY:latest .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📤 Pushing image to ECR..."
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

echo "✅ Docker image pushed successfully"

# Step 3: Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
cd ..
IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"

aws cloudformation deploy \
    --template-file infra/crawlchat-complete-infrastructure.yml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        LambdaImageUri=$IMAGE_URI \
        DomainName="api.crawlchat.site" \
    --region $AWS_REGION

echo "✅ Infrastructure deployed successfully"

# Step 4: Get outputs
echo "📋 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
    --output text)

echo "🎉 Deployment completed successfully!"
echo "📋 Summary:"
echo "   - Stack: $STACK_NAME"
echo "   - Region: $AWS_REGION"
echo "   - API Gateway URL: $API_URL"
echo "   - S3 Bucket: $S3_BUCKET"
echo "   - Lambda Function: $FUNCTION_NAME"
echo "   - Docker Image: $IMAGE_URI"

# Step 5: Test the deployment
echo "🧪 Testing the deployment..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"url": "https://example.com", "content_type": "generic"}' \
    --region $AWS_REGION \
    response.json

echo "📄 Lambda response:"
cat response.json
rm response.json

echo "✅ Deployment and test completed successfully!" 