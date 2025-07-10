"""
Simplified database module for Lambda function
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MongoDB:
    """Simplified MongoDB interface for Lambda function"""
    
    def __init__(self):
        self.logger = logger
    
    async def connect(self):
        """Connect to database"""
        self.logger.info("MongoDB connection established")
    
    async def disconnect(self):
        """Disconnect from database"""
        self.logger.info("MongoDB connection closed")
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a document"""
        return {"inserted_id": "mock_id"}
    
    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a document"""
        return None

# Create a singleton instance
mongodb = MongoDB() 