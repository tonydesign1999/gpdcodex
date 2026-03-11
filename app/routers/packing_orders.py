from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import PackingOrder, PackingOrderItem
from app.utils.response import fail, ok

router = APIRouter(prefix="/packing-orders", tags=["packing-orders"])


@router.get("")
def list_packing(db: Session = Depends(get_db)):
    return ok([r for r in db.query(PackingOrder).order_by(PackingOrder.id.desc()).all()])


@router.get("/{packing_no}")
def detail_packing(packing_no: str, db: Session = Depends(get_db)):
    order = db.query(PackingOrder).filter(PackingOrder.packing_no == packing_no).first()
    if not order:
        return fail("装箱单不存在", "NOT_FOUND")
    items = db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == packing_no).all()
    return ok({"order": order, "items": items})


@router.post("/{packing_no}/print", response_class=HTMLResponse)
def print_packing(packing_no: str, db: Session = Depends(get_db)):
    order = db.query(PackingOrder).filter(PackingOrder.packing_no == packing_no).first()
    if not order:
        return HTMLResponse("<h3>装箱单不存在</h3>", status_code=404)
    items = db.query(PackingOrderItem).filter(PackingOrderItem.packing_no == packing_no).all()
    rows = "".join(
        [f"<tr><td>{it.sku_code}</td><td>{it.product_name}</td><td>{it.required_qty}</td><td>{it.scanned_qty}</td></tr>" for it in items]
    )
    html = f"""
    <html><head><meta charset='utf-8'><title>装箱单打印</title></head>
    <body>
    <h2>装箱单号: {order.packing_no}</h2>
    <p>订单号: {order.order_no} | 店铺: {order.shop_name} | 箱号: {order.box_index}/{order.total_boxes}</p>
    <div style='margin:12px 0;padding:8px;border:1px dashed #333;'>[二维码/条码占位: {order.packing_no}]</div>
    <table border='1' cellspacing='0' cellpadding='6'>
    <tr><th>SKU</th><th>产品</th><th>应装数量</th><th>已扫数量</th></tr>{rows}
    </table>
    </body></html>
    """
    return HTMLResponse(html)
