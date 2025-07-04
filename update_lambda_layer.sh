#!/bin/bash

echo "🚀 Updating Lambda Function to Use Latest Layer"
echo "================================================"

# Configuration
FUNCTION_NAME="crawlchat-api-function"  # Update this to your actual function name
LAYER_NAME="crawlchat-dependencies"     # Update this to your actual layer name
S3_BUCKET="crawlchat-deployment"
LATEST_LAYER="lambda-layer-complete (1).zip"

echo "📋 Configuration:"
echo "   Function Name: $FUNCTION_NAME"
echo "   Layer Name: $LAYER_NAME"
echo "   S3 Bucket: $S3_BUCKET"
echo "   Latest Layer: $LATEST_LAYER"
echo ""

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if ! aws lambda get-function --function-name "$FUNCTION_NAME" > /dev/null 2>&1; then
    echo "❌ Lambda function '$FUNCTION_NAME' not found!"
    echo "   Please update the FUNCTION_NAME variable in this script."
    exit 1
fi
echo "✅ Lambda function found!"

# Check if layer exists
echo "🔍 Checking if layer exists..."
if ! aws lambda list-layers --query "Layers[?LayerName=='$LAYER_NAME']" --output text | grep -q "$LAYER_NAME"; then
    echo "⚠️  Layer '$LAYER_NAME' not found. Creating new layer..."
    CREATE_NEW_LAYER=true
else
    echo "✅ Layer found!"
    CREATE_NEW_LAYER=false
fi

# Get current function configuration
echo "📊 Getting current function configuration..."
CURRENT_CONFIG=$(aws lambda get-function --function-name "$FUNCTION_NAME" --query 'Configuration.{Runtime:Runtime,Handler:Handler,Role:Role,Timeout:Timeout,MemorySize:MemorySize}' --output json)
echo "✅ Current configuration retrieved"

# Create new layer version
echo "📦 Creating new layer version..."
if [ "$CREATE_NEW_LAYER" = true ]; then
    echo "   Creating new layer: $LAYER_NAME"
    LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name "$LAYER_NAME" \
        --description "CrawlChat dependencies with mangum and all required packages" \
        --content S3Bucket="$S3_BUCKET",S3Key="$LATEST_LAYER" \
        --compatible-runtimes python3.9 python3.10 python3.11 \
        --query 'LayerVersionArn' --output text)
else
    echo "   Publishing new version for existing layer: $LAYER_NAME"
    LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name "$LAYER_NAME" \
        --description "CrawlChat dependencies with mangum and all required packages" \
        --content S3Bucket="$S3_BUCKET",S3Key="$LATEST_LAYER" \
        --compatible-runtimes python3.9 python3.10 python3.11 \
        --query 'LayerVersionArn' --output text)
fi

if [ $? -eq 0 ]; then
    echo "✅ Layer version created: $LAYER_ARN"
else
    echo "❌ Failed to create layer version!"
    exit 1
fi

# Update function configuration
echo "🔄 Updating Lambda function configuration..."
aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --layers "$LAYER_ARN" \
    --runtime python3.9 \
    --timeout 30 \
    --memory-size 512

if [ $? -eq 0 ]; then
    echo "✅ Function configuration updated!"
else
    echo "❌ Failed to update function configuration!"
    exit 1
fi

# Wait for update to complete
echo "⏳ Waiting for function update to complete..."
aws lambda wait function-updated --function-name "$FUNCTION_NAME"
echo "✅ Function update completed!"

# Test the function
echo "🧪 Testing the function..."
TEST_RESPONSE=$(aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{"httpMethod": "GET", "path": "/health"}' \
    --cli-binary-format raw-in-base64-out \
    response.json 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Function test successful!"
    echo "📄 Response:"
    cat response.json
    rm -f response.json
else
    echo "❌ Function test failed!"
    echo "Error: $TEST_RESPONSE"
    echo ""
    echo "📄 Full response (if any):"
    if [ -f response.json ]; then
        cat response.json
        rm -f response.json
    fi
fi

echo ""
echo "🎉 Lambda function updated successfully!"
echo ""
echo "📋 Summary:"
echo "   ✅ Function: $FUNCTION_NAME"
echo "   ✅ Layer: $LAYER_ARN"
echo "   ✅ Layer contains: mangum, uvicorn, pydantic-settings, and all dependencies"
echo ""
echo "🔗 Next steps:"
echo "   1. Test your API endpoints"
echo "   2. Monitor CloudWatch logs for any issues"
echo "   3. The mangum import error should now be resolved!" 