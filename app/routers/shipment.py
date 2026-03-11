from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.shipment import (
    ShipmentBindSFRequest,
    ShipmentConfirmRequest,
    ShipmentScanProductRequest,
    ShipmentStartRequest,
)
from app.services.shipment_service import bind_sf, confirm_shipment, scan_product, shipment_start
from app.utils.response import fail, ok

router = APIRouter(prefix="/shipment", tags=["shipment"])


@router.post("/start")
def start(payload: ShipmentStartRequest, db: Session = Depends(get_db)):
    data, err = shipment_start(db, payload.packing_no, payload.operator_id, payload.operator_name)
    if err:
        db.rollback()
        return fail(err, "SHIPMENT_START_FAILED")
    db.commit()
    return ok(data)


@router.post("/scan-product")
def scan(payload: ShipmentScanProductRequest, db: Session = Depends(get_db)):
    data, err = scan_product(db, payload.packing_no, payload.barcode, payload.operator_id, payload.operator_name)
    if err:
        db.rollback()
        return fail(err, "SCAN_FAILED")
    db.commit()
    return ok(data)


@router.post("/bind-sf")
def bind(payload: ShipmentBindSFRequest, db: Session = Depends(get_db)):
    data, err = bind_sf(db, payload.packing_no, payload.sf_tracking_no)
    if err:
        db.rollback()
        return fail(err, "SF_DUPLICATE" if "重复" in err else "BIND_FAILED")
    db.commit()
    return ok(data)


@router.post("/confirm")
def confirm(payload: ShipmentConfirmRequest, db: Session = Depends(get_db)):
    data, err = confirm_shipment(db, payload.packing_no, payload.operator_id, payload.operator_name)
    if err:
        db.rollback()
        return fail(err, "CONFIRM_FAILED")
    db.commit()
    return ok(data)
