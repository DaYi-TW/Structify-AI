# Structure Data Service — 解析模式的分派層
# 根據 method 參數將請求路由到對應的 parser，隔離路由邏輯與解析邏輯

from app.models.product import ProductResult, RawItem
from app.parsers.rule_parser import parse_by_rule
from app.parsers.llm_parser import parse_by_llm
from app.parsers.auto_parser import parse_auto


async def structure_data(raw_data: list[RawItem], method: str) -> list[ProductResult]:
    """
    依照指定的解析模式處理非結構化資料，回傳結構化產品列表。

    Args:
        raw_data: 原始文字輸入列表
        method:   "rule" | "llm" | "auto"

    Returns:
        結構化後的 ProductResult 列表
    """
    if method == "rule":
        # Rule-based：純 Regex，不呼叫外部 API，速度最快
        return parse_by_rule(raw_data)

    if method == "llm":
        # LLM：呼叫 Azure OpenAI，可處理自然語言，但有延遲與 token 成本
        return await parse_by_llm(raw_data)

    if method == "auto":
        # Auto：Rule 優先，Pydantic 驗證失敗才 fallback 到 LLM（推薦模式）
        return await parse_auto(raw_data)

    raise ValueError(f"Unknown method: {method}")
