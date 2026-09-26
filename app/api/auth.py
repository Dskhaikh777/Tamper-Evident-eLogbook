"""
Authentication and Role-Based Access Control (RBAC) engine.

Enterprise pivot changes:
    - Authentication uses ``employee_id`` (not username).
    - Soft-deleted users (``is_active=False``) are strictly rejected.
    - JWT payload embeds ``sub`` (employee_id), ``role``, and ``user_id``
      for downstream RBAC dependency injection.
    - The ``setup-users`` seed endpoint is removed — user provisioning
      is now exclusively via the admin API.

Provides:
    - JWT access-token issuance via OAuth2 password flow.
    - Bcrypt password hashing and verification.
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
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse

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


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches *hashed*."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
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
    Decode the JWT, extract the ``sub`` (employee_id), and return the
    corresponding active ``User`` row.

    Raises:
        HTTP 401 — invalid/expired token or unknown employee_id.
        HTTP 403 — user account has been deactivated (soft-deleted).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employee_id: str | None = payload.get("sub")
        if employee_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: User | None = (
        db.query(User)
        .filter(User.employee_id == employee_id)
        .first()
    )
    if user is None:
        raise credentials_exception

    # ── Soft-delete gate ─────────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Account deactivated. Contact your administrator to "
                "restore access."
            ),
        )

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
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    description=(
        "Authenticate with employee_id and password via the OAuth2 password "
        "flow. Returns a Bearer token, the user's RBAC role, and identity."
    ),
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Validate credentials and issue a signed JWT.

    The OAuth2 spec mandates ``username`` / ``password`` form fields,
    so the client sends ``employee_id`` in the ``username`` field.

    The token payload includes:
        - ``sub``       – the authenticated employee_id.
        - ``role``      – the user's RBAC role.
        - ``user_id``   – the database PK (for FK injection on log creation).

    Security gates:
        1. Unknown employee_id → 401.
        2. Wrong password → 401.
        3. Deactivated account (is_active=False) → 403.
    """
    # OAuth2PasswordRequestForm uses `username` field — we map it to employee_id.
    user: User | None = (
        db.query(User)
        .filter(func.lower(User.employee_id) == form_data.username.lower())
        .first()
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee ID or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Soft-delete gate ─────────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Account deactivated. This employee ID has been disabled "
                "by an administrator. Contact your supervisor."
            ),
        )

    access_token = create_access_token(
        data={
            "sub": user.employee_id,
            "role": user.role,
            "user_id": user.id,
        },
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        employee_id=user.employee_id,
        full_name=user.full_name,
    )
