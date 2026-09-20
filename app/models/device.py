"""
Device model for the Asset-Centric Distributed Ledger.

Represents a physical machine/instrument/equipment that operators interact
with on the production floor.  Each device is the **root of its own
isolated cryptographic hash chain** — every audit-log entry references a
``device_id``, and ``previous_hash`` always points to the last log entry
*of that same device*.

Workflow:
    1. An Admin registers a device via the API → a UUID ``id`` is generated.
    2. That UUID is encoded into a **static QR code** and physically affixed
       to the machine.
    3. Operators scan the QR → append log entries to that device's chain.
    4. Auditors scan the same QR → fetch & mathematically verify the
       device-specific chain.

The UUID primary key is chosen over an auto-incrementing integer because:
    - It is globally unique without a central sequence (supports future
      multi-site deployments).
    - It is safe to embed in a QR code and expose externally.
    - It cannot be guessed or enumerated by an attacker.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Device(Base):
    """
    A registered physical asset whose operational history is tracked
    via a per-device tamper-evident hash chain.

    The ``id`` (UUID) is the value printed on the static QR sticker
    affixed to the machine.  It serves as the entry point for both
    the Operator write-flow and the Auditor verification-flow.
    """

    __tablename__ = "devices"

    # ── Primary Key (UUID) ───────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Globally unique device identifier — printed as QR code",
    )

    # ── Device Metadata ──────────────────────────────────────────────────
    name = Column(
        String(200),
        nullable=False,
        comment="Human-readable device name (e.g. 'Tablet Press #3')",
    )
    model_number = Column(
        String(100),
        nullable=True,
        comment="Manufacturer model/part number",
    )
    location = Column(
        String(200),
        nullable=True,
        comment="Physical location (e.g. 'Building A, Room 204')",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp when the device was registered",
    )

    # ── Relationships ────────────────────────────────────────────────────
    # One device → many audit-log entries (its hash chain).
    # ``passive_deletes=True`` prevents SQLAlchemy from nullifying FKs.
    # Devices should NEVER be hard-deleted once logs exist; use
    # business-logic guards to enforce this.
    audit_logs = relationship(
        "AuditLog",
        back_populates="device",
        passive_deletes=True,
        lazy="dynamic",
        order_by="AuditLog.id",
    )

    def __repr__(self) -> str:
        return (
            f"<Device(id='{self.id}', name='{self.name}', "
            f"location='{self.location}')>"
        )
