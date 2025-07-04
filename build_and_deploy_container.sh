#!/bin/bash

echo "🐳 Building Lambda Container with OCR Support"
echo "============================================="

# Set variables
AWS_REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="crawlchat-api-function"
IMAGE_TAG="latest"
FUNCTION_NAME="crawlchat-api-function"

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Account ID: $ACCOUNT_ID"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  Image Tag: $IMAGE_TAG"
echo "  Function Name: $FUNCTION_NAME"
echo ""

# Create ECR repository if it doesn't exist
echo "🏗️ Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Tag the image for ECR
echo "🏷️ Tagging image for ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# Push the image to ECR
echo "📤 Pushing image to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Failed to push image to ECR!"
    exit 1
fi

# Get the image URI
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"

echo "✅ Image successfully pushed to ECR: $IMAGE_URI"
echo ""

# Check if Lambda function exists
echo "🔍 Checking if Lambda function exists..."
FUNCTION_EXISTS=$(aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION 2>/dev/null && echo "true" || echo "false")

if [ "$FUNCTION_EXISTS" = "true" ]; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $IMAGE_URI \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo "✅ Lambda function updated successfully!"
    else
        echo "❌ Failed to update Lambda function!"
        exit 1
    fi
else
    echo "📝 Creating new Lambda function..."
    
    # Get role ARN (you may need to adjust this)
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$IMAGE_URI \
        --role $ROLE_ARN \
        --timeout 900 \
        --memory-size 1024 \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo "✅ Lambda function created successfully!"
    else
        echo "❌ Failed to create Lambda function!"
        echo "💡 Make sure you have a valid IAM role: $ROLE_ARN"
        exit 1
    fi
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test your Lambda function with a PDF upload"
echo "2. Check CloudWatch logs for OCR processing"
echo "3. The function now has full OCR support for scanned PDFs"
echo ""
echo "🔧 Container includes:"
echo "  ✅ Tesseract OCR engine"
echo "  ✅ Poppler utilities (pdf2image)"
echo "  ✅ All Python dependencies"
echo "  ✅ 1024MB memory allocation"
echo "  ✅ 15-minute timeout for OCR processing" 