import logging
import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core import mqtt_listener

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

import asyncio
from app.core.ws_manager import manager as ws_manager
from app.core.admin_ws_manager import manager as admin_ws_manager

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    ws_manager.set_event_loop(asyncio.get_event_loop())
    admin_ws_manager.set_event_loop(asyncio.get_event_loop())
    mqtt_client = mqtt_listener.start_mqtt_listener()
    logger.info("Startup: Database tables created & MQTT Listener started")
    yield
    # Shutdown
    if mqtt_client:
        mqtt_client.loop_stop()
    logger.info("Shutdown: Cleanup")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Accept browser clients from any origin. Authentication uses bearer headers,
# so wildcard origins can safely be used without credentialed CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to AURA API"}

app.include_router(api_router, prefix=settings.API_V1_STR)
