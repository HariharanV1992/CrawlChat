# AWS Textract Setup Guide

## Problem
Your Lambda function is getting `AccessDeniedException` when trying to use AWS Textract. This means the Lambda execution role doesn't have the necessary permissions.

## Solution Options

### Option 1: Automated Setup (Recommended)
Run the provided script:
```bash
./setup-textract-permissions.sh
```

### Option 2: Manual Setup via AWS Console

#### Step 1: Find Your Lambda Function's Execution Role
1. Go to AWS Lambda Console
2. Select your function
3. Go to the "Configuration" tab
4. Click on "Permissions"
5. Note the "Execution role" name (e.g., `crawlchat-lambda-role`)

#### Step 2: Create IAM Policy
1. Go to AWS IAM Console
2. Click "Policies" → "Create policy"
3. Use JSON editor and paste this policy:

```json
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
```

4. Name it: `LambdaTextractPolicy`
5. Click "Create policy"

#### Step 3: Attach Policy to Role
1. Go to IAM Console → "Roles"
2. Find your Lambda execution role
3. Click on the role name
4. Click "Attach policies"
5. Search for and select `LambdaTextractPolicy`
6. Click "Attach policy"

#### Step 4: Verify Permissions
1. Go back to your Lambda function
2. Test with a PDF/image upload
3. Check CloudWatch logs for success

## Additional Permissions (if needed)

If you have specific S3 bucket restrictions, add this to your policy:

```json
{
    "Sid": "S3PermissionsForTextract",
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
    ],
    "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
    ]
}
```

## Testing

After setting up permissions:
1. Upload a PDF or image to your application
2. Check CloudWatch logs for successful Textract processing
3. Verify the page usage counter updates correctly

## Troubleshooting

### Still getting AccessDeniedException?
1. Wait 5-10 minutes for IAM changes to propagate
2. Check if your Lambda function is in a different AWS region than Textract
3. Verify the execution role is correctly attached to your function

### Lambda timeout issues?
1. Increase Lambda timeout to 5-10 minutes
2. Consider using async Textract operations for large documents

### Cost considerations?
- Textract charges per page processed
- Consider implementing document size limits
- Monitor usage in AWS Cost Explorer 