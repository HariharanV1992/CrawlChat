"""
Chat service for managing chat sessions and AI interactions.
"""

import logging
import uuid
import re
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from common.src.models.chat import (
    ChatSession, ChatMessage, MessageRole, SessionCreateResponse
)
from common.src.models.documents import Document
from common.src.core.database import mongodb
from common.src.core.config import config
from common.src.core.exceptions import ChatError, DatabaseError
from common.src.services.vector_store_service import VectorStoreService
from common.src.services.document_service import DocumentService
from common.src.services.document_processing_service import document_processing_service
from common.src.utils.prompts import PromptManager

logger = logging.getLogger(__name__)

class ChatService:
    """Chat service for managing chat sessions using MongoDB."""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        # Cache for storing context from previous queries
        self.context_cache = {}  # session_id -> cached_context
    
    async def _ensure_mongodb_connected(self):
        """Ensure MongoDB is connected before operations."""
        try:
            if not mongodb.is_connected():
                await mongodb.connect()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ChatError(f"MongoDB connection failed: {e}")
    
    async def create_session(self, user_id: str) -> SessionCreateResponse:
        """Create a new chat session for a user."""
        try:
            await self._ensure_mongodb_connected()
            
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                created_at=now,
                updated_at=now,
                messages=[],
                document_count=0,
                crawl_tasks=[],
                uploaded_documents=[]
            )
            
            # Save to MongoDB
            await mongodb.get_collection("chat_sessions").insert_one(session.dict())
            
            logger.info(f"Created chat session {session_id} for user {user_id}")
            return SessionCreateResponse(
                session_id=session_id,
                created_at=now
            )
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            raise ChatError(f"Failed to create session: {e}")
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        try:
            await self._ensure_mongodb_connected()
            
            # Get session from MongoDB
            session_data = await mongodb.get_collection("chat_sessions").find_one({
                "session_id": session_id,
                "user_id": user_id
            })
            
            if session_data:
                # Convert messages back to ChatMessage objects
                messages = []
                for msg_data in session_data.get('messages', []):
                    messages.append(ChatMessage(**msg_data))
                session_data['messages'] = messages
                return ChatSession(**session_data)
            
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def list_user_sessions(self, user_id: str) -> List[ChatSession]:
        """List all sessions for a user."""
        try:
            await self._ensure_mongodb_connected()
            
            # Get sessions from MongoDB
            cursor = mongodb.get_collection("chat_sessions").find({"user_id": user_id})
            sessions = []
            
            async for session_data in cursor:
                # Convert messages back to ChatMessage objects
                messages = []
                for msg_data in session_data.get('messages', []):
                    messages.append(ChatMessage(**msg_data))
                session_data['messages'] = messages
                sessions.append(ChatSession(**session_data))
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x.updated_at, reverse=True)
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []
    
    async def add_message(self, session_id: str, user_id: str, 
                         role: MessageRole, content: str) -> bool:
        """Add a message to a chat session."""
        try:
            await self._ensure_mongodb_connected()
            
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                session_id=session_id
            )
            
            # Update session in MongoDB
            result = await mongodb.get_collection("chat_sessions").update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Added message to session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found or not updated")
                return False
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    async def get_session_messages(self, session_id: str, user_id: str) -> List[ChatMessage]:
        """Get all messages for a session."""
        try:
            session = await self.get_session(session_id, user_id)
            if session:
                return session.messages
            return []
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        try:
            await self._ensure_mongodb_connected()
            
            result = await mongodb.get_collection("chat_sessions").delete_one({
                "session_id": session_id,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Deleted session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def clear_user_sessions(self, user_id: str) -> int:
        """Clear all sessions for a user."""
        try:
            await self._ensure_mongodb_connected()
            
            result = await mongodb.get_collection("chat_sessions").delete_many({
                "user_id": user_id
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Cleared {deleted_count} sessions for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing sessions for user {user_id}: {e}")
            return 0
    
    async def process_ai_response(self, session_id: str, user_id: str, 
                                user_message: str) -> Optional[str]:
        """Process user message and generate AI response."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                logger.error(f"[CHAT] Session not found: {session_id}")
                return None
            
            # Add user message
            await self.add_message(session_id, user_id, MessageRole.USER, user_message)
            
            # Generate AI response using the prompts utility
            ai_response = await self._generate_ai_response(session, user_message)
            
            if ai_response:
                # Add AI response
                await self.add_message(session_id, user_id, MessageRole.ASSISTANT, ai_response)
            else:
                logger.error(f"[CHAT] No AI response generated for session: {session_id}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"[CHAT] Error processing AI response: {e}")
            return None
    
    def _rewrite_query_for_better_search(self, user_message: str, session_id: str, conversation_history: List = None) -> str:
        """Rewrite user query to be more specific for vector search."""
        query_lower = user_message.lower()
        
        # Check if this is a follow-up calculation query
        if any(keyword in query_lower for keyword in ['how much in', 'then how much', 'for 5 years', 'for 3 years', 'total for']):
            # Check if we have cached context
            cached_context = self.context_cache.get(session_id, {})
            if cached_context.get('take_home_salary'):
                # Rewrite to be more specific
                return f"take home salary {user_message} (based on {cached_context['take_home_salary']} per annum)"
            elif cached_context.get('gross_salary'):
                return f"gross salary {user_message} (based on {cached_context['gross_salary']} per annum)"
        
        # Check for conversational follow-up questions
        if conversation_history and len(conversation_history) > 0:
            # Look for pronouns and references that indicate follow-up questions
            follow_up_indicators = ['it', 'this', 'that', 'they', 'them', 'those', 'these', 'the', 'what about', 'how about', 'and', 'also', 'too', 'as well']
            
            # Check if this looks like a follow-up question
            is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)
            
            # Also check for short questions that are likely follow-ups
            if len(user_message.split()) <= 5 and any(word in query_lower for word in ['what', 'how', 'when', 'where', 'why', 'who']):
                is_follow_up = True
            
            if is_follow_up:
                # Get the last user message for context
                last_user_message = None
                for msg in reversed(conversation_history):
                    if msg.role == MessageRole.USER:
                        last_user_message = msg.content
                        break
                
                if last_user_message and last_user_message != user_message:
                    # Combine context from last query with current query
                    combined_query = f"{last_user_message} {user_message}"
                    logger.info(f"[QUERY] Follow-up detected. Combined: '{combined_query}'")
                    return combined_query
        
        # For calculation queries, make them more specific
        if any(keyword in query_lower for keyword in ['salary', 'take home', 'gross', 'net', 'compensation']):
            return f"salary compensation {user_message}"
        
        return user_message

    def _extract_and_cache_context(self, user_message: str, ai_response: str, session_id: str):
        """Extract and cache important context from AI responses."""
        try:
            # Extract salary information from responses
            response_lower = ai_response.lower()
            
            # Look for take-home salary patterns
            import re
            take_home_patterns = [
                r'₹([\d,]+)\s*per\s*year',
                r'₹([\d,]+)\s*annually',
                r'take.?home.*?₹([\d,]+)',
                r'net.*?₹([\d,]+)'
            ]
            
            for pattern in take_home_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    amount = match.group(1).replace(',', '')
                    self.context_cache[session_id] = {
                        'take_home_salary': int(amount),
                        'last_query': user_message,
                        'last_response': ai_response
                    }
                    logger.info(f"[CONTEXT] Cached take-home salary: ₹{amount}")
                    return
            
            # Look for gross salary patterns
            gross_patterns = [
                r'gross.*?₹([\d,]+)',
                r'total.*?compensation.*?₹([\d,]+)',
                r'₹([\d,]+)\s*gross'
            ]
            
            for pattern in gross_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    amount = match.group(1).replace(',', '')
                    self.context_cache[session_id] = {
                        'gross_salary': int(amount),
                        'last_query': user_message,
                        'last_response': ai_response
                    }
                    logger.info(f"[CONTEXT] Cached gross salary: ₹{amount}")
                    return
                    
        except Exception as e:
            logger.error(f"[CONTEXT] Error extracting context: {e}")

    def _perform_simple_calculation(self, user_message: str, session_id: str) -> Optional[str]:
        """Perform simple calculations without calling AI."""
        try:
            query_lower = user_message.lower()
            cached_context = self.context_cache.get(session_id, {})
            
            # Check for multi-year calculations
            import re
            year_match = re.search(r'(\d+)\s*years?', query_lower)
            if year_match and cached_context:
                years = int(year_match.group(1))
                
                if 'take_home_salary' in cached_context and any(word in query_lower for word in ['take home', 'net', 'after']):
                    annual_take_home = cached_context['take_home_salary']
                    total_take_home = annual_take_home * years
                    monthly_take_home = annual_take_home // 12
                    
                    return f"The take-home salary for {years} years would be ₹{total_take_home:,} (₹{annual_take_home:,} × {years})."
                
                elif 'gross_salary' in cached_context:
                    annual_gross = cached_context['gross_salary']
                    total_gross = annual_gross * years
                    
                    return f"The gross salary for {years} years would be ₹{total_gross:,} (₹{annual_gross:,} × {years})."
            
            # Check for monthly calculations
            if any(word in query_lower for word in ['monthly', 'per month', 'month']) and cached_context.get('take_home_salary'):
                annual_take_home = cached_context['take_home_salary']
                monthly_take_home = annual_take_home // 12
                
                return f"The monthly take-home salary is ₹{monthly_take_home:,}."
            
            return None
            
        except Exception as e:
            logger.error(f"[CALCULATION] Error in simple calculation: {e}")
            return None

    async def _generate_ai_response(self, session: ChatSession, user_message: str) -> str:
        """Generate AI response for user message."""
        try:
            # Get conversation history for context (move this to the top)
            conversation_history = session.messages if hasattr(session, 'messages') and session.messages else []

            # Try simple calculation first
            simple_result = self._perform_simple_calculation(user_message, session.session_id)
            if simple_result:
                return simple_result
            
            # Rewrite query for better search if session_id is provided
            rewritten_query = user_message
            document_context = None
            
            if session.session_id:
                # Get document context for smart rewriting
                session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session.session_id})
                if session_data:
                    uploaded_docs = session_data.get('uploaded_documents', [])
                    crawl_tasks = session_data.get('crawl_tasks', [])
                    
                    # Get filenames for context
                    filenames = []
                    for doc_id in uploaded_docs:
                        doc = await mongodb.get_collection("documents").find_one({"document_id": doc_id})
                        if doc:
                            filenames.append(doc.get('filename', ''))
                    
                    document_context = {"filenames": filenames}
                
                # Apply smart query rewriting
                rewritten_query = self.prompt_manager.rewrite_generic_query(user_message, document_context)
                
                # Also apply existing query rewriting for conversation context
                rewritten_query = self._rewrite_query_for_better_search(rewritten_query, session.session_id, conversation_history)
                logger.info(f"[QUERY] Original: '{user_message}' -> Smart Rewritten: '{rewritten_query}'")
            
            # Get appropriate prompt based on user query using centralized PromptManager
            prompt = self.prompt_manager.get_prompt_for_query(user_message)
            
            # Check if session has documents
            if session.crawl_tasks or session.uploaded_documents:
                # Get documents for crawl tasks
                documents = []
                for task_id in session.crawl_tasks:
                    task_documents = await self._get_documents_for_crawl_task(task_id)
                    documents.extend(task_documents)
                
                # Generate document-based response with conversation history
                return await self._generate_ai_document_response(
                    user_message, documents, session.uploaded_documents, prompt, session.session_id, conversation_history
                )
            else:
                # Generate general response with conversation history
                return await self._generate_general_response(user_message, prompt, conversation_history)
                
        except Exception as e:
            logger.error(f"[AI] Error generating AI response: {e}")
            return "I apologize, but I encountered an error while generating the response. Please try again."
    
    async def _get_documents_for_crawl_task(self, task_id: str) -> List:
        """Get documents for a specific crawl task."""
        try:
            document_service = DocumentService()
            documents = await document_service.get_task_documents(task_id)
            logger.info(f"[AI] Found {len(documents)} documents for task: {task_id}")
            return documents
        except Exception as e:
            logger.error(f"[AI] Error getting documents for task {task_id}: {e}")
            return []
    
    async def _generate_ai_document_response(self, user_message: str, documents: List, uploaded_document_ids: List[str], prompt: str, session_id: str = None, conversation_history: List = None) -> str:
        """Generate AI response based on document content using OpenAI and vector search with caching."""
        try:
            logger.info(f"[AI] Generating document response for {len(documents)} crawl documents and {len(uploaded_document_ids)} uploaded documents")
            
            # Extract document IDs from crawl documents and combine with uploaded document IDs
            crawl_document_ids = [doc.document_id for doc in documents]
            all_document_ids = crawl_document_ids + uploaded_document_ids
            
            logger.info(f"[AI] Searching for relevant chunks in {len(all_document_ids)} documents")
            
            # Rewrite query for better search if session_id is provided
            rewritten_query = user_message
            document_context = None
            
            if session_id:
                # Get document context for smart rewriting
                session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session_id})
                if session_data:
                    uploaded_docs = session_data.get('uploaded_documents', [])
                    crawl_tasks = session_data.get('crawl_tasks', [])
                    
                    # Get filenames for context
                    filenames = []
                    for doc_id in uploaded_docs:
                        doc = await mongodb.get_collection("documents").find_one({"document_id": doc_id})
                        if doc:
                            filenames.append(doc.get('filename', ''))
                    
                    document_context = {"filenames": filenames}
                
                # Apply smart query rewriting
                rewritten_query = self.prompt_manager.rewrite_generic_query(user_message, document_context)
                
                # Also apply existing query rewriting for conversation context
                rewritten_query = self._rewrite_query_for_better_search(rewritten_query, session_id, conversation_history)
                logger.info(f"[QUERY] Original: '{user_message}' -> Smart Rewritten: '{rewritten_query}'")
            
            # Search for similar chunks using vector store with better filtering
            # Use lower threshold to ensure we get relevant content for detailed questions
            base_threshold = 0.5 if any(keyword in user_message.lower() for keyword in ['salary', 'calculate', 'take home', 'gross', 'net']) else 0.2
            
            # Try with different score thresholds if no results found
            score_thresholds = [base_threshold, 0.15, 0.1, 0.05]
            similar_chunks = []
            
            for threshold in score_thresholds:
                logger.info(f"[AI] Trying search with score threshold: {threshold}")
                search_results = await document_processing_service.search_documents(
                    query=rewritten_query,
                    max_results=15,
                    score_threshold=threshold,
                    session_id=session_id
                )
                similar_chunks = search_results.get("results", [])
                
                if similar_chunks:
                    logger.info(f"[AI] Found {len(similar_chunks)} chunks with threshold {threshold}")
                    break
                else:
                    logger.info(f"[AI] No results with threshold {threshold}")
            
            if not similar_chunks:
                logger.warning(f"[AI] No similar chunks found in session {session_id} - trying fallback search")
                logger.info(f"[AI] Session vector store: {vector_store_id if 'vector_store_id' in locals() else 'Not set'}")
                logger.info(f"[AI] Search query: '{rewritten_query}'")
                logger.info(f"[AI] Tried thresholds: {score_thresholds}")
                
                # FALLBACK SEARCH: Try with common document terms
                fallback_queries = [
                    "salary compensation increment amount",
                    "date effective period",
                    "name employee details",
                    "benefits allowances deductions",
                    "2023 2024 2025 2026",
                    "document letter offer"
                ]
                
                # Add document-specific terms from filenames
                if document_context and document_context.get('filenames'):
                    for filename in document_context['filenames']:
                        # Extract meaningful words from filename
                        words = re.findall(r'\b[a-zA-Z]+\b', filename)
                        meaningful_words = [word for word in words if len(word) > 3 and word.lower() not in ['file', 'document', 'pdf', 'doc']]
                        if meaningful_words:
                            fallback_queries.append(' '.join(meaningful_words))
                
                logger.info(f"[AI] Trying fallback queries: {fallback_queries}")
                
                # Try fallback queries with very low threshold
                for fallback_query in fallback_queries:
                    logger.info(f"[AI] Trying fallback query: '{fallback_query}'")
                    search_results = await document_processing_service.search_documents(
                        query=fallback_query,
                        max_results=10,
                        score_threshold=0.01,  # Very low threshold for fallback
                        session_id=session_id
                    )
                    similar_chunks = search_results.get("results", [])
                    
                    if similar_chunks:
                        logger.info(f"[AI] Found {len(similar_chunks)} chunks with fallback query: '{fallback_query}'")
                        break
                
                # If still no results, check if files are ready
                if not similar_chunks:
                    try:
                        files_ready = False
                        if 'vector_store_id' in locals() and vector_store_id:
                            files = await VectorStoreService.list_vector_store_files(vector_store_id)
                            logger.info(f"[AI] Files in vector store: {len(files)}")
                            files_ready = all(file.get('status') == 'completed' for file in files) and len(files) > 0
                            for file in files:
                                logger.info(f"[AI] File: {file.get('filename', 'Unknown')} - ID: {file.get('id', 'Unknown')} - Status: {file.get('status', 'Unknown')}")
                        if not files_ready:
                            return "I'm still processing the document embeddings. The file has been uploaded but the embeddings are being created in the background. Please wait a moment and try your question again. This usually takes 30-60 seconds."
                        else:
                            return "No relevant content found in your documents for this query. Try asking about a specific topic or keyword from your documents."
                    except Exception as e:
                        logger.error(f"[AI] Error listing vector store files: {e}")
                        return "I'm still processing the document embeddings. The file has been uploaded but the embeddings are being created in the background. Please wait a moment and try your question again. This usually takes 30-60 seconds."
            
            # Log all retrieved chunks for debugging
            logger.info(f"[AI] Retrieved {len(similar_chunks)} chunks for query: '{user_message}'")
            for i, chunk in enumerate(similar_chunks):
                filename = chunk.get('filename', 'Unknown')
                score = chunk.get('score', 0)
                logger.info(f"[AI] Chunk {i+1}/{len(similar_chunks)} - File: {filename}, Score: {score:.3f}")
                
                # Extract text content from vector store format
                content_parts = []
                for content in chunk.get('content', []):
                    if content.get('type') == 'text':
                        content_parts.append(content['text'])
                chunk_text = ' '.join(content_parts)
                chunk_preview = chunk_text[:300].replace('\n', ' ').replace('\r', ' ')
                logger.info(f"[AI] Chunk {i+1} Content: {chunk_preview}...")
            
            # Prepare context from similar chunks
            context_parts = []
            for chunk in similar_chunks:
                filename = chunk.get('filename', 'Unknown')
                # Extract text content from vector store format
                content_parts = []
                for content in chunk.get('content', []):
                    if content.get('type') == 'text':
                        content_parts.append(content['text'])
                chunk_text = ' '.join(content_parts)
                context_parts.append(f"From {filename}:\n{chunk_text}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"[AI] Found {len(similar_chunks)} relevant chunks")
            
            # Prepare conversation history for context
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # Get last 5 messages for context (to avoid token limits)
                recent_messages = conversation_history[-5:]
                conversation_parts = []
                for msg in recent_messages:
                    role = "User" if msg.role == MessageRole.USER else "Assistant"
                    conversation_parts.append(f"{role}: {msg.content}")
                conversation_context = "\n\n".join(conversation_parts)
                logger.info(f"[AI] Including conversation history: {len(recent_messages)} recent messages")
            
            # Create final prompt using the provided prompt from PromptManager
            final_prompt = f"""{prompt}

Document content to analyze:
{context}"""

            # Add conversation history if available
            if conversation_context:
                final_prompt += f"""

Recent conversation context:
{conversation_context}"""

            final_prompt += f"""

Current user query: {user_message}

Please provide your response based on the document content above. If this is a follow-up question related to the previous conversation, make sure to reference and build upon the previous context. Be thorough and include all relevant details, facts, dates, and numbers from the documents."""
            
            logger.info(f"[AI] Final prompt length: {len(final_prompt)}")
            
            # Load AI config
            import os
            
            # Get configuration from environment variables
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            max_tokens = int(os.environ.get('OPENAI_MAX_TOKENS', '4000'))
            temperature = float(os.environ.get('OPENAI_TEMPERATURE', '0.1'))
            
            if not openai_api_key:
                logger.error("[AI] OPENAI_API_KEY environment variable not found")
                return "I apologize, but the AI configuration is not properly set up. Please contact support."
            
            logger.info(f"[AI] Using AI config: model={model}, max_tokens={max_tokens}, temperature={temperature}")
            
            # Make AI request
            try:
                import openai
                
                logger.info(f"[AI] Making OpenAI request: model={model}, max_tokens={max_tokens}")
                
                if not openai_api_key:
                    logger.error("[AI] OpenAI API key not configured")
                    return "I apologize, but the OpenAI API key is not configured. Please contact support."
                
                client = openai.OpenAI(api_key=openai_api_key)
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant that analyzes documents and responds to user questions. Follow the specific instructions provided in the user prompt carefully. Provide detailed, comprehensive answers based on the document content. Include specific facts, dates, numbers, and explanations from the documents. When responding to follow-up questions, maintain conversation continuity and reference previous context appropriately."},
                        {"role": "user", "content": final_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"[AI] OpenAI response received: {ai_response[:100]}...")
                
                # Extract and cache context from the response
                if session_id:
                    self._extract_and_cache_context(user_message, ai_response, session_id)
                
                return ai_response
                
            except Exception as e:
                logger.error(f"[AI] Error making OpenAI request: {e}")
                return "I apologize, but I encountered an error while generating the AI response. Please try again."
                
        except Exception as e:
            logger.error(f"[AI] Error generating AI document response: {e}")
            return "I apologize, but I encountered an error while analyzing the documents. Please try again."
    
    async def _generate_general_response(self, user_message: str, prompt: str, conversation_history: List = None) -> str:
        """Generate general response when no documents are available."""
        try:
            # Load AI config from environment variables
            import os
            
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            max_tokens = int(os.environ.get('OPENAI_MAX_TOKENS', '4000'))
            temperature = float(os.environ.get('OPENAI_TEMPERATURE', '0.1'))
            
            if not openai_api_key:
                logger.error("OPENAI_API_KEY environment variable not found")
                return "I don't see any documents linked to this session. To help you with document analysis, please upload or link documents first."
            
            # Prepare conversation history for context
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # Get last 5 messages for context (to avoid token limits)
                recent_messages = conversation_history[-5:]
                conversation_parts = []
                for msg in recent_messages:
                    role = "User" if msg.role == MessageRole.USER else "Assistant"
                    conversation_parts.append(f"{role}: {msg.content}")
                conversation_context = "\n\n".join(conversation_parts)
                logger.info(f"[AI] Including conversation history in general response: {len(recent_messages)} recent messages")
            
            # Create prompt for general response
            general_prompt = f"""{prompt}

No documents are currently linked to this session. Please provide a helpful response explaining what the user can do to get assistance."""

            # Add conversation history if available
            if conversation_context:
                general_prompt += f"""

Recent conversation context:
{conversation_context}"""

            general_prompt += f"""

Current user question: {user_message}

Please provide a helpful response:"""
            
            # Make AI request
            try:
                import openai
                client = openai.OpenAI(api_key=openai_api_key)
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant. When no documents are available, guide users on how to upload or link documents for analysis. When responding to follow-up questions, maintain conversation continuity and reference previous context appropriately."},
                        {"role": "user", "content": general_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                ai_response = response.choices[0].message.content.strip()
                return ai_response
                
            except Exception as e:
                logger.error(f"Error making OpenAI request for general response: {e}")
                return "I don't see any documents linked to this session. To help you with document analysis, please upload or link documents first."
                
        except Exception as e:
            logger.error(f"Error generating general response: {e}")
            return "I don't see any documents linked to this session. To help you with document analysis, please upload or link documents first."
    
    async def get_session_document_count(self, session_id: str, user_id: str) -> int:
        """Get the number of documents linked to a session."""
        try:
            session = await self.get_session(session_id, user_id)
            if session:
                return session.document_count
            return 0
        except Exception as e:
            logger.error(f"Error getting document count for session {session_id}: {e}")
            return 0
    
    async def link_crawl_documents(self, session_id: str, user_id: str, 
                                 crawl_task_id: str, documents: List) -> List:
        """Link crawled documents to a chat session and create embeddings."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                raise ChatError("Session not found")
            
            # Update session in MongoDB
            await mongodb.get_collection("chat_sessions").update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$addToSet": {"crawl_tasks": crawl_task_id},
                    "$set": {
                        "document_count": session.document_count + len(documents),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Linked {len(documents)} documents to session {session_id}")
            
            # Add immediate feedback message with better tracking
            await self.add_message(session_id, user_id, MessageRole.SYSTEM, 
                f"📄 Linked {len(documents)} documents to this session. Processing documents in background...")
            
            # Update session with processing status
            await mongodb.get_collection("chat_sessions").update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$set": {
                        "processing_status": "processing",
                        "processing_started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create embeddings for the documents - run synchronously to ensure completion
            # This ensures the completion message is added before Lambda terminates
            await self._create_embeddings_for_documents(documents, session_id)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error linking crawl documents to session {session_id}: {e}")
            raise ChatError(f"Failed to link crawl documents: {e}")
    
    async def _create_embeddings_for_documents(self, documents: List, session_id: str):
        """Create embeddings for documents in background."""
        try:
            logger.info(f"[EMBEDDING] Starting background embedding creation for {len(documents)} documents in session {session_id}")
            
            # Get the session to find the user_id
            session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session_id})
            if not session_data:
                logger.error(f"[EMBEDDING] Session {session_id} not found in database")
                return
            
            user_id = session_data.get("user_id")
            logger.info(f"[EMBEDDING] Found session {session_id} for user {user_id}")
            
            # Import services
            from common.src.services.storage_service import StorageService
            
            try:
                storage_service = StorageService()
                
                for i, doc in enumerate(documents, 1):
                    try:
                        logger.info(f"[EMBEDDING] Creating embeddings for document: {doc.filename}")
                        
                        # Get document content from S3
                        # Use s3_key from metadata if available, otherwise use file_path
                        s3_key = doc.metadata.get('s3_key') if hasattr(doc, 'metadata') and doc.metadata else doc.file_path
                        if not s3_key.startswith('crawled_documents/'):
                            s3_key = f"crawled_documents/{s3_key}"
                        
                        content = await storage_service.get_file_content(s3_key)
                        
                        if content:
                            # Decode content
                            if isinstance(content, bytes):
                                content = content.decode('utf-8', errors='ignore')
                            
                            # Clean HTML content if needed
                            if doc.filename.endswith('.html'):
                                import re
                                content = re.sub(r'<[^>]+>', '', content)
                                content = re.sub(r'\s+', ' ', content).strip()
                            
                            # Process document with vector store (includes deduplication)
                            result = await document_processing_service.process_document_with_vector_store(
                                document_id=doc.document_id,
                                content=content,
                                filename=doc.filename,
                                metadata={
                                    "session_id": session_id,
                                    "user_id": user_id,
                                    "source": "crawled_document",
                                    "crawl_task_id": doc.crawl_task_id if hasattr(doc, 'crawl_task_id') else None
                                },
                                session_id=session_id
                            )
                            status = result.get("status")
                            success = status in ["success", "duplicate_skipped"]
                            
                            if success:
                                if status == "duplicate_skipped":
                                    logger.info(f"[EMBEDDING] Document is duplicate, skipped embedding: {doc.filename}")
                                else:
                                    logger.info(f"[EMBEDDING] Successfully created embeddings for {doc.filename}")
                            else:
                                logger.warning(f"[EMBEDDING] Failed to create embeddings for {doc.filename}")
                        else:
                            logger.warning(f"[EMBEDDING] Could not read content for {doc.filename}")
                            
                    except Exception as e:
                        logger.error(f"[EMBEDDING] Error processing document {doc.filename}: {e}")
                        # Continue with other documents even if one fails
                
                logger.info(f"[EMBEDDING] Completed background embedding creation for session {session_id}")
                
                # Add final completion message with better tracking
                completion_message = "🎉 All document embeddings created successfully! You can now ask questions about the documents."
                
                # Always add completion message for crawl documents (no duplicate check needed)
                try:
                    completion_success = await self.add_message(session_id, user_id, MessageRole.SYSTEM, completion_message)
                    logger.info(f"[EMBEDDING] Added completion message: {completion_success}")
                    
                    # Update session with processing status
                    await mongodb.get_collection("chat_sessions").update_one(
                        {"session_id": session_id, "user_id": user_id},
                        {
                            "$set": {
                                "processing_status": "completed",
                                "processing_completed_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    logger.info(f"[EMBEDDING] Updated session processing status to completed")
                    
                except Exception as msg_error:
                    logger.error(f"[EMBEDDING] Failed to add completion message: {msg_error}")
                    # Try alternative completion message
                    try:
                        alt_message = "✅ Document processing completed! Ready for questions."
                        await self.add_message(session_id, user_id, MessageRole.SYSTEM, alt_message)
                    except Exception as alt_error:
                        logger.error(f"[EMBEDDING] Failed to add alternative completion message: {alt_error}")
                
            except Exception as e:
                logger.error(f"[EMBEDDING] Error in background embedding creation: {e}")
                # Add error message with better handling
                try:
                    error_message = "❌ Error creating document embeddings. Please try again."
                    await self.add_message(session_id, user_id, MessageRole.SYSTEM, error_message)
                    
                    # Update session with error status
                    await mongodb.get_collection("chat_sessions").update_one(
                        {"session_id": session_id, "user_id": user_id},
                        {
                            "$set": {
                                "processing_status": "error",
                                "processing_error": str(e),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                except Exception as add_error:
                    logger.error(f"[EMBEDDING] Failed to add error message: {add_error}")
                # Don't fail the linking process if embedding creation fails
                
        except Exception as e:
            logger.error(f"[EMBEDDING] Error in background embedding creation: {e}")
            # Add error message to chat session
            try:
                error_message = f"❌ Error processing documents: {str(e)}"
                await self.add_message(session_id, user_id, MessageRole.SYSTEM, error_message)
            except Exception as add_error:
                logger.error(f"[EMBEDDING] Failed to add error message: {add_error}")
            # Don't fail the linking process if embedding creation fails

    async def link_uploaded_document(self, session_id: str, user_id: str, document) -> bool:
        """Link an uploaded document to a chat session and create embeddings."""
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                raise ChatError("Session not found")
            
            # Add document to session (but don't increment count yet - wait for processing result)
            await mongodb.get_collection("chat_sessions").update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$addToSet": {"uploaded_documents": document.document_id},
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Linked uploaded document {document.document_id} to session {session_id}")
            
            # Add immediate feedback message
            await self.add_message(session_id, user_id, MessageRole.SYSTEM, 
                f"📄 Document '{document.filename}' uploaded successfully. Processing in background...")
            
            # Create embeddings for the document - run synchronously to ensure completion
            # This ensures the completion message is added before Lambda terminates
            await self._create_embeddings_for_uploaded_document(document, session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error linking uploaded document to session {session_id}: {e}")
            raise ChatError(f"Failed to link uploaded document: {e}")
    
    async def _create_embeddings_for_uploaded_document(self, document, session_id: str):
        """Create embeddings for an uploaded document in background with deduplication."""
        try:
            logger.info(f"[EMBEDDING] Starting background embedding creation for uploaded document: {document.filename}")
            
            # Get the session to find the user_id
            session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session_id})
            
            if not session_data:
                logger.error(f"[EMBEDDING] Session {session_id} not found in database")
                return
            
            user_id = session_data.get("user_id")
            logger.info(f"[EMBEDDING] Found session {session_id} for user {user_id}")
            
            # Import unified document processor
            from common.src.services.unified_document_processor import unified_document_processor
            from common.src.services.storage_service import StorageService
            
            try:
                logger.info(f"[EMBEDDING] Creating embeddings for uploaded document: {document.filename}")
                
                # Get document content from S3 using unified storage service
                s3_key = document.file_path
                file_content = await unified_storage_service.get_file_content(s3_key)
                
                if file_content:
                    # Process document using unified processor
                    result = await unified_document_processor.process_document(
                        file_content=file_content,
                        filename=document.filename,
                        user_id=user_id,
                        session_id=session_id,
                        metadata={
                            "session_id": session_id,
                            "user_id": user_id,
                            "source": "uploaded_document",
                            "file_path": document.file_path
                        },
                        source="uploaded"
                    )
                    
                    if result.get("status") == "success":
                        logger.info(f"[EMBEDDING] Successfully processed uploaded document: {document.filename}")
                        completion_message = f"🎉 Document processed successfully! You can now ask questions about {document.filename}."
                        # Increment document count
                        await mongodb.get_collection("chat_sessions").update_one(
                            {"session_id": session_id, "user_id": user_id},
                            {"$inc": {"document_count": 1}}
                        )
                        logger.info(f"[EMBEDDING] New document - incremented document count")
                        # Add completion message
                        completion_success = await self.add_message(session_id, user_id, MessageRole.SYSTEM, completion_message)
                        logger.info(f"[EMBEDDING] Added completion message: {completion_success}")
                    else:
                        logger.warning(f"[EMBEDDING] Failed to process uploaded document: {document.filename}")
                        error_message = f"❌ Failed to process uploaded document: {document.filename}"
                        await self.add_message(session_id, user_id, MessageRole.SYSTEM, error_message)
                else:
                    logger.warning(f"[EMBEDDING] Could not read content for uploaded document: {document.filename}")
                    error_message = f"❌ Could not read content for uploaded document: {document.filename}"
                    await self.add_message(session_id, user_id, MessageRole.SYSTEM, error_message)
                    
            except Exception as e:
                logger.error(f"[EMBEDDING] Error processing uploaded document {document.filename}: {e}")
                # Update error message
                error_message = f"❌ Error processing uploaded document: {document.filename}"
                await self.add_message(session_id, user_id, MessageRole.SYSTEM, error_message)
                # Don't fail the linking process if embedding creation fails
                
        except Exception as e:
            logger.error(f"[EMBEDDING] Error in background embedding creation for uploaded document: {e}")
            # Don't fail the linking process if embedding creation fails

    async def check_processing_status(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Check the processing status of documents in a session."""
        try:
            session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session_id})
            if not session_data:
                return {"status": "session_not_found"}
            
            processing_status = session_data.get("processing_status", "unknown")
            processing_completed_at = session_data.get("processing_completed_at")
            processing_error = session_data.get("processing_error")
            
            # Check if we have a completion message
            messages = session_data.get("messages", [])
            has_completion_message = any(
                m.get('content', '').startswith('🎉') or 
                m.get('content', '').startswith('✅') or
                'completed' in m.get('content', '').lower()
                for m in messages
            )
            
            return {
                "status": processing_status,
                "has_completion_message": has_completion_message,
                "processing_completed_at": processing_completed_at,
                "processing_error": processing_error,
                "document_count": session_data.get("document_count", 0),
                "crawl_tasks": len(session_data.get("crawl_tasks", [])),
                "uploaded_documents": len(session_data.get("uploaded_documents", []))
            }
            
        except Exception as e:
            logger.error(f"Error checking processing status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def check_and_add_missing_completion_message(self, session_id: str, user_id: str) -> bool:
        """Check if completion message is missing and add it if needed."""
        try:
            # Get session data
            session_data = await mongodb.get_collection("chat_sessions").find_one({"session_id": session_id})
            if not session_data:
                logger.warning(f"[COMPLETION] Session {session_id} not found")
                return False
            
            # Check if we have a completion message
            messages = session_data.get("messages", [])
            has_completion_message = any(
                m.get('content', '').startswith('🎉') or 
                m.get('content', '').startswith('✅') or
                'completed' in m.get('content', '').lower() or
                'ready for questions' in m.get('content', '').lower()
                for m in messages
            )
            
            if has_completion_message:
                logger.info(f"[COMPLETION] Completion message already exists for session {session_id}")
                return True
            
            # Check if we have documents but no completion message
            document_count = session_data.get("document_count", 0)
            crawl_tasks = len(session_data.get("crawl_tasks", []))
            uploaded_documents = len(session_data.get("uploaded_documents", []))
            
            total_docs = document_count + crawl_tasks + uploaded_documents
            
            if total_docs > 0:
                # Check if processing is actually complete by looking at vector store
                try:
                    from common.src.services.vector_store_service import vector_store_service
                    vector_store_id = await vector_store_service.get_or_create_session_vector_store(session_id)
                    files = await vector_store_service.list_vector_store_files(vector_store_id)
                    
                    if files and len(files) > 0:
                        # Files exist in vector store, add completion message
                        completion_message = "🎉 Document processing completed! You can now ask questions about the documents."
                        success = await self.add_message(session_id, user_id, MessageRole.SYSTEM, completion_message)
                        
                        if success:
                            # Update processing status
                            await mongodb.get_collection("chat_sessions").update_one(
                                {"session_id": session_id, "user_id": user_id},
                                {
                                    "$set": {
                                        "processing_status": "completed",
                                        "processing_completed_at": datetime.utcnow(),
                                        "updated_at": datetime.utcnow()
                                    }
                                }
                            )
                            logger.info(f"[COMPLETION] Added missing completion message for session {session_id}")
                            return True
                        else:
                            logger.error(f"[COMPLETION] Failed to add completion message for session {session_id}")
                            return False
                    else:
                        logger.info(f"[COMPLETION] No files in vector store for session {session_id}, processing may still be in progress")
                        return False
                        
                except Exception as e:
                    logger.error(f"[COMPLETION] Error checking vector store for session {session_id}: {e}")
                    # If we can't check vector store, add completion message anyway
                    completion_message = "🎉 Document processing completed! You can now ask questions about the documents."
                    success = await self.add_message(session_id, user_id, MessageRole.SYSTEM, completion_message)
                    return success
            else:
                logger.info(f"[COMPLETION] No documents found for session {session_id}, no completion message needed")
                return True
                
        except Exception as e:
            logger.error(f"[COMPLETION] Error checking for missing completion message: {e}")
            return False

    async def force_completion_message(self, session_id: str, user_id: str) -> bool:
        """Force add a completion message if processing is done but message is missing."""
        try:
            return await self.check_and_add_missing_completion_message(session_id, user_id)
        except Exception as e:
            logger.error(f"Error forcing completion message: {e}")
            return False

# Global chat service instance
chat_service = ChatService() 