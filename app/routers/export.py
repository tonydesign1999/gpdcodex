from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.export_service import export_customer_order, export_inventory, export_shipments

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/inventory")
def export_inventory_api(db: Session = Depends(get_db)):
    file_path = export_inventory(db)
    return FileResponse(file_path, filename=file_path.name)


@router.get("/shipments")
def export_shipments_api(db: Session = Depends(get_db)):
    file_path = export_shipments(db)
    return FileResponse(file_path, filename=file_path.name)


@router.get("/customer/{order_no}")
def export_customer_api(order_no: str, db: Session = Depends(get_db)):
    file_path = export_customer_order(db, order_no)
    return FileResponse(file_path, filename=file_path.name)
