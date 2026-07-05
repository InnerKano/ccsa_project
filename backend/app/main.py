"""Application entry point for CCSA backend."""

from fastapi import FastAPI

app = FastAPI(
    title="Credit Card Savings Analyzer",
    description="CCSA API — upload CSV statements, detect subscriptions, estimate savings.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Verify the backend is running. No authentication required."""
    return {"status": "healthy"}
