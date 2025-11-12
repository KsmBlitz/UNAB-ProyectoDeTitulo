"""
Authentication routes
Login, password reset, and token management
Refactored to use repository pattern
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.models import (
    Token,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest
)
from app.config import reset_tokens_collection
from app.repositories.user_repository import user_repository
from app.services.user_service import user_service
from app.services import (
    verify_password,
    get_password_hash,
    create_access_token,
    send_reset_email,
    generate_reset_token,
    log_audit_from_request
)
from app.utils import get_current_user
from app.models.audit_models import AuditAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Autenticación"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login endpoint - authenticate user and return JWT token
    
    Args:
        request: FastAPI request for audit logging
        form_data: OAuth2 form with username (email) and password
        
    Returns:
        JWT access token and token type
    """
    user = await user_repository.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        # Log failed login attempt
        await log_audit_from_request(
            request=request,
            action=AuditAction.LOGIN_FAILED,
            description=f"Failed login attempt for email: {form_data.username}",
            user_email=form_data.username,
            success=False
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "role": user.get("role"),
            "full_name": user.get("full_name")
        }
    )
    
    # Log successful login
    await log_audit_from_request(
        request=request,
        action=AuditAction.LOGIN,
        description=f"User logged in: {user['email']}",
        user_id=str(user["_id"]),
        user_email=user["email"],
        details={
            "role": user.get("role"),
            "full_name": user.get("full_name")
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Logout endpoint - logs the logout action for audit purposes
    
    Note: JWT tokens are stateless, so the token remains valid until expiration.
    The client must delete the token locally.
    
    Args:
        request: FastAPI request for audit logging
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Log logout
    await log_audit_from_request(
        request=request,
        action=AuditAction.LOGOUT,
        description=f"User logged out: {current_user['email']}",
        user_id=str(current_user.get("_id")) if current_user.get("_id") else None,
        user_email=current_user["email"],
        details={
            "role": current_user.get("role"),
            "full_name": current_user.get("full_name")
        }
    )
    
    return {"message": "Logout exitoso"}


@router.post("/auth/forgot-password")
async def forgot_password(
    fastapi_request: Request,
    request: ForgotPasswordRequest
):
    """
    Initiate password reset process
    
    Generates a reset token and sends it via email.
    Always returns success for security (no user enumeration).
    """
    try:
        # Check if user exists
        user = await user_repository.get_user_by_email(request.email)
        
        if not user:
            # Security: always return success even if email doesn't exist
            return {"message": "Si el email existe, recibirás un enlace de recuperación"}
        
        # Generate secure token
        reset_token = generate_reset_token()
        
        # Store token in database with 1 hour expiration
        token_data = {
            "email": request.email,
            "token": reset_token,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": False
        }
        
        await reset_tokens_collection.insert_one(token_data)
        
        # Send recovery email
        email_sent = await send_reset_email(request.email, reset_token)
        
        if email_sent:
            logger.info(f"Email de recuperación enviado a: {request.email}")
        else:
            # Fallback: log token if email fails
            logger.warning(
                f"Email falló - Token de recuperación para {request.email}: {reset_token}"
            )
        
        # Log password reset request
        await log_audit_from_request(
            request=fastapi_request,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            description=f"Password reset requested for: {request.email}",
            user_id=str(user["_id"]),
            user_email=request.email
        )
        
        return {"message": "Si el email existe, recibirás un enlace de recuperación"}
    
    except Exception as e:
        logger.error(f"Error en forgot_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/auth/reset-password")
async def reset_password(
    fastapi_request: Request,
    request: ResetPasswordRequest
):
    """
    Complete password reset process
    
    Validates reset token and updates user password.
    """
    try:
        # Find valid token
        token_data = await reset_tokens_collection.find_one({
            "token": request.token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not token_data:
            raise HTTPException(
                status_code=400,
                detail="Token inválido o expirado"
            )
        
        # Get user to update
        user = await user_repository.get_user_by_email(token_data["email"])
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Update password using user service
        await user_service.update_password(
            user_id=str(user["_id"]),
            new_password=request.new_password
        )
        
        # Mark token as used
        await reset_tokens_collection.update_one(
            {"token": request.token},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"Password updated for user: {token_data['email']}")
        
        # Log password reset completion
        await log_audit_from_request(
            request=fastapi_request,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            description=f"Password reset completed for: {token_data['email']}",
            user_id=str(user["_id"]) if user else None,
            user_email=token_data["email"]
        )
        
        return {"message": "Contraseña actualizada exitosamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en reset_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.get("/auth/validate-reset-token/{token}")
async def validate_reset_token(token: str):
    """
    Validate if a reset token is still valid
    
    Used by frontend to check token before showing reset form.
    """
    try:
        token_data = await reset_tokens_collection.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if token_data:
            return {"valid": True, "email": token_data["email"]}
        else:
            return {"valid": False}
    
    except Exception as e:
        logger.error(f"Error validando token: {e}")
        return {"valid": False}


@router.post("/auth/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Change password for authenticated user
    
    Args:
        password_request: Request containing old and new passwords
        request: FastAPI request for audit logging
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If old password is incorrect or update fails
    """
    try:
        user_email = current_user.get("email")
        
        # Get user from database
        user = await user_repository.get_user_by_email(user_email)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Verify old password
        if not verify_password(password_request.old_password, user["hashed_password"]):
            # Log failed attempt
            await log_audit_from_request(
                request=request,
                action=AuditAction.PASSWORD_CHANGED,
                description=f"Failed password change attempt for: {user_email}",
                user_id=str(user["_id"]),
                user_email=user_email,
                success=False
            )
            
            raise HTTPException(
                status_code=400,
                detail="La contraseña actual es incorrecta"
            )
        
        # Update password using user service
        await user_service.update_password(
            user_id=str(user["_id"]),
            new_password=password_request.new_password
        )
        
        logger.info(f"Password changed for user: {user_email}")
        
        # Log successful password change
        await log_audit_from_request(
            request=request,
            action=AuditAction.PASSWORD_CHANGED,
            description=f"Password changed successfully for: {user_email}",
            user_id=str(user["_id"]),
            user_email=user_email,
            success=True
        )
        
        return {"message": "Contraseña actualizada exitosamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
