"""
Admin provisioning API — User & Device management.

All endpoints are strictly protected by ``require_role(["admin"])``.

Endpoints:
    POST /admin/users     — Provision a new user (Operator / Auditor / Admin).
    GET  /admin/users     — List all users (with soft-delete status).
    PATCH /admin/users/{id}/deactivate — Soft-delete a user.
    POST /admin/devices   — Register a new physical device (returns UUID for QR).
    GET  /admin/devices   — List all registered devices.

Design Principles:
    - Users are NEVER hard-deleted — soft-delete via ``is_active=False``
      preserves referential integrity of the audit chain.
    - Devices are NEVER deleted — the ``RESTRICT`` FK constraint on
      ``AuditLog.device_id`` makes this a database-level impossibility
      once logs exist.
    - Duplicate ``employee_id`` is caught and returned as HTTP 409.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.honey_token import HoneyToken
from app.api.auth import require_role, hash_password
from app.schemas.user import UserCreate, UserResponse
from app.schemas.device import DeviceCreate, DeviceResponse


router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
# USER PROVISIONING
# ═════════════════════════════════════════════════════════════════════════════


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new user",
    description=(
        "Create a new user account with the specified role. "
        "The password is bcrypt-hashed server-side before storage. "
        "Duplicate employee_id values are rejected with HTTP 409."
    ),
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """
    Provision a new user in the system.

    Steps:
        1. Validate the Pydantic schema (automatic via FastAPI).
        2. Hash the raw password with bcrypt.
        3. Persist the User row.
        4. Return the created user (without password hash).

    Raises:
        HTTP 409 — if ``employee_id`` already exists.
    """
    new_user = User(
        full_name=payload.full_name,
        employee_id=payload.employee_id,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Employee ID '{payload.employee_id}' is already registered. "
                f"Each employee must have a unique identifier."
            ),
        )

    db.refresh(new_user)
    return new_user


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description=(
        "Return all registered users including deactivated ones. "
        "The ``is_active`` flag indicates soft-delete status."
    ),
)
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """Fetch all users ordered by creation time."""
    users = (
        db.query(User)
        .order_by(User.created_at.asc())
        .all()
    )
    return users


@router.patch(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate (soft-delete) a user",
    description=(
        "Set the user's ``is_active`` flag to ``False``. The user can "
        "no longer authenticate, but their audit-log entries remain "
        "cryptographically intact and attributed."
    ),
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    """
    Soft-delete a user by setting ``is_active = False``.

    Guards:
        - Cannot deactivate yourself (prevents admin lockout).
        - Returns 404 if the user_id doesn't exist.
        - Returns 409 if the user is already deactivated.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    # Prevent admin self-deactivation (lockout protection).
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate your own account.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{user.employee_id}' is already deactivated.",
        )

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


# ═════════════════════════════════════════════════════════════════════════════
# DEVICE REGISTRATION
# ═════════════════════════════════════════════════════════════════════════════


@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new physical device",
    description=(
        "Register a machine/instrument in the system. Returns the "
        "auto-generated UUID that must be printed as a QR code and "
        "physically affixed to the device."
    ),
)
def register_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """
    Register a new device and return its UUID for QR code generation.

    The UUID is generated server-side via ``uuid4()`` (set as the column
    default in the Device model).  The admin takes this UUID and prints
    it as a static QR sticker to affix on the physical machine.
    """
    new_device = Device(
        name=payload.name,
        model_number=payload.model_number,
        location=payload.location,
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return new_device


@router.get(
    "/devices",
    response_model=List[DeviceResponse],
    summary="List all registered devices",
    description="Return all physical devices registered in the system.",
)
def list_devices(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """Fetch all devices ordered by registration time."""
    devices = (
        db.query(Device)
        .order_by(Device.created_at.asc())
        .all()
    )
    return devices

# ═════════════════════════════════════════════════════════════════════════════
# SOC THREAT RESET
# ═════════════════════════════════════════════════════════════════════════════

@router.post(
    "/soc/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset SOC Threat Status",
    description="Reset all honey-token probe counts to 0 and clear breach timestamps.",
)
def reset_soc_threats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
):
    """Reset all decoy nodes to restore system integrity to 100%."""
    db.query(HoneyToken).update(
        {
            HoneyToken.accessed_count: 0,
            HoneyToken.last_breach_timestamp: None,
        }
    )
    db.commit()
    return {"message": "SOC Threat monitoring reset to SECURE status."}
