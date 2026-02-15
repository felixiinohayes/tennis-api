import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import UserDB, PlayerDB
from app.schemas import RegisterRequest, AuthResponse, LoginRequest
from app.auth import hash_password, verify_password, make_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user_id = str(uuid.uuid4())
    user = UserDB(
        id=user_id,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    player = PlayerDB(
        user_id=user_id,
        name=payload.name,
        initials="".join([p[0] for p in payload.name.split()[:2]]).upper(),
    )

    db.add(player)
    db.add(user)
    db.commit()

    token = make_token(user.id)
    return AuthResponse(token=token, user_id=user.id, username=user.username)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = make_token(user.id)
    return AuthResponse(token=token, user_id=user.id, username=user.username)
