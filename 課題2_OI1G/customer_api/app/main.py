"""FastAPI アプリ本体・ルーティング。"""
from typing import Literal

from fastapi import Depends, FastAPI, Response

from app import db, log_crypto, repository
from app.auth import require_auth
from app.errors import duplicate, not_found, register_handlers
from app.schemas import CustomerIn

app = FastAPI(title="顧客マスタ API", dependencies=[Depends(require_auth)])
register_handlers(app)


@app.post("/customers", status_code=201)
def create_customer(body: CustomerIn):
    with db.write_tx() as conn:
        if repository.has_duplicate(conn, body):
            raise duplicate()
        new_id = repository.insert(conn, body)
    log_crypto.log_event("create", 201, customer_id=new_id, customer=body.model_dump())
    return {"id": new_id}


@app.put("/customers/{customer_id}", status_code=204)
def update_customer(customer_id: int, body: CustomerIn):
    with db.write_tx() as conn:
        if not repository.exists(conn, customer_id):
            raise not_found()
        if repository.has_duplicate(conn, body, exclude_id=customer_id):
            raise duplicate()
        repository.update(conn, customer_id, body)
    log_crypto.log_event("update", 204, customer_id=customer_id, customer=body.model_dump())
    return Response(status_code=204)


@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int):
    with db.write_tx() as conn:
        if not repository.exists(conn, customer_id):
            raise not_found()
        repository.delete(conn, customer_id)
    log_crypto.log_event("delete", 204, customer_id=customer_id)
    return Response(status_code=204)


@app.get("/customers")
def search_customers(name: str | None = None, age: int | None = None,
                     gender: Literal["male", "female"] | None = None, job: str | None = None):
    conditions = {"name": name, "age": age, "gender": gender, "job": job}
    if all(v is None for v in conditions.values()):
        return []  # 条件なしは DB にアクセスせず 0件
    with db.read_conn() as conn:
        result = repository.search(conn, conditions)
    log_crypto.log_event("search", 200)
    return result
