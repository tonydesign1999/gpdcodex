from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import token_store, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, LogoutRequest
from app.utils.response import fail, ok

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.enabled.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        return fail("用户名或密码错误", "AUTH_FAILED")
    token = token_store.create_token(user.username)
    return ok({"token": token, "username": user.username, "role": user.role})


@router.post("/logout")
def logout(payload: LogoutRequest):
    token_store.revoke(payload.token)
    return ok()
