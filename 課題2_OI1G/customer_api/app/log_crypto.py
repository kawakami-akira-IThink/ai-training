"""顧客情報を Fernet で暗号化して標準出力にログ出力する。"""
import json
import os

from cryptography.fernet import Fernet


def encrypt_customer(customer: dict) -> str:
    key = os.environ.get("LOG_ENCRYPTION_KEY")
    if not key:
        # 鍵がなくても平文は出さない
        return "<NO_KEY>"
    data = json.dumps(customer, ensure_ascii=False).encode()
    return Fernet(key.encode()).encrypt(data).decode()


def log_event(op: str, status: int, customer_id: int | None = None,
              customer: dict | None = None, code: str | None = None) -> None:
    parts = [f"op={op}", f"status={status}"]
    if customer_id is not None:
        parts.append(f"id={customer_id}")
    if code:
        parts.append(f"code={code}")
    if customer is not None:
        parts.append(f"customer_enc={encrypt_customer(customer)}")
    print(" ".join(parts), flush=True)
