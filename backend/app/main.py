from dotenv import load_dotenv
from pathlib import Path
from app.api.routes import router as api_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Carrega variáveis de ambiente (.env)
load_dotenv()

app = FastAPI(title="Diagram Analysis API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho absoluto da pasta frontend (subindo 2 níveis)
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"

# Verifica se a pasta existe
if not frontend_path.exists():
    raise RuntimeError(f"Frontend directory not found: {frontend_path}")

# Monta como /frontend
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

# Rota opcional para abrir index.html na raiz
@app.get("/", response_class=HTMLResponse)
async def read_index():
    return (frontend_path / "index.html").read_text()

# Monta todas as rotas da API
app.include_router(api_router, prefix="/api")