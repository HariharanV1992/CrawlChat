"""
Database connection management for Stock Market Crawler using MongoDB.
"""

import motor.motor_asyncio
from src.core.config import config
import os
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB with Lambda-optimized settings."""
        # If already connected, return early
        if self.is_connected():
            logger.info("MongoDB already connected")
            return
            
        try:
            logger.info("Connecting to MongoDB...")
            logger.info(f"MongoDB URI: {config.mongodb_uri[:20]}...")  # Log first 20 chars for debugging
            
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.mongodb_uri,
                serverSelectionTimeoutMS=10000,  # Reduced timeout for Lambda
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=1,
                minPoolSize=0,
                maxIdleTimeMS=30000,
                retryWrites=True,
                retryReads=True
            )
            
            logger.info("MongoDB client created, testing connection...")
            
            # Test the connection
            await self.client.admin.command('ping')
            self.db = self.client[config.mongodb_db]
            logger.info(f"MongoDB connected successfully to database: {config.mongodb_db}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            logger.error(f"Connection error type: {type(e).__name__}")
            # Keep the client for potential retry
            self.client = None
            self.db = None
            raise

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        return self.client is not None and self.db is not None

    def get_collection(self, name: str):
        """Get a collection with lazy connection."""
        if not self.is_connected():
            # Don't connect here - let the calling code handle connection
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db[name]

# Global MongoDB instance
mongodb = MongoDB() 