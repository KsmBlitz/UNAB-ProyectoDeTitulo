"""
Authentication routes
Login, password reset, and token management
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.models import (
    Token,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.config import users_collection, reset_tokens_collection
from app.services import (
    verify_password,
    get_password_hash,
    create_access_token,
    send_reset_email,
    generate_reset_token
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Autenticación"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - authenticate user and return JWT token
    
    Args:
        form_data: OAuth2 form with username (email) and password
        
    Returns:
        JWT access token and token type
    """
    user = await users_collection.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
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
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Initiate password reset process
    
    Generates a reset token and sends it via email.
    Always returns success for security (no user enumeration).
    """
    try:
        # Check if user exists
        user = await users_collection.find_one({"email": request.email})
        
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
        
        return {"message": "Si el email existe, recibirás un enlace de recuperación"}
    
    except Exception as e:
        logger.error(f"Error en forgot_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )


@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
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
        
        # Update user password
        hashed_password = get_password_hash(request.new_password)
        
        result = await users_collection.update_one(
            {"email": token_data["email"]},
            {"$set": {"hashed_password": hashed_password}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Mark token as used
        await reset_tokens_collection.update_one(
            {"token": request.token},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"Contraseña actualizada para usuario: {token_data['email']}")
        
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
