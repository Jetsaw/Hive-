from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict

from app.core.logging import setup_logging
from app.core.config import settings
from app.memory.db import init_db
from app.agents import IngestionAgent, Trace

from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.admin import router as admin_router
from app.api.admin_dashboard import router as admin_dashboard_router
from app.api.calendar import router as calendar_router
from app.api.comparison import router as comparison_router
from app.api.feedback import router as feedback_router
from app.api.study_groups import router as study_groups_router
from app.api.export import router as export_router
from app.api.suggestions import router as suggestions_router
import app.api.chat as chat_module

logger = logging.getLogger("hive")


# Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter: 100 requests per minute per IP."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]

        if len(self.requests[client_ip]) >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit exceeded. Max 100 requests per minute."}',
                status_code=429,
                media_type="application/json",
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response


def create_app() -> FastAPI:
    setup_logging()
    init_db()

    app = FastAPI(title="HIVE Backend", version="2.0")

    # Track start time for uptime
    app.state.start_time = time.time()

    # Rate Limiting Middleware (100 req/min)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

    # CORS - allow frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:8080", "http://localhost:3000"],
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

    # Core routers
    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(voice_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(admin_dashboard_router, prefix="/api")

    # New feature routers
    app.include_router(calendar_router)
    app.include_router(comparison_router)
    app.include_router(feedback_router)
    app.include_router(study_groups_router)
    app.include_router(export_router)
    app.include_router(suggestions_router)

    logger.info("HIVE Backend v2.0 started with all features enabled")
    return app


app = create_app()
