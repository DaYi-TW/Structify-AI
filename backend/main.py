# Structify AI — FastAPI 應用程式入口
# 負責初始化 app、掛載 CORS middleware 與 router

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.structure_data import router

# 從 .env 檔案載入環境變數（AZURE_OPENAI_* 等設定）
load_dotenv()

app = FastAPI(title="Structify AI")

# 允許所有來源的跨域請求，方便前端開發環境直接呼叫
# 正式環境應將 allow_origins 限縮為特定網域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 /api/structure-data 路由
app.include_router(router)


@app.get("/")
def root():
    # 健康檢查端點，確認服務是否正常啟動
    return {"message": "Structify AI Backend is running"}
