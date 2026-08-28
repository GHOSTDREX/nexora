from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = "en"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    has_farm: bool


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    preferred_language: str

    class Config:
        from_attributes = True


class UpdateLanguageRequest(BaseModel):
    preferred_language: str
