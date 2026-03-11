from datetime import datetime

from pydantic import BaseModel


class PackingOrderItemOut(BaseModel):
    sku_code: str
    product_name: str
    required_qty: int
    scanned_qty: int

    class Config:
        from_attributes = True


class PackingOrderOut(BaseModel):
    packing_no: str
    order_no: str
    customer_name: str
    shop_name: str
    box_index: int
    total_boxes: int
    sf_tracking_no: str | None
    packing_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
