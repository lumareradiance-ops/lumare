from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
      return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
      return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str, email: str, is_admin: bool = False) -> str:
      payload = {
                "sub": user_id,
                "email": email,
                "is_admin": is_admin,
                "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
      }
      return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
      try:
                return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
      credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
      db: Session = Depends(get_db),
) -> User:
      if credentials is None:
                raise HTTPException(status_code=401, detail="Missing authorization token")
            payload = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
              raise HTTPException(status_code=401, detail="User not found")
          return user


def get_current_user_optional(
      credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
      db: Session = Depends(get_db),
) -> Optional[User]:
      if credentials is None:
                return None
            try:
                      payload = decode_token(credentials.credentials)
except HTTPException:
        return None
    return db.query(User).filter(User.id == payload.get("sub")).first()


def require_admin(user: User = Depends(get_current_user)) -> User:
      if not user.is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")
            return user
