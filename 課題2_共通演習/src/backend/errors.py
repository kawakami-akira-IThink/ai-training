"""エラー辞書・共通エラーレスポンス・例外ハンドラ（定義書 3.1、API仕様書 1.5 / 1.7）。"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from i18n import get_message, resolve_lang

logger = logging.getLogger("inventory")

# コード -> (HTTPステータス, メッセージキー)（定義書 3.1）
ERRORS: dict[str, tuple[int, str]] = {
    "E001": (400, "err.invalid_request"),
    "E002": (400, "err.item_name_required"),
    "E003": (400, "err.item_name_too_long"),
    "E004": (400, "err.initial_quantity_invalid"),
    "E005": (400, "err.delta_invalid"),
    "E006": (400, "err.expected_quantity_invalid"),
    "E007": (400, "err.item_id_invalid"),
    "E008": (404, "err.item_not_found"),
    "E009": (409, "err.item_name_duplicate"),
    "E010": (409, "err.stock_conflict"),
    "E099": (500, "err.internal_server_error"),
}


class AppError(Exception):
    """業務・検証エラー。ハンドラが共通形式に変換する。"""

    def __init__(self, code: str, details: dict | None = None):
        super().__init__(code)
        self.code = code
        self.details = details or {}


def build_error_response(code: str, details: dict | None, lang: str) -> JSONResponse:
    """共通エラー形式 {"error": {code, message, details}} を作る（共通 AC5）。"""
    status, key = ERRORS[code]
    details = details or {}
    body = {
        "error": {
            "code": code,
            "message": get_message(lang, key, details),
            "details": details,
        }
    }
    return JSONResponse(status_code=status, content=body, headers={"Content-Language": lang})


def _lang_of(request: Request) -> str:
    lang = getattr(request.state, "lang", None)
    return lang or resolve_lang(request.headers.get("accept-language"))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return build_error_response(exc.code, exc.details, _lang_of(request))

    # 422 を使わず 400 に統一する安全網（API仕様書 1.7）
    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        errs = exc.errors()
        if errs and errs[0].get("loc") and errs[0]["loc"][0] == "path":
            return build_error_response("E007", {"field": "id"}, _lang_of(request))
        return build_error_response("E001", {}, _lang_of(request))

    # 想定外の例外は E099。トレースはログのみ（定義書 4.2）
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.error("unhandled exception", exc_info=exc)
        return build_error_response("E099", {}, _lang_of(request))
