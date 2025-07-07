# AWS Credential Setup Checklist for Textract

## **For AWS Lambda Deployment**

### 1. **IAM Role Permissions**
Your Lambda function needs an IAM role with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument",
                "textract:StartDocumentAnalysis",
                "textract:GetDocumentAnalysis"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### 2. **Environment Variables**
Set these in your Lambda function:
```
AWS_REGION=us-east-1 (or your preferred region)
AWS_DEFAULT_REGION=us-east-1
TEXTRACT_REGION=us-east-1
S3_BUCKET=your-bucket-name
```

### 3. **Lambda Function Configuration**
- **Memory**: At least 1024 MB (Textract operations can be memory-intensive)
- **Timeout**: At least 5 minutes (Textract can take time)
- **Runtime**: Python 3.9 or higher

---

## **For Local Development**

### 1. **AWS CLI Setup**
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

### 2. **Credentials File**
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

### 3. **Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
export TEXTRACT_REGION=us-east-1
export S3_BUCKET=your-bucket-name
```

---

## **Testing AWS Credentials**

### 1. **Test S3 Access**
```bash
aws s3 ls s3://your-bucket-name
```

### 2. **Test Textract Access**
```python
import boto3

# Test Textract client
textract = boto3.client('textract', region_name='us-east-1')
print("Textract client created successfully")

# Test S3 client
s3 = boto3.client('s3', region_name='us-east-1')
print("S3 client created successfully")
```

### 3. **Check IAM Permissions**
```bash
# Check if your role/user has Textract permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

---

## **Common Issues & Solutions**

### 1. **"NoCredentialsError"**
- **Cause**: AWS credentials not configured
- **Solution**: Set up credentials as above

### 2. **"AccessDenied" for Textract**
- **Cause**: Missing Textract permissions
- **Solution**: Add Textract permissions to IAM role

### 3. **"AccessDenied" for S3**
- **Cause**: Missing S3 permissions
- **Solution**: Add S3 permissions to IAM role

### 4. **"UnsupportedDocumentException"**
- **Cause**: File format not supported by Textract
- **Solution**: Ensure file is PDF, PNG, JPEG, or TIFF

### 5. **"InvalidS3ObjectException"**
- **Cause**: S3 object not accessible or corrupted
- **Solution**: Check S3 permissions and file integrity

---

## **Verification Steps**

### 1. **Check Lambda Logs**
Look for these messages:
```
Textract client initialized successfully in region: us-east-1
S3 client initialized successfully in region: us-east-1
[EMBEDDING] Using AWS Textract for PDF: filename.pdf
```

### 2. **Check AWS Console**
- Go to AWS Textract console
- Check for recent jobs
- Look for any error messages

### 3. **Test with Simple PDF**
Upload a simple text-based PDF to test the integration

---

## **Troubleshooting Commands**

### 1. **Check AWS Configuration**
```bash
aws sts get-caller-identity
```

### 2. **Test Textract Directly**
```python
import boto3

textract = boto3.client('textract')
response = textract.detect_document_text(
    Document={
        'S3Object': {
            'Bucket': 'your-bucket',
            'Name': 'test.pdf'
        }
    }
)
print("Textract test successful")
```

### 3. **Check Environment Variables**
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_DEFAULT_REGION
```

---

## **Security Best Practices**

1. **Use IAM Roles** instead of hardcoded credentials
2. **Limit Permissions** to only what's needed
3. **Rotate Credentials** regularly
4. **Use VPC** for additional security (if needed)
5. **Enable CloudTrail** for audit logging

---

## **Next Steps After Setup**

1. **Deploy the updated code** with Textract-only PDF processing
2. **Test with a PDF upload** in your chat interface
3. **Check logs** for Textract usage messages
4. **Verify completion messages** appear correctly
5. **Monitor AWS costs** (Textract has usage-based pricing) 