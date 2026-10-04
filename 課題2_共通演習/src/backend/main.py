"""在庫管理 API（FastAPI + SQLite）。API-1〜4 と入力検証。"""
import json
import logging
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

import db
from errors import AppError, build_error_response, register_exception_handlers
from i18n import resolve_lang

logger = logging.getLogger("inventory")

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
NAME_MAX_LENGTH = 100


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()  # 起動時にテーブル作成
    yield


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


# 登録順に注意: http ミドルウェアを先、CORS を後に登録（後のものが外側）。
# これで E099 応答にも CORS ヘッダーが付く（計画書 4.2）。
@app.middleware("http")
async def lang_and_error_middleware(request: Request, call_next):
    """言語を1回だけ決定し、全レスポンスへ Content-Language を付与。想定外例外は E099（共通 AC5）。"""
    lang = resolve_lang(request.headers.get("accept-language"))
    request.state.lang = lang
    try:
        response = await call_next(request)
    except Exception as exc:  # sqlite3.Error を含む想定外例外。内部情報は応答に出さない
        logger.error("unhandled exception", exc_info=exc)
        response = build_error_response("E099", {}, lang)
    response.headers["Content-Language"] = lang
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept-Language"],
    expose_headers=["Content-Language", "Location"],
)


# ---------------- 入力検証（検証順: E001 -> E007 -> Body 各項目） ----------------

def _is_int(value) -> bool:
    """JSON の整数のみ True。bool・float・str は False。"""
    return type(value) is int


def _in_int64(value: int) -> bool:
    return INT64_MIN <= value <= INT64_MAX


async def read_json_object(request: Request) -> dict:
    """E001: Content-Type・JSON 構文・トップレベル object を検証（API-2/4 共通）。"""
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != "application/json":
        raise AppError("E001")
    raw = await request.body()
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise AppError("E001")
    if not isinstance(body, dict):
        raise AppError("E001")
    return body


def parse_item_id(raw: str) -> int:
    """E007: ASCII 数字のみ・1 以上・64bit 範囲内（API-3/4）。"""
    if not (raw.isascii() and raw.isdigit()):
        raise AppError("E007", {"field": "id"})
    value = int(raw)
    if value < 1 or value > INT64_MAX:
        raise AppError("E007", {"field": "id"})
    return value


def validate_name(body: dict) -> str:
    """E002/E003: 前後空白除去後 1〜100 文字（PBI-2 AC5, AC6）。strip 後の名称を返す。"""
    name = body.get("name")
    if not isinstance(name, str):
        raise AppError("E002", {"field": "name"})
    name = name.strip()
    if name == "":
        raise AppError("E002", {"field": "name"})
    if len(name) > NAME_MAX_LENGTH:
        raise AppError("E003", {"field": "name", "max_length": NAME_MAX_LENGTH})
    return name


def validate_initial_quantity(body: dict) -> int:
    """E004: 省略時 0。0 以上の整数のみ（PBI-2 AC2, AC7）。"""
    if "quantity" not in body:
        return 0
    q = body["quantity"]
    if not _is_int(q) or q < 0 or not _in_int64(q):
        raise AppError("E004", {"field": "quantity"})
    return q


def validate_delta(body: dict) -> int:
    """E005: 0 以外の整数（PBI-4 AC5）。"""
    d = body.get("delta")
    if not _is_int(d) or d == 0 or not _in_int64(d):
        raise AppError("E005", {"field": "delta"})
    return d


def validate_expected(body: dict) -> int:
    """E006: 整数（負も可）（PBI-4 AC6）。範囲外も E006。"""
    e = body.get("expected_quantity")
    if not _is_int(e) or not _in_int64(e):
        raise AppError("E006", {"field": "expected_quantity"})
    return e


# ---------------- DB 処理（同期。スレッドプールで実行） ----------------

def _select_all() -> list[dict]:
    conn = db.connect()
    try:
        rows = conn.execute(f"SELECT {db.ITEM_COLUMNS} FROM items ORDER BY id ASC").fetchall()
        return [db.row_to_item(r) for r in rows]
    finally:
        conn.close()


def _insert(name: str, quantity: int) -> dict:
    conn = db.connect()
    try:
        now = db.now_utc()
        try:
            cur = conn.execute(
                "INSERT INTO items(name, name_key, quantity, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, db.normalize_name(name), quantity, now, now),
            )
        except sqlite3.IntegrityError:
            raise AppError("E009", {"field": "name"})  # name_key の UNIQUE 違反（PBI-2 AC3, AC4）
        conn.commit()
        row = conn.execute(
            f"SELECT {db.ITEM_COLUMNS} FROM items WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return db.row_to_item(row)
    finally:
        conn.close()


def _delete(item_id: int) -> None:
    conn = db.connect()
    try:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))  # 在庫は条件にしない
        conn.commit()
        if cur.rowcount == 0:
            raise AppError("E008", {"id": item_id})
    finally:
        conn.close()


def _adjust(item_id: int, delta: int, expected: int) -> dict:
    conn = db.connect()
    try:
        # 条件付き単一 UPDATE（楽観ロック）。判定と更新を分離しない
        cur = conn.execute(
            "UPDATE items SET quantity = quantity + :delta, updated_at = :now "
            "WHERE id = :id AND quantity = :expected",
            {"delta": delta, "now": db.now_utc(), "id": item_id, "expected": expected},
        )
        conn.commit()
        row = conn.execute(
            f"SELECT {db.ITEM_COLUMNS} FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        if cur.rowcount == 1:
            return db.row_to_item(row)
        if row is None:
            raise AppError("E008", {"id": item_id})  # PBI-4 AC7
        raise AppError("E010", {"item": db.row_to_item(row)})  # PBI-4 AC4
    finally:
        conn.close()


# ---------------- エンドポイント ----------------

@app.get("/api/items")
async def list_items():
    """API-1: 一覧（ID 昇順、0 件は []）。PBI-1 AC1-4。"""
    items = await run_in_threadpool(_select_all)
    return {"items": items}


@app.post("/api/items")
async def create_item(request: Request):
    """API-2: 品目追加。PBI-2 AC1-7。"""
    body = await read_json_object(request)
    name = validate_name(body)
    quantity = validate_initial_quantity(body)
    item = await run_in_threadpool(_insert, name, quantity)
    return JSONResponse(
        status_code=201, content=item, headers={"Location": f"/api/items/{item['id']}"}
    )


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str):
    """API-3: 品目削除。PBI-3 AC1, AC3, AC4。"""
    iid = parse_item_id(item_id)
    await run_in_threadpool(_delete, iid)
    return Response(status_code=204)


@app.post("/api/items/{item_id}/adjust")
async def adjust_item(item_id: str, request: Request):
    """API-4: 在庫増減（楽観ロック）。PBI-4 AC1-7。"""
    body = await read_json_object(request)  # E001
    iid = parse_item_id(item_id)  # E007
    delta = validate_delta(body)  # E005
    expected = validate_expected(body)  # E006
    if not _in_int64(expected + delta):  # 増減後の範囲外は E005（API仕様書 1.9）
        raise AppError("E005", {"field": "delta"})
    return await run_in_threadpool(_adjust, iid, delta, expected)
