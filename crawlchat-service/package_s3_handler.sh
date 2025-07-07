#!/bin/bash

# Package S3-based Lambda handler
echo "📦 Packaging S3-based Lambda handler..."

# Create temporary directory
mkdir -p temp_package

# Copy handler
cp lambda_handler_s3.py temp_package/lambda_handler.py

# Install dependencies
pip install boto3 PyPDF2 pdfminer.six -t temp_package/

# Create zip file
cd temp_package
zip -r ../lambda_handler_s3.zip .
cd ..

# Clean up
rm -rf temp_package

echo "✅ Package created: lambda_handler_s3.zip"
echo ""
echo "📋 Deploy commands:"
echo "aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda_handler_s3.zip"
echo ""
echo "aws lambda update-function-configuration --function-name your-function-name --environment Variables='{S3_BUCKET=your-bucket-name,S3_PDF_KEY=pdfs/Namecheap.pdf}'" 