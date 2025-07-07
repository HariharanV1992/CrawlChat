#!/bin/bash

echo "🔧 AWS Credentials Configuration Helper"
echo "======================================"
echo ""

echo "Current AWS configuration:"
aws configure list
echo ""

echo "To fix the credentials issue, you need to:"
echo ""
echo "1. Get your AWS credentials from AWS Console:"
echo "   - Go to AWS Console → IAM → Users → Your User"
echo "   - Go to 'Security credentials' tab"
echo "   - Create new access key"
echo ""
echo "2. Configure AWS CLI with the new credentials:"
echo "   aws configure"
echo ""
echo "3. Enter the following when prompted:"
echo "   - AWS Access Key ID: [your access key]"
echo "   - AWS Secret Access Key: [your secret key]"
echo "   - Default region name: ap-south-1"
echo "   - Default output format: json"
echo ""
echo "4. Test the configuration:"
echo "   aws sts get-caller-identity"
echo ""
echo "5. Then run the environment update script:"
echo "   ./update_lambda_env.sh"
echo ""

echo "Alternative: You can also set environment variables:"
echo "export AWS_ACCESS_KEY_ID=your_access_key"
echo "export AWS_SECRET_ACCESS_KEY=your_secret_key"
echo "export AWS_DEFAULT_REGION=ap-south-1"
echo ""

echo "Would you like to proceed with aws configure now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Running aws configure..."
    aws configure
    echo ""
    echo "Testing configuration..."
    aws sts get-caller-identity
else
    echo "Please configure AWS credentials manually and then run:"
    echo "./update_lambda_env.sh"
fi 