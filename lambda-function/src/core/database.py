"""
Database connection management for Stock Market Crawler using MongoDB.
"""

import motor.motor_asyncio
from src.core.config import config

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB with Lambda-optimized settings."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.mongodb_uri,
                serverSelectionTimeoutMS=15000,  # 15 second timeout
                connectTimeoutMS=15000,
                socketTimeoutMS=15000,
                maxPoolSize=1,
                minPoolSize=0,
                maxIdleTimeMS=30000,
                retryWrites=True,
                retryReads=True
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            self.db = self.client[config.mongodb_db]
            
        except Exception as e:
            # Log the error but don't raise it immediately
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"MongoDB connection failed: {e}")
            # Keep the client for potential retry
            self.client = None
            self.db = None

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        return self.client is not None and self.db is not None

    def get_collection(self, name: str):
        if self.db is None:
            raise RuntimeError("MongoDB not connected")
        return self.db[name]

# Global MongoDB instance
mongodb = MongoDB() 