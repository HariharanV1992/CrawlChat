#!/usr/bin/env python3
"""
Script to update import statements across the service.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path):
    """Update import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update common imports
        content = re.sub(
            r'from common\.src\.',
            'from common.src.',
            content
        )
        
        # Update lambda service imports
        content = re.sub(
            r'from src\.',
            'from lambda_service.src.',
            content
        )
        
        # Update crawler service imports
        content = re.sub(
            r'from crawler\.',
            'from crawler_service.src.crawler.',
            content
        )
        
        # Update relative imports
        content = re.sub(
            r'from \.\.',
            'from lambda_service.src',
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update imports across all Python files."""
    print("🔄 Starting import updates...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Define services to process
    services = ['lambda-service', 'crawler-service']
    
    updated_count = 0
    total_count = 0
    
    for service in services:
        service_path = project_root / service
        if not service_path.exists():
            print(f"⚠️  Service directory not found: {service}")
            continue
            
        print(f"\n📁 Processing {service}...")
        
        # Find all Python files
        python_files = list(service_path.rglob("*.py"))
        
        for py_file in python_files:
            total_count += 1
            if update_imports_in_file(py_file):
                updated_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Total files processed: {total_count}")
    print(f"   Files updated: {updated_count}")
    print(f"   Files unchanged: {total_count - updated_count}")
    
    if updated_count > 0:
        print("✅ Import updates completed!")
    else:
        print("ℹ️  No import updates needed.")

if __name__ == "__main__":
    main() 