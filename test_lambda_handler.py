"""
Test Lambda handler to debug import issues
"""

import json
import sys
import os

def lambda_handler(event, context):
    """Test handler to check module availability"""
    
    result = {
        "python_version": sys.version,
        "python_path": sys.path,
        "cwd": os.getcwd(),
        "modules": {}
    }
    
    # Test key modules
    modules_to_test = [
        'mangum', 'fastapi', 'uvicorn', 'motor', 'pymongo', 
        'aiohttp', 'requests', 'beautifulsoup4', 'lxml', 
        'selenium', 'PyPDF2', 'pypdf', 'PyMuPDF', 'pdfplumber', 
        'openai', 'numpy', 'passlib', 'python_jose', 'PyJWT', 
        'cryptography', 'python_dotenv', 'email_validator', 
        'html2text', 'tqdm', 'python_multipart', 'click', 
        'pydantic', 'pydantic_settings', 'pydantic_core', 
        'aiofiles', 'asyncio_throttle', 'anyio', 'typing_extensions', 
        'typing_inspection', 'exceptiongroup', 'sniffio', 'starlette'
    ]
    
    for module in modules_to_test:
        try:
            imported_module = __import__(module)
            result["modules"][module] = {
                "status": "available",
                "version": getattr(imported_module, '__version__', 'unknown'),
                "file": getattr(imported_module, '__file__', 'unknown')
            }
        except ImportError as e:
            result["modules"][module] = {
                "status": "missing",
                "error": str(e)
            }
    
    return {
        'statusCode': 200,
        'body': json.dumps(result, indent=2),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    } 