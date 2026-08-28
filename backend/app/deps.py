"""
AgriNova Backend — shared FastAPI dependencies.

Every farm-scoped route depends on get_current_farm, which derives the farm
strictly from the JWT-authenticated user — a client can never pass a farm_id
and see someone else's data.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import Farm, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_farm(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Farm:
    farm = db.query(Farm).filter(Farm.owner_id == user.id).first()
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No farm configured yet — complete onboarding first.",
        )
    return farm
