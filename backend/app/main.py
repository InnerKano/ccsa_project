"""Application entry point for CCSA backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Explicit allow-list (no "*"): the frontend authenticates with a Bearer JWT,
# so browser requests must come from a known origin (ARCHITECTURE.md, A4).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.modules.analysis.api import router as analysis_router
from app.modules.auth.api import router as auth_router
from app.modules.statements.api import router as statements_router

app.include_router(auth_router)
app.include_router(statements_router)
app.include_router(analysis_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Verify the backend is running. No authentication required."""
    return {"status": "healthy"}
