#!/usr/bin/env python3
"""
Lambda PDF Extraction Debug Script
Identifies differences between local and Lambda environments
"""

import sys
import os
import hashlib
import logging
import platform
import importlib
from pathlib import Path
from typing import Dict, Any, List

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

from common.src.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def check_environment_info() -> Dict[str, Any]:
    """Check environment information for debugging."""
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "node": platform.node(),
        "environment_vars": {
            "AWS_LAMBDA_FUNCTION_NAME": os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            "AWS_LAMBDA_FUNCTION_VERSION": os.getenv("AWS_LAMBDA_FUNCTION_VERSION"),
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"),
            "AWS_LAMBDA_LOG_GROUP_NAME": os.getenv("AWS_LAMBDA_LOG_GROUP_NAME"),
            "AWS_LAMBDA_RUNTIME_API": os.getenv("AWS_LAMBDA_RUNTIME_API"),
            "LAMBDA_TASK_ROOT": os.getenv("LAMBDA_TASK_ROOT"),
            "LAMBDA_RUNTIME_DIR": os.getenv("LAMBDA_RUNTIME_DIR"),
            "AWS_EXECUTION_ENV": os.getenv("AWS_EXECUTION_ENV"),
        }
    }
    return info

def check_pdf_libraries() -> Dict[str, Any]:
    """Check PDF processing library availability and versions."""
    libraries = {}
    
    # Check PyPDF2
    try:
        import PyPDF2
        libraries["PyPDF2"] = {
            "available": True,
            "version": getattr(PyPDF2, "__version__", "unknown"),
            "path": PyPDF2.__file__,
            "import_success": True
        }
    except ImportError as e:
        libraries["PyPDF2"] = {
            "available": False,
            "error": str(e),
            "import_success": False
        }
    except Exception as e:
        libraries["PyPDF2"] = {
            "available": True,
            "version": "unknown",
            "error": str(e),
            "import_success": False
        }
    
    # Check pdfminer.six
    try:
        import pdfminer
        from pdfminer.high_level import extract_text
        libraries["pdfminer.six"] = {
            "available": True,
            "version": getattr(pdfminer, "__version__", "unknown"),
            "path": pdfminer.__file__,
            "import_success": True,
            "extract_text_available": True
        }
    except ImportError as e:
        libraries["pdfminer.six"] = {
            "available": False,
            "error": str(e),
            "import_success": False
        }
    except Exception as e:
        libraries["pdfminer.six"] = {
            "available": True,
            "version": "unknown",
            "error": str(e),
            "import_success": False
        }
    
    # Check boto3 (AWS SDK)
    try:
        import boto3
        libraries["boto3"] = {
            "available": True,
            "version": boto3.__version__,
            "path": boto3.__file__,
            "import_success": True
        }
    except ImportError as e:
        libraries["boto3"] = {
            "available": False,
            "error": str(e),
            "import_success": False
        }
    
    # Check other dependencies
    dependencies = [
        "io", "asyncio", "time", "uuid", "typing", "enum", 
        "botocore", "logging", "json", "base64"
    ]
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            libraries[dep] = {
                "available": True,
                "path": getattr(module, "__file__", "built-in"),
                "import_success": True
            }
        except ImportError as e:
            libraries[dep] = {
                "available": False,
                "error": str(e),
                "import_success": False
            }
    
    return libraries

def check_file_system_access() -> Dict[str, Any]:
    """Check file system access and permissions."""
    fs_info = {}
    
    # Check temp directory
    import tempfile
    try:
        temp_dir = tempfile.gettempdir()
        fs_info["temp_directory"] = {
            "path": temp_dir,
            "writable": os.access(temp_dir, os.W_OK),
            "readable": os.access(temp_dir, os.R_OK),
            "exists": os.path.exists(temp_dir)
        }
    except Exception as e:
        fs_info["temp_directory"] = {"error": str(e)}
    
    # Check current working directory
    try:
        cwd = os.getcwd()
        fs_info["current_working_directory"] = {
            "path": cwd,
            "writable": os.access(cwd, os.W_OK),
            "readable": os.access(cwd, os.R_OK),
            "exists": os.path.exists(cwd)
        }
    except Exception as e:
        fs_info["current_working_directory"] = {"error": str(e)}
    
    # Check if we can create test files
    try:
        test_file = tempfile.NamedTemporaryFile(delete=False)
        test_file.write(b"test content")
        test_file.close()
        fs_info["file_creation"] = {
            "success": True,
            "test_file": test_file.name
        }
        # Clean up
        os.unlink(test_file.name)
    except Exception as e:
        fs_info["file_creation"] = {
            "success": False,
            "error": str(e)
        }
    
    return fs_info

def check_memory_limits() -> Dict[str, Any]:
    """Check memory availability and limits."""
    memory_info = {}
    
    try:
        import psutil
        memory_info["psutil_available"] = True
        memory_info["virtual_memory"] = {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
            "used": psutil.virtual_memory().used,
            "free": psutil.virtual_memory().free
        }
    except ImportError:
        memory_info["psutil_available"] = False
    
    # Check Lambda memory limit
    lambda_memory = os.getenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE")
    if lambda_memory:
        memory_info["lambda_memory_limit_mb"] = int(lambda_memory)
        memory_info["lambda_memory_limit_bytes"] = int(lambda_memory) * 1024 * 1024
    
    return memory_info

def test_pdf_extraction_with_debug(pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Test PDF extraction with detailed debugging information."""
    debug_info = {
        "file_info": {
            "filename": filename,
            "size_bytes": len(pdf_bytes),
            "size_mb": len(pdf_bytes) / (1024 * 1024),
            "md5_hash": hashlib.md5(pdf_bytes).hexdigest(),
            "first_20_bytes": pdf_bytes[:20].hex(),
            "last_20_bytes": pdf_bytes[-20:].hex(),
            "is_pdf_header": pdf_bytes.startswith(b'%PDF-'),
            "has_eof_marker": b'%%EOF' in pdf_bytes[-1000:]
        },
        "extraction_tests": {}
    }
    
    # Test PyPDF2
    try:
        import PyPDF2
        import io
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        debug_info["extraction_tests"]["PyPDF2"] = {
            "success": True,
            "page_count": len(pdf_reader.pages),
            "info": str(pdf_reader.metadata) if pdf_reader.metadata else "No metadata",
            "is_encrypted": pdf_reader.is_encrypted
        }
        
        # Try to extract text from first page
        if len(pdf_reader.pages) > 0:
            try:
                first_page_text = pdf_reader.pages[0].extract_text()
                debug_info["extraction_tests"]["PyPDF2"]["first_page_text_length"] = len(first_page_text)
                debug_info["extraction_tests"]["PyPDF2"]["first_page_text_preview"] = first_page_text[:100]
            except Exception as e:
                debug_info["extraction_tests"]["PyPDF2"]["first_page_extraction_error"] = str(e)
        
    except Exception as e:
        debug_info["extraction_tests"]["PyPDF2"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Test pdfminer.six
    try:
        from pdfminer.high_level import extract_text
        import io
        
        text_content = extract_text(io.BytesIO(pdf_bytes))
        
        debug_info["extraction_tests"]["pdfminer.six"] = {
            "success": True,
            "extracted_text_length": len(text_content),
            "extracted_text_preview": text_content[:100],
            "has_content": bool(text_content.strip())
        }
        
    except Exception as e:
        debug_info["extraction_tests"]["pdfminer.six"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    return debug_info

def generate_debug_report() -> str:
    """Generate a comprehensive debug report."""
    report_lines = []
    
    report_lines.append("🔍 LAMBDA PDF EXTRACTION DEBUG REPORT")
    report_lines.append("=" * 60)
    
    # Environment info
    env_info = check_environment_info()
    report_lines.append("\n🌍 ENVIRONMENT INFORMATION:")
    report_lines.append(f"Python Version: {env_info['python_version']}")
    report_lines.append(f"Platform: {env_info['platform']}")
    report_lines.append(f"Architecture: {env_info['architecture']}")
    report_lines.append(f"System: {env_info['system']}")
    report_lines.append(f"Machine: {env_info['machine']}")
    
    # Lambda-specific info
    if env_info['environment_vars']['AWS_LAMBDA_FUNCTION_NAME']:
        report_lines.append("\n🚀 LAMBDA ENVIRONMENT:")
        for key, value in env_info['environment_vars'].items():
            if value:
                report_lines.append(f"{key}: {value}")
    else:
        report_lines.append("\n💻 LOCAL ENVIRONMENT (not Lambda)")
    
    # Library info
    libraries = check_pdf_libraries()
    report_lines.append("\n📚 PDF PROCESSING LIBRARIES:")
    for lib_name, lib_info in libraries.items():
        if lib_info.get("import_success"):
            version = lib_info.get("version", "unknown")
            report_lines.append(f"✅ {lib_name}: {version}")
        else:
            error = lib_info.get("error", "unknown error")
            report_lines.append(f"❌ {lib_name}: {error}")
    
    # File system info
    fs_info = check_file_system_access()
    report_lines.append("\n💾 FILE SYSTEM ACCESS:")
    for key, info in fs_info.items():
        if "error" in info:
            report_lines.append(f"❌ {key}: {info['error']}")
        else:
            status = "✅" if info.get("writable", False) else "⚠️"
            report_lines.append(f"{status} {key}: {info.get('path', 'N/A')}")
    
    # Memory info
    memory_info = check_memory_limits()
    report_lines.append("\n🧠 MEMORY INFORMATION:")
    if memory_info.get("psutil_available"):
        vm = memory_info["virtual_memory"]
        report_lines.append(f"Total Memory: {vm['total'] / (1024**3):.2f} GB")
        report_lines.append(f"Available Memory: {vm['available'] / (1024**3):.2f} GB")
        report_lines.append(f"Memory Usage: {vm['percent']:.1f}%")
    
    if memory_info.get("lambda_memory_limit_mb"):
        report_lines.append(f"Lambda Memory Limit: {memory_info['lambda_memory_limit_mb']} MB")
    
    return "\n".join(report_lines)

def main():
    """Main debug function."""
    print("🚀 Starting Lambda PDF Extraction Debug...")
    
    # Generate comprehensive report
    report = generate_debug_report()
    print(report)
    
    # Test with a sample PDF if available
    test_pdf_path = "Namecheap.pdf"  # Use the existing test file
    if os.path.exists(test_pdf_path):
        print(f"\n📄 TESTING WITH SAMPLE PDF: {test_pdf_path}")
        try:
            with open(test_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            debug_info = test_pdf_extraction_with_debug(pdf_bytes, test_pdf_path)
            
            print(f"File Size: {debug_info['file_info']['size_bytes']} bytes ({debug_info['file_info']['size_mb']:.2f} MB)")
            print(f"MD5 Hash: {debug_info['file_info']['md5_hash']}")
            print(f"PDF Header: {'✅' if debug_info['file_info']['is_pdf_header'] else '❌'}")
            print(f"EOF Marker: {'✅' if debug_info['file_info']['has_eof_marker'] else '❌'}")
            
            for method, result in debug_info['extraction_tests'].items():
                if result.get("success"):
                    print(f"✅ {method}: Success")
                    if "page_count" in result:
                        print(f"   Pages: {result['page_count']}")
                    if "extracted_text_length" in result:
                        print(f"   Text Length: {result['extracted_text_length']} characters")
                else:
                    print(f"❌ {method}: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Error testing PDF: {e}")
    else:
        print(f"\n⚠️ Test PDF not found: {test_pdf_path}")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("1. Compare this output with Lambda logs")
    print("2. Check for missing dependencies in Lambda package")
    print("3. Verify memory limits are sufficient")
    print("4. Test with smaller PDFs first")
    print("5. Add more detailed logging to Lambda function")

if __name__ == "__main__":
    main() 