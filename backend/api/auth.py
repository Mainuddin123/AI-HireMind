
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database.connection import get_db
from backend.models.user import User
from backend.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse
)
from backend.authentication.security import (
    hash_password,
    verify_password,
    create_access_token
)
from backend.authentication.dependencies import get_current_user
from backend.authentication.dependencies import require_role

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Candidate registration
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="candidate"
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )


# User login
@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive."
        )

    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# Get currently authenticated user
@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user=Depends(get_current_user)
):
    return current_user


# Recruiter-only test endpoint
@router.get("/recruiter-check")
def recruiter_check(
    current_user=Depends(require_role("recruiter", "admin"))
):
    return {
        "message": "Recruiter access granted",
        "user_role": current_user.role
    }
