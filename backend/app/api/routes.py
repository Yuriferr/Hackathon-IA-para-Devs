from fastapi import APIRouter

# Importa routers dos controllers
from app.api.controllers.analyze_controller import router as analyze_router
from app.api.controllers.health_controller import router as health_router

# Router principal da API
router = APIRouter()

# Inclui os routers individuais
router.include_router(
    analyze_router, 
    prefix="/analyze", 
    tags=["Analyze"])

router.include_router(
    health_router, 
    prefix="/health", 
    tags=["Health"])