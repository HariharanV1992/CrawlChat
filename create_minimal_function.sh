#!/bin/bash

set -e  # Exit on any error

echo "🔧 Creating Minimal Lambda Function Package"
echo "=========================================="

# Configuration
FUNCTION_NAME="crawlchat-function-minimal"
S3_BUCKET="crawlchat-deployment"
LAMBDA_FUNCTION_NAME="crawlchat-api-function"

# Clean up existing directory
if [ -d "lambda-function" ]; then
    echo "🧹 Cleaning up existing lambda-function directory..."
    rm -rf lambda-function
fi

# Create function directory
mkdir -p lambda-function
cd lambda-function

echo "📁 Copying source code..."
cp -r ../src/ .
cp ../main.py .
cp ../lambda_handler.py .

echo "📁 Copying static files and templates..."
cp -r ../static/ .
cp -r ../templates/ .

echo "📄 Copying documentation..."
cp ../MOBILE_IMPROVEMENTS.md .

echo "🔧 Ensuring correct storage service for Lambda..."
# Check if we have the storage service
if [ -f "./src/services/storage_service.py" ]; then
    echo "✅ Storage service found"
else
    echo "❌ Storage service not found"
    exit 1
fi

echo "🔧 Checking mobile improvements..."
# Check if mobile improvements are included
if [ -f "./templates/test_mobile.html" ]; then
    echo "✅ Mobile test page included"
else
    echo "⚠️  Mobile test page not found"
fi

if grep -q "mobile-nav-toggle" ./templates/chat.html; then
    echo "✅ Mobile navigation included in chat template"
else
    echo "⚠️  Mobile navigation not found in chat template"
fi

if grep -q "@media (max-width: 768px)" ./static/css/main.css; then
    echo "✅ Mobile CSS styles included"
else
    echo "⚠️  Mobile CSS styles not found"
fi

echo "🧹 Cleaning up unnecessary files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true

cd ..

echo "📦 Creating function ZIP file..."
cd lambda-function
zip -r "../${FUNCTION_NAME}.zip" . -x "*.pyc" "__pycache__/*" "*.pyo" "*.pyd" ".git/*" ".gitignore" "*.log" "*.tmp" ".DS_Store"
cd ..

echo "📊 Function package size: $(du -h ${FUNCTION_NAME}.zip | cut -f1)"
echo "✅ Minimal function package created: ${FUNCTION_NAME}.zip"

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI and configure it."
    echo "   You can download it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Upload to S3
echo "☁️ Uploading to S3..."
aws s3 cp "${FUNCTION_NAME}.zip" "s3://${S3_BUCKET}/"

echo "🎉 Function package uploaded to S3: s3://${S3_BUCKET}/${FUNCTION_NAME}.zip"
echo ""
echo "📋 Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Select your function: ${LAMBDA_FUNCTION_NAME}"
echo "3. In 'Code' tab, click 'Upload from' → 'Amazon S3 location'"
echo "4. Enter S3 URL: s3://${S3_BUCKET}/${FUNCTION_NAME}.zip"
echo "5. Click 'Save'"
echo "6. Test your function"
echo ""
echo "🔗 Your API Gateway URL: https://api.crawlchat.site"
echo "🧪 Mobile Test URL: https://api.crawlchat.site/test-mobile"
echo ""
echo "📱 Mobile Improvements Included:"
echo "   - Mobile navigation with hamburger menu"
echo "   - Touch-friendly interface (44px minimum touch targets)"
echo "   - Responsive layouts for all screen sizes"
echo "   - iOS zoom prevention (16px font-size on inputs)"
echo "   - Mobile-optimized forms and buttons"
echo ""
echo "📝 Note: Make sure your Lambda function has the correct IAM role with:"
echo "   - S3 access to bucket: ${S3_BUCKET}"
echo "   - S3 access to bucket: crawlchat-data"
echo "   - SQS access (if using background processing)" 