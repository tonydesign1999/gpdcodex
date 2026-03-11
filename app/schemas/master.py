from datetime import datetime

from pydantic import BaseModel


class ProductBase(BaseModel):
    sku_code: str
    product_name: str
    barcode: str | None = None
    spec: str | None = None
    pack_qty_per_box: int = 1
    enabled: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: str | None = None
    barcode: str | None = None
    spec: str | None = None
    pack_qty_per_box: int | None = None
    enabled: bool | None = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShopBase(BaseModel):
    customer_name: str
    shop_name: str
    export_template_type: str = "default"
    enabled: bool = True


class ShopCreate(ShopBase):
    pass


class ShopUpdate(BaseModel):
    customer_name: str | None = None
    shop_name: str | None = None
    export_template_type: str | None = None
    enabled: bool | None = None


class ShopOut(ShopBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
