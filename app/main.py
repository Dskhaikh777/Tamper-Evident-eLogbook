"""
FastAPI application entry point for the Tamper-Evident eLogbook API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine, SessionLocal
from app.api.routes import router

# Import all models so Base.metadata.create_all discovers them.
from app.models.ledger import LogRecord          # noqa: F401
from app.models.honey_token import HoneyToken    # noqa: F401

from app.utils.seed_honey_tokens import seed_honey_tokens


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables and seed honey-tokens."""
    # Create all tables that don't already exist in the database.
    Base.metadata.create_all(bind=engine)

    # Seed the honey-token decoy table if it's empty.
    db = SessionLocal()
    try:
        count = seed_honey_tokens(db)
        if count:
            print(f"[STARTUP] Seeded {count} honey-token decoy nodes.")
    finally:
        db.close()

    yield  # application runs here


app = FastAPI(
    title="Tamper-Evident eLogbook API",
    lifespan=lifespan,
)

# Mount the API router under the /api/v1 prefix.
app.include_router(router, prefix="/api/v1")
