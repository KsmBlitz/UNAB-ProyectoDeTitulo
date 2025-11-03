"""
User models
Pydantic models for user management and authentication
"""

from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class TokenData(BaseModel):
    """JWT token payload data"""
    email: Optional[str] = None


class Token(BaseModel):
    """JWT access token response"""
    access_token: str
    token_type: str


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    disabled: Optional[bool] = False
    phone: Optional[str] = None  # Teléfono en formato internacional (ej: +56912345678)
    whatsapp_notifications_enabled: Optional[bool] = False  # Preferencia de notificaciones WhatsApp


class UserCreate(UserBase):
    """User creation model with password"""
    password: str


class UserUpdate(BaseModel):
    """User update model - all fields optional"""
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None
    phone: Optional[str] = None
    whatsapp_notifications_enabled: Optional[bool] = None


class UserPublic(UserBase):
    """Public user model with ID - returned in API responses"""
    id: str = Field(alias='_id')
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class ForgotPasswordRequest(BaseModel):
    """Request model for password reset request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for password reset confirmation"""
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password while authenticated"""
    old_password: str
    new_password: str
