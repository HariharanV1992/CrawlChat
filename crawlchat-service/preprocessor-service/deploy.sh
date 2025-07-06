#!/bin/bash

# PDF Preprocessor Deployment Script
# This script deploys the PDF preprocessor to ECS Fargate

set -e

# Configuration
AWS_REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="crawlchat-data"  # Your actual S3 bucket
ECR_REPOSITORY="pdf-preprocessor"
ECS_CLUSTER="pdf-preprocessing-cluster"
ECS_SERVICE="pdf-preprocessor-service"

echo "🚀 Starting PDF Preprocessor Deployment"
echo "Account ID: $ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "S3 Bucket: $S3_BUCKET"

# Step 1: Create ECR Repository
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION || echo "Repository already exists"

# Step 2: Get ECR login token
echo "🔐 Getting ECR login token..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 3: Build and push Docker image
echo "🏗️ Building Docker image..."
docker build -t $ECR_REPOSITORY .

echo "🏷️ Tagging image..."
docker tag $ECR_REPOSITORY:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

echo "📤 Pushing image to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Step 4: Create SQS Queue
echo "📬 Creating SQS queue..."
aws sqs create-queue --queue-name pdf-preprocess-queue --region $AWS_REGION || echo "Queue already exists"

# Step 5: Create CloudWatch Log Group
echo "📊 Creating CloudWatch log group..."
aws logs create-log-group --log-group-name /ecs/pdf-preprocessor --region $AWS_REGION || echo "Log group already exists"

# Step 6: Create IAM Roles
echo "🔑 Creating IAM roles..."

# Task Execution Role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}' || echo "Task execution role already exists"

# Attach managed policy for ECS task execution
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Task Role
aws iam create-role --role-name pdf-preprocessor-task-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}' || echo "Task role already exists"

# Create and attach task role policy
cat > task-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:$AWS_REGION:$ACCOUNT_ID:pdf-preprocess-queue"
    }
  ]
}
EOF

aws iam put-role-policy --role-name pdf-preprocessor-task-role --policy-name pdf-preprocessor-policy --policy-document file://task-role-policy.json

# Step 7: Update task definition
echo "📋 Updating ECS task definition..."
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" ecs-task-definition.json
sed -i "s/YOUR_S3_BUCKET/$S3_BUCKET/g" ecs-task-definition.json

aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Step 8: Create ECS Cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION || echo "Cluster already exists"

# Step 9: Create ECS Service
echo "🚀 Creating ECS service..."
cat > service-definition.json << EOF
{
  "cluster": "$ECS_CLUSTER",
  "serviceName": "$ECS_SERVICE",
  "taskDefinition": "pdf-preprocessor",
  "desiredCount": 1,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-06c6fea962ae73e48"],
      "securityGroups": ["sg-025568b6da190067d"],
      "assignPublicIp": "ENABLED"
    }
  }
}
EOF

aws ecs create-service --cli-input-json file://service-definition.json --region $AWS_REGION || echo "Service already exists"

# Step 10: Set up S3 Event Notification
echo "🔔 Setting up S3 event notification..."
QUEUE_URL=$(aws sqs get-queue-url --queue-name pdf-preprocess-queue --region $AWS_REGION --query QueueUrl --output text)
QUEUE_ARN=$(aws sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --region $AWS_REGION --query Attributes.QueueArn --output text)

# Create S3 event notification configuration
cat > s3-notification.json << EOF
{
  "QueueConfigurations": [
    {
      "Id": "pdf-upload-notification",
      "QueueArn": "$QUEUE_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "uploaded_documents/"
            },
            {
              "Name": "suffix",
              "Value": ".pdf"
            }
          ]
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-notification-configuration --bucket $S3_BUCKET --notification-configuration file://s3-notification.json

echo "✅ PDF Preprocessor deployment completed!"
echo ""
echo "📋 Summary:"
echo "  - ECR Repository: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
echo "  - ECS Cluster: $ECS_CLUSTER"
echo "  - ECS Service: $ECS_SERVICE"
echo "  - SQS Queue: pdf-preprocess-queue"
echo "  - S3 Bucket: $S3_BUCKET"
echo ""
echo "🔍 Monitor the deployment:"
echo "  - ECS Service: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER/services/$ECS_SERVICE"
echo "  - CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups/log-group/ecs/pdf-preprocessor"
echo "  - SQS Queue: https://console.aws.amazon.com/sqs/home?region=$AWS_REGION#/queues/https%3A%2F%2Fsqs.$AWS_REGION.amazonaws.com%2F$ACCOUNT_ID%2Fpdf-preprocess-queue" 