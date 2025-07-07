# Lambda PDF Debug Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Create Lambda Function
```bash
# Using AWS CLI
aws lambda create-function \
  --function-name pdf-debug-test \
  --runtime python3.10 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda_debug_deploy.zip \
  --memory-size 512 \
  --timeout 30
```

### 2. Package and Deploy
```bash
# Create deployment package
zip -r lambda_debug_deploy.zip lambda_handler.py Namecheap.pdf common/

# Update existing function
aws lambda update-function-code \
  --function-name pdf-debug-test \
  --zip-file fileb://lambda_debug_deploy.zip
```

### 3. Test the Function
```bash
# Using the test script
python test_lambda_deployment.py pdf-debug-test us-east-1

# Or using AWS CLI
aws lambda invoke \
  --function-name pdf-debug-test \
  --payload '{}' \
  response.json
```

## 📋 Manual AWS Console Steps

### 1. Create Lambda Function
1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `pdf-debug-test`
5. Runtime: Python 3.10
6. Architecture: x86_64
7. Click "Create function"

### 2. Upload Code
1. In the function code editor, replace the default code with `lambda_handler.py`
2. Upload `Namecheap.pdf` to the function (or adjust the path in the code)
3. Click "Deploy"

### 3. Configure Function
1. Go to "Configuration" tab
2. Set memory to 512 MB
3. Set timeout to 30 seconds
4. Save changes

### 4. Test Function
1. Go to "Test" tab
2. Create test event (empty JSON: `{}`)
3. Click "Test"
4. Check the execution results

## 🔍 What to Look For

### Expected Output Structure
```json
{
  "statusCode": 200,
  "body": {
    "debug_info": {
      "file_info": {
        "filename": "/var/task/Namecheap.pdf",
        "size_bytes": 361791,
        "md5_hash": "a474e61ccfd35d416d76ddc5345e9e0f",
        "is_pdf_header": true,
        "has_eof_marker": true
      },
      "environment": {
        "python_version": "3.10.x",
        "is_lambda": true,
        "lambda_memory": "512"
      },
      "libraries": {
        "PyPDF2": {"available": true, "version": "3.0.1"},
        "pdfminer.six": {"available": true, "version": "20250506"},
        "boto3": {"available": true, "version": "1.39.2"}
      }
    },
    "extraction": {
      "success": true,
      "pages_with_text": 1,
      "preview": ["Page 1: SIGN UP CONT ACT US SIGN IN..."]
    }
  }
}
```

### Comparison with Local Results
| Metric | Local | Lambda | Status |
|--------|-------|--------|--------|
| File Size | 361,791 bytes | ? | Compare |
| MD5 Hash | a474e61ccfd35d416d76ddc5345e9e0f | ? | Compare |
| PDF Header | ✅ | ? | Compare |
| EOF Marker | ✅ | ? | Compare |
| PyPDF2 | 3.0.1 | ? | Compare |
| pdfminer.six | 20250506 | ? | Compare |
| Extraction | ✅ Success | ? | Compare |

## 🚨 Common Issues and Solutions

### 1. Missing Dependencies
**Symptoms:** Libraries show as unavailable in Lambda
**Solution:** 
- Create Lambda layer with PDF libraries
- Include libraries in deployment package
- Use container image deployment

### 2. File Not Found
**Symptoms:** Error reading PDF file
**Solution:**
- Check file path in Lambda handler
- Upload PDF to S3 and read from there
- Verify file is included in deployment package

### 3. Memory Issues
**Symptoms:** Function times out or crashes
**Solution:**
- Increase Lambda memory (512 MB or higher)
- Check CloudWatch logs for OOM errors
- Optimize PDF processing

### 4. Version Mismatches
**Symptoms:** Different library versions between local and Lambda
**Solution:**
- Use exact same versions in Lambda
- Create requirements.txt with pinned versions
- Use Lambda layers for consistent dependencies

## 📊 Testing Commands

### Using the Test Script
```bash
# Test with function name
python test_lambda_deployment.py pdf-debug-test

# Test with custom region
python test_lambda_deployment.py pdf-debug-test us-west-2
```

### Using AWS CLI
```bash
# Invoke function
aws lambda invoke \
  --function-name pdf-debug-test \
  --payload '{}' \
  response.json

# Check logs
aws logs tail /aws/lambda/pdf-debug-test --follow
```

### Using CloudWatch
1. Go to CloudWatch > Log groups
2. Find `/aws/lambda/pdf-debug-test`
3. Click on latest log stream
4. Check for debug output and errors

## 🎯 Next Steps After Testing

1. **If Lambda results match local:** Your environment is consistent
2. **If there are differences:** 
   - File corruption → Fix upload/read logic
   - Library issues → Update Lambda package/layer
   - Memory issues → Increase Lambda memory
   - Other errors → Check CloudWatch logs for details

3. **Apply fixes to your main Lambda function**
4. **Test with real PDF uploads**
5. **Monitor performance and errors**

## 📞 Need Help?

If you encounter issues:
1. Check CloudWatch logs for detailed error messages
2. Compare Lambda output with local results
3. Verify all dependencies are properly packaged
4. Ensure sufficient memory and timeout settings 

## 🚀 Quick Deployment

### Option 1: Standard Deployment (Current)
```bash
# Package and deploy
./package_lambda.sh
aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda_package.zip
```

### Option 2: S3-Based Deployment (Recommended for PDF Issues)

If you're experiencing PDF corruption issues in Lambda, use S3-based deployment:

```bash
# 1. Upload PDF to S3
chmod +x upload_pdf_to_s3.sh
./upload_pdf_to_s3.sh

# 2. Package S3-based handler
chmod +x package_s3_handler.sh
./package_s3_handler.sh

# 3. Deploy S3-based handler
aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda_handler_s3.zip

# 4. Set environment variables
aws lambda update-function-configuration --function-name your-function-name \
  --environment Variables='{S3_BUCKET=your-bucket-name,S3_PDF_KEY=pdfs/Namecheap.pdf}'
```

## 🔧 Configuration

### Environment Variables
- `S3_BUCKET`: Your S3 bucket name
- `S3_PDF_KEY`: S3 key for the PDF file (e.g., `pdfs/Namecheap.pdf`)

### IAM Permissions
Ensure your Lambda execution role has:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## 🧪 Testing

### Test S3-Based Handler
```bash
# Test with empty event (reads from S3)
aws lambda invoke --function-name your-function-name \
  --payload '{}' \
  response.json

# View results
cat response.json
```

## 📊 Performance

### Current Performance (from logs)
- **Cold Start**: ~10 seconds (timeout on first run)
- **Warm Start**: ~7-14 seconds for PDF processing
- **Memory Usage**: 113-145 MB
- **Success Rate**: ✅ Working with user-friendly error messages

### Optimization Tips
1. **Increase Memory**: Higher memory = faster CPU
2. **Use S3**: Avoid deployment package corruption
3. **Warm Functions**: Keep functions warm for consistent performance

## 🐛 Troubleshooting

### Common Issues

#### 1. PDF Corruption in Lambda
**Symptoms**: `Data-loss while decompressing corrupted data`
**Solution**: Use S3-based deployment (Option 2 above)

#### 2. Cold Start Timeouts
**Symptoms**: `INIT_REPORT Status: timeout`
**Solution**: Increase timeout to 30 seconds

#### 3. Import Errors
**Symptoms**: `No module named 'crawler'`
**Solution**: Ensure all dependencies are in the deployment package

### Debug Commands
```bash
# Check Lambda logs
aws logs tail /aws/lambda/your-function-name --follow

# Test function
aws lambda invoke --function-name your-function-name --payload '{}' response.json

# Update configuration
aws lambda update-function-configuration --function-name your-function-name --timeout 30
```

## 📈 Monitoring

### Key Metrics to Watch
- **Duration**: Should be < 15 seconds
- **Memory Usage**: Should be < 200 MB
- **Error Rate**: Should be < 5%
- **Cold Start Frequency**: Monitor for performance impact

### CloudWatch Alarms
```bash
# Create error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-Error-Rate" \
  --alarm-description "Lambda function error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
``` 