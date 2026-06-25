# 關鍵字比對分類工具
# 透過預定義關鍵字列表從文字中推論產品分類
# 若無任何關鍵字命中，回傳 "Unknown"，由上層決定是否 fallback 到 LLM


def infer_category(text: str) -> str:
    """
    從文字中推論產品分類。

    Args:
        text: 產品描述文字（name 或原始 content 均可）

    Returns:
        分類字串；無法判斷時回傳 "Unknown"
    """
    t = text.lower()  # 統一轉小寫，避免大小寫造成匹配失敗

    if any(k in t for k in ("shoe", "sneaker", "boot", "sandal")):
        return "Footwear"

    if any(k in t for k in ("shirt", "jacket", "pants", "coat")):
        return "Apparel"

    if any(k in t for k in ("bag", "backpack", "luggage")):
        return "Bag"

    # 無關鍵字命中 → 回傳 Unknown，觸發 auto mode 的 LLM fallback
    return "Unknown"
