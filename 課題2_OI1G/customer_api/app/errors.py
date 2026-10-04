"""エラーコード定義と例外ハンドラ（{"code", "message"} 形式）。"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import log_crypto


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


def validation_error(message: str = "入力値が不正です") -> AppError:
    return AppError(400, "VALIDATION_ERROR", message)


def unauthorized() -> AppError:
    return AppError(401, "UNAUTHORIZED", "認証トークンがない、または不正です")


def not_found() -> AppError:
    return AppError(404, "NOT_FOUND", "指定した id の顧客が存在しません")


def duplicate() -> AppError:
    return AppError(409, "DUPLICATE", "全項目が一致する顧客がすでに存在します")


def locked() -> AppError:
    return AppError(409, "LOCKED", "別の処理で変更・削除中です")


def _respond(request: Request, status: int, code: str, message: str) -> JSONResponse:
    log_crypto.log_event(f"{request.method} {request.url.path}", status, code=code)
    return JSONResponse(status_code=status, content={"code": code, "message": message})


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return _respond(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        # exc の詳細には入力値（顧客情報）が含まれるため、ログにもレスポンスにも出さない
        e = validation_error()
        return _respond(request, e.status, e.code, e.message)
