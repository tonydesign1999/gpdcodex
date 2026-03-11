from datetime import datetime

from pydantic import BaseModel


class SalesOrderItemOut(BaseModel):
    sku_code: str
    product_name: str
    qty: int
    pack_qty_per_box: int
    required_box_count: int
    shortage_qty: int
    can_fulfill: bool

    class Config:
        from_attributes = True


class SalesOrderOut(BaseModel):
    order_no: str
    customer_name: str
    shop_name: str
    import_file_name: str | None
    order_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
