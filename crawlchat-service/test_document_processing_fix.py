#!/usr/bin/env python3
"""
Test script to manually trigger document processing for existing crawl tasks.
"""

import asyncio
import sys
import os
sys.path.append('common/src')

from common.src.core.database import mongodb
from common.src.services.document_service import DocumentService
from common.src.services.document_processing_service import DocumentProcessingService
from common.src.services.storage_service import get_storage_service
from common.src.models.documents import Document
from pathlib import Path
import uuid

async def test_document_processing():
    """Test document processing for existing crawl tasks."""
    await mongodb.connect()
    
    # Get a completed task with S3 files
    task = await mongodb.get_collection('tasks').find_one({
        'status': 'completed',
        's3_files': {'$exists': True, '$ne': []}
    })
    
    if not task:
        print("No completed tasks with S3 files found")
        return
    
    task_id = task['task_id']
    print(f"Testing document processing for task: {task_id}")
    print(f"S3 files: {task.get('s3_files', [])}")
    
    # Check if documents already exist
    existing_docs = await mongodb.get_collection('documents').find({'task_id': task_id}).to_list(length=None)
    print(f"Existing documents for this task: {len(existing_docs)}")
    
    if existing_docs:
        print("Documents already exist, skipping processing")
        return
    
    # Try to process documents
    try:
        document_service = DocumentService()
        processing_service = DocumentProcessingService()
        storage_service = get_storage_service()
        
        processed_count = 0
        
        for s3_file_path in task.get('s3_files', []):
            try:
                print(f"Processing document: {s3_file_path}")
                
                # Create document record
                filename = Path(s3_file_path).name
                document_id = str(uuid.uuid4())
                
                # Create document record
                document_data = Document(
                    document_id=document_id,
                    filename=filename,
                    file_path=s3_file_path,
                    file_size=0,  # Will be updated after processing
                    document_type=DocumentService()._get_document_type(Path(filename).suffix),
                    user_id=task['user_id'],
                    task_id=task_id,
                    metadata={
                        "source_url": task.get('url', ''),
                        "crawl_task_id": task_id,
                        "crawled_at": task.get('completed_at', '').isoformat() if task.get('completed_at') else None
                    }
                )
                
                # Create document in database
                document = await document_service.create_document(document_data)
                print(f"Created document record: {document.document_id}")
                
                # Get document content from S3
                content = await storage_service.get_file_content(s3_file_path)
                
                if content:
                    # Decode content
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                    
                    # Clean HTML content if needed
                    if filename.endswith('.html'):
                        import re
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Process document with vector store (includes deduplication)
                    result = await processing_service.process_document_with_vector_store(
                        document_id=document.document_id,
                        content=content,
                        filename=filename,
                        metadata={
                            "source_url": task.get('url', ''),
                            "crawl_task_id": task_id,
                            "source": "crawled_document"
                        }
                    )
                    
                    status = result.get("status")
                    success = status in ["success", "duplicate_skipped"]
                    
                    if success:
                        processed_count += 1
                        if status == "duplicate_skipped":
                            print(f"Document is duplicate, skipped embedding: {document.document_id}")
                        else:
                            print(f"Successfully processed document: {document.document_id}")
                    else:
                        print(f"Failed to process document: {document.document_id}")
                else:
                    print(f"Could not read content for {s3_file_path}")
                    
            except Exception as e:
                print(f"Error processing document {s3_file_path}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Processed {processed_count}/{len(task.get('s3_files', []))} documents for task {task_id}")
        
    except Exception as e:
        print(f"Error in document processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_processing()) 