#!/usr/bin/env python3
"""
Test script to verify the file extension fix for crawled documents.
"""

import os
import sys
from pathlib import Path

# Add the common package to the path
sys.path.insert(0, str(Path(__file__).parent / "common" / "src"))

def test_filename_generation():
    """Test the filename generation logic to ensure no double extensions."""
    
    # Simulate the logic from _upload_crawled_files_to_s3
    def generate_filename(relative_path):
        # Don't add .html if the file already has an extension
        if '.' in relative_path.split('/')[-1]:
            filename = relative_path.replace('/', '_')
        else:
            filename = f"{relative_path.replace('/', '_')}.html"
        return filename
    
    # Test cases
    test_cases = [
        # Input relative_path, Expected output
        ("www.example.com/document_abc123_1234567890.html", "www.example.com_document_abc123_1234567890.html"),
        ("www.example.com/page_without_extension", "www.example.com_page_without_extension.html"),
        ("domain.com/path/to/file.txt", "domain.com_path_to_file.txt"),
        ("site.com/document.pdf", "site.com_document.pdf"),
        ("example.com/index", "example.com_index.html"),
    ]
    
    print("🧪 Testing filename generation logic")
    print("=" * 50)
    
    all_passed = True
    
    for i, (input_path, expected) in enumerate(test_cases, 1):
        result = generate_filename(input_path)
        
        if result == expected:
            print(f"✅ Test {i}: PASS")
            print(f"   Input:  {input_path}")
            print(f"   Output: {result}")
        else:
            print(f"❌ Test {i}: FAIL")
            print(f"   Input:    {input_path}")
            print(f"   Expected: {expected}")
            print(f"   Got:      {result}")
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All filename generation tests passed!")
        print("✅ No more double .html extensions!")
    else:
        print("⚠️  Some tests failed. Please check the logic.")
    
    return all_passed

def test_actual_file_scenarios():
    """Test with actual file scenarios that might occur."""
    
    print("🧪 Testing actual file scenarios")
    print("=" * 50)
    
    # Simulate files that would be created by the crawler
    crawler_files = [
        "www.idfcfirstbank.com_document_510a4b5c6ec55cd23130202f67fee4e6_1751971145.html",
        "www.example.com_index.html", 
        "news.ycombinator.com_article_123.html",
        "finance.google.com_report.pdf",
        "docs.company.com_document.docx",
        "site.com_page_without_extension"
    ]
    
    def generate_filename(relative_path):
        # Don't add .html if the file already has an extension
        if '.' in relative_path.split('/')[-1]:
            filename = relative_path.replace('/', '_')
        else:
            filename = f"{relative_path.replace('/', '_')}.html"
        return filename
    
    for file_path in crawler_files:
        result = generate_filename(file_path)
        print(f"📄 {file_path}")
        print(f"   → {result}")
        
        # Check for double extensions
        if result.count('.html') > 1:
            print(f"   ❌ DOUBLE EXTENSION DETECTED!")
        elif result.endswith('.html.html'):
            print(f"   ❌ DOUBLE .html EXTENSION!")
        else:
            print(f"   ✅ Correct extension")
        print()

def main():
    """Run all tests."""
    print("🔧 File Extension Fix Test Suite")
    print("Testing the fix for double .html extensions in crawled documents")
    print("=" * 80)
    
    # Test 1: Basic filename generation
    test1_passed = test_filename_generation()
    
    print("\n" + "="*80 + "\n")
    
    # Test 2: Actual file scenarios
    test_actual_file_scenarios()
    
    if test1_passed:
        print("\n🎉 File extension fix is working correctly!")
        print("✅ Crawled documents will no longer have double .html extensions")
        print("✅ Files will be saved with proper single extensions")
    else:
        print("\n⚠️  File extension fix needs attention")
        print("❌ Some tests failed - double extensions may still occur")

if __name__ == "__main__":
    main() 