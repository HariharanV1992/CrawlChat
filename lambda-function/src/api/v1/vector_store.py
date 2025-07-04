"""
Vector Store API endpoints for advanced document search and processing.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
import logging

from src.services.vector_store_service import vector_store_service
from src.services.document_processing_service import document_processing_service
from src.api.dependencies import get_current_user
from src.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vector-store", tags=["Vector Store"])

@router.post("/search")
async def search_documents(
    query: str = Body(..., description="Search query"),
    max_results: int = Body(10, description="Maximum number of results"),
    score_threshold: Optional[float] = Body(None, description="Minimum similarity score"),
    current_user: User = Depends(get_current_user)
):
    """Search documents using semantic similarity."""
    try:
        results = await document_processing_service.search_documents(
            query=query,
            max_results=max_results,
            score_threshold=score_threshold
        )
        
        return {
            "success": True,
            "data": results,
            "message": f"Found {results['total_results']} results"
        }
        
    except Exception as e:
        logger.error(f"[API] Error in document search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/search-with-summary")
async def search_with_summary(
    query: str = Body(..., description="Search query"),
    max_results: int = Body(5, description="Maximum number of results for summary"),
    current_user: User = Depends(get_current_user)
):
    """Search documents and generate a synthesized summary."""
    try:
        # Get search results
        search_results = await document_processing_service.search_documents(
            query=query,
            max_results=max_results
        )
        
        # Generate summary
        summary = await document_processing_service.get_document_summary(
            query=query,
            max_results=max_results
        )
        
        return {
            "success": True,
            "data": {
                "search_results": search_results,
                "summary": summary
            },
            "message": "Search and summary completed successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error in search with summary: {e}")
        raise HTTPException(status_code=500, detail=f"Search with summary failed: {str(e)}")

@router.post("/process-document")
async def process_document(
    content: str = Body(..., description="Document content"),
    filename: str = Body(..., description="Document filename"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Document metadata"),
    current_user: User = Depends(get_current_user)
):
    """Process a single document and add it to the vector store."""
    try:
        import uuid
        
        document_id = str(uuid.uuid4())
        
        result = await document_processing_service.process_document_with_vector_store(
            document_id=document_id,
            content=content,
            filename=filename,
            metadata=metadata
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
        
        return {
            "success": True,
            "data": result,
            "message": "Document processed successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/process-crawled-data")
async def process_crawled_data(
    crawled_data: List[Dict[str, Any]] = Body(..., description="List of crawled data"),
    current_user: User = Depends(get_current_user)
):
    """Process multiple crawled data entries."""
    try:
        results = await document_processing_service.process_crawled_data(crawled_data)
        
        # Count successes and failures
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = len(results) - success_count
        
        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total_processed": len(results),
                    "successful": success_count,
                    "failed": error_count
                }
            },
            "message": f"Processed {len(results)} documents ({success_count} successful, {error_count} failed)"
        }
        
    except Exception as e:
        logger.error(f"[API] Error processing crawled data: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.post("/batch-process-files")
async def batch_process_files(
    file_paths: List[str] = Body(..., description="List of file paths to process"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Metadata for all files"),
    current_user: User = Depends(get_current_user)
):
    """Process multiple files in batch."""
    try:
        results = await document_processing_service.batch_process_files(
            file_paths=file_paths,
            metadata=metadata
        )
        
        # Count successes and failures
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = len(results) - success_count
        
        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total_files": len(file_paths),
                    "successful": success_count,
                    "failed": error_count
                }
            },
            "message": f"Processed {len(file_paths)} files ({success_count} successful, {error_count} failed)"
        }
        
    except Exception as e:
        logger.error(f"[API] Error in batch file processing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch file processing failed: {str(e)}")

@router.get("/documents")
async def list_documents(
    limit: int = Query(50, description="Number of documents to return"),
    skip: int = Query(0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user)
):
    """List processed documents with pagination."""
    try:
        documents = await document_processing_service.list_processed_documents(
            limit=limit,
            skip=skip
        )
        
        return {
            "success": True,
            "data": documents,
            "message": f"Retrieved {len(documents)} documents"
        }
        
    except Exception as e:
        logger.error(f"[API] Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document from the vector store."""
    try:
        success = await document_processing_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/stats")
async def get_vector_store_stats(
    current_user: User = Depends(get_current_user)
):
    """Get vector store statistics."""
    try:
        stats = await document_processing_service.get_vector_store_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "success": True,
            "data": stats,
            "message": "Vector store statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting vector store stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/files")
async def list_vector_store_files(
    current_user: User = Depends(get_current_user)
):
    """List all files in the vector store."""
    try:
        files = await vector_store_service.list_vector_store_files()
        
        return {
            "success": True,
            "data": files,
            "message": f"Retrieved {len(files)} files from vector store"
        }
        
    except Exception as e:
        logger.error(f"[API] Error listing vector store files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_vector_store_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file from the vector store."""
    try:
        success = await vector_store_service.delete_vector_store_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "success": True,
            "message": f"File {file_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error deleting vector store file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.post("/create-vector-store")
async def create_vector_store(
    name: str = Body(..., description="Vector store name"),
    current_user: User = Depends(get_current_user)
):
    """Create a new vector store."""
    try:
        vector_store_id = await vector_store_service.create_vector_store(name=name)
        
        return {
            "success": True,
            "data": {"vector_store_id": vector_store_id},
            "message": f"Vector store '{name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error creating vector store: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create vector store: {str(e)}")

@router.get("/vector-store-info")
async def get_vector_store_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the current vector store."""
    try:
        info = await vector_store_service.get_vector_store_info()
        
        return {
            "success": True,
            "data": info,
            "message": "Vector store information retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting vector store info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get vector store info: {str(e)}")

@router.post("/update-file-attributes/{file_id}")
async def update_file_attributes(
    file_id: str,
    attributes: Dict[str, Any] = Body(..., description="New attributes"),
    current_user: User = Depends(get_current_user)
):
    """Update attributes of a file in the vector store."""
    try:
        success = await vector_store_service.update_vector_store_attributes(
            file_id=file_id,
            attributes=attributes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "success": True,
            "message": f"Attributes updated for file {file_id}"
        }
        
    except Exception as e:
        logger.error(f"[API] Error updating file attributes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update attributes: {str(e)}") 