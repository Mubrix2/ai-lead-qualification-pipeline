# app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import leads, health
from app.config import APP_ENV
from app.core.qualifier import get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Lead Qualification API | env={APP_ENV}")
    get_client()
    logger.info("Qualifier client ready.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Lead Qualification Pipeline",
        description=(
            "Qualifies incoming leads using AI scoring, "
            "saves to Airtable CRM, and notifies Slack for hot leads."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(leads.router, prefix="/api/v1")

    return app


app = create_app()