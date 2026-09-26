"""
AuditLog model — the core of the Per-Device Tamper-Evident Hash Chain.

Replaces the former global ``LogRecord`` with an asset-centric model where
each physical device maintains its **own isolated cryptographic chain**.

Chain Invariant (Per-Device):
    For any two consecutive log entries L[n-1] and L[n] belonging to the
    same ``device_id``:

        L[n].previous_hash  ==  L[n-1].current_hash

    The very first entry for a device uses the **genesis sentinel**:

        previous_hash = "0" * 64   (64-char hex string of zeros)

    This allows independent verification of each device's chain without
    needing to traverse logs of other devices.

Crypto Fields:
    - ``public_key``   – Hex-encoded Ed25519 public key of the signing client.
    - ``signature``    – Hex-encoded Ed25519 signature over the payload.
    - ``previous_hash`` – SHA3-256 digest of the preceding block *in this
                          device's chain*.
    - ``current_hash`` – SHA3-256 digest of this block's canonical fields.

Referential Integrity:
    - ``device_id``   FK → Device.id    (RESTRICT delete — chain must survive)
    - ``operator_id`` FK → User.id      (RESTRICT delete — attribution is permanent)

    Both foreign keys use ``ondelete="RESTRICT"`` to make it a database-level
    impossibility to destroy a device or user that has associated audit records.
    This is the strongest guarantee for ALCOA+ *Enduring* compliance.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

# ── Genesis Sentinel ─────────────────────────────────────────────────────────
# The ``previous_hash`` of the very first log entry for any device.
# Using a fixed, well-known value makes chain-start detection deterministic.
GENESIS_HASH = "0" * 64


class AuditLog(Base):
    """
    A single immutable entry in a device-specific tamper-evident hash chain.

    Each row cryptographically links to the previous row *of the same device*
    via ``previous_hash → current_hash``, forming an independently verifiable
    per-device ledger.

    Foreign keys are ``RESTRICT``-protected: you cannot delete a User or
    Device that has associated audit records.  This is intentional — audit
    history is permanent and non-negotiable.
    """

    __tablename__ = "audit_logs"

    # ── Primary Key ──────────────────────────────────────────────────────
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The device this log entry belongs to (hash-chain root)",
    )
    operator_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The user who performed the action (ALCOA+ attribution)",
    )

    # ── Temporal ─────────────────────────────────────────────────────────
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of the recorded action",
    )

    # ── Payload ──────────────────────────────────────────────────────────
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: PM, Calibration, Inspection, Cleaning, etc.",
    )
    data_payload = Column(
        Text,
        nullable=False,
        comment="Free-form action details / observation notes",
    )

    # ── Cryptographic Fields ─────────────────────────────────────────────
    public_key = Column(
        String(64),
        nullable=False,
        comment="Hex-encoded Ed25519 public key of the signing client",
    )
    signature = Column(
        String(128),
        nullable=False,
        comment="Hex-encoded Ed25519 signature over the canonical payload",
    )
    previous_hash = Column(
        String(64),
        nullable=False,
        comment="SHA3-256 hash of the preceding block IN THIS DEVICE'S CHAIN",
    )
    current_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA3-256 hash of this block's canonical fields",
    )

    # ── Relationships ────────────────────────────────────────────────────
    device = relationship(
        "Device",
        back_populates="audit_logs",
    )
    operator = relationship(
        "User",
        back_populates="audit_logs",
    )

    @property
    def operator_employee_id(self) -> str:
        return self.operator.employee_id if self.operator else "UNKNOWN"

    # ── Composite Indexes ────────────────────────────────────────────────
    # Optimise the critical query: "get the latest log for device X"
    # This is hit on every new log append (to fetch previous_hash) and
    # on every device-list call (to compute dynamic state).
    __table_args__ = (
        Index(
            "ix_audit_logs_device_latest",
            "device_id",
            id.desc(),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, device='{self.device_id}', "
            f"operator={self.operator_id}, action='{self.action_type}', "
            f"hash='{self.current_hash[:12]}...')>"
        )
