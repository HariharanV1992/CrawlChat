#!/bin/bash

# Upload PDF to S3 for Lambda testing
# This avoids file corruption during Lambda deployment

BUCKET_NAME="your-bucket-name"  # Replace with your actual bucket name
PDF_PATH="Namecheap.pdf"
S3_KEY="pdfs/Namecheap.pdf"

echo "📤 Uploading PDF to S3..."

# Check if bucket exists, create if not
if ! aws s3 ls "s3://$BUCKET_NAME" 2>&1 > /dev/null; then
    echo "Creating bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME"
fi

# Upload PDF
aws s3 cp "$PDF_PATH" "s3://$BUCKET_NAME/$S3_KEY"

if [ $? -eq 0 ]; then
    echo "✅ PDF uploaded successfully to s3://$BUCKET_NAME/$S3_KEY"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update Lambda environment variables:"
    echo "   S3_BUCKET=$BUCKET_NAME"
    echo "   S3_PDF_KEY=$S3_KEY"
    echo ""
    echo "2. Deploy the S3-based Lambda handler:"
    echo "   aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda_handler_s3.zip"
    echo ""
    echo "3. Test the Lambda function"
else
    echo "❌ Failed to upload PDF to S3"
    exit 1
fi 