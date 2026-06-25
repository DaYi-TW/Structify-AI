# LLM Parser — Azure OpenAI Structured Output
# 適合格式不固定、自然語言描述、或 Rule-based 無法處理的輸入
# 透過 response_format: json_object 強制模型輸出合法 JSON，避免 markdown 包裝

import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from app.models.product import ProductResult, RawItem
from app.utils.category_util import infer_category

# 確保在 Docker 環境外直接執行時也能讀到 .env
load_dotenv()

# module-level 初始化 client，避免每次請求重新建立連線
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
)

# 從環境變數讀取 deployment 名稱，方便在不同環境切換模型版本
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

# System Prompt 要求模型回傳包含 products 陣列的 JSON
# 使用 "products" 作為頂層 key，確保 response_format: json_object 模式下結構一致
SYSTEM_PROMPT = """You are a data extraction assistant.
Extract ALL products from the user's text. There may be one or multiple products in a single input.

Return ONLY valid JSON in this format:
{
  "products": [
    {
      "name": "<product name>",
      "category": "<Footwear | Apparel | Bag | Other>",
      "cost": <number>
    }
  ]
}
Rules:
- Extract every distinct product mentioned
- name: the product name only, no cost description
- category: infer from the product type
- cost: extract as a number; 0 if not mentioned"""


async def parse_by_llm(items: list[RawItem]) -> list[ProductResult]:
    """
    對每筆 RawItem 呼叫 Azure OpenAI 進行結構化解析。
    若 LLM 回傳的 category 為 Unknown，補跑關鍵字比對作為後備。
    """
    results = []
    for item in items:
        extracted_list = await _call_azure_openai(item.content)
        for extracted in extracted_list:
            category = extracted.get("category", "Unknown")
            # LLM 有時對邊緣類別回傳 "Other" 或 "Unknown"，改用關鍵字比對補救
            if not category or category == "Unknown":
                category = infer_category(extracted.get("name", ""))
            results.append(
                ProductResult(
                    name=extracted.get("name", ""),
                    category=category,
                    cost=float(extracted.get("cost", 0)),
                    source="llm",
                )
            )
    return results


async def _call_azure_openai(content: str) -> list[dict]:
    """
    呼叫 Azure OpenAI Chat Completions API 並解析回應。

    response_format: json_object 確保模型輸出純 JSON，不包含 markdown 或說明文字。
    容錯處理：若模型未依格式回傳 products 陣列，將整個 dict 包成單元素列表。
    """
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        response_format={"type": "json_object"},  # 強制輸出合法 JSON
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    # 若模型直接回傳單個 product 物件而非 products 陣列，包裝成列表確保後續處理一致
    return data.get("products", [data]) if isinstance(data, dict) else data
