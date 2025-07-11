#!/bin/bash

# Crawler Lambda Deployment Script
# This script deploys the crawler service to AWS Lambda

set -e  # Exit on any error

# Configuration
AWS_REGION="ap-south-1"
AWS_ACCOUNT_ID="169164939839"
ECR_REPOSITORY="crawlchat-crawler"
LAMBDA_FUNCTION_NAME="crawlchat-api-function"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    success "AWS CLI found"
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    success "Docker is running"
}

# Configure AWS credentials
configure_aws() {
    log "Configuring AWS credentials..."
    
    # Set AWS credentials
    export AWS_ACCESS_KEY_ID="AKIASOYYEEI7QBNWAEF6"
    export AWS_SECRET_ACCESS_KEY="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"
    export AWS_DEFAULT_REGION="$AWS_REGION"
    
    # Test AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        success "AWS credentials configured successfully"
        aws sts get-caller-identity --query 'Account' --output text
    else
        error "Failed to configure AWS credentials"
        exit 1
    fi
}

# Login to ECR
login_to_ecr() {
    log "Logging in to Amazon ECR..."
    
    ECR_LOGIN_COMMAND=$(aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com")
    
    if [ $? -eq 0 ]; then
        success "Successfully logged in to ECR"
    else
        error "Failed to login to ECR"
        exit 1
    fi
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    # Navigate to the crawler service directory
    cd crawler-service
    
    # Build the image
    docker build --no-cache -t "$ECR_REPOSITORY:$IMAGE_TAG" .
    
    if [ $? -eq 0 ]; then
        success "Docker image built successfully"
    else
        error "Failed to build Docker image"
        exit 1
    fi
    
    # Tag for ECR
    docker tag "$ECR_REPOSITORY:$IMAGE_TAG" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    
    cd ..
}

# Push image to ECR
push_to_ecr() {
    log "Pushing image to ECR..."
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &> /dev/null || {
        log "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION"
    }
    
    # Push the image
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    
    if [ $? -eq 0 ]; then
        success "Image pushed to ECR successfully"
    else
        error "Failed to push image to ECR"
        exit 1
    fi
}

# Update Lambda function
update_lambda() {
    log "Updating Lambda function..."
    
    # Get the image URI
    IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
    
    # Update the Lambda function
    aws lambda update-function-code \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --image-uri "$IMAGE_URI" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        success "Lambda function updated successfully"
    else
        error "Failed to update Lambda function"
        exit 1
    fi
    
    # Wait for the update to complete
    log "Waiting for Lambda function update to complete..."
    aws lambda wait function-updated --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION"
    
    success "Lambda function update completed"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Get function configuration
    FUNCTION_CONFIG=$(aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" --query 'Configuration.{LastModified:LastModified,State:State,Version:Version}' --output json)
    
    echo "Function configuration:"
    echo "$FUNCTION_CONFIG"
    
    # Check if function is active
    STATE=$(echo "$FUNCTION_CONFIG" | jq -r '.State')
    if [ "$STATE" = "Active" ]; then
        success "Lambda function is active and ready"
    else
        warning "Lambda function state: $STATE"
    fi
}

# Main deployment function
main() {
    log "Starting crawler Lambda deployment..."
    log "Region: $AWS_REGION"
    log "Account ID: $AWS_ACCOUNT_ID"
    log "Function: $LAMBDA_FUNCTION_NAME"
    log "ECR Repository: $ECR_REPOSITORY"
    
    # Run deployment steps
    check_aws_cli
    check_docker
    configure_aws
    login_to_ecr
    build_image
    push_to_ecr
    update_lambda
    verify_deployment
    
    success "Crawler Lambda deployment completed successfully!"
    
    log "You can now test the crawler functionality on your website."
    log "Check CloudWatch logs for any issues:"
    log "aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow --region $AWS_REGION"
}

# Run main function
main "$@" 