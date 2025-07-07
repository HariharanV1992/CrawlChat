import json
import os
import sys
import hashlib
import platform
import boto3

def get_pdf_debug_info(content: bytes, filename: str):
    debug_info = {
        "file_info": {
            "filename": filename,
            "size_bytes": len(content),
            "size_mb": len(content) / (1024 * 1024),
            "md5_hash": hashlib.md5(content).hexdigest(),
            "first_20_bytes": content[:20].hex(),
            "last_20_bytes": content[-20:].hex(),
            "is_pdf_header": content.startswith(b'%PDF-'),
            "has_eof_marker": b'%%EOF' in content[-1000:],
            "null_byte_ratio": content.count(b'\x00') / len(content) if content else 0
        },
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "is_lambda": bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME")),
            "lambda_memory": os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"),
            "lambda_function": os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        },
        "libraries": {}
    }
    
    # Check library availability
    try:
        import PyPDF2
        debug_info["libraries"]["PyPDF2"] = {
            "available": True,
            "version": getattr(PyPDF2, "__version__", "unknown"),
            "path": PyPDF2.__file__
        }
    except Exception as e:
        debug_info["libraries"]["PyPDF2"] = {
            "available": False,
            "error": str(e)
        }
    
    try:
        import pdfminer
        debug_info["libraries"]["pdfminer.six"] = {
            "available": True,
            "version": getattr(pdfminer, "__version__", "unknown"),
            "path": pdfminer.__file__
        }
    except Exception as e:
        debug_info["libraries"]["pdfminer.six"] = {
            "available": False,
            "error": str(e)
        }
    
    try:
        import boto3
        debug_info["libraries"]["boto3"] = {
            "available": True,
            "version": boto3.__version__,
            "path": boto3.__file__
        }
    except Exception as e:
        debug_info["libraries"]["boto3"] = {
            "available": False,
            "error": str(e)
        }
    
    return debug_info

def lambda_handler(event, context):
    # Read PDF from S3 instead of deployment package
    s3_bucket = os.getenv('S3_BUCKET', 'your-bucket-name')
    s3_key = os.getenv('S3_PDF_KEY', 'pdfs/Namecheap.pdf')
    
    result = {}
    
    try:
        # Download PDF from S3
        s3_client = boto3.client('s3')
        print(f"📥 Downloading PDF from s3://{s3_bucket}/{s3_key}")
        
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        content = response['Body'].read()
        
        print(f"✅ Downloaded {len(content)} bytes from S3")
        
        # Get debug info
        result["debug_info"] = get_pdf_debug_info(content, f"s3://{s3_bucket}/{s3_key}")
        
        # Try PyPDF2 extraction
        try:
            import PyPDF2
            import io
            pdf = PyPDF2.PdfReader(io.BytesIO(content))
            text_content = []
            
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(f"Page {i+1}: {page_text[:100]}")
                except Exception as e:
                    text_content.append(f"Page {i+1} error: {str(e)}")
            
            result["extraction"] = {
                "success": bool(text_content),
                "pages_with_text": len(text_content),
                "preview": text_content[:2]
            }
            
        except Exception as e:
            result["extraction"] = {"success": False, "error": str(e)}
            
    except Exception as e:
        result["error"] = f"Failed to read PDF from S3: {e}"
    
    # Print to CloudWatch logs
    print(json.dumps(result, indent=2, default=str))
    
    # Return as Lambda response
    return {
        "statusCode": 200,
        "body": json.dumps(result, default=str)
    } 