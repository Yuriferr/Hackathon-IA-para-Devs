from app.services.analyze_service import AnalyzeService
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/")
async def analyze(file: UploadFile = File(...), metamodel: UploadFile = File(None)):
    try:        
        service = AnalyzeService()
        report = await service.analyze(file, metamodel)

        return JSONResponse(content={"report": report})        
    except Exception as e:
        print(f"Erro: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})