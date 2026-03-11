from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import SalesOrder, SalesOrderItem
from app.services.order_service import generate_packing_orders, import_order_excel, lock_order_inventory
from app.utils.response import fail, ok

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/import")
def import_orders(file: UploadFile = File(...), db: Session = Depends(get_db)):
    target = settings.data_dir / file.filename
    with target.open("wb") as f:
        f.write(file.file.read())
    data, err = import_order_excel(db, str(target), file.filename)
    if err:
        db.rollback()
        return fail(err, "IMPORT_FAILED")
    db.commit()
    return ok(data)


@router.get("")
def list_orders(db: Session = Depends(get_db)):
    return ok([o for o in db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()])


@router.get("/{order_no}")
def order_detail(order_no: str, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
    if not order:
        return fail("订单不存在", "NOT_FOUND")
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_no == order_no).all()
    return ok({"order": order, "items": items})


@router.post("/{order_no}/lock")
def lock_order(order_no: str, db: Session = Depends(get_db)):
    data, err = lock_order_inventory(db, order_no)
    if err:
        db.rollback()
        return fail(err, "LOCK_FAILED")
    db.commit()
    return ok(data)


@router.post("/{order_no}/generate-packing")
def gen_packing(order_no: str, db: Session = Depends(get_db)):
    data, err = generate_packing_orders(db, order_no)
    if err:
        db.rollback()
        return fail(err, "PACKING_FAILED")
    db.commit()
    return ok(data)
