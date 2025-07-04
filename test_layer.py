#!/usr/bin/env python3
"""
Test script to verify Lambda layer dependencies work correctly.
"""

import sys
import os

# Add the layer to Python path
layer_path = "./lambda-layer-lambda-compatible/python"
if layer_path not in sys.path:
    sys.path.insert(0, layer_path)

def test_imports():
    """Test all critical imports."""
    tests = [
        ("pydantic_core._pydantic_core", "Pydantic Core"),
        ("pydantic", "Pydantic"),
        ("fastapi", "FastAPI"),
        ("motor", "Motor (MongoDB)"),
        ("PyPDF2", "PyPDF2"),
        ("pdfminer.high_level", "PDFMiner"),
        ("openai", "OpenAI"),
        ("mangum", "Mangum"),
        ("cryptography", "Cryptography"),
    ]
    
    results = []
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✅ {description} imported successfully")
            results.append((description, True, None))
        except Exception as e:
            print(f"❌ {description} failed: {e}")
            results.append((description, False, str(e)))
    
    return results

def test_pydantic_specific():
    """Test Pydantic-specific functionality."""
    try:
        import pydantic_core._pydantic_core
        print("✅ pydantic_core._pydantic_core imported successfully")
        
        from pydantic import BaseModel
        print("✅ Pydantic BaseModel imported successfully")
        
        # Test creating a simple model
        class TestModel(BaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        print(f"✅ Pydantic model created: {model}")
        
        return True
    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Lambda Layer Dependencies")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")
    print()
    
    # Test basic imports
    results = test_imports()
    print()
    
    # Test Pydantic specifically
    pydantic_ok = test_pydantic_specific()
    print()
    
    # Summary
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print("📊 Summary:")
    print(f"Successful imports: {successful}/{total}")
    print(f"Pydantic working: {'Yes' if pydantic_ok else 'No'}")
    
    if successful == total and pydantic_ok:
        print("🎉 All tests passed! Layer should work in Lambda.")
    else:
        print("⚠️  Some tests failed. Check the errors above.") 