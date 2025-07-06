# AWS Textract Integration

This document describes the AWS Textract integration that replaces Tesseract OCR for document text extraction.

## Overview

The document service now uses AWS Textract instead of Tesseract for extracting text from scanned PDFs and images. AWS Textract provides more accurate OCR results and better handling of complex document layouts.

## Architecture Flow

```
User Upload / Crawler
        ↓
S3 (raw document storage)
        ↓
AWS Textract API
        ↓
Extracted text (or structured data if forms/tables)
        ↓
Chunking / preprocessing
        ↓
Embedding (OpenAI / other)
        ↓
Vector DB
        ↓
RAG pipeline → OpenAI model response
```

## Design Decision: Textract API Choice

| API | Cost per 1,000 pages | When to Use |
|------|---------------------|-------------|
| `DetectDocumentText` | ~$1.50 | Default. Extract plain text for embedding |
| `AnalyzeDocument` | ~$5.00 | Use only if document contains forms or complex tables |

✅ Free Tier (first 12 months):  
- 1,000 pages/month `DetectDocumentText`
- 100 pages/month `AnalyzeDocument`

## Implementation Details

### 1. New AWS Textract Service (`src/services/aws_textract_service.py`)

The new service implements:

- **S3-based processing**: Documents are uploaded to S3 and processed directly by Textract
- **API selection logic**: Automatically chooses between `DetectDocumentText` and `AnalyzeDocument`
- **Whole PDF processing**: Processes entire PDFs instead of page-by-page conversion
- **Structured data extraction**: Handles forms, tables, and key-value pairs
- **Cost estimation**: Provides cost estimates for different document types

### 2. Document Type Detection

The service automatically detects document types:

```python
# General documents (annual reports, general PDFs)
DocumentType.GENERAL -> DetectDocumentText

# Forms, invoices, tables
DocumentType.FORM -> AnalyzeDocument
DocumentType.INVOICE -> AnalyzeDocument  
DocumentType.TABLE_HEAVY -> AnalyzeDocument
```

### 3. API Call Pattern

```python
# DetectDocumentText (default, cheaper)
response = client.detect_document_text(
  Document={
    'S3Object': {
      'Bucket': 'your-bucket',
      'Name': 'path/to/file.pdf'
    }
  }
)

# AnalyzeDocument (for forms/tables)
response = client.analyze_document(
  Document={
    'S3Object': {
      'Bucket': 'your-bucket',
      'Name': 'path/to/file.pdf'
    }
  },
  FeatureTypes=['TABLES', 'FORMS']
)
```

## Changes Made

### 1. Dependencies Updated

**Added:**
- `boto3>=1.34.0` - AWS SDK for Python
- `botocore>=1.34.0` - AWS SDK core library

**Removed:**
- `pytesseract>=0.3.10` - Tesseract OCR engine
- `pdf2image>=1.16.0` - PDF to image conversion (no longer needed)

### 2. Dockerfile Updates

- Removed Tesseract and Tesseract language pack installations
- Removed poppler-utils (no longer needed for page-by-page conversion)
- Reduced container size significantly

### 3. Code Changes

#### Document Service (`src/services/document_service.py`)
- Updated `_extract_text_with_ocr()` method to use new AWS Textract service
- Simplified document type detection logic
- Removed page-by-page image conversion

#### New AWS Textract Service (`src/services/aws_textract_service.py`)
- Implements S3-based document processing
- Handles both `DetectDocumentText` and `AnalyzeDocument` APIs
- Extracts structured data from forms and tables
- Provides cost estimation functionality

#### AWS Configuration (`src/core/aws_config.py`)
- Added Textract region configuration
- Added `textract_region` property
- Supports environment variable `TEXTRACT_REGION` (defaults to `us-east-1`)

## Configuration

### Environment Variables

```bash
# AWS Textract region (optional, defaults to us-east-1)
TEXTRACT_REGION=us-east-1

# AWS credentials (required)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region

# S3 bucket for document processing
S3_BUCKET_NAME=your-document-bucket
```

### AWS Permissions

The AWS credentials used must have the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-document-bucket/*"
        }
    ]
}
```

## Usage

The integration is transparent to the end user. When a PDF is uploaded:

1. **Text-based PDFs**: Extracted using PyPDF2 or pdfminer.six
2. **Scanned PDFs**: Uploaded to S3 and processed with AWS Textract
3. **Forms/Tables**: Automatically detected and processed with AnalyzeDocument
4. **Fallback**: If Textract fails, returns an error message

## Benefits

### Compared to Tesseract:

1. **Better Accuracy**: AWS Textract provides superior OCR accuracy
2. **Layout Understanding**: Better handling of complex document layouts
3. **No Local Dependencies**: No need to install and maintain Tesseract
4. **Scalability**: AWS handles the processing load
5. **Cost Effective**: Pay-per-use pricing model
6. **Structured Data**: Can extract forms, tables, and key-value pairs

### Performance Improvements:

- **Faster Processing**: AWS Textract is optimized for cloud processing
- **Reduced Container Size**: Smaller Lambda container without OCR dependencies
- **Better Error Handling**: More detailed error messages and fallback options
- **Whole Document Processing**: No need for page-by-page conversion

## Testing

Run the test script to verify the integration:

```bash
python test_textract.py
```

The test script will:
1. Check AWS configuration
2. Verify Textract service initialization
3. Test cost estimation
4. Validate API selection logic
5. Test S3 bucket access
6. Verify Textract permissions
7. Test with sample PDF (if available)

## Error Handling

The service includes comprehensive error handling:

1. **AWS Credentials**: Checks for valid AWS credentials
2. **Network Issues**: Handles AWS API connectivity problems
3. **Document Processing**: Graceful fallback for unsupported formats
4. **Rate Limiting**: Respects AWS Textract rate limits
5. **S3 Operations**: Handles S3 upload/download errors

## Cost Considerations

AWS Textract pricing (as of 2024):
- **DetectDocumentText**: $1.50 per 1,000 pages
- **AnalyzeDocument**: $5.00 per 1,000 pages

For most use cases, `DetectDocumentText` is sufficient for basic text extraction.

## Migration Notes

If migrating from an existing Tesseract implementation:

1. Update dependencies in `requirements.txt`
2. Ensure AWS credentials are properly configured
3. Test with sample documents to verify accuracy
4. Monitor AWS costs during initial deployment
5. Update any custom OCR logic to use the new service

## Troubleshooting

### Common Issues:

1. **AWS Credentials Not Found**
   - Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
   - Check IAM permissions for Textract access

2. **S3 Bucket Access Denied**
   - Verify S3 bucket exists and is accessible
   - Check S3 permissions for the configured bucket

3. **Textract API Errors**
   - Check document format (PDF, PNG, JPEG, TIFF supported)
   - Verify document size (max 5MB for synchronous API)
   - Ensure document is not corrupted

4. **High Costs**
   - Monitor usage of `AnalyzeDocument` vs `DetectDocumentText`
   - Implement document type detection to minimize expensive API calls

## Future Enhancements

1. **Async Processing**: Implement async Textract jobs for large documents
2. **Document Classification**: Add ML-based document type detection
3. **Batch Processing**: Process multiple documents in parallel
4. **Caching**: Cache Textract results to avoid reprocessing
5. **Custom Models**: Use Textract custom models for domain-specific documents 