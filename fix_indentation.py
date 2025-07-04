#!/usr/bin/env python3
"""
Script to fix indentation issues in document_service.py
"""

import re

def fix_indentation():
    with open('src/services/document_service.py', 'r') as f:
        content = f.read()
    
    # Fix specific indentation issues
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix line 152: content = await storage_service.get_file_content(document.file_path)
        if i == 151:  # 0-indexed
            if line.strip().startswith('content = await storage_service.get_file_content'):
                line = '            ' + line.strip()
        
        # Fix line 164: return text_content
        elif i == 163:  # 0-indexed
            if line.strip().startswith('return text_content'):
                line = '                    ' + line.strip()
        
        # Fix line 259: return f"Content extraction not implemented for {document.document_type}"
        elif i == 258:  # 0-indexed
            if line.strip().startswith('return f"Content extraction not implemented'):
                line = '            ' + line.strip()
        
        # Fix line 470: extension_map = {
        elif i == 469:  # 0-indexed
            if line.strip().startswith('extension_map = {'):
                line = '            ' + line.strip()
        
        # Fix line 487: content_types = {
        elif i == 486:  # 0-indexed
            if line.strip().startswith('content_types = {'):
                line = '            ' + line.strip()
        
        # Fix line 506: doc = await mongodb.get_collection("documents").find_one
        elif i == 505:  # 0-indexed
            if line.strip().startswith('doc = await mongodb.get_collection'):
                line = '            ' + line.strip()
        
        # Fix line 514: docs = [Document(**doc) async for doc in cursor]
        elif i == 513:  # 0-indexed
            if line.strip().startswith('docs = [Document(**doc) async for doc in cursor]'):
                line = '            ' + line.strip()
        
        # Fix line 515: total_count = await mongodb.get_collection("documents").count_documents
        elif i == 514:  # 0-indexed
            if line.strip().startswith('total_count = await mongodb.get_collection'):
                line = '            ' + line.strip()
        
        # Fix line 516: return DocumentList(documents=docs, total_count=total_count)
        elif i == 515:  # 0-indexed
            if line.strip().startswith('return DocumentList(documents=docs, total_count=total_count)'):
                line = '            ' + line.strip()
        
        # Fix line 517: except Exception as e:
        elif i == 516:  # 0-indexed
            if line.strip().startswith('except Exception as e:'):
                line = '        ' + line.strip()
        
        # Fix line 518: logger.error(f"Error listing documents for user {user_id}: {e}")
        elif i == 517:  # 0-indexed
            if line.strip().startswith('logger.error(f"Error listing documents for user'):
                line = '            ' + line.strip()
        
        # Fix line 519: return DocumentList(documents=[], total_count=0)
        elif i == 518:  # 0-indexed
            if line.strip().startswith('return DocumentList(documents=[], total_count=0)'):
                line = '            ' + line.strip()
        
        # Fix line 521: return None
        elif i == 520:  # 0-indexed
            if line.strip().startswith('return None'):
                line = '        ' + line.strip()
        
        # Fix line 522: except Exception as e:
        elif i == 521:  # 0-indexed
            if line.strip().startswith('except Exception as e:'):
                line = '        ' + line.strip()
        
        # Fix line 523: logger.error(f"Error getting document {document_id}: {e}")
        elif i == 522:  # 0-indexed
            if line.strip().startswith('logger.error(f"Error getting document'):
                line = '            ' + line.strip()
        
        # Fix line 524: return None
        elif i == 523:  # 0-indexed
            if line.strip().startswith('return None'):
                line = '        ' + line.strip()
        
        fixed_lines.append(line)
    
    # Write the fixed content
    with open('src/services/document_service.py', 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed indentation issues in document_service.py")

if __name__ == "__main__":
    fix_indentation() 