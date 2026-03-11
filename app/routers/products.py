from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product
from app.schemas.master import ProductCreate, ProductUpdate
from app.utils.response import fail, ok

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(db: Session = Depends(get_db)):
    return ok([p for p in db.query(Product).order_by(Product.id.desc()).all()])


@router.post("")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    exists = db.query(Product).filter(Product.sku_code == payload.sku_code).first()
    if exists:
        return fail("SKU已存在", "SKU_DUPLICATE")
    obj = Product(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return ok(obj)


@router.put("/{id}")
def update_product(id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    obj = db.query(Product).filter(Product.id == id).first()
    if not obj:
        return fail("产品不存在", "NOT_FOUND")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return ok(obj)


@router.delete("/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    obj = db.query(Product).filter(Product.id == id).first()
    if not obj:
        return fail("产品不存在", "NOT_FOUND")
    db.delete(obj)
    db.commit()
    return ok(message="deleted")
