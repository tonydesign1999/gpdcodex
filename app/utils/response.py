from fastapi.encoders import jsonable_encoder

from app.schemas.common import APIResponse


def ok(data=None, message: str = "ok") -> APIResponse:
    return APIResponse(success=True, message=message, data=jsonable_encoder(data))


def fail(message: str, error_code: str = "BUSINESS_ERROR") -> APIResponse:
    return APIResponse(success=False, message=message, error_code=error_code)
