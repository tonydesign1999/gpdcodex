from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "LAN Inventory & Shipment Management"
    database_url: str = "sqlite:///./data/inventory.db"
    api_prefix: str = "/api"
    token_expire_minutes: int = 60 * 12
    data_dir: Path = Path("data")
    export_dir: Path = Path("data/exports")
    template_dir: Path = Path("data/templates")


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.export_dir.mkdir(parents=True, exist_ok=True)
settings.template_dir.mkdir(parents=True, exist_ok=True)
