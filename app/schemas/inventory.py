from datetime import datetime

from pydantic import BaseModel


class InventoryInboundScanRequest(BaseModel):
    barcode: str
    qty: int = 1
    operator_id: int | None = None
    operator_name: str | None = None
    remark: str | None = None


class InventoryAdjustRequest(BaseModel):
    sku_code: str
    qty: int
    operator_id: int | None = None
    operator_name: str | None = None
    remark: str | None = None


class InventorySummaryOut(BaseModel):
    sku_code: str
    product_name: str
    total_in_qty: int
    total_out_qty: int
    locked_qty: int
    current_qty: int
    available_qty: int
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryTransactionOut(BaseModel):
    sku_code: str
    barcode: str | None
    transaction_type: str
    qty: int
    source_type: str
    source_no: str | None
    operator_id: int | None
    operator_name: str | None
    remark: str | None
    created_at: datetime

    class Config:
        from_attributes = True
