# Rule-based Parser
# 使用正規表達式從固定格式文字中抽取產品資訊
# 不依賴外部 API，速度快、成本低，但只適合格式規律的輸入

import re
from app.models.product import ProductResult, RawItem
from app.utils.category_util import infer_category


def extract_cost(content: str) -> float:
    """
    用 Regex 抽取文字中的費用數字。
    支援 "cost 25"、"cost: 25"、"cost25" 等多種寫法。
    未找到時回傳 0.0，後續 Pydantic 驗證會將其視為解析失敗。
    """
    match = re.search(r"cost\s*:?\s*(\d+(\.\d+)?)", content, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0


def extract_name(content: str) -> str:
    """
    移除 cost 描述後取得產品名稱。

    處理步驟：
      1. 用 Regex 移除 "cost XX" 片段
      2. 壓縮連續空白為單一空格
      3. 移除尾端殘留的標點與空白（如 ","、"."、"。"）
    """
    # 移除整段 cost 描述，包含數字
    name = re.sub(r"cost\s*:?\s*\d+(\.\d+)?", "", content, flags=re.IGNORECASE)
    # 壓縮多餘空白
    name = re.sub(r"\s+", " ", name).strip()
    # 移除移除 cost 後尾端殘留的逗號、句號等標點
    return re.sub(r"[,.。\s]+$", "", name)


def split_into_segments(content: str) -> list[str]:
    """
    偵測單筆 content 是否包含多個產品，若是則拆分成多個 segment。

    判斷方式：計算文字中 "cost" 出現次數；
    出現超過一次代表有多個產品，依產品邊界拆分。

    切割邏輯：
      用 (?<=\\d)[,.]\\s+ 切割 ── 「緊接在數字後的逗號或句號 + 空白」
      逗號/句號若是產品分隔符，必定出現在 cost 數字後面；
      若出現在數字前（如 "outdoor shoe, cost 25" 的逗號），不會被切到。

      支援格式：
        "...cost 25. Running shoe..."  ← 句號分隔
        "...cost 25, Running shoe..."  ← 逗號分隔

    範例：
      "Waterproof shoe, cost 25. Running shoe, cost 20."
      → ["Waterproof shoe, cost 25", "Running shoe, cost 20."]

      "Waterproof shoe, cost 25, Running shoe, cost 20"
      → ["Waterproof shoe, cost 25", "Running shoe, cost 20"]
    """
    cost_count = len(re.findall(r"cost\s*:?\s*\d+", content, re.IGNORECASE))
    if cost_count <= 1:
        # 只有一個產品，直接回傳原文不拆分
        return [content]

    # (?<=\d) lookbehind 確保只切「數字後面」的逗號/句號，避免切到名稱裡的逗號
    parts = re.split(r"(?<=\d)[,.]\s+", content)
    return [p.strip() for p in parts if p.strip()]


def parse_by_rule(items: list[RawItem]) -> list[ProductResult]:
    """
    對每筆 RawItem 執行 Rule-based 解析。
    先拆分多產品 segment，再對每個 segment 抽取 name / category / cost。
    Pydantic 驗證失敗（如 cost=0 或 category=Unknown）會直接拋出例外。
    """
    results = []
    for item in items:
        # 先嘗試拆分出多個產品 segment
        for segment in split_into_segments(item.content):
            results.append(
                ProductResult(
                    name=extract_name(segment),
                    category=infer_category(segment),
                    cost=extract_cost(segment),
                    source="rule",
                )
            )
    return results
