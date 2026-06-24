"""业务异常与错误码

1. ErrorCode：错误码枚举，按模块分段
2. BusinessException：业务异常，Service 层抛出表示预期内的业务错误
3. register_exception_handlers()：注册全局异常处理器，返回统一 JSON 格式
"""

import logging
from enum import IntEnum

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.result import Result

log = logging.getLogger(__name__)


class ErrorCode(IntEnum):
    """错误码枚举

    按模块分段：
    - 4xx：通用请求错误
    - 3xxx：面试模块
    - 6xxx：知识库模块
    - 7xxx：AI 服务模块
    """

    # ---- 通用 ----
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

    # ---- 面试模块 (3xxx) ----
    INTERVIEW_SESSION_NOT_FOUND = 3001
    INTERVIEW_INVALID_ANSWER = 3002
    INTERVIEW_EVALUATION_FAILED = 3003
    INTERVIEW_GRAPH_ERROR = 3004

    # ---- 知识库模块 (6xxx) ----
    KNOWLEDGE_BASE_NOT_FOUND = 6001
    KNOWLEDGE_BASE_VECTORIZE_FAILED = 6002

    # ---- AI 服务模块 (7xxx) ----
    AI_SERVICE_TIMEOUT = 7002
    AI_SERVICE_ERROR = 7003


class BusinessException(Exception):
    """业务异常

    用法：
        raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND, "会话不存在: abc123")
    """

    def __init__(self, code: ErrorCode, message: str = ""):
        self.code = code
        self.message = message or code.name
        super().__init__(self.message)


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器

    所有异常返回 HTTP 200，错误信息通过响应体 code 字段传递。
    前端统一通过 code !== 0 判断成功/失败。
    """

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        log.warning("业务异常: %s %s -> [%s] %s",
                     request.method, request.url.path,
                     exc.code.name, exc.message)
        return JSONResponse(
            status_code=200,
            content=Result.error(exc.code.value, exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        log.error("系统异常: %s %s -> %s: %s",
                   request.method, request.url.path,
                   type(exc).__name__, exc,
                   exc_info=True)
        return JSONResponse(
            status_code=200,
            content=Result.error(ErrorCode.INTERNAL_ERROR, str(exc)).model_dump(),
        )
