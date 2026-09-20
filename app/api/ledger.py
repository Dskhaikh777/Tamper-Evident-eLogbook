"""
Per-Device Ledger API — the core of the Asset-Centric Hash Chain.

This module implements the two most critical endpoints in the system:

1. **Operator Append** — ``POST /api/v1/ledger/{device_id}``
   Appends a new cryptographically-linked block to a specific device's
   isolated hash chain.  The ``operator_id`` is securely injected from
   the JWT — never client-supplied.

2. **Auditor Chain Export** — ``GET /api/v1/ledger/{device_id}/chain``
   Returns the full immutable timeline of a device's hash chain in
   chronological order, enabling offline mathematical verification.

Chain Invariant:
    For consecutive blocks B[n-1], B[n] in the same device's chain:

        B[n].previous_hash  ==  B[n-1].current_hash

    The first block uses GENESIS_HASH ("0" * 64) as previous_hash.
"""

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import create_block_hash
from app.models.device import Device
from app.models.ledger import AuditLog, GENESIS_HASH
from app.models.user import User
from app.api.auth import require_role
from app.schemas.ledger import LogCreate, LogResponse
from app.utils.crypto_keys import build_signing_payload, verify_signature

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
# OPERATOR APPEND — Per-Device Hash Chain Write
# ═════════════════════════════════════════════════════════════════════════════


@router.post(
    "/{device_id}",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append a block to a device's hash chain",
    description=(
        "Create a new tamper-evident log entry for the specified device. "
        "The operator's identity is securely extracted from the JWT — "
        "it cannot be spoofed. The Ed25519 signature is verified "
        "server-side before the block is accepted.\n\n"
        "**Chain Logic:** The new block's `previous_hash` is set to the "
        "`current_hash` of the latest existing block for THIS device. "
        "If this is the device's very first block, the genesis sentinel "
        "(64 zeros) is used."
    ),
)
def append_to_device_chain(
    device_id: UUID,
    entry: LogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    The Per-Device Append Protocol.

    Steps:
        0. Validate that the path ``device_id`` matches the body ``device_id``.
        1. Verify the target device exists.
        2. Verify the Ed25519 digital signature against the authenticated
           operator's ``employee_id`` (not a client-supplied ID).
        3. Query the latest block in THIS device's chain to obtain
           ``previous_hash``.  Use GENESIS_HASH if the chain is empty.
        4. Generate a UTC timestamp.
        5. Compute ``current_hash`` via SHA3-256 over the canonical fields.
        6. Persist the new ``AuditLog`` row and return it.

    Raises:
        HTTP 400 — ``device_id`` in path vs body mismatch.
        HTTP 401 — Ed25519 signature verification failure.
        HTTP 404 — Device not found.
    """

    # ── 0. Path / body consistency check ─────────────────────────────────
    if entry.device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Device ID mismatch: path says '{device_id}' but body "
                f"says '{entry.device_id}'. They must be identical."
            ),
        )

    # ── 1. Verify device exists ──────────────────────────────────────────
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered in the system.",
        )

    # ── 2. Verify Ed25519 signature ──────────────────────────────────────
    # The canonical payload uses the AUTHENTICATED user's employee_id —
    # this is what the client must sign on their side.
    canonical_payload = build_signing_payload(
        operator_id=current_user.employee_id,
        action_type=entry.action_type,
        data_payload=entry.data_payload,
    )

    if not verify_signature(
        public_key_hex=entry.public_key,
        payload=canonical_payload,
        signature_hex=entry.signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Ed25519 signature verification failed. "
                "Ensure you are signing the canonical payload: "
                "employee_id || \\x1f || action_type || \\x1f || data_payload "
                f"where employee_id = '{current_user.employee_id}'. "
                "Entry rejected for non-repudiation."
            ),
        )

    # ── 3. Fetch previous_hash from THIS DEVICE's chain ──────────────────
    latest_block = (
        db.query(AuditLog)
        .filter(AuditLog.device_id == device_id)
        .order_by(AuditLog.id.desc())
        .first()
    )
    previous_hash = latest_block.current_hash if latest_block else GENESIS_HASH

    # ── 4. UTC timestamp ─────────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc)

    # ── 5. Compute current_hash (SHA3-256) ───────────────────────────────
    current_hash = create_block_hash(
        operator_id=current_user.employee_id,
        timestamp=timestamp.isoformat(),
        action_type=entry.action_type,
        payload=entry.data_payload,
        previous_hash=previous_hash,
    )

    # ── 6. Persist and return ────────────────────────────────────────────
    new_block = AuditLog(
        device_id=device_id,
        operator_id=current_user.id,
        timestamp=timestamp,
        action_type=entry.action_type,
        data_payload=entry.data_payload,
        public_key=entry.public_key,
        signature=entry.signature,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

    db.add(new_block)
    db.commit()
    db.refresh(new_block)

    return new_block


# ═════════════════════════════════════════════════════════════════════════════
# AUDITOR CHAIN EXPORT — Air-Gapped Verification Flow
# ═════════════════════════════════════════════════════════════════════════════


@router.get(
    "/{device_id}/chain",
    response_model=List[LogResponse],
    summary="Export a device's complete hash chain",
    description=(
        "Fetch the full, chronologically-ordered hash chain for a specific "
        "device. This is the endpoint the Auditor's frontend calls after "
        "scanning the device's static QR sticker.\n\n"
        "The response contains every block in the chain from genesis to "
        "the latest, enabling the client to perform offline mathematical "
        "verification:\n\n"
        "1. Verify block[0].previous_hash == GENESIS_HASH (64 zeros).\n"
        "2. For each block[i], recompute SHA3-256 and compare to current_hash.\n"
        "3. Verify block[i].previous_hash == block[i-1].current_hash."
    ),
)
def get_device_chain(
    device_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(["auditor", "admin"])),
):
    """
    Auditor's air-gapped verification data source.

    Returns the entire device-specific chain in ascending ID order
    (genesis → latest).  The Auditor's frontend downloads this once
    and runs verification math entirely client-side — no further
    server calls needed.

    Raises:
        HTTP 404 — Device not found.
    """

    # ── Verify device exists ─────────────────────────────────────────────
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered in the system.",
        )

    # ── Fetch the full chain in chronological order ──────────────────────
    chain = (
        db.query(AuditLog)
        .filter(AuditLog.device_id == device_id)
        .order_by(AuditLog.id.asc())
        .all()
    )

    return chain
