import logging
from datetime import datetime, timedelta

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
logger = logging.getLogger("agrinova.security")

LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 15
# bcrypt-verified against on every login for a user that doesn't exist, so a
# missing-account response takes the same time as a wrong-password one and
# timing can't be used to enumerate registered emails.
_DUMMY_HASH = hash_password("no-such-account-dummy-hash")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="register", max_attempts=5, window_seconds=3600)

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        logger.info("Register attempt for an email that's already registered")
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

    logger.info("New user registered: user_id=%s", user.id)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, has_farm=False)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, key_prefix="login", max_attempts=10, window_seconds=300)

    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if user is not None and user.locked_until and user.locked_until > datetime.utcnow():
        logger.warning("Login blocked for locked account: user_id=%s", user.id)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    # Always run the bcrypt check, even for an email that doesn't exist —
    # against a fixed dummy hash — so this endpoint's response time doesn't
    # leak which emails are registered.
    password_hash = user.password_hash if user is not None else _DUMMY_HASH
    password_ok = verify_password(payload.password, password_hash)

    if user is None or not password_ok:
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                logger.warning(
                    "Account locked after %s failed logins: user_id=%s",
                    user.failed_login_attempts, user.id,
                )
            else:
                logger.warning(
                    "Failed login attempt %s/%s: user_id=%s",
                    user.failed_login_attempts, LOCKOUT_THRESHOLD, user.id,
                )
            db.commit()
        else:
            logger.warning("Failed login attempt for unregistered email")
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    logger.info("Successful login: user_id=%s", user.id)
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
