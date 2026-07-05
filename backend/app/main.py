"""Application entry point for CCSA backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import check_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.skip_db_check:
        check_database_connection()
    yield


app = FastAPI(
    title="Credit Card Savings Analyzer",
    description="CCSA API — upload CSV statements, detect subscriptions, estimate savings.",
    version="0.1.0",
    lifespan=lifespan,
)

from app.modules.auth.api import router as auth_router

app.include_router(auth_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Verify the backend is running. No authentication required."""
    return {"status": "healthy"}
