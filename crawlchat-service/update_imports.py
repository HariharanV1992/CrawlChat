#!/usr/bin/env python3
"""
Script to update all import statements to use the common package.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Update import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update imports
        original_content = content
        
        # Update from src. imports to common.src.
        content = re.sub(r'from src\.', 'from common.src.', content)
        content = re.sub(r'import src\.', 'import common.src.', content)
        
        # Update direct package imports to common.src.
        content = re.sub(r'from core\.', 'from common.src.core.', content)
        content = re.sub(r'from models\.', 'from common.src.models.', content)
        content = re.sub(r'from services\.', 'from common.src.services.', content)
        content = re.sub(r'from utils\.', 'from common.src.utils.', content)
        content = re.sub(r'from crawler\.', 'from common.src.crawler.', content)
        
        # Update api imports
        content = re.sub(r'from api\.', 'from common.src.api.', content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def find_python_files(directory):
    """Find all Python files in a directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directory to avoid circular imports
        if 'common' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to update all imports."""
    services = ['lambda-service', 'crawler-service', 'preprocessor-service']
    
    for service in services:
        service_path = f"{service}/src"
        print(f"Checking path: {service_path}")
        if os.path.exists(service_path):
            print(f"\nProcessing {service}...")
            python_files = find_python_files(service_path)
            print(f"Found {len(python_files)} Python files")
            updated_count = 0
            
            for file_path in python_files:
                if update_imports_in_file(file_path):
                    updated_count += 1
            
            print(f"Updated {updated_count} files in {service}")
        else:
            print(f"Path not found: {service_path}")

if __name__ == "__main__":
    main() 