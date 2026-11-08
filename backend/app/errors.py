"""One error type so every failure has the same JSON shape:
{"error": {"code": "...", "message": "...", "details": [...]}}"""
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def _body(code: str, message: str, details: Any = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in err["loc"][1:]),
                "message": err["msg"].lower(),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body(
                "invalid_request",
                "Request body failed validation.",
                details,
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception(request: Request, exc: Exception):
        import logging
        logging.getLogger("irrigation").exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content=_body(
                "internal_error",
                str(exc) or "Internal server error",
            ),
        )
