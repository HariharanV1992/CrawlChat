# Unified Storage Architecture

## Overview

The unified storage service centralizes all S3 operations across the application, providing consistent file upload, download, and management for both user-uploaded documents and crawled content.

## Architecture Benefits

### 1. **Centralized S3 Operations**
- All S3 uploads, downloads, and deletions go through a single service
- Consistent error handling and logging
- Unified metadata management
- Standardized file naming conventions

### 2. **Consistent File Organization**
- **User Documents**: `uploaded_documents/{user_id}/{timestamp}_{unique_id}{extension}`
- **Crawled Content**: `crawled_documents/{task_id}/{filename}`
- **Temporary Files**: `temp_files/{purpose}/{unique_id}/{filename}`

### 3. **Enhanced Metadata**
- File integrity hashes (MD5)
- Upload timestamps
- User and task associations
- Content type detection
- Source tracking (uploaded vs crawled)

## Service Integration

### Updated Services

1. **Crawler Service** (`crawler_service.py`)
   - Uses `unified_storage_service.upload_crawled_content()` for crawled files
   - Consistent S3 key generation and metadata

2. **Document Service** (`document_service.py`)
   - Uses `unified_storage_service.upload_user_document()` for user uploads
   - Enhanced file integrity checking

3. **Chat Service** (`chat_service.py`)
   - Uses `unified_storage_service.get_file_content()` for document retrieval
   - Consistent file access patterns

4. **Unified Document Processor** (`unified_document_processor.py`)
   - Uses `unified_storage_service.upload_temp_file()` for Textract processing
   - Automatic cleanup of temporary files

5. **API Endpoints** (`chat.py`)
   - Uses unified storage for document uploads
   - Consistent error handling

## Key Features

### File Upload Methods

```python
# User document upload
result = await unified_storage_service.upload_user_document(
    file_content=bytes,
    filename=str,
    user_id=str,
    content_type=Optional[str]
)

# Crawled content upload
result = await unified_storage_service.upload_crawled_content(
    content=str,
    filename=str,
    task_id=str,
    user_id=str,
    metadata=Optional[Dict]
)

# Temporary file upload
result = await unified_storage_service.upload_temp_file(
    file_content=bytes,
    filename=str,
    purpose=str,
    user_id=Optional[str]
)
```

### File Management

```python
# Get file content
content = await unified_storage_service.get_file_content(s3_key)

# Delete file
success = await unified_storage_service.delete_file(s3_key)

# List user files
files = await unified_storage_service.list_user_files(user_id)

# List task files
files = await unified_storage_service.list_task_files(task_id)
```

## File Organization Structure

```
s3://bucket/
├── uploaded_documents/
│   └── {user_id}/
│       ├── {timestamp}_{unique_id}.pdf
│       ├── {timestamp}_{unique_id}.docx
│       └── {timestamp}_{unique_id}.txt
├── crawled_documents/
│   └── {task_id}/
│       ├── page_1.html
│       ├── page_2.html
│       └── article_content.txt
└── temp_files/
    ├── textract_pdf/
    ├── textract_image/
    └── processing/
```

## Metadata Structure

### User Documents
```json
{
  "original_filename": "document.pdf",
  "user_id": "user_123",
  "upload_timestamp": "1703123456",
  "file_hash": "md5_hash",
  "file_size": "1024000"
}
```

### Crawled Content
```json
{
  "original_filename": "page_1.html",
  "user_id": "user_123",
  "task_id": "task_456",
  "content_type": "text/plain",
  "upload_timestamp": "1703123456",
  "file_hash": "md5_hash",
  "file_size": "50000",
  "source": "crawler",
  "source_url": "https://example.com",
  "crawl_depth": 1
}
```

## Error Handling

The unified storage service provides consistent error handling:

- **StorageError**: Raised for storage-related issues
- **Graceful degradation**: Falls back to local storage if S3 unavailable
- **Detailed logging**: All operations logged with context
- **Retry logic**: Built-in retry mechanisms for transient failures

## Testing

Run the test script to verify functionality:

```bash
python test_unified_storage.py
```

This will test:
- User document upload and retrieval
- Crawled content upload
- File deletion and verification
- Content integrity checks

## Migration Benefits

### Before (Scattered S3 Operations)
- Multiple services with different S3 implementations
- Inconsistent file naming and organization
- Duplicate error handling code
- No centralized metadata management
- Inconsistent logging

### After (Unified Storage)
- Single point of control for all S3 operations
- Consistent file organization and naming
- Centralized error handling and logging
- Enhanced metadata and integrity checking
- Easier maintenance and debugging

## Future Enhancements

1. **File Versioning**: Support for document versioning
2. **Compression**: Automatic compression for large files
3. **CDN Integration**: CloudFront integration for faster access
4. **Lifecycle Policies**: Automatic cleanup of old files
5. **Encryption**: Server-side encryption for sensitive documents
6. **Access Control**: Fine-grained access control per file 