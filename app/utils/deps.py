from fastapi import Header
from sqlalchemy.orm import Session

from app.core.security import token_store
from app.db.session import get_db
from app.models import User


def db_dep() -> Session:
    return next(get_db())


def get_current_user(authorization: str | None = Header(default=None), db: Session = None):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    username = token_store.verify(token)
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()
