from datetime import datetime


def gen_order_no() -> str:
    return f"SO{datetime.now().strftime('%Y%m%d%H%M%S%f')[-16:]}"


def gen_packing_no(seq: int) -> str:
    return f"PK{datetime.now().strftime('%Y%m%d')}{seq:04d}"


def gen_shipment_no() -> str:
    return f"SH{datetime.now().strftime('%Y%m%d%H%M%S%f')[-16:]}"
