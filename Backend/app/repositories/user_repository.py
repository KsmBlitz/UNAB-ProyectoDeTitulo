"""
User Repository
Data access layer for users
Implements IUserRepository interface
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.config import users_collection
from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user operations
    Implements the IUserRepository interface
    """
    
    def __init__(self):
        super().__init__(users_collection)
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find user by email address (interface method)
        
        Args:
            email: User email
            
        Returns:
            User document or None
        """
        return await self.find_one({"email": email.lower()})
    
    # Alias for backwards compatibility
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Alias for find_by_email"""
        return await self.find_by_email(email)
    
    async def get_admin_users(self) -> List[Dict[str, Any]]:
        """
        Get all admin users (interface method)
        
        Returns:
            List of admin user documents
        """
        return await self.find_many({"role": "admin"}, limit=100)
    
    async def update_password(
        self,
        user_id: str,
        hashed_password: str
    ) -> bool:
        """
        Update user password (interface method)
        
        Args:
            user_id: User ID
            hashed_password: New hashed password
            
        Returns:
            True if updated successfully
        """
        try:
            from bson import ObjectId
            return await self.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "password_updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {e}")
            return False
    
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
        updates["updated_at"] = datetime.utcnow()
        return await self.update_one(
            {"email": email.lower()},
            {"$set": updates}
        )
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user
        
        Args:
            user_data: User data including email, hashed_password, etc.
            
        Returns:
            Inserted document ID or None
        """
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        user_data["email"] = user_data.get("email", "").lower()
        
        return await self.insert_one(user_data)


# Singleton instance
user_repository = UserRepository()
