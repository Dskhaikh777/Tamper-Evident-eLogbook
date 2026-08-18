"""
FastAPI application entry point for the Tamper-Evident eLogbook API.
"""

from fastapi import FastAPI

from app.core.database import Base, engine
from app.api.routes import router

# Create all tables that don't already exist in the database.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tamper-Evident eLogbook API")

# Mount the API router under the /api/v1 prefix.
app.include_router(router, prefix="/api/v1")
