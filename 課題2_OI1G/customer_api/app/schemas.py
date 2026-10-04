"""入力モデルとバリデーション。"""
from typing import Literal

from pydantic import BaseModel, Field


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    age: int = Field(ge=0, le=1000)
    gender: Literal["male", "female"]
    job: str = Field(default="", max_length=256)
