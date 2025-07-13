"""
MongoDB helper for task progress updates
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MongoDBHelper:
    """Helper class for MongoDB operations in crawler Lambda."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB."""
        try:
            import pymongo
            from pymongo import MongoClient
            
            # Get MongoDB connection string from environment
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
            db_name = os.getenv('MONGODB_DB', 'crawlchat')
            
            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]
            
            logger.info(f"MongoDB helper connected to database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
    
    def update_task_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """Update task progress in MongoDB."""
        if not self.db:
            logger.warning("MongoDB not connected, skipping progress update")
            return
        
        try:
            collection = self.db.crawler_tasks
            
            # Update the task with new progress data
            update_data = {
                "$set": {
                    "progress": progress_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
            result = collection.update_one(
                {"task_id": task_id},
                update_data
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated progress for task {task_id}")
            else:
                logger.warning(f"Task {task_id} not found for progress update")
                
        except Exception as e:
            logger.error(f"Failed to update task progress: {e}")
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB helper connection closed") 