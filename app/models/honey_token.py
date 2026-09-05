"""
HoneyToken model for the active threat monitoring subsystem.

Each record represents a decoy data-node planted as bait.  Any access
to a honey-token endpoint is treated as a potential intrusion indicator.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.core.database import Base


class HoneyToken(Base):
    """
    A decoy record designed to lure and detect unauthorized access.

    When an attacker probes internal-looking endpoints, the system
    silently increments ``accessed_count`` and records the breach
    timestamp — giving the SOC team early warning of reconnaissance
    activity.
    """

    __tablename__ = "honey_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    decoy_name = Column(
        String(150),
        nullable=False,
        unique=True,
        comment="Human-readable label for this decoy node.",
    )
    fake_secret_data = Column(
        String(500),
        nullable=False,
        comment="Convincing-looking fake secret value.",
    )
    accessed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this decoy has been probed.",
    )
    last_breach_timestamp = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the most recent probe.",
    )

    def __repr__(self) -> str:
        return (
            f"<HoneyToken(id={self.id}, decoy='{self.decoy_name}', "
            f"hits={self.accessed_count})>"
        )
