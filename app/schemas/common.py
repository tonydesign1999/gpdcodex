from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool
    message: str = "ok"
    data: Any | None = None
    error_code: str | None = None
