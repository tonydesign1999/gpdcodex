"""写入示例测试数据。"""

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Product, Shop, User


def main():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin", enabled=True))
        products = [
            {"sku_code": "SKU001", "product_name": "测试产品A", "barcode": "BCODE001", "pack_qty_per_box": 3},
            {"sku_code": "SKU002", "product_name": "测试产品B", "barcode": "BCODE002", "pack_qty_per_box": 2},
        ]
        for p in products:
            if not db.query(Product).filter(Product.sku_code == p["sku_code"]).first():
                db.add(Product(**p))

        if not db.query(Shop).filter(Shop.shop_name == "广州天河店").first():
            db.add(Shop(customer_name="华南客户", shop_name="广州天河店", export_template_type="default"))
        db.commit()
        print("示例数据写入完成")
    finally:
        db.close()


if __name__ == "__main__":
    main()
