#!/bin/bash

# Enhanced Crawler Deployment Script
# Deploys the enhanced crawler with progressive proxy strategy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="crawlchat-enhanced-crawler"
AWS_REGION=${AWS_REGION:-"us-east-1"}
ECR_REPOSITORY_NAME="crawlchat-crawl-worker"
LAMBDA_FUNCTION_NAME="crawlchat-crawl-worker"
SQS_QUEUE_NAME="crawlchat-crawl-tasks"

echo -e "${BLUE}🚀 Enhanced Crawler Deployment${NC}"
echo -e "${BLUE}============================${NC}"

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$SCRAPINGBEE_API_KEY" ]; then
    echo -e "${RED}❌ SCRAPINGBEE_API_KEY environment variable is not set.${NC}"
    echo -e "${YELLOW}Please set it: export SCRAPINGBEE_API_KEY='your-api-key'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get AWS account ID
echo -e "${YELLOW}🔍 Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}🏗️  Setting up ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${YELLOW}Creating ECR repository: ${ECR_REPOSITORY_NAME}${NC}"
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
    echo -e "${GREEN}✅ ECR repository created${NC}"
else
    echo -e "${GREEN}✅ ECR repository already exists${NC}"
fi

# Get ECR login token
echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo -e "${GREEN}✅ ECR login successful${NC}"

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
cd lambda-service

# Create .env file for build
cat > .env << EOF
SCRAPINGBEE_API_KEY=$SCRAPINGBEE_API_KEY
AWS_REGION=$AWS_REGION
EOF

# Build the image
docker build -t $ECR_REPOSITORY_NAME .
echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Tag the image
IMAGE_TAG="latest"
ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME:$IMAGE_TAG"
docker tag $ECR_REPOSITORY_NAME:latest $ECR_IMAGE_URI
echo -e "${GREEN}✅ Docker image tagged: $ECR_IMAGE_URI${NC}"

# Push the image to ECR
echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker push $ECR_IMAGE_URI
echo -e "${GREEN}✅ Docker image pushed to ECR${NC}"

# Deploy infrastructure using CloudFormation
echo -e "${YELLOW}🏗️  Deploying infrastructure...${NC}"
cd ..

# Update the CloudFormation template with the image URI
sed "s|REPLACE_WITH_IMAGE_URI|$ECR_IMAGE_URI|g" infra/crawlchat-crawl-worker.yml > infra/crawlchat-crawl-worker-deploy.yml

# Deploy CloudFormation stack
STACK_NAME="crawlchat-enhanced-crawler-stack"
echo -e "${YELLOW}Deploying CloudFormation stack: $STACK_NAME${NC}"

if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${YELLOW}Updating existing stack...${NC}"
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://infra/crawlchat-crawl-worker-deploy.yml \
        --parameters ParameterKey=LambdaImageUri,ParameterValue=$ECR_IMAGE_URI \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION
    
    echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $AWS_REGION
else
    echo -e "${YELLOW}Creating new stack...${NC}"
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://infra/crawlchat-crawl-worker-deploy.yml \
        --parameters ParameterKey=LambdaImageUri,ParameterValue=$ECR_IMAGE_URI \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION
    
    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $AWS_REGION
fi

echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"

# Get stack outputs
echo -e "${YELLOW}📊 Getting deployment information...${NC}"
SQS_QUEUE_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`SQSQueueUrl`].OutputValue' \
    --output text)

LAMBDA_FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaWorkerFunctionName`].OutputValue' \
    --output text)

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo -e "   Stack Name: $STACK_NAME"
echo -e "   ECR Repository: $ECR_REPOSITORY_NAME"
echo -e "   Lambda Function: $LAMBDA_FUNCTION_ARN"
echo -e "   SQS Queue: $SQS_QUEUE_URL"
echo -e "   Region: $AWS_REGION"

# Test the deployment
echo -e "${YELLOW}🧪 Testing the deployment...${NC}"

# Create a test event
TEST_EVENT=$(cat << EOF
{
    "url": "https://httpbin.org/html",
    "content_type": "generic",
    "country_code": "us"
}
EOF
)

echo -e "${YELLOW}Invoking Lambda function for testing...${NC}"
aws lambda invoke \
    --function-name $LAMBDA_FUNCTION_NAME \
    --payload "$TEST_EVENT" \
    --region $AWS_REGION \
    response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Lambda function test successful${NC}"
    echo -e "${YELLOW}Response:${NC}"
    cat response.json | jq '.' 2>/dev/null || cat response.json
    rm -f response.json
else
    echo -e "${RED}❌ Lambda function test failed${NC}"
    if [ -f response.json ]; then
        echo -e "${YELLOW}Error response:${NC}"
        cat response.json
        rm -f response.json
    fi
fi

# Create usage examples
echo -e "${YELLOW}📝 Creating usage examples...${NC}"

cat > usage_examples.md << EOF
# Enhanced Crawler Usage Examples

## Basic Crawling
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://example.com", "content_type": "generic"}' \\
    response.json
\`\`\`

## News Site Crawling
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://news.ycombinator.com", "content_type": "news", "use_js_scenario": true}' \\
    response.json
\`\`\`

## E-commerce Site Crawling
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://example-store.com", "content_type": "ecommerce", "use_js_scenario": true}' \\
    response.json
\`\`\`

## Financial Site Crawling (Stealth Mode)
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://financial-reports.com", "content_type": "financial", "force_mode": "stealth"}' \\
    response.json
\`\`\`

## Screenshot Capture
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://example.com", "take_screenshot": true, "full_page": true}' \\
    response.json
\`\`\`

## File Download
\`\`\`bash
aws lambda invoke \\
    --function-name $LAMBDA_FUNCTION_NAME \\
    --payload '{"url": "https://example.com/document.pdf", "download_file": true}' \\
    response.json
\`\`\`

## SQS Batch Processing
\`\`\`bash
aws sqs send-message \\
    --queue-url $SQS_QUEUE_URL \\
    --message-body '{"urls": ["https://example1.com", "https://example2.com"], "content_type": "generic", "batch_id": "test-batch-1"}'
\`\`\`
EOF

echo -e "${GREEN}✅ Usage examples created: usage_examples.md${NC}"

# Create monitoring script
echo -e "${YELLOW}📊 Creating monitoring script...${NC}"

cat > monitor_crawler.sh << 'EOF'
#!/bin/bash

# Enhanced Crawler Monitoring Script

FUNCTION_NAME="crawlchat-crawl-worker"
REGION="us-east-1"

echo "🔍 Enhanced Crawler Monitoring"
echo "=============================="

# Get function metrics
echo "📊 Lambda Function Metrics:"
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=$FUNCTION_NAME \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum

echo ""
echo "⏱️  Duration Metrics:"
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Duration \
    --dimensions Name=FunctionName,Value=$FUNCTION_NAME \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average

echo ""
echo "❌ Error Metrics:"
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Errors \
    --dimensions Name=FunctionName,Value=$FUNCTION_NAME \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum

# Get recent logs
echo ""
echo "📝 Recent Logs:"
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$FUNCTION_NAME" --query 'logGroups[0].logGroupName' --output text | xargs -I {} aws logs describe-log-streams --log-group-name {} --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text | xargs -I {} aws logs get-log-events --log-group-name "/aws/lambda/$FUNCTION_NAME" --log-stream-name {} --start-time $(date -u -d '10 minutes ago' +%s)000 --query 'events[*].message' --output text
EOF

chmod +x monitor_crawler.sh
echo -e "${GREEN}✅ Monitoring script created: monitor_crawler.sh${NC}"

# Final summary
echo -e "${BLUE}🎉 Enhanced Crawler Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Progressive proxy strategy implemented${NC}"
echo -e "${GREEN}✅ JavaScript scenarios supported${NC}"
echo -e "${GREEN}✅ File download capabilities added${NC}"
echo -e "${GREEN}✅ Screenshot functionality included${NC}"
echo -e "${GREEN}✅ Cost-effective crawling with fallback${NC}"
echo -e "${GREEN}✅ Comprehensive monitoring and logging${NC}"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo -e "   1. Review usage_examples.md for usage patterns"
echo -e "   2. Run monitor_crawler.sh to check performance"
echo -e "   3. Test different content types and scenarios"
echo -e "   4. Monitor costs in AWS Cost Explorer"
echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo -e "   View logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow"
echo -e "   Monitor: ./monitor_crawler.sh"
echo -e "   Test: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"url\": \"https://example.com\"}' response.json"
echo ""
echo -e "${GREEN}🚀 Your enhanced crawler is ready to use!${NC}" 