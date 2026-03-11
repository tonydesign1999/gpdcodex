from datetime import datetime

from sqlalchemy.orm import Session

from app.models import InventorySummary, InventoryTransaction, Product


def recalc_summary(summary: InventorySummary) -> None:
    summary.current_qty = summary.total_in_qty - summary.total_out_qty
    summary.available_qty = summary.current_qty - summary.locked_qty
    summary.updated_at = datetime.utcnow()


def get_or_create_summary(db: Session, sku_code: str, product_name: str) -> InventorySummary:
    summary = db.query(InventorySummary).filter(InventorySummary.sku_code == sku_code).first()
    if not summary:
        summary = InventorySummary(sku_code=sku_code, product_name=product_name)
        db.add(summary)
        db.flush()
    return summary


def inbound_scan(
    db: Session,
    barcode: str,
    qty: int,
    operator_id: int | None,
    operator_name: str | None,
    remark: str | None,
):
    product = db.query(Product).filter(Product.barcode == barcode, Product.enabled.is_(True)).first()
    if not product:
        return None, "条码无效"
    summary = get_or_create_summary(db, product.sku_code, product.product_name)
    summary.total_in_qty += qty
    recalc_summary(summary)

    tx = InventoryTransaction(
        sku_code=product.sku_code,
        barcode=barcode,
        transaction_type="IN",
        qty=qty,
        source_type="manual_in",
        operator_id=operator_id,
        operator_name=operator_name,
        remark=remark,
    )
    db.add(tx)
    db.flush()
    return {"sku_code": product.sku_code, "qty": qty, "available_qty": summary.available_qty}, None


def adjust_inventory(db: Session, sku_code: str, qty: int, operator_id: int | None, operator_name: str | None, remark: str | None):
    summary = db.query(InventorySummary).filter(InventorySummary.sku_code == sku_code).first()
    if not summary:
        return None, "SKU不存在"
    if qty >= 0:
        summary.total_in_qty += qty
        tx_type = "ADJUST"
    else:
        if summary.available_qty < abs(qty):
            return None, "可用库存不足"
        summary.total_out_qty += abs(qty)
        tx_type = "ADJUST"
    recalc_summary(summary)

    db.add(
        InventoryTransaction(
            sku_code=sku_code,
            transaction_type=tx_type,
            qty=qty,
            source_type="adjust",
            operator_id=operator_id,
            operator_name=operator_name,
            remark=remark,
        )
    )
    return {"sku_code": sku_code, "current_qty": summary.current_qty, "available_qty": summary.available_qty}, None
