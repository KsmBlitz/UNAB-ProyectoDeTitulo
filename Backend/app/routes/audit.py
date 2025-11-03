"""
Audit routes
API endpoints for audit log management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, Dict, Any
from datetime import datetime

from app.utils.dependencies import get_current_user, get_current_admin_user
from app.services.audit import (
    get_audit_logs,
    get_user_activity,
    get_audit_statistics
)
from models.audit_models import AuditLogFilter, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    return current_user


@router.get("/logs", response_model=AuditLogResponse)
async def get_logs(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get audit logs with filtering and pagination
    
    Only accessible by admin users.
    """
    filters = AuditLogFilter(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        success=success,
        page=page,
        page_size=page_size
    )
    
    return await get_audit_logs(filters)


@router.get("/user/{user_id}")
async def get_user_audit_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of entries"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get audit activity for a specific user
    
    Only accessible by admin users.
    """
    logs = await get_user_activity(user_id, limit)
    
    return {
        "user_id": user_id,
        "total": len(logs),
        "logs": logs
    }


@router.get("/statistics")
async def get_statistics(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get audit log statistics
    
    Returns aggregated statistics about audit logs including:
    - Total number of logs
    - Failed actions count
    - Success rate
    - Action counts by type
    - Most active users
    
    Only accessible by admin users.
    """
    return await get_audit_statistics()


@router.get("/actions")
async def get_available_actions(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get list of available audit action types
    
    Returns all possible action types that can be filtered.
    Only accessible by admin users.
    """
    from models.audit_models import AuditAction
    
    return {
        "actions": [
            {
                "value": action.value,
                "label": action.value.replace("_", " ").title()
            }
            for action in AuditAction
        ]
    }
