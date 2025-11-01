"""
Database module
MongoDB connection and collections management
"""

import motor.motor_asyncio
from typing import Any
import logging

from .settings import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager"""
    
    client: Any = None
    db: Any = None
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize database connection"""
        try:
            cls.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_CONNECTION_STRING,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.DATABASE_NAME]
            logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close(cls) -> None:
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("📕 MongoDB connection closed")
    
    @classmethod
    def get_collection(cls, name: str) -> Any:
        """Get a collection from the database"""
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call Database.initialize() first")
        return cls.db[name]


# Initialize database connection
Database.initialize()

# Collections
users_collection = Database.get_collection("users")
sensor_collection = Database.get_collection("Sensor_Data")
alerts_collection = Database.get_collection("alerts")
alert_history_collection = Database.get_collection("alert_history")
alert_thresholds_collection = Database.get_collection("alert_thresholds")
reset_tokens_collection = Database.get_collection("reset_tokens")
notifications_sent_collection = Database.get_collection("notifications_sent")
