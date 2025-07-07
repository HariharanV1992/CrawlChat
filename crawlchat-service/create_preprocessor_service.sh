#!/bin/bash
# Script to create the ECS preprocessor service

set -e

# Configuration
REGION="ap-south-1"
CLUSTER_NAME="crawlchat-cluster"
SERVICE_NAME="crawlchat-preprocessor"
TASK_DEFINITION_NAME="crawlchat-preprocessor-task"
ECR_REPO="crawlchat-preprocessor"

echo "🔧 Creating ECS Preprocessor Service..."

# 1. Create ECS cluster if it doesn't exist
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION 2>/dev/null || echo "Cluster exists"

# 2. Create task execution role
echo "📋 Creating task execution role..."
aws iam create-role \
  --role-name crawlchat-ecs-task-execution-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  2>/dev/null || echo "Role exists"

# 3. Attach task execution policy
echo "🔐 Attaching task execution policy..."
aws iam attach-role-policy \
  --role-name crawlchat-ecs-task-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 4. Create task role for preprocessor
echo "📝 Creating task role..."
aws iam create-role \
  --role-name crawlchat-preprocessor-task-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  2>/dev/null || echo "Role exists"

# 5. Create custom policy for preprocessor
echo "🔑 Creating preprocessor policy..."
aws iam put-role-policy \
  --role-name crawlchat-preprocessor-task-role \
  --policy-name PreprocessorPermissions \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
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
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ],
        "Resource": "arn:aws:sqs:ap-south-1:169164939839:crawlchat-preprocessing-queue"
      },
      {
        "Effect": "Allow",
        "Action": [
          "textract:DetectDocumentText",
          "textract:AnalyzeDocument"
        ],
        "Resource": "*"
      }
    ]
  }'

# 6. Get role ARNs
TASK_EXECUTION_ROLE_ARN=$(aws iam get-role --role-name crawlchat-ecs-task-execution-role --query 'Role.Arn' --output text)
TASK_ROLE_ARN=$(aws iam get-role --role-name crawlchat-preprocessor-task-role --query 'Role.Arn' --output text)

echo "🎯 Task Execution Role ARN: $TASK_EXECUTION_ROLE_ARN"
echo "🎯 Task Role ARN: $TASK_ROLE_ARN"

# 7. Create task definition
echo "📋 Creating task definition..."
cat > task-definition.json <<EOF
{
  "family": "$TASK_DEFINITION_NAME",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "$TASK_EXECUTION_ROLE_ARN",
  "taskRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "preprocessor",
      "image": "169164939839.dkr.ecr.ap-south-1.amazonaws.com/crawlchat-preprocessor:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "ap-south-1"
        },
        {
          "name": "S3_BUCKET",
          "value": "crawlchat-data"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/crawlchat-preprocessor",
          "awslogs-region": "ap-south-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION

# 8. Create CloudWatch log group
echo "📊 Creating log group..."
aws logs create-log-group --log-group-name /ecs/crawlchat-preprocessor --region $REGION 2>/dev/null || echo "Log group already exists"

# 9. Create service
echo "🚀 Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION_NAME \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345678"],
      "securityGroups": ["sg-12345678"],
      "assignPublicIp": "ENABLED"
    }
  }' \
  --region $REGION 2>/dev/null || echo "Service already exists"

echo "✅ ECS Preprocessor service created successfully!"
echo "📋 Service details:"
echo "   Cluster: $CLUSTER_NAME"
echo "   Service: $SERVICE_NAME"
echo "   Task Definition: $TASK_DEFINITION_NAME"
echo "   CPU: 1024"
echo "   Memory: 2048MB"
echo "   Desired Count: 1"

echo ""
echo "🎉 Your CrawlChat system now has all 3 services:"
echo "   1. ✅ API Service (Lambda - crawlchat-api-function)"
echo "   2. ✅ Crawler Service (Lambda - crawlchat-crawler-function)"
echo "   3. ✅ Preprocessor Service (ECS - crawlchat-preprocessor)"

echo ""
echo "⚠️  IMPORTANT: You need to update the subnet and security group IDs in the script!"
echo "   Run: aws ec2 describe-subnets --region ap-south-1"
echo "   Run: aws ec2 describe-security-groups --region ap-south-1" 