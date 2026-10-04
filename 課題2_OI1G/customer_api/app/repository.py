"""顧客の CRUD SQL。"""
import sqlite3

from app.schemas import CustomerIn

COLUMNS = ("name", "age", "gender", "job")


def exists(conn: sqlite3.Connection, customer_id: int) -> bool:
    return conn.execute("SELECT 1 FROM customers WHERE id = ?", (customer_id,)).fetchone() is not None


def has_duplicate(conn: sqlite3.Connection, c: CustomerIn, exclude_id: int | None = None) -> bool:
    sql = "SELECT 1 FROM customers WHERE name = ? AND age = ? AND gender = ? AND job = ?"
    params: list = [c.name, c.age, c.gender, c.job]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return conn.execute(sql, params).fetchone() is not None


def insert(conn: sqlite3.Connection, c: CustomerIn) -> int:
    cur = conn.execute(
        "INSERT INTO customers (name, age, gender, job) VALUES (?, ?, ?, ?)",
        (c.name, c.age, c.gender, c.job),
    )
    return cur.lastrowid


def update(conn: sqlite3.Connection, customer_id: int, c: CustomerIn) -> None:
    conn.execute(
        "UPDATE customers SET name = ?, age = ?, gender = ?, job = ? WHERE id = ?",
        (c.name, c.age, c.gender, c.job, customer_id),
    )


def delete(conn: sqlite3.Connection, customer_id: int) -> None:
    conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))


def search(conn: sqlite3.Connection, conditions: dict) -> list[dict]:
    # 列名は固定のタプルからのみ組み立て、値はプレースホルダで渡す
    keys = [k for k in COLUMNS if conditions.get(k) is not None]
    where = " AND ".join(f"{k} = ?" for k in keys)
    rows = conn.execute(
        f"SELECT id, name, age, gender, job FROM customers WHERE {where} ORDER BY id",
        [conditions[k] for k in keys],
    ).fetchall()
    return [dict(r) for r in rows]
