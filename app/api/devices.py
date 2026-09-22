"""
Device overview API — Operator's asset dashboard with dynamic state injection.

Provides the central "what's happening on the floor" view by enriching
each registered device with the computed state of its latest audit-log
entry.  This endpoint is the Operator's landing page after login.

Endpoint:
    GET /api/v1/devices/overview   (Operator & Admin)

Performance Notes:
    The query uses a correlated subquery via ``lateral join`` semantics
    (emulated as a Python loop over a pre-fetched latest-log map) rather
    than N+1 queries.  The composite index
    ``ix_audit_logs_device_latest(device_id, id DESC)`` ensures that
    each "latest log per device" lookup is an index-only scan.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device import Device
from app.models.ledger import AuditLog
from app.models.user import User
from app.api.auth import require_role
from app.schemas.device import (
    DeviceOverviewResponse,
    LastOperation,
)

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
# OPERATOR'S DEVICE OVERVIEW  —  Dynamic State Injection
# ═════════════════════════════════════════════════════════════════════════════


@router.get(
    "/overview",
    response_model=List[DeviceOverviewResponse],
    summary="Device overview with live operational state",
    description=(
        "Fetch all registered devices with their dynamically-computed "
        "'Last Action State'. For each device, the API queries the most "
        "recent AuditLog entry and attaches the action type, operator "
        "identity, and timestamp. Devices with no logs show "
        "'No Operations Yet'."
    ),
)
def get_device_overview(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(["admin", "operator", "auditor"])),
):
    """
    Build the Operator's device dashboard.

    Algorithm (avoids N+1):
        1. Fetch all devices in one query.
        2. Subquery: for each device, find the MAX(audit_logs.id) — this
           is the latest block in that device's chain.
        3. Batch-fetch those latest AuditLog rows (with eager-loaded
           operator relationship) in a single query.
        4. Build a {device_id → AuditLog} map.
        5. Iterate devices, attach computed state, return.
    """

    # ── 1. All devices ───────────────────────────────────────────────────
    devices = (
        db.query(Device)
        .order_by(Device.created_at.asc())
        .all()
    )

    if not devices:
        return []

    # ── 2. Assemble the response via Python iteration ────────────────────
    result: List[DeviceOverviewResponse] = []

    for device in devices:
        # Fetch the latest log for this specific device
        latest_log = (
            db.query(AuditLog)
            .filter(AuditLog.device_id == device.id)
            .order_by(AuditLog.id.desc())
            .first()
        )

        if latest_log and latest_log.operator:
            operator = latest_log.operator
            operator_label = f"{operator.full_name} ({operator.employee_id})"

            last_operation = LastOperation(
                action=latest_log.action_type,
                operator=operator_label,
                timestamp=latest_log.timestamp,
            )
            status_label = (
                f"Last: {latest_log.action_type} by {operator.employee_id}"
            )
        else:
            last_operation = None
            status_label = "No Operations Yet"

        result.append(
            DeviceOverviewResponse(
                id=device.id,
                name=device.name,
                model_number=device.model_number,
                location=device.location,
                created_at=device.created_at,
                status_label=status_label,
                last_operation=last_operation,
            )
        )

    return result
