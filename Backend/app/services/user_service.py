"""
User Service - Business Logic Layer
Handles user management operations following SOLID principles
"""

import logging
from typing import Dict, List, Any, Optional
from bson import ObjectId

from app.repositories.user_repository import user_repository
from app.services.auth import get_password_hash

logger = logging.getLogger(__name__)


class UserService:
    """
    Service layer for user management business logic
    
    Responsibilities:
    - User CRUD operations
    - Password management
    - User validation
    - Role and permission validation
    """
    
    def __init__(self, user_repo=None):
        """Initialize with user repository (dependency injection for testability)"""
        self.user_repo = user_repo or user_repository
    
    async def get_all_users(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all users in the system
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user dictionaries
        """
        try:
            from app.config import users_collection
            cursor = users_collection.find().limit(limit)
            users = await cursor.to_list(length=limit)
            logger.info(f"Retrieved {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ObjectId as string
            
        Returns:
            User dictionary or None if not found
            
        Raises:
            ValueError: If user_id is not a valid ObjectId
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        
        try:
            from app.config import users_collection
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User dictionary or None if not found
        """
        try:
            user = await self.user_repo.get_user_by_email(email)
            return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "operario",
        phone: Optional[str] = None,
        notifications_enabled: bool = True,
        whatsapp_notifications_enabled: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new user
        
        Business logic:
        1. Validate email doesn't already exist
        2. Hash the password securely
        3. Create user document with proper defaults
        4. Return created user (without password)
        
        Args:
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role (operario, admin)
            phone: Optional phone number
            notifications_enabled: Enable email notifications
            whatsapp_notifications_enabled: Enable WhatsApp notifications
            
        Returns:
            Created user dictionary
            
        Raises:
            ValueError: If email already exists or validation fails
            RuntimeError: If creation fails
        """
        try:
            # Check if email already exists
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                raise ValueError(f"User with email {email} already exists")
            
            # Validate role
            if role not in ["operario", "admin"]:
                raise ValueError(f"Invalid role: {role}. Must be 'operario' or 'admin'")
            
            # Hash password
            hashed_password = get_password_hash(password)
            
            # Prepare user document
            user_data = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "role": role,
                "disabled": False,
                "notifications_enabled": notifications_enabled,
                "whatsapp_notifications_enabled": whatsapp_notifications_enabled
            }
            
            if phone:
                user_data["phone"] = phone
            
            # Insert user
            from app.config import users_collection
            result = await users_collection.insert_one(user_data)
            
            # Retrieve created user
            created_user = await users_collection.find_one({"_id": result.inserted_id})
            
            if not created_user:
                raise RuntimeError("User created but could not be retrieved")
            
            logger.info(f"User created successfully: {email} ({role})")
            return created_user
            
        except ValueError as ve:
            logger.warning(f"Validation error creating user: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            raise RuntimeError(f"Failed to create user: {e}")
    
    async def update_user(
        self,
        user_id: str,
        update_data: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update user information
        
        Business logic:
        1. Validate user exists
        2. Filter out None values
        3. Validate permissions (users can't change their own role)
        4. Apply updates
        5. Return updated user
        
        Args:
            user_id: User ID to update
            update_data: Dictionary of fields to update
            current_user: User performing the update (for permission checks)
            
        Returns:
            Updated user dictionary
            
        Raises:
            ValueError: If user not found or validation fails
            PermissionError: If user lacks permissions for operation
            RuntimeError: If update fails
        """
        try:
            # Validate user ID format
            if not ObjectId.is_valid(user_id):
                raise ValueError("Invalid user ID format")
            
            # Get existing user
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Filter out None values
            filtered_updates = {k: v for k, v in update_data.items() if v is not None}
            
            if not filtered_updates:
                raise ValueError("No data provided for update")
            
            # Permission check: users can't change their own role to admin
            if current_user and str(current_user.get("_id")) == user_id:
                if "role" in filtered_updates and filtered_updates["role"] == "admin":
                    if current_user.get("role") != "admin":
                        raise PermissionError("Users cannot promote themselves to admin")
            
            # Apply updates
            from app.config import users_collection
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": filtered_updates}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"User not found: {user_id}")
            
            # Retrieve updated user
            updated_user = await self.get_user_by_id(user_id)
            
            if not updated_user:
                raise RuntimeError("User updated but could not be retrieved")
            
            logger.info(f"User updated successfully: {user_id} (fields: {list(filtered_updates.keys())})")
            return updated_user
            
        except (ValueError, PermissionError) as e:
            logger.warning(f"Validation/Permission error updating user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise RuntimeError(f"Failed to update user: {e}")
    
    async def delete_user(
        self,
        user_id: str,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete a user
        
        Business logic:
        1. Validate user exists
        2. Prevent self-deletion
        3. Delete user
        
        Args:
            user_id: User ID to delete
            current_user: User performing the deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If user not found or validation fails
            PermissionError: If user tries to delete themselves
            RuntimeError: If deletion fails
        """
        try:
            # Validate user ID format
            if not ObjectId.is_valid(user_id):
                raise ValueError("Invalid user ID format")
            
            # Get user to delete
            user_to_delete = await self.get_user_by_id(user_id)
            if not user_to_delete:
                raise ValueError(f"User not found: {user_id}")
            
            # Prevent self-deletion
            current_user_id = str(current_user.get("_id"))
            if current_user_id == user_id:
                raise PermissionError("Users cannot delete themselves")
            
            # Delete user
            from app.config import users_collection
            result = await users_collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                raise RuntimeError("User deletion failed")
            
            logger.info(f"User deleted successfully: {user_id} ({user_to_delete.get('email')})")
            return True
            
        except (ValueError, PermissionError) as e:
            logger.warning(f"Validation/Permission error deleting user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise RuntimeError(f"Failed to delete user: {e}")
    
    async def update_password(
        self,
        user_id: str,
        new_password: str
    ) -> bool:
        """
        Update user password
        
        Args:
            user_id: User ID
            new_password: New plain text password (will be hashed)
            
        Returns:
            True if updated successfully
            
        Raises:
            ValueError: If user not found or password invalid
            RuntimeError: If update fails
        """
        try:
            # Validate user exists
            user = await self.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Validate password (basic check)
            if len(new_password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            # Update password
            from app.config import users_collection
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"hashed_password": hashed_password}}
            )
            
            if result.modified_count == 0:
                raise RuntimeError("Password update failed")
            
            logger.info(f"Password updated successfully for user: {user_id}")
            return True
            
        except ValueError as ve:
            logger.warning(f"Validation error updating password: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {e}")
            raise RuntimeError(f"Failed to update password: {e}")
    
    def validate_user_role(self, user: Dict[str, Any], required_role: str) -> bool:
        """
        Validate user has required role
        
        Args:
            user: User dictionary
            required_role: Required role (e.g., "admin")
            
        Returns:
            True if user has required role
        """
        user_role = user.get("role", "operario")
        
        if required_role == "admin":
            return user_role == "admin"
        
        return True  # All users have access to non-admin operations


# Singleton instance
user_service = UserService()
