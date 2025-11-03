"""
FastAPI dependencies
Reusable dependencies for route handlers
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.services import get_user_from_token, validate_admin_role


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User document from database
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Usage:
        ```python
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_email": user["email"]}
        ```
    """
    return await get_user_from_token(token)


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user and validate admin role
    
    Args:
        current_user: User document from get_current_user dependency
        
    Returns:
        User document if user is admin
        
    Raises:
        HTTPException: If user is not admin
        
    Usage:
        ```python
        @router.post("/admin-only")
        async def admin_route(admin: dict = Depends(get_current_admin_user)):
            return {"message": "Admin access granted"}
        ```
    """
    return validate_admin_role(current_user)
