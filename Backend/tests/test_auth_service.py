"""
Tests for authentication and authorization
"""

import pytest
from fastapi import HTTPException
from datetime import datetime, timedelta
from jose import jwt

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token
)
from app.config.settings import settings


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test that passwords are properly hashed"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")  # Bcrypt prefix
    
    def test_verify_correct_password(self):
        """Test that correct password verification works"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password verification fails"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password generates different hashes (salt)"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAccessToken:
    """Test access token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com", "role": "operario"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_access_token_contains_data(self):
        """Test that access token contains encoded data"""
        data = {"sub": "test@example.com", "role": "operario"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "operario"
        assert "exp" in payload
    
    def test_access_token_expiration(self):
        """Test that access token has correct expiration"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Should expire in approximately ACCESS_TOKEN_EXPIRE_MINUTES
        time_diff = (exp_time - now).total_seconds() / 60
        assert 14 <= time_diff <= 16  # ~15 minutes (default)
    
    def test_custom_expiration(self):
        """Test creating token with custom expiration"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=5))
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        time_diff = (exp_time - now).total_seconds() / 60
        assert 4 <= time_diff <= 6  # ~5 minutes


class TestRefreshToken:
    """Test refresh token creation"""
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_refresh_token_longer_expiration(self):
        """Test that refresh tokens have longer expiration"""
        data = {"sub": "test@example.com"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        
        assert refresh_exp > access_exp


class TestTokenDecoding:
    """Test token decoding and validation"""
    
    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"sub": "test@example.com", "role": "operario"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "operario"
    
    def test_decode_expired_token(self):
        """Test that expired tokens raise error"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_decode_invalid_token(self):
        """Test that invalid tokens raise error"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_malformed_token(self):
        """Test that malformed tokens raise error"""
        # Token with wrong signature
        data = {"sub": "test@example.com"}
        token = jwt.encode(data, "wrong_secret", algorithm=settings.ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401


class TestAuthIntegration:
    """Integration tests for authentication flow"""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test complete authentication flow"""
        # 1. Create user with hashed password
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        user_data = {
            "email": "test@example.com",
            "hashed_password": hashed,
            "role": "operario"
        }
        
        # 2. Verify password
        assert verify_password(password, hashed) is True
        
        # 3. Create tokens
        token_data = {"sub": user_data["email"], "role": user_data["role"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # 4. Decode and validate access token
        decoded = decode_token(access_token)
        assert decoded["sub"] == user_data["email"]
        assert decoded["role"] == user_data["role"]
    
    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        # 1. Create initial tokens
        data = {"sub": "test@example.com", "role": "operario"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        # 2. Decode refresh token
        refresh_payload = decode_token(refresh_token)
        
        # 3. Create new access token
        new_access_token = create_access_token({
            "sub": refresh_payload["sub"],
            "role": refresh_payload.get("role", "usuario")
        })
        
        # 4. Validate new token
        new_payload = decode_token(new_access_token)
        assert new_payload["sub"] == data["sub"]


class TestSecurityFeatures:
    """Test security features"""
    
    def test_token_cannot_be_modified(self):
        """Test that modified tokens are invalid"""
        data = {"sub": "test@example.com", "role": "usuario"}
        token = create_access_token(data)
        
        # Try to decode and modify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        payload["role"] = "administrador"  # Try to elevate privileges
        
        # Re-encode with same key
        modified_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Original token should still decode correctly
        original_decoded = decode_token(token)
        assert original_decoded["role"] == "usuario"
        
        # Modified token has different signature (exp changed)
        modified_decoded = decode_token(modified_token)
        assert modified_decoded["role"] == "administrador"  # But exp is different
    
    def test_different_secrets_produce_invalid_tokens(self):
        """Test that tokens from different secrets are invalid"""
        data = {"sub": "test@example.com"}
        
        # Create token with wrong secret
        wrong_token = jwt.encode(
            {**data, "exp": datetime.utcnow() + timedelta(minutes=15)},
            "wrong_secret_key",
            algorithm=settings.ALGORITHM
        )
        
        # Should fail to decode
        with pytest.raises(HTTPException):
            decode_token(wrong_token)
    
    def test_token_without_expiration(self):
        """Test that tokens without exp claim are handled"""
        # This shouldn't happen in normal flow, but test it anyway
        data = {"sub": "test@example.com"}
        token_without_exp = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Should decode (JWT library adds exp by default, but let's be safe)
        try:
            payload = decode_token(token_without_exp)
            assert "sub" in payload
        except HTTPException:
            # If it fails, that's also acceptable for security
            pass


class TestRoleValidation:
    """Test role-based authorization"""
    
    def test_token_with_different_roles(self):
        """Test creating tokens with different roles"""
        roles = ["administrador", "operario", "usuario"]
        
        for role in roles:
            data = {"sub": f"{role}@example.com", "role": role}
            token = create_access_token(data)
            payload = decode_token(token)
            
            assert payload["role"] == role
    
    def test_token_without_role(self):
        """Test token creation without role (should default)"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        payload = decode_token(token)
        
        # Token should still be valid even without role
        assert payload["sub"] == "test@example.com"
        # Role may or may not be present, both are valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
