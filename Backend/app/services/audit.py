"""
Audit service
Service for logging and querying audit events
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import Request

from app.config.database import audit_log_collection
from models.audit_models import AuditAction, AuditLogEntry, AuditLogFilter, AuditLogResponse

logger = logging.getLogger(__name__)


async def log_audit_event(
    action: AuditAction,
    description: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True
) -> bool:
    """
    Log an audit event to the database
    
    Args:
        action: Type of action performed
        description: Human-readable description of the event
        user_id: ID of the user who performed the action
        user_email: Email of the user
        resource_type: Type of resource affected (e.g., "user", "alert_threshold")
        resource_id: ID of the affected resource
        details: Additional details about the event
        ip_address: IP address of the client
        user_agent: User agent string
        success: Whether the action was successful
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        entry = AuditLogEntry(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            timestamp=datetime.utcnow(),
            success=success
        )
        
        await audit_log_collection.insert_one(entry.dict())
        logger.info(f"Audit log created: {action.value} by {user_email or 'system'}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        return False


async def log_audit_from_request(
    request: Request,
    action: AuditAction,
    description: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True
) -> bool:
    """
    Log an audit event extracting info from FastAPI Request
    
    Args:
        request: FastAPI Request object
        action: Type of action performed
        description: Human-readable description
        user_id: User ID (optional, can be extracted from request.state)
        user_email: User email
        resource_type: Type of resource
        resource_id: Resource ID
        details: Additional details
        success: Whether action was successful
        
    Returns:
        True if logged successfully
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Try to get user info from request state if not provided
    if hasattr(request.state, "user") and not user_email:
        user_email = getattr(request.state.user, "email", None)
        user_id = getattr(request.state.user, "id", None)
    
    return await log_audit_event(
        action=action,
        description=description,
        user_id=user_id,
        user_email=user_email,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )


async def get_audit_logs(
    filters: AuditLogFilter
) -> AuditLogResponse:
    """
    Get audit logs with filtering and pagination
    
    Args:
        filters: Filter criteria for audit logs
        
    Returns:
        AuditLogResponse with paginated results
    """
    try:
        # Build query
        query: Dict[str, Any] = {}
        
        if filters.user_id:
            query["user_id"] = filters.user_id
        
        if filters.user_email:
            query["user_email"] = {"$regex": filters.user_email, "$options": "i"}
        
        if filters.action:
            query["action"] = filters.action
        
        if filters.resource_type:
            query["resource_type"] = filters.resource_type
        
        if filters.success is not None:
            query["success"] = filters.success
        
        # Date range filter
        if filters.start_date or filters.end_date:
            date_query: Dict[str, Any] = {}
            if filters.start_date:
                date_query["$gte"] = filters.start_date
            if filters.end_date:
                date_query["$lte"] = filters.end_date
            query["timestamp"] = date_query
        
        # Get total count
        total = await audit_log_collection.count_documents(query)
        
        # Calculate pagination
        skip = (filters.page - 1) * filters.page_size
        
        # Get paginated results
        cursor = audit_log_collection.find(query).sort("timestamp", -1).skip(skip).limit(filters.page_size)
        logs = await cursor.to_list(length=filters.page_size)
        
        # Convert ObjectId to string
        for log in logs:
            if "_id" in log:
                log["_id"] = str(log["_id"])
        
        return AuditLogResponse(
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            logs=logs
        )
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return AuditLogResponse(
            total=0,
            page=filters.page,
            page_size=filters.page_size,
            logs=[]
        )


async def get_user_activity(
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get recent activity for a specific user
    
    Args:
        user_id: User ID to get activity for
        limit: Maximum number of entries to return
        
    Returns:
        List of audit log entries
    """
    try:
        cursor = audit_log_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        logs = await cursor.to_list(length=limit)
        
        for log in logs:
            if "_id" in log:
                log["_id"] = str(log["_id"])
        
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get user activity: {e}")
        return []


async def get_audit_statistics() -> Dict[str, Any]:
    """
    Get audit log statistics
    
    Returns:
        Dictionary with statistics about audit logs
    """
    try:
        total_logs = await audit_log_collection.count_documents({})
        
        # Count by action type
        action_pipeline = [
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        action_counts = await audit_log_collection.aggregate(action_pipeline).to_list(length=100)
        
        # Count failed actions
        failed_count = await audit_log_collection.count_documents({"success": False})
        
        # Get most active users
        user_pipeline = [
            {"$match": {"user_email": {"$ne": None}}},
            {"$group": {"_id": "$user_email", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_users = await audit_log_collection.aggregate(user_pipeline).to_list(length=10)
        
        return {
            "total_logs": total_logs,
            "failed_actions": failed_count,
            "success_rate": round((total_logs - failed_count) / total_logs * 100, 2) if total_logs > 0 else 0,
            "action_counts": action_counts,
            "top_users": top_users
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit statistics: {e}")
        return {
            "total_logs": 0,
            "failed_actions": 0,
            "success_rate": 0,
            "action_counts": [],
            "top_users": []
        }
