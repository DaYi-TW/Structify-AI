# 定義所有 API 的 Pydantic request / response models
# Pydantic 在欄位賦值時自動執行 validator，讓資料驗證與型別轉換合併在同一層處理

from pydantic import BaseModel, field_validator
from typing import Literal


class RawItem(BaseModel):
    # 單筆非結構化輸入，content 為原始文字
    content: str


class StructureRequest(BaseModel):
    # API 請求 body
    # method 預設 "auto"：Rule-based 優先，失敗再 fallback 到 LLM
    method: Literal["rule", "llm", "auto"] = "auto"
    rawData: list[RawItem]


class ProductResult(BaseModel):
    # 單筆結構化產品資料
    # source 標記該筆由哪個 parser 產生，方便追蹤解析品質
    name: str
    category: str
    cost: float
    source: Literal["rule", "llm"]

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        # 空白名稱代表 rule parser 未能正確切割文字，應視為解析失敗
        if not v.strip():
            raise ValueError("Missing product name")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_not_unknown(cls, v: str) -> str:
        # "Unknown" 表示關鍵字比對未命中；在 auto mode 中這會觸發 LLM fallback
        if not v.strip() or v.strip() == "Unknown":
            raise ValueError("Unable to infer product category")
        return v.strip()

    @field_validator("cost")
    @classmethod
    def cost_positive(cls, v: float) -> float:
        # cost = 0 通常代表 regex 未在文字中找到數字，應視為解析失敗
        if v <= 0:
            raise ValueError("Product cost must be greater than 0")
        return v


class StructureResponse(BaseModel):
    # API 回應 body
    success: bool
    method: str
    data: list[ProductResult]
