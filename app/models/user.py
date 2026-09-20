"""
User model for Identity & Role-Based Access Control (RBAC).

Represents an authenticated operator, auditor, or administrator within the
Tamper-Evident eLogbook system.  Designed for FDA 21 CFR Part 11 / ALCOA+
compliance:

  - ``employee_id`` serves as the unique corporate identifier printed on
    badges and linked to training records.
  - ``is_active`` enables soft-delete semantics: deactivated users can no
    longer authenticate, but their past audit-log entries remain
    cryptographically bound — preserving chain integrity.
  - Passwords are stored as bcrypt digests; plain-text is never persisted.

Roles:
    admin    – Full system access: user/device management, threat monitoring.
    operator – Create log entries against registered devices.
    auditor  – Read-only access to device ledgers for verification.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    An authenticated identity within the eLogbook system.

    The ``employee_id`` is the externally-visible corporate identifier
    (e.g. "EMP-0042") and is guaranteed unique across the organisation.
    It is the value displayed on audit reports and used for traceability.

    Soft-delete via ``is_active = False`` ensures that foreign-key
    references from ``AuditLog.operator_id`` never become orphaned,
    satisfying ALCOA+ *Attributable* and *Enduring* principles.
    """

    __tablename__ = "users"

    # ── Primary Key ──────────────────────────────────────────────────────
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    # ── Identity Fields ──────────────────────────────────────────────────
    full_name = Column(
        String(200),
        nullable=False,
        comment="Full legal name as per corporate HR records",
    )
    employee_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique corporate employee identifier (e.g. EMP-0042)",
    )

    # ── Authentication ───────────────────────────────────────────────────
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt-hashed password digest",
    )

    # ── RBAC ─────────────────────────────────────────────────────────────
    role = Column(
        String(20),
        nullable=False,
        index=True,
        comment="RBAC role: admin | operator | auditor",
    )

    # ── Soft-Delete ──────────────────────────────────────────────────────
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="False = deactivated (soft-deleted for audit integrity)",
    )

    # ── Metadata ─────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of account creation",
    )

    # ── Relationships ────────────────────────────────────────────────────
    # One user → many audit-log entries they created.
    # ``passive_deletes=True`` tells SQLAlchemy NOT to nullify FKs on
    # delete — we rely on soft-delete instead of hard-delete.
    audit_logs = relationship(
        "AuditLog",
        back_populates="operator",
        passive_deletes=True,
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "deactivated"
        return (
            f"<User(id={self.id}, employee_id='{self.employee_id}', "
            f"role='{self.role}', {status})>"
        )
