import math
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from app.models import (
    InventorySummary,
    InventoryTransaction,
    PackingOrder,
    PackingOrderItem,
    Product,
    SalesOrder,
    SalesOrderItem,
)
from app.services.inventory_service import recalc_summary
from app.utils.id_gen import gen_order_no, gen_packing_no


HEADER_MAP = {"编码": "sku_code", "名称": "product_name", "店铺": "shop_name", "数量": "qty"}


def import_order_excel(db: Session, file_path: str, import_filename: str):
    df = pd.read_excel(file_path)
    rename_map = {col: HEADER_MAP.get(col, col) for col in df.columns}
    df = df.rename(columns=rename_map)
    for required in ["sku_code", "product_name", "shop_name", "qty"]:
        if required not in df.columns:
            return None, f"缺少列: {required}"

    order_no = gen_order_no()
    shop_name = str(df.iloc[0]["shop_name"])
    customer_name = "默认客户"
    order = SalesOrder(
        order_no=order_no,
        customer_name=customer_name,
        shop_name=shop_name,
        import_file_name=import_filename,
        order_status="DRAFT",
    )
    db.add(order)
    db.flush()

    shortage_exists = False
    for _, row in df.iterrows():
        sku_code = str(row["sku_code"]).strip()
        product_name = str(row["product_name"]).strip()
        qty = int(row["qty"])

        product = db.query(Product).filter(Product.sku_code == sku_code).first()
        pack_qty = product.pack_qty_per_box if product else 1
        required_box_count = math.ceil(qty / pack_qty)

        summary = db.query(InventorySummary).filter(InventorySummary.sku_code == sku_code).first()
        available = summary.available_qty if summary else 0
        can_fulfill = available >= qty
        shortage_qty = max(0, qty - available)
        shortage_exists = shortage_exists or (not can_fulfill)

        db.add(
            SalesOrderItem(
                order_no=order_no,
                sku_code=sku_code,
                product_name=product_name,
                qty=qty,
                pack_qty_per_box=pack_qty,
                required_box_count=required_box_count,
                shortage_qty=shortage_qty,
                can_fulfill=can_fulfill,
            )
        )

    order.order_status = "SHORTAGE" if shortage_exists else "CHECKED"
    return {"order_no": order_no, "order_status": order.order_status}, None


def lock_order_inventory(db: Session, order_no: str, operator_id: int | None = None, operator_name: str | None = None):
    order = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
    if not order:
        return None, "订单不存在"
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_no == order_no).all()
    for item in items:
        summary = db.query(InventorySummary).filter(InventorySummary.sku_code == item.sku_code).with_for_update().first()
        if not summary or summary.available_qty < item.qty:
            return None, f"SKU {item.sku_code} 可用库存不足"

    for item in items:
        summary = db.query(InventorySummary).filter(InventorySummary.sku_code == item.sku_code).first()
        summary.locked_qty += item.qty
        recalc_summary(summary)
        db.add(
            InventoryTransaction(
                sku_code=item.sku_code,
                transaction_type="LOCK",
                qty=item.qty,
                source_type="order_lock",
                source_no=order_no,
                operator_id=operator_id,
                operator_name=operator_name,
            )
        )
    order.order_status = "LOCKED"
    return {"order_no": order_no, "order_status": order.order_status}, None


def generate_packing_orders(db: Session, order_no: str):
    order = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
    if not order:
        return None, "订单不存在"
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_no == order_no).all()
    seq = (db.query(PackingOrder).count() or 0) + 1

    box_payload = []
    for item in items:
        remaining = item.qty
        while remaining > 0:
            take_qty = min(item.pack_qty_per_box, remaining)
            box_payload.append({"sku_code": item.sku_code, "product_name": item.product_name, "qty": take_qty})
            remaining -= take_qty

    total_boxes = len(box_payload)
    created = []
    for idx, box in enumerate(box_payload, start=1):
        packing_no = gen_packing_no(seq)
        seq += 1
        pack_order = PackingOrder(
            packing_no=packing_no,
            order_no=order_no,
            customer_name=order.customer_name,
            shop_name=order.shop_name,
            box_index=idx,
            total_boxes=total_boxes,
            packing_status="PENDING",
        )
        db.add(pack_order)
        db.flush()
        db.add(
            PackingOrderItem(
                packing_no=packing_no,
                sku_code=box["sku_code"],
                product_name=box["product_name"],
                required_qty=box["qty"],
                scanned_qty=0,
            )
        )
        created.append(packing_no)

    order.order_status = "READY"
    return {"order_no": order_no, "packing_count": len(created), "packing_nos": created}, None
