"""
User Repository
Data access layer for users
"""

from typing import List, Optional, Dict, Any
from app.config import users_collection
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    def __init__(self):
        super().__init__(users_collection)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User email
            
        Returns:
            User document or None
        """
        return await self.find_one({"email": email.lower()})
    
    async def get_admin_users(self) -> List[Dict[str, Any]]:
        """
        Get all admin users
        
        Returns:
            List of admin user documents
        """
        return await self.find_many({"role": "admin"}, limit=100)
    
    async def get_users_with_notifications_enabled(
        self,
        notification_type: str = "email"
    ) -> List[Dict[str, Any]]:
        """
        Get users with specific notification type enabled
        
        Args:
            notification_type: Type of notification (email/whatsapp)
            
        Returns:
            List of users with notifications enabled
        """
        if notification_type == "whatsapp":
            query = {
                "role": "admin",
                "whatsapp_notifications_enabled": True,
                "phone": {"$exists": True, "$ne": None, "$ne": ""}
            }
        else:  # email
            query = {
                "role": "admin",
                "email": {"$exists": True, "$ne": None, "$ne": ""}
            }
        
        return await self.find_many(query, limit=100)
    
    async def update_user(
        self,
        email: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update user data
        
        Args:
            email: User email
            updates: Fields to update
            
        Returns:
            True if updated
        """
        return await self.update_one(
            {"email": email.lower()},
            {"$set": updates}
        )


# Singleton instance
user_repository = UserRepository()
