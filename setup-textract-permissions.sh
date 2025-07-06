#!/bin/bash

# AWS Textract Permissions Setup Script
# This script helps you add the necessary permissions to your Lambda execution role

echo "🔧 AWS Textract Permissions Setup"
echo "=================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is configured"

# Get Lambda function name
read -p "Enter your Lambda function name: " FUNCTION_NAME

# Get the execution role ARN
ROLE_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --query 'Configuration.Role' --output text 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Could not find Lambda function: $FUNCTION_NAME"
    echo "Please check the function name and try again."
    exit 1
fi

echo "✅ Found Lambda function: $FUNCTION_NAME"
echo "✅ Execution role: $ROLE_ARN"

# Extract role name from ARN
ROLE_NAME=$(echo $ROLE_ARN | sed 's/.*role\///')

echo "📋 Role name: $ROLE_NAME"

# Create the policy
echo "📝 Creating IAM policy for Textract permissions..."

cat > textract-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "TextractPermissions",
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument",
                "textract:StartDocumentAnalysis",
                "textract:GetDocumentAnalysis",
                "textract:StartDocumentTextDetection",
                "textract:GetDocumentTextDetection"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create the policy in AWS
POLICY_ARN=$(aws iam create-policy \
    --policy-name "${ROLE_NAME}-TextractPolicy" \
    --policy-document file://textract-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Created IAM policy: $POLICY_ARN"
else
    echo "⚠️  Policy might already exist, trying to find it..."
    POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='${ROLE_NAME}-TextractPolicy'].Arn" --output text)
    if [ "$POLICY_ARN" != "None" ] && [ "$POLICY_ARN" != "" ]; then
        echo "✅ Found existing policy: $POLICY_ARN"
    else
        echo "❌ Failed to create or find policy"
        exit 1
    fi
fi

# Attach policy to role
echo "🔗 Attaching policy to role..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn $POLICY_ARN

if [ $? -eq 0 ]; then
    echo "✅ Successfully attached Textract policy to role"
else
    echo "❌ Failed to attach policy to role"
    exit 1
fi

# Clean up temporary files
rm -f textract-policy.json

echo ""
echo "🎉 Setup complete!"
echo "Your Lambda function should now have Textract permissions."
echo ""
echo "Next steps:"
echo "1. Test your Lambda function with a PDF/image upload"
echo "2. Check CloudWatch logs for any remaining errors"
echo "3. If you have S3 bucket restrictions, update the S3 permissions in the policy" 