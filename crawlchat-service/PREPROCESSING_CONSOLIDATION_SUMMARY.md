# Preprocessing Service Consolidation Summary

## Overview
This document summarizes the consolidation of preprocessing logic into a unified service, eliminating the need for separate PDF preprocessing services.

## What Was Consolidated

### 1. **Unified Preprocessing Service** (`unified_preprocessing_service.py`)
- **Location**: `common/src/services/unified_preprocessing_service.py`
- **Purpose**: Single service that handles all document types and preprocessing operations
- **Features**:
  - PDF text extraction (PyPDF2, pdfminer.six, PyMuPDF)
  - PDF to image conversion (pdf2image)
  - Image processing and normalization
  - Text document processing
  - Generic document handling
  - S3 integration
  - Batch processing capabilities

### 2. **Enhanced Document Processing Service**
- **Location**: `common/src/services/document_processing_service.py`
- **Enhancement**: Added `process_document_with_preprocessing()` method
- **Integration**: Seamlessly combines preprocessing with vector store operations

### 3. **New API Endpoints**
- **Location**: `common/src/api/v1/preprocessing.py`
- **Endpoints**:
  - `POST /api/v1/preprocessing/process-document` - Basic preprocessing
  - `POST /api/v1/preprocessing/process-document-with-vector-store` - Full pipeline
  - `POST /api/v1/preprocessing/process-from-s3` - S3-based processing
  - `POST /api/v1/preprocessing/batch-process` - Batch processing
  - `GET /api/v1/preprocessing/stats` - Service statistics
  - `GET /api/v1/preprocessing/supported-types` - Supported document types

## Supported Document Types

### 1. **PDF Documents**
- **Text Extraction**: Direct text extraction using multiple libraries
- **Image Conversion**: Convert to PNG images for OCR processing
- **Processing Types**: `direct_text`, `pdf_to_images`

### 2. **Image Documents**
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **Processing**: Normalization and S3 storage
- **Processing Type**: `normalization`

### 3. **Text Documents**
- **Supported Formats**: TXT, MD, CSV, JSON
- **Processing**: Direct text processing
- **Processing Type**: `direct_text`

### 4. **Generic Documents**
- **Supported Formats**: DOC, DOCX, XLS, XLSX, PPT, PPTX
- **Processing**: Normalization and storage
- **Processing Type**: `normalization`

## Key Benefits

### 1. **Simplified Architecture**
- Single service instead of multiple specialized services
- Unified API interface
- Consistent error handling and logging

### 2. **Enhanced Capabilities**
- Automatic document type detection
- Multiple text extraction methods for PDFs
- Batch processing support
- S3 integration for cloud storage

### 3. **Better Integration**
- Seamless integration with vector store service
- Session-based organization
- Metadata preservation throughout the pipeline

### 4. **Improved Maintainability**
- Single codebase to maintain
- Consistent patterns and error handling
- Better testability

## Migration Guide

### For Existing Code

#### Before (Separate Services)
```python
# Old way - separate PDF preprocessor
from preprocessor_service import PDFPreprocessor
preprocessor = PDFPreprocessor()
result = await preprocessor.process_pdf(s3_bucket, s3_key, user_id)
```

#### After (Unified Service)
```python
# New way - unified preprocessing
from common.src.services.unified_preprocessing_service import unified_preprocessing_service
result = await unified_preprocessing_service.process_document(
    file_content=file_content,
    filename=filename,
    user_id=user_id
)
```

### For New Integrations

#### Basic Document Processing
```python
# Process any document type
result = await unified_preprocessing_service.process_document(
    file_content=file_content,
    filename="document.pdf",
    user_id="user123"
)
```

#### Full Pipeline with Vector Store
```python
# Process with preprocessing and vector store integration
result = await document_processing_service.process_document_with_preprocessing(
    file_content=file_content,
    filename="document.pdf",
    user_id="user123",
    session_id="session456"
)
```

## API Usage Examples

### 1. **Process Single Document**
```bash
curl -X POST "https://api.crawlchat.site/api/v1/preprocessing/process-document" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "force_processing=false"
```

### 2. **Process with Vector Store Integration**
```bash
curl -X POST "https://api.crawlchat.site/api/v1/preprocessing/process-document-with-vector-store" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "session_id=session123"
```

### 3. **Process from S3**
```bash
curl -X POST "https://api.crawlchat.site/api/v1/preprocessing/process-from-s3" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "s3_bucket=my-bucket" \
  -F "s3_key=documents/document.pdf"
```

### 4. **Get Service Statistics**
```bash
curl -X GET "https://api.crawlchat.site/api/v1/preprocessing/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Dependencies Added

### New Python Packages
- `pdf2image==1.16.0` - PDF to image conversion
- `PyMuPDF==1.23.0` - Advanced PDF processing

### Updated Requirements
- Enhanced `lambda-service/requirements.txt` with preprocessing dependencies
- All dependencies are Lambda-compatible

## ECR Repository Cleanup

### Repositories to Keep
1. **crawlchat-api** - Main API service
2. **crawlchat-api-function** - Lambda function service
3. **crawlchat-preprocessor** - Main preprocessing service (consolidated)

### Repository to Delete
1. **pdf-preprocessor** - No longer needed (functionality consolidated)

## Testing

### Health Check
The unified preprocessing service is included in the service health check:
```bash
python service_health_check.py
```

### Manual Testing
```python
# Test document type detection
from common.src.services.unified_preprocessing_service import unified_preprocessing_service

# Test with sample PDF
with open("test.pdf", "rb") as f:
    result = await unified_preprocessing_service.process_document(
        file_content=f.read(),
        filename="test.pdf",
        user_id="test_user"
    )
print(result)
```

## Next Steps

1. **Deploy the consolidated service** to your Lambda environment
2. **Update any existing integrations** to use the new unified service
3. **Delete the unused `pdf-preprocessor` ECR repository**
4. **Test the new API endpoints** to ensure everything works correctly
5. **Monitor the service** for any issues during the transition

## Support

If you encounter any issues during the migration:
1. Check the service logs for detailed error messages
2. Verify that all dependencies are properly installed
3. Ensure AWS credentials and permissions are correctly configured
4. Test with the provided API examples

The unified preprocessing service provides a more robust, maintainable, and feature-rich solution for document processing across your entire platform. 