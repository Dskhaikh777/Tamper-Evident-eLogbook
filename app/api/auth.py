"""
Authentication and Role-Based Access Control (RBAC) engine.

Provides:
    - JWT access-token issuance via OAuth2 password flow.
    - Bcrypt password hashing and verification.
    - Default user seeding for initial setup.
    - ``get_current_user`` dependency for token validation.
    - ``require_role`` closure dependency for endpoint-level RBAC.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

# ── Configuration ────────────────────────────────────────────────────────────

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret")

ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

# ── Password hashing ────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme (points to the token endpoint) ────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# ── Router ───────────────────────────────────────────────────────────────────

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════


def _hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches *hashed*."""
    return pwd_context.verify(plain, hashed)


def _create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Encode a JWT with an expiration claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ═════════════════════════════════════════════════════════════════════════════
# DEPENDENCIES
# ═════════════════════════════════════════════════════════════════════════════


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT, extract the ``sub`` (username), and return the
    corresponding ``User`` row.  Raises HTTP 401 on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: User | None = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def require_role(allowed_roles: List[str]):
    """
    Closure that returns a FastAPI dependency enforcing RBAC.

    Usage::

        @router.get("/admin-only/", dependencies=[Depends(require_role(["admin"]))])
        def admin_endpoint(): ...

    Or inject the user directly::

        def endpoint(user: User = Depends(require_role(["admin", "operator"]))):
            ...
    """

    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Role '{current_user.role}' is not authorized. "
                    f"Required: {allowed_roles}."
                ),
            )
        return current_user

    return _role_checker


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════


@router.post(
    "/token",
    summary="Obtain a JWT access token",
    description=(
        "Authenticate with username and password via the OAuth2 password "
        "flow. Returns a Bearer token and the user's RBAC role."
    ),
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Validate credentials and issue a signed JWT.

    The token payload includes:
        - ``sub`` – the authenticated username.
        - ``role`` – the user's RBAC role (for convenience; authoritative
          role checks always query the database).
    """
    user: User | None = (
        db.query(User).filter(User.username == form_data.username).first()
    )

    if not user or not _verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token(
        data={"sub": user.username, "role": user.role},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }


@router.post(
    "/setup-users",
    summary="Seed default users",
    description=(
        "Populate the database with three default users (admin, auditor, "
        "operator) if the users table is empty. Intended for first-time "
        "setup only."
    ),
)
def setup_default_users(db: Session = Depends(get_db)):
    """
    Create default users with bcrypt-hashed passwords if none exist.

    This is a convenience endpoint for initial bootstrapping.  In a
    production deployment, disable or protect this endpoint after first
    use.
    """
    existing_count: int = db.query(User).count()
    if existing_count > 0:
        return {
            "message": "Users already exist. Setup skipped.",
            "user_count": existing_count,
        }

    default_users = [
        {"username": "admin", "password": "admin@secure123", "role": "admin"},
        {"username": "auditor", "password": "auditor@secure123", "role": "auditor"},
        {"username": "operator", "password": "operator@secure123", "role": "operator"},
    ]

    created = []
    for u in default_users:
        user = User(
            username=u["username"],
            hashed_password=_hash_password(u["password"]),
            role=u["role"],
        )
        db.add(user)
        created.append({"username": u["username"], "role": u["role"]})

    db.commit()

    return {
        "message": f"Successfully created {len(created)} default users.",
        "users": created,
    }
