#!/bin/bash

echo "🚀 Deploying Both Services: Lambda Function + Preprocessing Service"
echo "=================================================================="

# Configuration
AWS_REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_FUNCTION_NAME="crawlchat-api-function"
PREPROCESSOR_SERVICE_NAME="crawlchat-preprocessor"

# ECR Repositories
LAMBDA_ECR_REPO="crawlchat-api"
PREPROCESSOR_ECR_REPO="crawlchat-preprocessor"

echo "📋 Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Account ID: $ACCOUNT_ID"
echo "  Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "  Preprocessor Service: $PREPROCESSOR_SERVICE_NAME"
echo "  Lambda ECR: $LAMBDA_ECR_REPO"
echo "  Preprocessor ECR: $PREPROCESSOR_ECR_REPO"
echo ""

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name=$1
    echo "🏗️ Creating ECR repository: $repo_name"
    aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $repo_name --region $AWS_REGION
}

# Function to build and push Docker image
build_and_push() {
    local dockerfile=$1
    local repo_name=$2
    local image_tag=$3
    
    echo "🔨 Building $repo_name from $dockerfile..."
    docker build -f $dockerfile -t $repo_name:$image_tag .
    
    if [ $? -ne 0 ]; then
        echo "❌ Docker build failed for $repo_name!"
        return 1
    fi
    
    echo "🏷️ Tagging $repo_name for ECR..."
    docker tag $repo_name:$image_tag $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name:$image_tag
    
    echo "📤 Pushing $repo_name to ECR..."
    docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name:$image_tag
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to push $repo_name to ECR!"
        return 1
    fi
    
    echo "✅ $repo_name successfully pushed to ECR!"
    return 0
}

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repositories
create_ecr_repo $LAMBDA_ECR_REPO
create_ecr_repo $PREPROCESSOR_ECR_REPO

# Build and push Lambda function
echo ""
echo "🐳 Deploying Lambda Function..."
IMAGE_TAG="latest"
build_and_push "Dockerfile" $LAMBDA_ECR_REPO $IMAGE_TAG
LAMBDA_SUCCESS=$?

if [ $LAMBDA_SUCCESS -eq 0 ]; then
    # Update Lambda function
    echo "🔄 Updating Lambda function..."
    IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$LAMBDA_ECR_REPO:$IMAGE_TAG"
    
    # Check if function exists
    FUNCTION_EXISTS=$(aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION 2>/dev/null && echo "true" || echo "false")
    
    if [ "$FUNCTION_EXISTS" = "true" ]; then
        echo "✅ Updating existing Lambda function..."
        aws lambda update-function-code \
            --function-name $LAMBDA_FUNCTION_NAME \
            --image-uri $IMAGE_URI \
            --region $AWS_REGION
        
        if [ $? -eq 0 ]; then
            echo "⏳ Waiting for Lambda update to complete..."
            aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION
            echo "✅ Lambda function updated successfully!"
        else
            echo "❌ Failed to update Lambda function!"
        fi
    else
        echo "⚠️ Lambda function '$LAMBDA_FUNCTION_NAME' does not exist."
        echo "   Create it manually in AWS Console or use AWS CLI."
        echo "   Image URI: $IMAGE_URI"
    fi
fi

# Build and push Preprocessing service
echo ""
echo "🐳 Deploying Preprocessing Service..."
build_and_push "Dockerfile.preprocessor" $PREPROCESSOR_ECR_REPO $IMAGE_TAG
PREPROCESSOR_SUCCESS=$?

if [ $PREPROCESSOR_SUCCESS -eq 0 ]; then
    echo "✅ Preprocessing service image ready for deployment!"
    echo "   Image URI: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PREPROCESSOR_ECR_REPO:$IMAGE_TAG"
    echo ""
    echo "📋 Next steps for preprocessing service:"
    echo "   1. Deploy to ECS/Fargate for production use"
    echo "   2. Or run locally for testing:"
    echo "      docker run -p 8000:8000 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PREPROCESSOR_ECR_REPO:$IMAGE_TAG"
fi

# Summary
echo ""
echo "🎉 Deployment Summary:"
echo "======================"
if [ $LAMBDA_SUCCESS -eq 0 ]; then
    echo "✅ Lambda Function: Deployed successfully"
    echo "   Function: $LAMBDA_FUNCTION_NAME"
    echo "   Image: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$LAMBDA_ECR_REPO:$IMAGE_TAG"
else
    echo "❌ Lambda Function: Deployment failed"
fi

if [ $PREPROCESSOR_SUCCESS -eq 0 ]; then
    echo "✅ Preprocessing Service: Image built and pushed"
    echo "   Image: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PREPROCESSOR_ECR_REPO:$IMAGE_TAG"
    echo "   Status: Ready for ECS/Fargate deployment"
else
    echo "❌ Preprocessing Service: Build failed"
fi

echo ""
echo "🔗 Next Steps:"
echo "   1. Test your Lambda function endpoints"
echo "   2. Monitor CloudWatch logs for any issues"
echo "   3. Deploy preprocessing service to ECS/Fargate when needed"
echo "   4. Update Lambda environment variables manually in AWS Console" 