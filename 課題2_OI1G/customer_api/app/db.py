"""SQLite 接続・テーブル作成・ロック付きトランザクション。"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.errors import duplicate, locked

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "customers.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    job TEXT NOT NULL DEFAULT '',
    UNIQUE (name, age, gender, job)
)
"""


def connect() -> sqlite3.Connection:
    path = os.environ.get("DB_PATH") or str(DEFAULT_DB_PATH)
    # timeout=0: ロック待ちをせず即エラー。isolation_level=None: トランザクションは自分で管理
    conn = sqlite3.connect(path, timeout=0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


@contextmanager
def read_conn():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def write_tx():
    """BEGIN IMMEDIATE で書き込みロックを取る。取れなければ 409 LOCKED。"""
    conn = connect()
    try:
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                raise locked() from None
            raise
        try:
            yield conn
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            # UNIQUE 制約違反（保険）。例外メッセージに顧客情報が入りうるので握りつぶして変換する
            conn.execute("ROLLBACK")
            raise duplicate() from None
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
