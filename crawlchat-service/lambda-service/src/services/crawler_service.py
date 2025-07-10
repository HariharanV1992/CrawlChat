"""
Simplified crawler service for Lambda function
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CrawlerService:
    """Simplified crawler service for Lambda function"""
    
    def __init__(self):
        self.logger = logger
    
    async def create_task(self, url: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a crawler task"""
        return {
            "task_id": "mock_task_id",
            "url": url,
            "status": "created",
            "config": config or {}
        }
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {"success": True}
        }

# Create a singleton instance
crawler_service = CrawlerService() 