#!/bin/bash
# Script to clean up the ECS preprocessor service and related AWS resources

set -e

# Configuration
REGION="ap-south-1"
CLUSTER_NAME="crawlchat-cluster"
SERVICE_NAME="crawlchat-preprocessor"
TASK_DEFINITION_NAME="crawlchat-preprocessor-task"
ECR_REPO="crawlchat-preprocessor"

echo "🧹 Cleaning up ECS Preprocessor Service and related resources..."

# 1. Stop and delete the ECS service
echo "🛑 Stopping ECS service..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 0 \
  --region $REGION 2>/dev/null || echo "Service not found or already stopped"

echo "⏳ Waiting for service to stop..."
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION 2>/dev/null || echo "Service already stopped"

echo "🗑️ Deleting ECS service..."
aws ecs delete-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --region $REGION 2>/dev/null || echo "Service not found"

# 2. Deregister task definition
echo "📋 Deregistering task definition..."
TASK_DEFINITIONS=$(aws ecs list-task-definitions \
  --family-prefix $TASK_DEFINITION_NAME \
  --region $REGION \
  --query 'taskDefinitionArns' \
  --output text 2>/dev/null || echo "")

if [ ! -z "$TASK_DEFINITIONS" ]; then
  for TASK_DEF_ARN in $TASK_DEFINITIONS; do
    echo "🗑️ Deregistering: $TASK_DEF_ARN"
    aws ecs deregister-task-definition \
      --task-definition $TASK_DEF_ARN \
      --region $REGION 2>/dev/null || echo "Failed to deregister"
  done
else
  echo "No task definitions found"
fi

# 3. Delete CloudWatch log group
echo "📊 Deleting log group..."
aws logs delete-log-group \
  --log-group-name /ecs/crawlchat-preprocessor \
  --region $REGION 2>/dev/null || echo "Log group not found"

# 4. Delete IAM roles and policies
echo "🔑 Deleting IAM roles and policies..."

# Delete preprocessor task role policy
aws iam delete-role-policy \
  --role-name crawlchat-preprocessor-task-role \
  --policy-name PreprocessorPermissions \
  --region $REGION 2>/dev/null || echo "Policy not found"

# Delete preprocessor task role
aws iam delete-role \
  --role-name crawlchat-preprocessor-task-role \
  --region $REGION 2>/dev/null || echo "Role not found"

# 5. Delete ECR repository (optional - uncomment if you want to remove the Docker images too)
echo "🐳 ECR repository cleanup (skipped - uncomment if needed)..."
# aws ecr delete-repository \
#   --repository-name $ECR_REPO \
#   --force \
#   --region $REGION 2>/dev/null || echo "ECR repository not found"



echo "✅ Cleanup completed!"
echo ""
echo "📋 Cleaned up resources:"
echo "   ✅ ECS Service: $SERVICE_NAME"
echo "   ✅ Task Definition: $TASK_DEFINITION_NAME"
echo "   ✅ CloudWatch Log Group: /ecs/crawlchat-preprocessor"
echo "   ✅ IAM Role: crawlchat-preprocessor-task-role"
echo "   ✅ IAM Policy: PreprocessorPermissions"
echo ""
echo "⚠️  Manual cleanup needed:"
echo "   - ECR repository: $ECR_REPO (if you want to remove Docker images)"
echo "   - ECS cluster: $CLUSTER_NAME (if not used by other services)"
echo ""
echo "🎉 Preprocessor service has been successfully removed from AWS!" 