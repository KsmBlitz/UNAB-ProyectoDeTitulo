"""
Users routes
User management CRUD operations
Refactored to follow SOLID principles - delegates business logic to UserService
"""

from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging

from app.models import UserPublic, UserCreate, UserUpdate
from app.services.user_service import user_service
from app.utils import get_current_user, get_current_admin_user
from app.services.audit import log_audit_event
from app.models.audit_models import AuditAction

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
    try:
        users_list = await user_service.get_all_users(limit=1000)
        return [UserPublic(**user) for user in users_list]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving users"
        )


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    request: Request,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Create a new user (admin only)
    
    Args:
        user: User data including email, password, role, etc.
        
    Returns:
        Created user profile
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        # Delegate to user service
        created_user = await user_service.create_user(
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            role=user.role,
            phone=getattr(user, 'phone', None),
            notifications_enabled=getattr(user, 'notifications_enabled', True),
            whatsapp_notifications_enabled=getattr(user, 'whatsapp_notifications_enabled', False)
        )
        
        # Log audit event
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        await log_audit_event(
            action=AuditAction.USER_CREATED,
            description=f"User created: {user.email}",
            user_email=admin_user.get('email'),
            user_id=str(admin_user.get('_id')) if admin_user.get('_id') else None,
            resource_type="user",
            resource_id=str(created_user["_id"]),
            details={
                "created_user_email": user.email,
                "created_user_role": user.role,
                "created_user_full_name": user.full_name
            },
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(f"User created: {user.email}")
        return UserPublic(**created_user)
        
    except ValueError as ve:
        logger.warning(f"Validation error creating user: {ve}")
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except RuntimeError as re:
        logger.error(f"Runtime error creating user: {re}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
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
    try:
        # Prepare update data
        update_data = {
            k: v for k, v in user_update.model_dump().items() if v is not None
        }
        
        # Get user before update for audit
        user_before = await user_service.get_user_by_id(user_id)
        
        # Delegate to user service
        updated_user = await user_service.update_user(
            user_id=user_id,
            update_data=update_data,
            current_user=admin_user
        )
        
        # Log audit event
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        await log_audit_event(
            action=AuditAction.USER_UPDATED,
            description=f"User updated: {user_before.get('email', 'unknown') if user_before else 'unknown'}",
            user_email=admin_user.get('email'),
            user_id=str(admin_user.get('_id')) if admin_user.get('_id') else None,
            resource_type="user",
            resource_id=user_id,
            details={
                "updated_user_email": user_before.get('email') if user_before else None,
                "fields_updated": list(update_data.keys())
            },
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(f"User updated: {user_id}")
        return UserPublic(**updated_user)
        
    except ValueError as ve:
        logger.warning(f"Validation error updating user: {ve}")
        status_code = 400 if "not found" not in str(ve).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(ve))
    except PermissionError as pe:
        logger.warning(f"Permission error updating user: {pe}")
        raise HTTPException(status_code=403, detail=str(pe))
    except RuntimeError as re:
        logger.error(f"Runtime error updating user: {re}")
        raise HTTPException(status_code=500, detail="Failed to update user")
    except Exception as e:
        logger.error(f"Unexpected error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    admin_user: dict = Depends(get_current_admin_user)
):
    """
    Delete a user (admin only)
    
    Args:
        user_id: User ID to delete
        
    Raises:
        HTTPException: If user not found, invalid ID, or trying to delete self
    """
    try:
        # Get user before delete for audit
        user_to_delete = await user_service.get_user_by_id(user_id)
        
        # Delegate to user service
        await user_service.delete_user(
            user_id=user_id,
            current_user=admin_user
        )
        
        # Log audit event
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        await log_audit_event(
            action=AuditAction.USER_DELETED,
            description=f"User deleted: {user_to_delete.get('email', 'unknown') if user_to_delete else 'unknown'}",
            user_email=admin_user.get('email'),
            user_id=str(admin_user.get('_id')) if admin_user.get('_id') else None,
            resource_type="user",
            resource_id=user_id,
            details={
                "deleted_user_email": user_to_delete.get('email') if user_to_delete else None,
                "deleted_user_role": user_to_delete.get('role') if user_to_delete else None
            },
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )
        
        logger.info(f"User deleted: {user_id}")
        return
        
    except ValueError as ve:
        logger.warning(f"Validation error deleting user: {ve}")
        status_code = 400 if "invalid" in str(ve).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(ve))
    except PermissionError as pe:
        logger.warning(f"Permission error deleting user: {pe}")
        raise HTTPException(status_code=403, detail=str(pe))
    except RuntimeError as re:
        logger.error(f"Runtime error deleting user: {re}")
        raise HTTPException(status_code=500, detail="Failed to delete user")
    except Exception as e:
        logger.error(f"Unexpected error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
