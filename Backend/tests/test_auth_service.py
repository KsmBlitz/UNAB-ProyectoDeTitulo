# Backend/tests/test_auth_service.py
"""
Tests for authentication service
Password hashing, JWT tokens, and admin validation
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException

from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_admin_role
)
from app.config.settings import settings


# ============================================
# PASSWORD HASHING TESTS
# ============================================

class TestPasswordHashing:
    """Tests para hash de contraseñas con bcrypt"""
    
    def test_password_hashing(self):
        """Test: hash de contraseña produce hash único"""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt genera hashes largos
        assert hashed.startswith("$2b$")  # Bcrypt prefix
    
    def test_password_verification_success(self):
        """Test: verificar contraseña correcta"""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test: verificar contraseña incorrecta falla"""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test: mismo password genera diferentes hashes (salt)"""
        password = "MySecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Salt diferente
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password_handling(self):
        """Test: contraseña vacía puede hashearse"""
        # En producción, esto debería ser validado por Pydantic
        # pero el servicio debe manejarlo sin crash
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_special_characters_in_password(self):
        """Test: caracteres especiales en contraseña"""
        password = "P@ssw0rd!#$%^&*(){}[]<>?/\\|~`"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_unicode_password(self):
        """Test: contraseña con caracteres unicode"""
        password = "Contraseña123!@#äöü中文"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_very_long_password(self):
        """Test: contraseña muy larga"""
        password = "a" * 200
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True


# ============================================
# JWT TOKEN TESTS
# ============================================

class TestJWTTokens:
    """Tests para creación y validación de tokens JWT"""
    
    def test_create_token_basic(self):
        """Test: crear token JWT básico"""
        data = {"sub": "user@example.com", "role": "usuario"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Decodificar y verificar
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "usuario"
    
    def test_create_token_with_expiration(self):
        """Test: token con tiempo de expiración personalizado"""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verificar que tiene fecha de expiración
        assert "exp" in payload
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Debe expirar en aproximadamente 30 minutos
        time_diff = (exp_datetime - now).total_seconds()
        assert 1700 < time_diff < 1900  # ~30 minutos (1800s) con margen
    
    def test_token_contains_all_data(self):
        """Test: token contiene toda la data proporcionada"""
        data = {
            "sub": "admin@example.com",
            "role": "admin",
            "full_name": "Admin User",
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "admin@example.com"
        assert payload["role"] == "admin"
        assert payload["full_name"] == "Admin User"
        assert payload["custom_field"] == "custom_value"
    
    def test_token_expiration_in_payload(self):
        """Test: payload contiene exp (expiration)"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
    
    def test_default_expiration_time(self):
        """Test: tiempo de expiración por defecto"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Por defecto debería ser ACCESS_TOKEN_EXPIRE_MINUTES
        time_diff_minutes = (exp_datetime - now).total_seconds() / 60
        expected_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        assert expected_minutes - 1 < time_diff_minutes < expected_minutes + 1
    
    def test_token_with_no_expiration(self):
        """Test: token sin expiración explícita usa default"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data, expires_delta=None)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Aún debe tener expiración (la default)
        assert "exp" in payload
    
    def test_token_with_zero_expiration(self):
        """Test: token con expiración de 0 minutos"""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=0)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Token expira inmediatamente
        exp_datetime = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Debería estar muy cerca del tiempo actual
        time_diff = abs((exp_datetime - now).total_seconds())
        assert time_diff < 5  # Menos de 5 segundos de diferencia
    
    def test_token_signature_verification(self):
        """Test: token debe ser verificado con la clave correcta"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)
        
        # Decodificar con clave correcta funciona
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user@example.com"
        
        # Decodificar con clave incorrecta falla
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[settings.ALGORITHM])
    
    def test_tampered_token_rejected(self):
        """Test: token manipulado debe ser rechazado"""
        data = {"sub": "user@example.com", "role": "usuario"}
        token = create_access_token(data)
        
        # Intentar manipular el token cambiando un carácter
        tampered_token = token[:-10] + "XXXXXXXXXX"
        
        with pytest.raises(JWTError):
            jwt.decode(tampered_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ============================================
# ADMIN VALIDATION TESTS
# ============================================

class TestAdminValidation:
    """Tests para validación de rol de administrador"""
    
    def test_validate_admin_success(self):
        """Test: usuario admin pasa validación"""
        admin_user = {
            "email": "admin@example.com",
            "role": "admin",
            "full_name": "Admin User"
        }
        
        result = validate_admin_role(admin_user)
        
        assert result == admin_user
        assert result["role"] == "admin"
    
    def test_validate_admin_fails_for_usuario(self):
        """Test: usuario normal falla validación de admin"""
        normal_user = {
            "email": "user@example.com",
            "role": "usuario",
            "full_name": "Normal User"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_role(normal_user)
        
        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail.lower()
    
    def test_validate_admin_fails_for_operario(self):
        """Test: operario falla validación de admin"""
        operario_user = {
            "email": "operator@example.com",
            "role": "operario",
            "full_name": "Operator User"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_role(operario_user)
        
        assert exc_info.value.status_code == 403
    
    def test_validate_admin_fails_for_none_role(self):
        """Test: usuario sin rol falla validación"""
        user_no_role = {
            "email": "user@example.com",
            "role": None,
            "full_name": "User"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_role(user_no_role)
        
        assert exc_info.value.status_code == 403
    
    def test_validate_admin_case_sensitive(self):
        """Test: validación de rol es case-sensitive"""
        user_wrong_case = {
            "email": "user@example.com",
            "role": "Admin",  # Con mayúscula
            "full_name": "User"
        }
        
        # Debe fallar porque "Admin" != "admin"
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_role(user_wrong_case)
        
        assert exc_info.value.status_code == 403


# ============================================
# INTEGRATION TESTS
# ============================================

class TestAuthenticationIntegration:
    """Tests de integración de autenticación"""
    
    def test_full_auth_flow(self):
        """Test: flujo completo de autenticación"""
        # 1. Crear hash de contraseña
        password = "MyPassword123!"
        hashed = get_password_hash(password)
        
        # 2. Simular usuario en DB
        user = {
            "email": "test@example.com",
            "password": hashed,
            "role": "usuario",
            "full_name": "Test User"
        }
        
        # 3. Verificar contraseña en login
        assert verify_password(password, user["password"]) is True
        
        # 4. Crear token JWT
        token_data = {
            "sub": user["email"],
            "role": user["role"],
            "full_name": user["full_name"]
        }
        token = create_access_token(token_data)
        
        # 5. Verificar token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == user["email"]
        assert payload["role"] == user["role"]
    
    def test_admin_protected_resource_flow(self):
        """Test: flujo de recurso protegido para admin"""
        # 1. Usuario admin
        admin_user = {
            "email": "admin@example.com",
            "role": "admin"
        }
        
        # 2. Validar que es admin
        result = validate_admin_role(admin_user)
        assert result["role"] == "admin"
        
        # 3. Usuario normal
        normal_user = {
            "email": "user@example.com",
            "role": "usuario"
        }
        
        # 4. Validación falla
        with pytest.raises(HTTPException):
            validate_admin_role(normal_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
