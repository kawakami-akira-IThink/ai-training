"""FastAPI アプリ本体・ルーティング。"""
from typing import Annotated

from fastapi import Depends, FastAPI, Path, Response

from app import db, log_crypto, repository
from app.auth import require_auth
from app.errors import duplicate, not_found, register_handlers
from app.schemas import CustomerIn, SearchIn

# /docs 等は認証の依存関係がかからないため無効化する
app = FastAPI(title="顧客マスタ API", dependencies=[Depends(require_auth)],
              docs_url=None, redoc_url=None, openapi_url=None)
register_handlers(app)

# SQLite の整数上限を超える id は 500 になるため範囲を制限する
CustomerId = Annotated[int, Path(ge=1, le=2**63 - 1)]


@app.post("/customers", status_code=201)
def create_customer(body: CustomerIn):
    with db.write_tx() as conn:
        if repository.has_duplicate(conn, body):
            raise duplicate()
        new_id = repository.insert(conn, body)
    log_crypto.log_event("create", 201, customer_id=new_id, customer=body.model_dump())
    return {"id": new_id}


@app.put("/customers/{customer_id}", status_code=204)
def update_customer(customer_id: CustomerId, body: CustomerIn):
    with db.write_tx() as conn:
        if not repository.exists(conn, customer_id):
            raise not_found()
        if repository.has_duplicate(conn, body, exclude_id=customer_id):
            raise duplicate()
        repository.update(conn, customer_id, body)
    log_crypto.log_event("update", 204, customer_id=customer_id, customer=body.model_dump())
    return Response(status_code=204)


@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: CustomerId):
    with db.write_tx() as conn:
        if not repository.exists(conn, customer_id):
            raise not_found()
        repository.delete(conn, customer_id)
    log_crypto.log_event("delete", 204, customer_id=customer_id)
    return Response(status_code=204)


@app.post("/customers/search")
def search_customers(body: SearchIn):
    # 条件は body で受ける（URL に載せるとアクセスログに平文で出るため）
    conditions = body.model_dump()
    with db.read_conn() as conn:
        result = repository.search(conn, conditions)
    log_crypto.log_event("search", 200)
    return result
