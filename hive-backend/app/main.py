from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.config import settings
from app.memory.db import init_db
from app.agents import IngestionAgent, Trace

from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.admin import router as admin_router
from app.api.admin_dashboard import router as admin_dashboard_router
import app.api.chat as chat_module


def create_app() -> FastAPI:
    setup_logging()
    init_db()

    app = FastAPI(title="HIVE Backend", version="1.0")
    
    # Reload trigger: 2026-01-26
    # Track start time for uptime
    import time
    app.state.start_time = time.time()

    # When running behind nginx (localhost:8080), frontend calls /api/* (same origin).
    # But we still allow origin for direct testing if needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Build/load preloaded global KB index
    ingestion = IngestionAgent()
    trace = Trace()
    index, metas = ingestion.build_or_load(trace)
    chat_module.GLOBAL_INDEX = index
    chat_module.GLOBAL_METAS = metas

    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(voice_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(admin_dashboard_router, prefix="/api")
    return app


app = create_app()
