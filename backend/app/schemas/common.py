from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None

class PageData(BaseModel, Generic[T]):
    list: list[T]
    page: int
    pageSize: int
    total: int

def success_response(data: Any = None, message: str = "ok") -> dict:
    return {
        "code": 0,
        "message": message,
        "data": data
    }

def error_response(code: int = 5000, message: str = "操作失败") -> dict:
    return {
        "code": code,
        "message": message,
        "data": None
    }
