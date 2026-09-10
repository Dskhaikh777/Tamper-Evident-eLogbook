"""
User model for Role-Based Access Control (RBAC).

Stores user credentials (bcrypt-hashed passwords) and their assigned role
within the tamper-evident eLogbook system.

Roles:
    - admin    – Full system access including threat monitoring.
    - auditor  – Read-only access to ledger verification and audit trails.
    - operator – Create log entries and view the ledger.
"""

from sqlalchemy import Column, Integer, String
from app.core.database import Base


class User(Base):
    """
    Represents an authenticated user with a specific RBAC role.

    The ``hashed_password`` column stores a bcrypt digest — plain-text
    passwords are never persisted.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique login identifier",
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt-hashed password digest",
    )
    role = Column(
        String(20),
        nullable=False,
        index=True,
        comment="RBAC role: admin | auditor | operator",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
