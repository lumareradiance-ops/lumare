from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
      existing = db.query(User).filter(User.email == payload.email).first()
      if existing:
                raise HTTPException(status_code=409, detail="An account with this email already exists")

      user = User(
          name=payload.name,
          email=payload.email,
          phone=payload.phone,
          password_hash=hash_password(payload.password),
      )
      db.add(user)
      db.commit()
      db.refresh(user)

    token = create_access_token(user.id, user.email, user.is_admin)
    return {"token": token, "user": user}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
      user = db.query(User).filter(User.email == payload.email).first()
      if not user or not verify_password(payload.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid email or password")

      token = create_access_token(user.id, user.email, user.is_admin)
      return {"token": token, "user": user}
  
