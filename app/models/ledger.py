"""
LogRecord model for the tamper-evident eLogbook.

Each record stores an operational log entry along with its cryptographic
hash and the hash of the previous record, forming a hash-chain that
guarantees tamper evidence.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class LogRecord(Base):
    """
    Represents a single entry in the tamper-evident electronic logbook.

    The hash chain (previous_hash → current_hash) ensures that any
    modification to a past record will break the chain and be detectable.
    """

    __tablename__ = "log_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operator_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of action, e.g. PM, Calibration, Inspection",
    )
    data_payload = Column(Text, nullable=False)
    public_key = Column(String(64), nullable=False, comment="Hex-encoded Ed25519 public key")
    signature = Column(String(128), nullable=False, comment="Hex-encoded Ed25519 signature")
    previous_hash = Column(String(128), nullable=False)
    current_hash = Column(String(128), nullable=False, unique=True)

    def __repr__(self) -> str:
        return (
            f"<LogRecord(id={self.id}, operator='{self.operator_id}', "
            f"action='{self.action_type}', hash='{self.current_hash[:12]}...')>"
        )
