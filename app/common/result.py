"""统一响应封装

所有 API 接口返回统一 JSON 格式：
    成功: {"code": 0, "message": "success", "data": {...}}
    失败: {"code": 3001, "message": "面试会话不存在", "data": null}
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """统一响应体

    code=0 表示成功，非零值为业务错误码（对应 ErrorCode 枚举）。
    """

    code: int = 0
    message: str = "success"
    data: T | None = None

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "Result":
        """成功响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "Result":
        """失败响应"""
        return cls(code=code, message=message, data=None)
