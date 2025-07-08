#!/bin/bash

# Deploy Lambda Function with Fixed Handler (S3 Caching)
# This script rebuilds and redeploys the Lambda function to use the updated lambda-service
# which has S3 caching instead of local file caching

set -e

# Configuration
AWS_REGION="ap-south-1"
ECR_REPOSITORY="crawlchat-crawl-worker"
IMAGE_TAG="latest"
FUNCTION_NAME="crawlchat-crawl-worker"

echo "🚀 Deploying Lambda Function with Fixed Handler (S3 Caching)"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# ECR repository URI
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

echo "🏗️  Building Docker image with lambda-service (S3 caching)..."

# Build the Docker image
cd crawler-service
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

echo "✅ Docker image built successfully"

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Tag the image
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "✅ Image pushed to ECR: $ECR_URI:$IMAGE_TAG"

# Update Lambda function
echo "🔄 Updating Lambda function..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --image-uri $ECR_URI:$IMAGE_TAG \
    --region $AWS_REGION

echo "✅ Lambda function updated successfully"

# Wait for update to complete
echo "⏳ Waiting for Lambda function update to complete..."
aws lambda wait function-updated \
    --function-name $FUNCTION_NAME \
    --region $AWS_REGION

echo "✅ Lambda function update completed"

# Test the function
echo "🧪 Testing Lambda function..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"url": "https://example.com", "content_type": "generic"}' \
    --region $AWS_REGION \
    response.json

echo "📄 Lambda response:"
cat response.json
rm response.json

echo "🎉 Deployment completed successfully!"
echo "📋 Summary:"
echo "   - Function: $FUNCTION_NAME"
echo "   - Image: $ECR_URI:$IMAGE_TAG"
echo "   - Region: $AWS_REGION"
echo "   - Handler: lambda_handler.lambda_handler (from lambda-service)"
echo "   - Features: S3 caching, EnhancedScrapingBeeManager" 