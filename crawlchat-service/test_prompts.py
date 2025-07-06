#!/usr/bin/env python3
"""
Test script to verify the updated prompts work for all document types
"""

import sys
import os

# Add the common package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common', 'src'))

from common.src.utils.prompts import PromptManager

def test_prompt_detection():
    """Test that different query types are detected correctly"""
    
    test_cases = [
        # Technical document queries
        ("What is the API specification in this document?", "technical_document"),
        ("Explain the code architecture", "technical_document"),
        ("How does the database work?", "technical_document"),
        
        # Legal document queries
        ("What are the terms and conditions?", "legal_document"),
        ("Explain the contract clauses", "legal_document"),
        ("What are my legal obligations?", "legal_document"),
        
        # Educational content queries
        ("How do I learn this concept?", "educational_content"),
        ("Explain this tutorial", "educational_content"),
        ("What does this guide teach?", "educational_content"),
        
        # Financial queries (should still work)
        ("Analyze the stock performance", "stock_analysis"),
        ("What is the P/E ratio?", "stock_analysis"),
        ("Calculate my salary", "calculation"),
        
        # General queries
        ("What is this document about?", "general"),
        ("Tell me about the content", "general"),
        ("Summarize this document", "summary"),
        
        # Concise queries
        ("Give me a one line answer", "concise_response"),
        ("Brief summary", "concise_response"),
    ]
    
    print("Testing prompt detection:")
    print("=" * 50)
    
    for query, expected_type in test_cases:
        detected_type = PromptManager.detect_query_type(query)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_type}, Detected: {detected_type}")
        print()

def test_prompt_generation():
    """Test that appropriate prompts are generated"""
    
    test_queries = [
        "What is the API specification?",
        "Explain the contract terms",
        "How do I learn this concept?",
        "What is this document about?",
        "Calculate my salary",
        "Give me a one line answer"
    ]
    
    print("Testing prompt generation:")
    print("=" * 50)
    
    for query in test_queries:
        prompt = PromptManager.get_prompt_for_query(query)
        query_type = PromptManager.detect_query_type(query)
        
        print(f"Query: '{query}'")
        print(f"Type: {query_type}")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Prompt preview: {prompt[:100]}...")
        print("-" * 30)

def test_general_prompt():
    """Test that the general prompt handles non-financial content"""
    
    general_prompt = PromptManager.get_general_prompt()
    
    print("Testing general prompt:")
    print("=" * 50)
    
    # Check that it doesn't assume financial content
    if "Do NOT assume the document is financial" in general_prompt:
        print("✅ General prompt correctly warns against assuming financial content")
    else:
        print("❌ General prompt doesn't warn against assuming financial content")
    
    # Check that it mentions different document types
    if "technical" in general_prompt.lower() and "legal" in general_prompt.lower():
        print("✅ General prompt mentions different document types")
    else:
        print("❌ General prompt doesn't mention different document types")
    
    print(f"General prompt length: {len(general_prompt)} characters")

def test_summary_prompt():
    """Test that the summary prompt handles different document types"""
    
    summary_prompt = PromptManager.get_summary_prompt()
    
    print("Testing summary prompt:")
    print("=" * 50)
    
    # Check that it mentions different document types
    document_types = ["Financial", "Technical", "Legal", "Educational", "General"]
    for doc_type in document_types:
        if doc_type in summary_prompt:
            print(f"✅ Summary prompt mentions {doc_type} documents")
        else:
            print(f"❌ Summary prompt doesn't mention {doc_type} documents")
    
    print(f"Summary prompt length: {len(summary_prompt)} characters")

if __name__ == "__main__":
    print("Testing Updated Prompts for All Document Types")
    print("=" * 60)
    print()
    
    test_prompt_detection()
    print()
    test_prompt_generation()
    print()
    test_general_prompt()
    print()
    test_summary_prompt()
    
    print()
    print("✅ All tests completed!") 