
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# User registration request
class UserRegister(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


# Login request
class UserLogin(BaseModel):

    email: EmailStr
    password: str


# Successful login response
class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


# Authenticated user information
class UserResponse(BaseModel):

    id: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
