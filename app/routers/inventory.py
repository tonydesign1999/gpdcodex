from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import InventorySummary, InventoryTransaction
from app.schemas.inventory import InventoryAdjustRequest, InventoryInboundScanRequest
from app.services.export_service import export_inventory
from app.services.inventory_service import adjust_inventory, inbound_scan
from app.utils.response import fail, ok

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return ok([r for r in db.query(InventorySummary).order_by(InventorySummary.updated_at.desc()).all()])


@router.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return ok([r for r in db.query(InventoryTransaction).order_by(InventoryTransaction.id.desc()).limit(200).all()])


@router.post("/inbound/scan")
def inbound(payload: InventoryInboundScanRequest, db: Session = Depends(get_db)):
    data, err = inbound_scan(db, payload.barcode, payload.qty, payload.operator_id, payload.operator_name, payload.remark)
    if err:
        db.rollback()
        return fail(err, "INVALID_BARCODE")
    db.commit()
    return ok(data)


@router.post("/adjust")
def adjust(payload: InventoryAdjustRequest, db: Session = Depends(get_db)):
    data, err = adjust_inventory(db, payload.sku_code, payload.qty, payload.operator_id, payload.operator_name, payload.remark)
    if err:
        db.rollback()
        return fail(err, "ADJUST_FAILED")
    db.commit()
    return ok(data)


@router.get("/export")
def export_inventory_file(db: Session = Depends(get_db)):
    output = export_inventory(db)
    return FileResponse(output, filename=output.name)
