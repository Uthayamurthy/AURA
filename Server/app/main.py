from fastapi import FastAPI
from app.api.api import api_router
from fastapi.middleware.cors import CORSMiddleware
import contextlib

from app.core.config import settings
from app.core.database import init_db
from app.core import mqtt_listener

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    mqtt_client = mqtt_listener.start_mqtt_listener()
    print("Startup: Database tables created & MQTT Listener started")
    yield
    # Shutdown
    if mqtt_client:
        mqtt_client.loop_stop()
    print("Shutdown: Cleanup")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to AURA API"}

app.include_router(api_router, prefix=settings.API_V1_STR)
# Trigger reload for .env
