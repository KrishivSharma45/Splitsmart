from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UserOut
from app.security.password import validate_password_strength


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be blank")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        error = validate_password_strength(v)
        if error:
            raise ValueError(error)
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
