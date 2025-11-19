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
    async def initialize(cls) -> None:
        """Initialize database connection"""
        try:
            cls.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_CONNECTION_STRING,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.DATABASE_NAME]
            
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
            return cls.client
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close(cls) -> None:
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_collection(cls, name: str) -> Any:
        """Get a collection from the database"""
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call Database.initialize() first")
        return cls.db[name]


# MongoDB client instance
db_client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGO_CONNECTION_STRING,
    serverSelectionTimeoutMS=5000
)
db = db_client[settings.DATABASE_NAME]

# Collections
users_collection = db["users"]
sensor_collection = db["Sensor_Data"]
alerts_collection = db["alerts"]
alert_history_collection = db["alert_history"]
alert_thresholds_collection = db["alert_thresholds"]
reset_tokens_collection = db["reset_tokens"]
notifications_sent_collection = db["notifications_sent"]
audit_log_collection = db["audit_logs"]
embalses_collection = db["embalses"]
