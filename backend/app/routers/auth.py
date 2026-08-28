from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import Farm, User
from app.deps import get_current_user
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateLanguageRequest,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="register", max_attempts=5, window_seconds=3600)

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, has_farm=False)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="login", max_attempts=10, window_seconds=300)

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id, user.email)
    has_farm = db.query(Farm).filter(Farm.owner_id == user.id).first() is not None
    return TokenResponse(access_token=token, has_farm=has_farm)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me/language", response_model=UserOut)
def update_language(
    payload: UpdateLanguageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.preferred_language = payload.preferred_language
    db.commit()
    db.refresh(user)
    return user
