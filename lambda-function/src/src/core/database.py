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
        self.client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb_uri)
        self.db = self.client[config.mongodb_db]

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        return self.db is not None

    def get_collection(self, name: str):
        if self.db is None:
            raise RuntimeError("MongoDB not connected")
        return self.db[name]

# Global MongoDB instance
mongodb = MongoDB() 