"""
Pydantic schemas for Device input validation and response serialization.

Devices are registered by admins and identified by UUID primary keys.
The UUID is printed as a static QR code and affixed to the physical machine.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ═════════════════════════════════════════════════════════════════════════════
# INPUT SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class DeviceCreate(BaseModel):
    """
    Schema for registering a new physical device/machine.

    The admin provides descriptive metadata; the server generates
    the UUID ``id`` that will be encoded into the QR sticker.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Human-readable device name.",
        examples=["Tablet Press #3"],
    )
    model_number: str | None = Field(
        default=None,
        max_length=100,
        description="Manufacturer model or part number.",
        examples=["TP-9200X"],
    )
    location: str | None = Field(
        default=None,
        max_length=200,
        description="Physical location of the device.",
        examples=["Building A, Room 204"],
    )


# ═════════════════════════════════════════════════════════════════════════════
# OUTPUT / RESPONSE SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class DeviceResponse(BaseModel):
    """
    Public-facing device representation.

    The ``id`` (UUID) is the value the admin must print as a QR code
    and physically attach to the machine.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    model_number: str | None
    location: str | None
    created_at: datetime


# ── Dynamic State Injection ──────────────────────────────────────────────────


class LastOperation(BaseModel):
    """
    Computed snapshot of the most recent operation performed on a device.
    """
    action: str = Field(..., description="Action type of the most recent log entry.")
    operator: str = Field(..., description="Operator who performed the action.")
    timestamp: datetime = Field(..., description="UTC timestamp of the most recent action.")


class DeviceOverviewResponse(BaseModel):
    """
    Device record enriched with its dynamically-computed last action state.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    model_number: str | None
    location: str | None
    created_at: datetime
    status_label: str = Field(
        ...,
        description="Human-readable device status summary.",
    )
    last_operation: LastOperation | None = Field(
        default=None,
        description="Computed last-action snapshot, or null if no logs exist.",
    )
