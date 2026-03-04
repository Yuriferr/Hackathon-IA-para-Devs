import os
from http.client import HTTPException
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.analyze_service import AnalyzeService


router = APIRouter()

@router.post("/")
async def analyze(file: UploadFile = File(...), metamodel: UploadFile = File(None)):
    temp_filename = None
    try:
        # 0. Processar Metamodelo (se houver)
        metamodel_content = None
        # DEBUG import pdb; pdb.set_trace()
        try:
            if metamodel:
                content = await metamodel.read()
                metamodel_content = content.decode("utf-8")
                print(" > Metamodelo recebido e lido.")
        except Exception as e:
            print(f" > Erro ao ler metamodelo: {e}")
            # Segue sem metamodelo se der erro na leitura

        # # 1. Salvar arquivo temporário
        # suffix = os.path.splitext(file.filename)[1]
        # with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        #     shutil.copyfileobj(file.file, tmp)
        #     temp_filename = tmp.name
        
        # # 2. Configuração
        # base_dir = os.path.dirname(os.path.abspath(__file__))
        # model_path = os.path.join(base_dir, "Treinamentos", "yolov8n_icons", "weights", "best.pt")
        # import pdb; pdb.set_trace()
        # if not os.path.exists(model_path):
        #     raise HTTPException(status_code=500, detail="Modelo YOLO não encontrado.")

        # # 3. Execução Otimizada
        # # A: Detectar ícones localmente
        # icons = extract_icons(temp_filename, model_path)
        
        # # B: Análise completa (OCR + STRIDE + COMPLIANCE)
        # report = generate_stride_analysis(temp_filename, icons, metamodel_content)
        
        service = AnalyzeService()
        report = service.analyze(file, metamodel_content)

        return JSONResponse(content={"report": report})
        
    except Exception as e:
        print(f"Erro: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
        
    # finally:
    #     if temp_filename and os.path.exists(temp_filename):
    #         try:
    #             os.remove(temp_filename)
    #         except Exception:
    #             pass