"""
Tests for authentication services
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    validate_admin_role
)


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails verification"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com", "role": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
    
    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_token_contains_correct_data(self):
        """Test that token contains the correct data"""
        from jose import jwt
        from app.config import settings
        
        data = {"sub": "test@example.com", "role": "admin"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert "exp" in decoded


class TestAuthenticationLogic:
    """Test authentication business logic"""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mocker):
        """Test successful user authentication"""
        # Mock users collection
        mock_user = {
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123")
        }
        
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = mock_user
        
        mocker.patch("app.services.auth.users_collection", mock_collection)
        
        result = await authenticate_user("test@example.com", "password123")
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mocker):
        """Test authentication fails with wrong password"""
        mock_user = {
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123")
        }
        
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = mock_user
        
        mocker.patch("app.services.auth.users_collection", mock_collection)
        
        result = await authenticate_user("test@example.com", "wrongpassword")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mocker):
        """Test authentication fails when user not found"""
        mock_collection = mocker.AsyncMock()
        mock_collection.find_one.return_value = None
        
        mocker.patch("app.services.auth.users_collection", mock_collection)
        
        result = await authenticate_user("nonexistent@example.com", "password123")
        assert result is None


class TestAdminValidation:
    """Test admin role validation"""
    
    def test_validate_admin_role_success(self):
        """Test admin role validation succeeds for admin"""
        admin_user = {"_id": "123", "email": "admin@example.com", "role": "admin"}
        result = validate_admin_role(admin_user)
        assert result == admin_user
    
    def test_validate_admin_role_fails_for_non_admin(self):
        """Test admin role validation fails for non-admin"""
        from fastapi import HTTPException
        
        user = {"_id": "123", "email": "user@example.com", "role": "operario"}
        
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_role(user)
        
        assert exc_info.value.status_code == 403
        assert "administrador" in exc_info.value.detail.lower()
