from fastapi import APIRouter
from app.api.routers import auth

from app.api.routers import auth, admin, professor, student

api_router = APIRouter()
api_router.include_router(auth.router, tags=["login"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(professor.router, prefix="/professor", tags=["professor"])
api_router.include_router(student.router, prefix="/student", tags=["student"])
