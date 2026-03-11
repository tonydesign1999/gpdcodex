from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Shop
from app.schemas.master import ShopCreate, ShopUpdate
from app.utils.response import fail, ok

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("")
def list_shops(db: Session = Depends(get_db)):
    return ok([s for s in db.query(Shop).order_by(Shop.id.desc()).all()])


@router.post("")
def create_shop(payload: ShopCreate, db: Session = Depends(get_db)):
    obj = Shop(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return ok(obj)


@router.put("/{id}")
def update_shop(id: int, payload: ShopUpdate, db: Session = Depends(get_db)):
    obj = db.query(Shop).filter(Shop.id == id).first()
    if not obj:
        return fail("店铺不存在", "NOT_FOUND")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return ok(obj)


@router.delete("/{id}")
def delete_shop(id: int, db: Session = Depends(get_db)):
    obj = db.query(Shop).filter(Shop.id == id).first()
    if not obj:
        return fail("店铺不存在", "NOT_FOUND")
    db.delete(obj)
    db.commit()
    return ok(message="deleted")
