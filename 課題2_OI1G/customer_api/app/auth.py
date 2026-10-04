"""Bearer 固定値チェック。

OAuth 認証が実装済みであると仮定した場合のスタブ。正しい認証方式ではなく仮置きであり、
トークンの発行・検証は扱わない。
"""
import hmac
import os

from fastapi import Header

from app.errors import unauthorized


def require_auth(authorization: str | None = Header(default=None)) -> None:
    expected = os.environ.get("API_TOKEN")
    # API_TOKEN 未設定のときは全拒否（安全側）
    if not expected or not authorization:
        raise unauthorized()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(
        token.encode(), expected.encode()
    ):
        raise unauthorized()
