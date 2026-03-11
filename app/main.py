from fastapi import FastAPI

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.routers import auth, export, inventory, orders, packing_orders, products, shipment, shops

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(products.router, prefix=settings.api_prefix)
app.include_router(shops.router, prefix=settings.api_prefix)
app.include_router(inventory.router, prefix=settings.api_prefix)
app.include_router(orders.router, prefix=settings.api_prefix)
app.include_router(packing_orders.router, prefix=settings.api_prefix)
app.include_router(shipment.router, prefix=settings.api_prefix)
app.include_router(export.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"message": "LAN Inventory API running"}
