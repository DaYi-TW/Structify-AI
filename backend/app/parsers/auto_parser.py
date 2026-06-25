# Auto Parser — Rule-based 優先，失敗自動 fallback 到 LLM
# 這是推薦的實務模式：簡單資料不浪費 LLM token，複雜資料仍能正確處理
#
# Fallback 觸發條件（由 Pydantic ProductResult validator 判斷）：
#   - name 為空      → rule parser 未能從文字切出產品名稱
#   - category 為 Unknown → 關鍵字比對未命中任何分類
#   - cost <= 0      → regex 未找到費用數字

from pydantic import ValidationError
from app.models.product import ProductResult, RawItem
from app.parsers.rule_parser import extract_name, extract_cost, split_into_segments
from app.parsers.llm_parser import parse_by_llm
from app.utils.category_util import infer_category


async def parse_auto(items: list[RawItem]) -> list[ProductResult]:
    """
    對每筆 RawItem 先執行 Rule-based 解析；
    Pydantic 驗證失敗時，將該 segment 改送 LLM 重新解析。

    流程（每個 segment 獨立判斷，不因一個失敗影響其他）：
        segment → Rule Parser → Pydantic 驗證
                                    ├─ 通過 → source: "rule"
                                    └─ 失敗 → LLM Parser → source: "llm"
    """
    results = []
    for item in items:
        # 先拆分多產品 segment，再對每個 segment 獨立嘗試 rule → LLM
        for segment in split_into_segments(item.content):
            try:
                # 嘗試 Rule-based 解析，Pydantic 驗證不通過會拋出 ValidationError
                product = ProductResult(
                    name=extract_name(segment),
                    category=infer_category(segment),
                    cost=extract_cost(segment),
                    source="rule",
                )
                results.append(product)
            except (ValidationError, ValueError):
                # Rule 解析失敗，fallback 到 LLM
                # 將 segment 包成 RawItem 送給 LLM，維持介面一致
                llm_results = await parse_by_llm([RawItem(content=segment)])
                results.extend(llm_results)
    return results
