# POST /api/structure-data 路由
# 接收前端請求，呼叫 service 層取得結構化結果後回傳

from fastapi import APIRouter, HTTPException
from app.models.product import StructureRequest, StructureResponse
from app.services.structure_data_service import structure_data

router = APIRouter()


@router.post("/api/structure-data", response_model=StructureResponse)
async def structure_data_endpoint(request: StructureRequest):
    try:
        data = await structure_data(request.rawData, request.method)
        return StructureResponse(success=True, method=request.method, data=data)
    except Exception as e:
        # 將內部錯誤轉為 HTTP 500，避免 stack trace 直接暴露給前端
        raise HTTPException(status_code=500, detail=str(e))
