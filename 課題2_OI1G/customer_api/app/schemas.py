"""入力モデルとバリデーション。"""
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _clean(v: str) -> str:
    """前後の空白を除去し、制御文字（Unicode カテゴリ Cc。改行・タブ含む）を拒否する。"""
    v = v.strip()
    if any(unicodedata.category(ch) == "Cc" for ch in v):
        raise ValueError("制御文字は使えません")
    return v


class _Normalized(BaseModel):
    # strip は max_length 等の検証より前に行いたいので mode="before" で文字列のときだけ処理する
    @field_validator("name", "job", mode="before", check_fields=False)
    @classmethod
    def _normalize(cls, v):
        return _clean(v) if isinstance(v, str) else v


class CustomerIn(_Normalized):
    name: str = Field(min_length=1, max_length=256)
    age: int = Field(ge=0, le=1000)
    gender: Literal["male", "female"]
    job: str = Field(default="", max_length=256)


class SearchIn(_Normalized):
    name: str = Field(min_length=1, max_length=256)  # 必須（全件取得の防止）
    age: int | None = Field(default=None, ge=0, le=1000)
    gender: Literal["male", "female"] | None = None
    job: str | None = Field(default=None, max_length=256)
