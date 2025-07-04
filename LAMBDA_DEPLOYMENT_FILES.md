# Lambda Function Deployment Files

This document lists the files included in the Lambda function deployment.

## Essential Files Included

### Main Application Files
- `lambda_handler.py` - Custom Lambda handler
- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies

### Source Code (`src/`)
- `src/__init__.py`
- `src/api/` - API routers and endpoints
- `src/core/` - Core configuration, database, exceptions, logging
- `src/crawler/` - Web crawling functionality
- `src/models/` - Data models and schemas
- `src/services/` - Business logic services
- `src/utils/` - Utility functions
- `src/web/` - Web interface components

### Web Interface Files
- `templates/` - HTML templates for web UI
- `static/` - CSS, JavaScript, images, fonts

### System Dependencies (Installed in Container)
- Tesseract OCR engine
- Poppler utilities (pdf2image)
- Python packages from requirements.txt
- Build tools and system libraries

## Files Excluded

### Development Files
- `venv/` - Virtual environment
- `tests/` - Test files
- `docs/` - Documentation
- `logs/` - Log files
- `data/` - Data directories
- `lambda-layer-*/` - Lambda layers
- `.git/` - Git repository
- IDE files (`.vscode/`, `.idea/`)

### Build Artifacts
- `*.zip` - Compressed files
- `build/` - Build directories
- `dist/` - Distribution files

## Container Configuration

- **Base Image**: `public.ecr.aws/lambda/python:3.10`
- **Memory**: 1024MB
- **Timeout**: 15 minutes
- **Handler**: `lambda_handler.lambda_handler`

## Deployment Size Optimization

The deployment is optimized to include only the essential files needed for:
1. FastAPI application functionality
2. Document processing and OCR
3. Web interface rendering
4. Database operations
5. File storage operations

This reduces the container size and improves cold start times while maintaining all required functionality. 