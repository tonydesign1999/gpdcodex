from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    spec: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pack_qty_per_box: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Shop(Base, TimestampMixin):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    shop_name: Mapped[str] = mapped_column(String(255), index=True)
    export_template_type: Mapped[str] = mapped_column(String(64), default="default")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="worker")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20))
    qty: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(40))
    source_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InventorySummary(Base):
    __tablename__ = "inventory_summary"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    total_in_qty: Mapped[int] = mapped_column(Integer, default=0)
    total_out_qty: Mapped[int] = mapped_column(Integer, default=0)
    locked_qty: Mapped[int] = mapped_column(Integer, default=0)
    current_qty: Mapped[int] = mapped_column(Integer, default=0)
    available_qty: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    shop_name: Mapped[str] = mapped_column(String(255))
    import_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_status: Mapped[str] = mapped_column(String(20), default="DRAFT")


class SalesOrderItem(Base, TimestampMixin):
    __tablename__ = "sales_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer)
    pack_qty_per_box: Mapped[int] = mapped_column(Integer, default=1)
    required_box_count: Mapped[int] = mapped_column(Integer, default=1)
    shortage_qty: Mapped[int] = mapped_column(Integer, default=0)
    can_fulfill: Mapped[bool] = mapped_column(Boolean, default=True)


class PackingOrder(Base, TimestampMixin):
    __tablename__ = "packing_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    packing_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    shop_name: Mapped[str] = mapped_column(String(255))
    box_index: Mapped[int] = mapped_column(Integer)
    total_boxes: Mapped[int] = mapped_column(Integer)
    sf_tracking_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    packing_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PackingOrderItem(Base, TimestampMixin):
    __tablename__ = "packing_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    packing_no: Mapped[str] = mapped_column(String(64), index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    required_qty: Mapped[int] = mapped_column(Integer)
    scanned_qty: Mapped[int] = mapped_column(Integer, default=0)


class ShipmentRecord(Base, TimestampMixin):
    __tablename__ = "shipment_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), index=True)
    packing_no: Mapped[str] = mapped_column(String(64), index=True)
    sf_tracking_no: Mapped[str] = mapped_column(String(64))
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipment_status: Mapped[str] = mapped_column(String(20), default="SHIPPED")
    shipped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ShipmentScanLog(Base):
    __tablename__ = "shipment_scan_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    packing_no: Mapped[str] = mapped_column(String(64), index=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sku_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scan_type: Mapped[str] = mapped_column(String(20))
    scan_result: Mapped[str] = mapped_column(String(255))
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ActiveShipmentSession(Base):
    __tablename__ = "active_shipment_sessions"
    __table_args__ = (UniqueConstraint("packing_no", name="uq_active_packing_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    packing_no: Mapped[str] = mapped_column(String(64), index=True)
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
