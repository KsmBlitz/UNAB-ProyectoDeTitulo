"""
Users routes
User management CRUD operations
"""

from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.models import UserPublic, UserCreate, UserUpdate
from app.config import users_collection
from app.services import get_password_hash
from app.utils import get_current_user, get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Usuarios"])


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Returns:
        Current user profile
    """
    return UserPublic(**current_user)


@router.get("", response_model=List[UserPublic])
async def read_users(admin_user: dict = Depends(get_current_admin_user)):
    """
    Get all users (admin only)
    
    Returns:
        List of all users in the system
    """
    users_from_db = await users_collection.find().to_list(1000)
    return [UserPublic(**user) for user in users_from_db]


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Create a new user (admin only)
    
    Args:
        user: User data including email, password, role, etc.
        
    Returns:
        Created user profile
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con este email"
        )
    
    # Hash password and prepare user data
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    
    # Insert user
    new_user_doc = await users_collection.insert_one(user_data)
    
    # Retrieve and return created user
    created_user_from_db = await users_collection.find_one(
        {"_id": new_user_doc.inserted_id}
    )
    
    logger.info(f"Usuario creado: {user.email}")
    
    return UserPublic(**created_user_from_db)  # type: ignore


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Update user information (admin only)
    
    Args:
        user_id: User ID to update
        user_update: Fields to update (all optional)
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If user not found or invalid ID
    """
    # Validate ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=400,
            detail="El ID de usuario no es válido"
        )
    
    # Get only non-null fields
    update_data = {
        k: v for k, v in user_update.model_dump().items() if v is not None
    }
    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron datos para actualizar"
        )
    
    # Update user
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el usuario"
        )
    
    # Retrieve and return updated user
    updated_user_from_db = await users_collection.find_one(
        {"_id": ObjectId(user_id)}
    )
    
    logger.info(f"Usuario actualizado: {user_id}")
    
    return UserPublic(**updated_user_from_db)  # type: ignore


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Delete a user (admin only)
    
    Args:
        user_id: User ID to delete
        
    Raises:
        HTTPException: If user not found, invalid ID, or trying to delete self
    """
    # Validate ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=400,
            detail="El ID de usuario no es válido"
        )
    
    # Prevent admin from deleting themselves
    if str(admin_user["_id"]) == user_id:
        raise HTTPException(
            status_code=403,
            detail="Un administrador no puede eliminarse a sí mismo"
        )
    
    # Delete user
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el usuario a eliminar"
        )
    
    logger.info(f"Usuario eliminado: {user_id}")
    
    return
