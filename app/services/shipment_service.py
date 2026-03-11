from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    ActiveShipmentSession,
    InventorySummary,
    InventoryTransaction,
    PackingOrder,
    PackingOrderItem,
    Product,
    ShipmentRecord,
    ShipmentScanLog,
)
from app.services.inventory_service import recalc_summary
from app.utils.id_gen import gen_shipment_no


def log_scan(db: Session, **kwargs):
    db.add(ShipmentScanLog(**kwargs))


def shipment_start(db: Session, packing_no: str, operator_id: int | None, operator_name: str | None):
    pack = db.query(PackingOrder).filter(PackingOrder.packing_no == packing_no).first()
    if not pack:
        return None, "装箱单不存在"
    if pack.packing_status == "SHIPPED":
        return None, "该箱已发货"
    session = db.query(ActiveShipmentSession).filter(ActiveShipmentSession.packing_no == packing_no).first()
    if not session:
        db.add(ActiveShipmentSession(packing_no=packing_no, operator_id=operator_id, operator_name=operator_name))
    pack.packing_status = "PACKING"
    log_scan(db, packing_no=packing_no, scan_type="PACKING_SHEET", scan_result="OK", operator_id=operator_id, operator_name=operator_name)
    return {"packing_no": packing_no, "status": pack.packing_status}, None


def scan_product(db: Session, packing_no: str, barcode: str, operator_id: int | None, operator_name: str | None):
    pack_item = None
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        log_scan(db, packing_no=packing_no, barcode=barcode, scan_type="PRODUCT", scan_result="INVALID_BARCODE")
        return None, "条码无效"

    pack_item = db.query(PackingOrderItem).filter(
        PackingOrderItem.packing_no == packing_no, PackingOrderItem.sku_code == product.sku_code
    ).first()
    if not pack_item:
        log_scan(db, packing_no=packing_no, barcode=barcode, sku_code=product.sku_code, scan_type="PRODUCT", scan_result="SKU_NOT_IN_PACK")
        return None, "该SKU不属于当前箱"
    if pack_item.scanned_qty >= pack_item.required_qty:
        log_scan(db, packing_no=packing_no, barcode=barcode, sku_code=product.sku_code, scan_type="PRODUCT", scan_result="OVER_SCAN")
        return None, "扫描数量超过应装数量"
    pack_item.scanned_qty += 1
    log_scan(db, packing_no=packing_no, barcode=barcode, sku_code=product.sku_code, scan_type="PRODUCT", scan_result="OK", operator_id=operator_id, operator_name=operator_name)
    return {"packing_no": packing_no, "sku_code": product.sku_code, "scanned_qty": pack_item.scanned_qty}, None


def bind_sf(db: Session, packing_no: str, sf_tracking_no: str):
    pack = db.query(PackingOrder).filter(PackingOrder.packing_no == packing_no).first()
    if not pack:
        return None, "装箱单不存在"
    duplicate = db.query(PackingOrder).filter(PackingOrder.sf_tracking_no == sf_tracking_no, PackingOrder.packing_no != packing_no).first()
    if duplicate:
        return None, "顺丰单号重复"
    items = db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == packing_no).all()
    if any(it.scanned_qty < it.required_qty for it in items):
        return None, "商品未扫描完成，不能绑定顺丰单号"
    pack.sf_tracking_no = sf_tracking_no
    pack.packing_status = "SF_BOUND"
    log_scan(db, packing_no=packing_no, scan_type="SF_NO", scan_result="OK")
    return {"packing_no": packing_no, "sf_tracking_no": sf_tracking_no}, None


def confirm_shipment(db: Session, packing_no: str, operator_id: int | None, operator_name: str | None):
    pack = db.query(PackingOrder).filter(PackingOrder.packing_no == packing_no).first()
    if not pack:
        return None, "装箱单不存在"
    if pack.packing_status == "SHIPPED":
        return None, "不允许重复发货"
    if not pack.sf_tracking_no:
        return None, "请先绑定顺丰单号"

    items = db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == packing_no).all()
    for item in items:
        summary = db.query(InventorySummary).filter(InventorySummary.sku_code == item.sku_code).with_for_update().first()
        if not summary or summary.locked_qty < item.required_qty:
            return None, f"SKU {item.sku_code} 锁定库存不足"

    shipment_no = gen_shipment_no()
    db.add(
        ShipmentRecord(
            shipment_no=shipment_no,
            order_no=pack.order_no,
            packing_no=packing_no,
            sf_tracking_no=pack.sf_tracking_no,
            operator_id=operator_id,
            operator_name=operator_name,
            shipment_status="SHIPPED",
            shipped_at=datetime.utcnow(),
        )
    )

    for item in items:
        summary = db.query(InventorySummary).filter(InventorySummary.sku_code == item.sku_code).first()
        summary.total_out_qty += item.required_qty
        summary.locked_qty -= item.required_qty
        recalc_summary(summary)
        db.add(
            InventoryTransaction(
                sku_code=item.sku_code,
                transaction_type="OUT",
                qty=item.required_qty,
                source_type="shipment",
                source_no=packing_no,
                operator_id=operator_id,
                operator_name=operator_name,
            )
        )

    pack.packing_status = "SHIPPED"
    log_scan(db, packing_no=packing_no, scan_type="CONFIRM", scan_result="OK", operator_id=operator_id, operator_name=operator_name)
    db.query(ActiveShipmentSession).filter(ActiveShipmentSession.packing_no == packing_no).delete()
    return {"packing_no": packing_no, "shipment_no": shipment_no}, None
