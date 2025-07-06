"""
Vector Store Service using OpenAI's Vector Store API.
Provides advanced semantic search capabilities with automatic chunking and embedding.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid
import asyncio
from pathlib import Path

from openai import OpenAI
from common.src.models.documents import Document
from common.src.core.database import mongodb
from common.src.core.config import config
from common.src.core.exceptions import VectorStoreError, DatabaseError
from common.src.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing vector stores using OpenAI's Vector Store API."""
    
    def __init__(self):
        self.client = self._initialize_openai_client()
        self.vector_store_id = None
        self.session_vector_stores = {}  # Cache for session-specific vector stores
    
    def _initialize_openai_client(self) -> OpenAI:
        """Initialize OpenAI client with API key from environment variables."""
        try:
            import os
            
            # Get API key from environment variable
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not found")
            
            return OpenAI(api_key=api_key)
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error initializing OpenAI client: {e}")
            raise
    
    async def create_vector_store(self, name: str = "Stock Market Data") -> str:
        """Create a new vector store."""
        try:
            logger.info(f"[VECTOR_STORE] Creating vector store: {name}")
            
            vector_store = self.client.vector_stores.create(name=name)
            self.vector_store_id = vector_store.id
            
            logger.info(f"[VECTOR_STORE] Created vector store with ID: {self.vector_store_id}")
            return self.vector_store_id
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error creating vector store: {e}")
            raise
    
    async def get_or_create_vector_store(self, name: str = "Stock Market Data") -> str:
        """Get existing vector store or create a new one."""
        try:
            # First, try to list existing vector stores
            vector_stores = self.client.vector_stores.list()
            
            # Look for a vector store with the given name
            for store in vector_stores.data:
                if store.name == name:
                    self.vector_store_id = store.id
                    logger.info(f"[VECTOR_STORE] Using existing vector store: {store.id}")
                    return self.vector_store_id
            
            # If not found, create a new one
            return await self.create_vector_store(name)
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error getting or creating vector store: {e}")
            raise

    async def get_or_create_session_vector_store(self, session_id: str) -> str:
        """Get or create a session-specific vector store."""
        try:
            # Check if we already have this session's vector store cached
            if session_id in self.session_vector_stores:
                logger.info(f"[VECTOR_STORE] Using cached session vector store: {self.session_vector_stores[session_id]}")
                return self.session_vector_stores[session_id]
            
            # Create a unique name for this session's vector store
            session_store_name = f"Session_{session_id[:8]}_Data"
            
            # First, try to list existing vector stores
            vector_stores = self.client.vector_stores.list()
            
            # Look for a vector store with the session-specific name
            for store in vector_stores.data:
                if store.name == session_store_name:
                    self.session_vector_stores[session_id] = store.id
                    logger.info(f"[VECTOR_STORE] Using existing session vector store: {store.id}")
                    return store.id
            
            # If not found, create a new session-specific vector store
            vector_store_id = await self.create_vector_store(session_store_name)
            self.session_vector_stores[session_id] = vector_store_id
            logger.info(f"[VECTOR_STORE] Created new session vector store: {vector_store_id}")
            return vector_store_id
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error getting or creating session vector store: {e}")
            raise
    
    async def upload_file_to_vector_store(
        self, 
        file_path: str, 
        vector_store_id: Optional[str] = None
    ) -> str:
        """Upload a file to the vector store with automatic chunking and embedding."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"[VECTOR_STORE] Uploading file: {file_path}")
            
            # Upload file with automatic chunking
            with open(file_path, "rb") as file:
                vector_store_file = self.client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store_id,
                    file=file
                )
            
            logger.info(f"[VECTOR_STORE] Successfully uploaded file: {vector_store_file.id}")
            return vector_store_file.id
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error uploading file {file_path}: {e}")
            raise
    
    async def upload_text_to_vector_store(
        self, 
        text: str, 
        filename: str,
        vector_store_id: Optional[str] = None
    ) -> str:
        """Upload text content to the vector store by creating a temporary file."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            # Create a temporary file with the text content
            # Use /tmp directory in Lambda environment
            temp_dir = Path("/tmp")
            if not temp_dir.exists():
                temp_dir = Path("temp_fix_deploy")  # Fallback for local development
                temp_dir.mkdir(exist_ok=True)
            
            temp_file_path = temp_dir / f"{filename}_{uuid.uuid4().hex[:8]}.txt"
            
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            try:
                # Upload the temporary file
                file_id = await self.upload_file_to_vector_store(
                    str(temp_file_path), 
                    vector_store_id
                )
                return file_id
            finally:
                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error uploading text content: {e}")
            raise
    
    async def search_vector_store(
        self, 
        query: str, 
        vector_store_id: Optional[str] = None,
        max_results: int = 10,
        score_threshold: Optional[float] = None,
        rewrite_query: bool = True
    ) -> Dict[str, Any]:
        """Perform semantic search on the vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            logger.info(f"[VECTOR_STORE] Searching for: {query[:50]}...")
            
            # Prepare search parameters
            search_params = {
                "vector_store_id": vector_store_id,
                "query": query,
                "max_num_results": max_results,
                "rewrite_query": rewrite_query
            }
            
            if score_threshold is not None:
                search_params["ranking_options"] = {
                    "score_threshold": score_threshold
                }
            
            # Check if vector store has files before searching
            try:
                files = await self.list_vector_store_files(vector_store_id)
                logger.info(f"[VECTOR_STORE] Vector store has {len(files)} files before search")
                if files:
                    processed_files = 0
                    for file in files:
                        status = file.get('status', 'Unknown')
                        logger.info(f"[VECTOR_STORE] File: {file.get('filename', 'Unknown')} - Status: {status}")
                        # Check for both 'processed' and 'completed' status
                        if status in ['processed', 'completed']:
                            processed_files += 1
                    logger.info(f"[VECTOR_STORE] {processed_files}/{len(files)} files are processed and ready for search")
                    
                    # If no files are processed, try to wait a bit and retry
                    if processed_files == 0:
                        logger.warning(f"[VECTOR_STORE] No files are processed yet, waiting 3 seconds and retrying...")
                        import asyncio
                        await asyncio.sleep(3)
                        
                        # Retry once
                        files = await self.list_vector_store_files(vector_store_id)
                        processed_files = 0
                        for file in files:
                            status = file.get('status', 'Unknown')
                            if status in ['processed', 'completed']:
                                processed_files += 1
                        
                        if processed_files == 0:
                            logger.warning(f"[VECTOR_STORE] Still no files processed after retry, but will attempt search anyway")
                            # Don't return empty results immediately, try the search anyway
                    else:
                        # If files are processed, add a small delay to ensure they're fully ready
                        logger.info(f"[VECTOR_STORE] Files are processed, adding 1 second delay to ensure readiness")
                        import asyncio
                        await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[VECTOR_STORE] Error listing files before search: {e}")
            
            # Perform search with retry mechanism
            logger.info(f"[VECTOR_STORE] Search params: {search_params}")
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    results = self.client.vector_stores.search(**search_params)
                    logger.info(f"[VECTOR_STORE] Search API call successful (attempt {attempt + 1})")
                    break
                except Exception as search_error:
                    logger.error(f"[VECTOR_STORE] Search API error (attempt {attempt + 1}): {search_error}")
                    if attempt < max_retries - 1:
                        logger.info(f"[VECTOR_STORE] Retrying in {retry_delay} seconds...")
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"[VECTOR_STORE] All search attempts failed")
                        # If search fails, return empty results
                        return {
                            "results": [],
                            "search_query": query,
                            "has_more": False
                        }
            
            logger.info(f"[VECTOR_STORE] Found {len(results.data)} results")
            logger.info(f"[VECTOR_STORE] Results data type: {type(results.data)}")
            if results.data:
                logger.info(f"[VECTOR_STORE] First result keys: {list(results.data[0].model_dump().keys()) if hasattr(results.data[0], 'model_dump') else 'No model_dump'}")
            
            return {
                "results": [result.model_dump() for result in results.data],
                "search_query": results.search_query,
                "has_more": results.has_more,
                "next_page": results.next_page
            }
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error searching vector store: {e}")
            raise
    
    async def synthesize_response(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]],
        model: str = "gpt-4o-mini"
    ) -> str:
        """Synthesize a response based on search results."""
        try:
            if not search_results:
                return "I couldn't find any relevant information to answer your question."
            
            # Format the search results
            formatted_results = self._format_search_results(search_results)
            
            # Create completion with the search results as context
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate answers based on the provided sources. Always cite your sources and be concise but thorough."
                    },
                    {
                        "role": "user",
                        "content": f"Sources:\n{formatted_results}\n\nQuery: {query}\n\nPlease provide a comprehensive answer based on the sources above."
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error synthesizing response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for the LLM."""
        formatted = []
        
        for i, result in enumerate(results, 1):
            file_info = f"Source {i}: {result.get('filename', 'Unknown file')}"
            if result.get('file_id'):
                file_info += f" (ID: {result['file_id']})"
            
            content_parts = []
            for content in result.get('content', []):
                if content.get('type') == 'text':
                    content_parts.append(content['text'])
            
            content_text = "\n".join(content_parts)
            score = result.get('score', 0)
            
            formatted.append(f"{file_info}\nRelevance Score: {score:.3f}\nContent:\n{content_text}\n")
        
        return "\n---\n".join(formatted)
    
    async def list_vector_store_files(
        self, 
        vector_store_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all files in the vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            files = self.client.vector_stores.files.list(vector_store_id=vector_store_id)
            return [file.model_dump() for file in files.data]
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error listing vector store files: {e}")
            raise
    
    async def delete_vector_store_file(
        self, 
        file_id: str, 
        vector_store_id: Optional[str] = None
    ) -> bool:
        """Delete a file from the vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            self.client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            logger.info(f"[VECTOR_STORE] Deleted file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error deleting file {file_id}: {e}")
            return False
    
    async def delete_vector_store(self, vector_store_id: Optional[str] = None) -> bool:
        """Delete the entire vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id
            
            if not vector_store_id:
                logger.warning("[VECTOR_STORE] No vector store ID provided for deletion")
                return False
            
            self.client.vector_stores.delete(vector_store_id=vector_store_id)
            
            logger.info(f"[VECTOR_STORE] Deleted vector store: {vector_store_id}")
            self.vector_store_id = None
            return True
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error deleting vector store: {e}")
            return False
    
    async def get_vector_store_info(self, vector_store_id: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            store_info = self.client.vector_stores.retrieve(vector_store_id=vector_store_id)
            return store_info.model_dump()
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error getting vector store info: {e}")
            raise
    
    async def update_vector_store_attributes(
        self, 
        file_id: str,
        attributes: Dict[str, Any],
        vector_store_id: Optional[str] = None
    ) -> bool:
        """Update attributes of a file in the vector store."""
        try:
            if not vector_store_id:
                vector_store_id = self.vector_store_id or await self.get_or_create_vector_store()
            
            self.client.vector_stores.files.update(
                vector_store_id=vector_store_id,
                file_id=file_id,
                attributes=attributes
            )
            
            logger.info(f"[VECTOR_STORE] Updated attributes for file: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Error updating file attributes: {e}")
            return False

# Global instance
vector_store_service = VectorStoreService() 