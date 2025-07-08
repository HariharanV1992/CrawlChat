#!/bin/bash

# CrawlChat Lambda Functions Deployment Script
# This script deploys the Lambda functions with proper container images

set -e

# Configuration
AWS_REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_PREFIX="crawlchat"

echo "🚀 CrawlChat Lambda Functions Deployment"
echo "========================================"
echo "AWS Region: $AWS_REGION"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Function to check if ECR repository exists
check_ecr_repository() {
    local repo_name=$1
    aws ecr describe-repositories --repository-names "$repo_name" --region "$AWS_REGION" >/dev/null 2>&1
}

# Function to create ECR repository if it doesn't exist
create_ecr_repository() {
    local repo_name=$1
    echo "📦 Creating ECR repository: $repo_name"
    aws ecr create-repository \
        --repository-name "$repo_name" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
}

# Function to build and push Docker image
build_and_push_image() {
    local repo_name=$1
    local dockerfile_path=$2
    local image_tag="latest"
    
    echo "🔨 Building Docker image for $repo_name"
    
    # Get ECR login token
    aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build image
    docker build -t "$repo_name:$image_tag" -f "$dockerfile_path" .
    
    # Tag for ECR
    docker tag "$repo_name:$image_tag" "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name:$image_tag"
    
    # Push to ECR
    echo "📤 Pushing image to ECR..."
    docker push "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name:$image_tag"
    
    echo "✅ Image pushed successfully: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name:$image_tag"
}

# Function to update Lambda function
update_lambda_function() {
    local function_name=$1
    local image_uri=$2
    
    echo "🔄 Updating Lambda function: $function_name"
    
    # Check if function exists
    if aws lambda get-function --function-name "$function_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo "   Function exists, updating..."
        aws lambda update-function-code \
            --function-name "$function_name" \
            --image-uri "$image_uri" \
            --region "$AWS_REGION"
    else
        echo "   Function doesn't exist, creating..."
        aws lambda create-function \
            --function-name "$function_name" \
            --package-type Image \
            --code ImageUri="$image_uri" \
            --role "arn:aws:iam::$ACCOUNT_ID:role/crawlchat-lambda-role" \
            --timeout 900 \
            --memory-size 1024 \
            --region "$AWS_REGION"
    fi
    
    echo "✅ Lambda function updated: $function_name"
}

# Main deployment process
echo "📋 Starting deployment process..."

# 1. Deploy API Function
echo ""
echo "🔧 Step 1: Deploying API Function"
echo "---------------------------------"

API_REPO_NAME="$ECR_REPOSITORY_PREFIX-api-function"
API_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$API_REPO_NAME:latest"

# Create ECR repository if it doesn't exist
if ! check_ecr_repository "$API_REPO_NAME"; then
    create_ecr_repository "$API_REPO_NAME"
else
    echo "📦 ECR repository already exists: $API_REPO_NAME"
fi

# Build and push API image
build_and_push_image "$API_REPO_NAME" "lambda-service/Dockerfile"

# Update Lambda function
update_lambda_function "crawlchat-api-function" "$API_IMAGE_URI"

# 2. Deploy Crawler Function
echo ""
echo "🔧 Step 2: Deploying Crawler Function"
echo "------------------------------------"

CRAWLER_REPO_NAME="$ECR_REPOSITORY_PREFIX-crawler-function"
CRAWLER_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$CRAWLER_REPO_NAME:latest"

# Create ECR repository if it doesn't exist
if ! check_ecr_repository "$CRAWLER_REPO_NAME"; then
    create_ecr_repository "$CRAWLER_REPO_NAME"
else
    echo "📦 ECR repository already exists: $CRAWLER_REPO_NAME"
fi

# Build and push crawler image
build_and_push_image "$CRAWLER_REPO_NAME" "lambda-service/Dockerfile"

# Update Lambda function
update_lambda_function "crawlchat-crawler-function" "$CRAWLER_IMAGE_URI"

# 3. Test the deployment
echo ""
echo "🔧 Step 3: Testing Deployment"
echo "-----------------------------"

echo "🧪 Testing API function..."
sleep 10  # Wait for function to be ready

# Test the API function
aws lambda invoke \
    --function-name "crawlchat-api-function" \
    --payload '{"httpMethod":"GET","path":"/health","headers":{},"queryStringParameters":null,"body":null,"isBase64Encoded":false}' \
    --region "$AWS_REGION" \
    response.json

echo "📄 API Function Response:"
cat response.json | jq .
rm response.json

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Summary:"
echo "   API Function: crawlchat-api-function"
echo "   API Image: $API_IMAGE_URI"
echo "   Crawler Function: crawlchat-crawler-function"
echo "   Crawler Image: $CRAWLER_IMAGE_URI"
echo ""
echo "🔗 Next steps:"
echo "   1. Test the API Gateway: https://6a24mtpa4i.execute-api.ap-south-1.amazonaws.com/prod/health"
echo "   2. Test the login endpoint: https://6a24mtpa4i.execute-api.ap-south-1.amazonaws.com/prod/api/v1/auth/login"
echo "   3. Fix DNS configuration for custom domains" 