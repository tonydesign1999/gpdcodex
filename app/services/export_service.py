from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import InventorySummary, PackingOrderItem, ShipmentRecord, PackingOrder, SalesOrder, Product


def export_inventory(db: Session) -> Path:
    rows = db.query(InventorySummary).all()
    data = [
        {
            "SKU编码": r.sku_code,
            "产品名称": r.product_name,
            "当前库存": r.current_qty,
            "锁定库存": r.locked_qty,
            "可用库存": r.available_qty,
            "最近更新时间": r.updated_at,
        }
        for r in rows
    ]
    output = settings.export_dir / "inventory_export.xlsx"
    pd.DataFrame(data).to_excel(output, index=False)
    return output


def export_shipments(db: Session) -> Path:
    records = db.query(ShipmentRecord, PackingOrder, SalesOrder).join(PackingOrder, ShipmentRecord.packing_no == PackingOrder.packing_no).join(SalesOrder, PackingOrder.order_no == SalesOrder.order_no).all()
    data = []
    for rec, pack, order in records:
        items = db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == pack.packing_no).all()
        for item in items:
            data.append(
                {
                    "客户": order.customer_name,
                    "店铺": order.shop_name,
                    "订单号": order.order_no,
                    "装箱单号": pack.packing_no,
                    "顺丰单号": rec.sf_tracking_no,
                    "SKU编码": item.sku_code,
                    "产品名称": item.product_name,
                    "数量": item.required_qty,
                    "发货时间": rec.shipped_at,
                    "操作人": rec.operator_name,
                }
            )
    output = settings.export_dir / "shipment_export.xlsx"
    pd.DataFrame(data).to_excel(output, index=False)
    return output


def export_customer_order(db: Session, order_no: str) -> Path:
    order = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
    packs = db.query(PackingOrder).filter(PackingOrder.order_no == order_no).all()
    data = []
    for pack in packs:
        for item in db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == pack.packing_no).all():
            data.append(
                {
                    "客户": order.customer_name,
                    "店铺": order.shop_name,
                    "订单号": order_no,
                    "装箱单号": pack.packing_no,
                    "SKU编码": item.sku_code,
                    "产品名称": item.product_name,
                    "数量": item.required_qty,
                }
            )
    output = settings.export_dir / f"customer_{order_no}.xlsx"
    pd.DataFrame(data).to_excel(output, index=False)
    return output
