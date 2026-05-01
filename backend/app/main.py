# backend/app/main.py

"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pathlib import Path

from app.core.config import settings
from app.db.database import engine
from app.api.v1 import auth, transactions, dashboard
from app.services.csv_parser import CSVParser

# ─── App Instance ────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered personal finance copilot — analyze spending, detect patterns, and get AI insights.",
    version="0.3.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(auth.router,         prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(dashboard.router,    prefix="/api/v1")

# ─── Root ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — confirms app is running."""
    return {
        "app":         settings.APP_NAME,
        "version":     "0.3.0",
        "status":      "running",
        "environment": settings.ENVIRONMENT,
        "docs":        "/docs",
    }

# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check — database + AI service status."""

    db_status = "disconnected"

    if "sqlite" in settings.DATABASE_URL.lower():
        db_status = "skipped (test mode)"
    else:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

    ai_status = (
        "configured"
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here"
        else "not configured"
    )

    return {
        "status":     "healthy" if "connected" in db_status or "skipped" in db_status else "degraded",
        "version":    "0.3.0",
        "database":   db_status,
        "ai_service": ai_status,
    }

# ─── Multi-Bank Test ─────────────────────────────────────────────────────────

@app.get("/test-multi-bank", tags=["Dev Tools"])
async def test_multi_bank():
    """Dev endpoint — verify all bank CSV formats parse correctly."""

    parser        = CSVParser()
    results       = {}
    fixtures_path = Path("tests/fixtures")

    if not fixtures_path.exists():
        return {
            "error": "Fixtures directory not found",
            "path":  str(fixtures_path.absolute()),
        }

    for csv_file in fixtures_path.glob("sample_*.csv"):
        bank_name = csv_file.stem.replace("sample_", "").replace("_", " ").title()
        try:
            with open(csv_file) as f:
                transactions = parser.parse(f.read())
                results[bank_name] = {
                    "status":           "success",
                    "count":            len(transactions),
                    "sample":           transactions[0] if transactions else None,
                    "all_transactions": transactions,
                }
        except Exception as e:
            results[bank_name] = {
                "status": "error",
                "error":  str(e),
            }

    return {
        "total_banks_tested": len(results),
        "results":            results,
    }


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
