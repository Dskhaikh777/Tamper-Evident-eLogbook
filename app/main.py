"""
FastAPI application entry point for the Tamper-Evident eLogbook API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine, SessionLocal
from app.api.routes import router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.devices import router as devices_router
from app.api.ledger import router as ledger_router

# Import all models so Base.metadata.create_all discovers them.
from app.models.ledger import AuditLog           # noqa: F401
from app.models.device import Device             # noqa: F401
from app.models.honey_token import HoneyToken    # noqa: F401
from app.models.user import User                 # noqa: F401

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

# ── CORS — allow frontend dev servers (localhost:3000, :5173, etc.) ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API router under the /api/v1 prefix.
app.include_router(router, prefix="/api/v1")

# Mount the authentication router.
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Mount the admin provisioning router.
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

# Mount the device overview router (Operator dashboard).
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])

# Mount the per-device ledger router (Append + Auditor chain export).
app.include_router(ledger_router, prefix="/api/v1/ledger", tags=["Ledger"])
