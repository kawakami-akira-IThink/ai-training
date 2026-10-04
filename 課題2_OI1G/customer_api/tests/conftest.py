import sqlite3
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def log_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("LOG_ENCRYPTION_KEY", key)
    return key


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path


@pytest.fixture
def client(db_path, log_key, monkeypatch):
    monkeypatch.setenv("API_TOKEN", TOKEN)
    return TestClient(app, headers=HEADERS)


@pytest.fixture
def lock_db(client, db_path):
    """別接続で BEGIN IMMEDIATE を保持する（テーブルは先に API 呼び出しで作成しておく）。"""
    client.get("/customers", params={"name": "x"})
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.execute("BEGIN IMMEDIATE")
    yield conn
    if conn.in_transaction:
        conn.execute("ROLLBACK")
    conn.close()


def make(name="山田太郎", age=30, gender="male", job="営業"):
    return {"name": name, "age": age, "gender": gender, "job": job}
