"""
API routes for the tamper-evident eLogbook.

Provides endpoints for creating log records with automatic hash-chain
integrity.  Each new record's hash is derived from its own fields plus
the preceding record's hash, forming an append-only ledger.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import create_block_hash
from app.models.ledger import LogRecord
from app.schemas.ledger import LogRecordCreate, LogRecordResponse

# Genesis hash – used as `previous_hash` for the very first record.
GENESIS_HASH = "0" * 64

router = APIRouter()


@router.post(
    "/logs/",
    response_model=LogRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new log record",
    description=(
        "Append a new entry to the tamper-evident logbook. "
        "The server automatically timestamps the record and computes "
        "its cryptographic hash based on the preceding record's hash."
    ),
)
def create_log(entry: LogRecordCreate, db: Session = Depends(get_db)):
    """
    Create and persist a new log record in the hash chain.

    1. Fetch the most recent record's ``current_hash`` to use as this
       record's ``previous_hash``.  If the ledger is empty the genesis
       hash (64 zeros) is used instead.
    2. Generate the current UTC timestamp.
    3. Compute ``current_hash`` via SHA3-256 over all record fields plus
       the ``previous_hash``.
    4. Persist the new ``LogRecord`` and return it.
    """

    # --- 1. Determine the previous hash ----------------------------------
    latest_record = (
        db.query(LogRecord)
        .order_by(LogRecord.id.desc())
        .first()
    )
    previous_hash = latest_record.current_hash if latest_record else GENESIS_HASH

    # --- 2. Current UTC timestamp -----------------------------------------
    timestamp = datetime.now(timezone.utc)

    # --- 3. Compute the current hash --------------------------------------
    current_hash = create_block_hash(
        operator_id=entry.operator_id,
        timestamp=timestamp.isoformat(),
        action_type=entry.action_type,
        payload=entry.data_payload,
        previous_hash=previous_hash,
    )

    # --- 4. Create, persist, and return the record ------------------------
    new_record = LogRecord(
        operator_id=entry.operator_id,
        timestamp=timestamp,
        action_type=entry.action_type,
        data_payload=entry.data_payload,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record
