from pydantic import BaseModel


class ShipmentStartRequest(BaseModel):
    packing_no: str
    operator_id: int | None = None
    operator_name: str | None = None


class ShipmentScanProductRequest(BaseModel):
    packing_no: str
    barcode: str
    operator_id: int | None = None
    operator_name: str | None = None


class ShipmentBindSFRequest(BaseModel):
    packing_no: str
    sf_tracking_no: str


class ShipmentConfirmRequest(BaseModel):
    packing_no: str
    operator_id: int | None = None
    operator_name: str | None = None
