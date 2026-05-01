"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pathlib import Path
import os

from app.core.config import settings
from app.db.database import engine
from app.api.v1 import auth, transactions
from app.services.csv_parser import CSVParser  # Add this import

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered personal finance copilot",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    # Test database connection (skip in test mode)
    db_status = "disconnected"

    # Skip DB check if using SQLite (test environment)
    if "sqlite" in settings.DATABASE_URL.lower():
        db_status = "skipped (test mode)"
    else:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if "connected" in db_status or "skipped" in db_status else "degraded",
        "database": db_status,
        "ai_service": "configured" if settings.OPENAI_API_KEY != "sk-your-key-here" else "not configured"
    }


@app.get("/test-multi-bank")  # Changed to GET for easier browser testing
async def test_multi_bank():
    """Test endpoint to verify all bank formats work"""
    parser = CSVParser()  # Initialize parser
    results = {}
    fixtures_path = Path("tests/fixtures")

    # Check if fixtures directory exists
    if not fixtures_path.exists():
        return {
            "error": "Fixtures directory not found",
            "path": str(fixtures_path.absolute())
        }

    for csv_file in fixtures_path.glob("sample_*.csv"):
        bank_name = csv_file.stem.replace("sample_", "").replace("_", " ").title()
        try:
            with open(csv_file) as f:
                transactions = parser.parse(f.read())
                results[bank_name] = {
                    "status": "success",
                    "count": len(transactions),
                    "sample": transactions[0] if transactions else None,
                    "all_transactions": transactions  # Include all for demo
                }
        except Exception as e:
            results[bank_name] = {
                "status": "error",
                "error": str(e)
            }

    return {
        "total_banks_tested": len(results),
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
