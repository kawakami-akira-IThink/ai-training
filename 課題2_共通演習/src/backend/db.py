"""SQLite 接続・スキーマ・Item 変換（計画書 3章）。"""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get(
    "INVENTORY_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    name_key    TEXT    NOT NULL UNIQUE,
    quantity    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""

ITEM_COLUMNS = "id, name, quantity, created_at, updated_at"


def connect() -> sqlite3.Connection:
    """リクエスト単位の接続（呼び出し側で close する）。"""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db() -> None:
    """起動時にテーブルを作成する。"""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def now_utc() -> str:
    """ISO 8601 UTC 秒精度・末尾 Z。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_name(name: str) -> str:
    """同一名称判定用キー（PBI-2 AC4）。NFKC はかけない。"""
    return name.casefold()


def row_to_item(row: sqlite3.Row) -> dict:
    """Item 変換。quantity は負値のまま返す（PBI-1 AC2）。name_key は含めない。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "quantity": row["quantity"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
