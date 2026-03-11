from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    token: str
    username: str
    role: str


class LogoutRequest(BaseModel):
    token: str
