"""
API routes for the tamper-evident eLogbook.

Provides endpoints for creating log records with automatic hash-chain
integrity.  Each new record's hash is derived from its own fields plus
the preceding record's hash, forming an append-only ledger.

Ed25519 digital signatures are required on every new entry for
operator non-repudiation.

Includes active threat monitoring via honey-token decoy endpoints.

NOTE: The log-creation and verification endpoints in this file still
use the OLD global-chain logic.  They will be fully rewritten in
Phase 3 to operate per-device.  The imports and model references have
been updated to compile against the new schema.
"""

from datetime import datetime, timezone
from typing import List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import require_role
from app.models.user import User
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import create_block_hash
from app.models.ledger import AuditLog, GENESIS_HASH
from app.models.honey_token import HoneyToken
from app.schemas.ledger import (
    LogCreate,
    LogResponse,
    KeyPairResponse,
    LedgerVerificationSuccess,
    LedgerVerificationFailure,
    ThreatStatusSecure,
    ThreatStatusBreached,
    BreachedDecoyDetail,
)
from app.utils.crypto_keys import (
    generate_ed25519_keypair,
    build_signing_payload,
    sign_payload,
    verify_signature,
)

router = APIRouter()


# ── POST /logs/ ──────────────────────────────────────────────────────────────
# NOTE: This endpoint will be rewritten in Phase 3 for per-device chains.
# It is temporarily updated to compile against the new models.

@router.post(
    "/logs/",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new log record",
    description=(
        "Append a new entry to the tamper-evident logbook. "
        "The client must include a valid Ed25519 signature over the "
        "canonical payload for non-repudiation. The server verifies "
        "the signature before accepting the record. "
        "NOTE: Will be rewritten in Phase 3 for per-device chains."
    ),
)
def create_log(
    entry: LogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Create and persist a new log record in the hash chain.

    This is a TRANSITIONAL implementation — it appends to the correct
    device's chain using the new model structure, but the full per-device
    flow (dynamic state injection, etc.) comes in Phase 3.
    """

    # --- 0. Verify the Ed25519 digital signature --------------------------
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
                "The signature does not match the provided public key "
                "and payload. Entry rejected for non-repudiation."
            ),
        )

    # --- 1. Determine the previous hash (GLOBAL) ---------------------
    latest_record = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )
    previous_hash = latest_record.current_hash if latest_record else GENESIS_HASH

    # --- 2. Current UTC timestamp -----------------------------------------
    timestamp = datetime.now(timezone.utc)

    # --- 3. Compute the current hash --------------------------------------
    current_hash = create_block_hash(
        operator_id=current_user.employee_id,
        timestamp=timestamp.isoformat(),
        action_type=entry.action_type,
        payload=entry.data_payload,
        previous_hash=previous_hash,
    )

    # --- 4. Create, persist, and return the record ------------------------
    new_record = AuditLog(
        device_id=entry.device_id,
        operator_id=current_user.id,
        timestamp=timestamp,
        action_type=entry.action_type,
        data_payload=entry.data_payload,
        public_key=entry.public_key,
        signature=entry.signature,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


# ── GET /generate-keys/ ─────────────────────────────────────────────────────

@router.get(
    "/generate-keys/",
    response_model=KeyPairResponse,
    summary="Generate a test Ed25519 key pair with sample signature",
    description=(
        "Utility endpoint for development and testing. Generates a fresh "
        "Ed25519 key pair and signs a sample payload so the keys and "
        "signature can be copy-pasted into Swagger UI to test the POST "
        "/logs/ endpoint."
    ),
)
def generate_keys():
    """
    Generate a fresh Ed25519 key pair and produce a sample signature.

    The sample payload uses fixed test values so the caller knows
    exactly which ``operator_id``, ``action_type``, and ``data_payload``
    to use with the returned signature.
    """
    private_hex, public_hex = generate_ed25519_keypair()

    # Fixed test values — the caller must use these exact strings
    # with the returned signature for it to verify.
    sample_operator = "EMP-TEST"
    sample_action = "Inspection"
    sample_data = "Test entry for Ed25519 signature verification."

    canonical = build_signing_payload(
        operator_id=sample_operator,
        action_type=sample_action,
        data_payload=sample_data,
    )
    sample_sig = sign_payload(private_hex, canonical)

    return KeyPairResponse(
        private_key=private_hex,
        public_key=public_hex,
        sample_payload=canonical,
        sample_signature=sample_sig,
    )


# ── GET /logs/ ───────────────────────────────────────────────────────────────

@router.get(
    "/logs/",
    response_model=List[LogResponse],
    summary="Retrieve the complete ledger history",
    description=(
        "Return every log record in the ledger, ordered by block ID in "
        "ascending order (genesis → latest). "
        "NOTE: Will be scoped per-device in Phase 3."
    ),
)
def get_all_logs(
    device_id: UUID | None = None,
    db: Session = Depends(get_db)
):
    """
    Fetch and return the full, ordered ledger for display or audit.
    Optionally filter by a specific device.
    """
    # Evaluate chain integrity globally first
    all_records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    
    from app.models.ledger import GENESIS_HASH
    
    last_hash = GENESIS_HASH
    for record in all_records:
        if record.previous_hash == last_hash:
            record.is_chain_intact = True
        else:
            record.is_chain_intact = False
        last_hash = record.current_hash

    # Then filter if device_id is provided
    if device_id:
        return [r for r in all_records if r.device_id == device_id]
        
    return all_records


# ── POST /admin/reset-ledger ────────────────────────────────────────────────
@router.post(
    "/admin/reset-ledger",
    status_code=status.HTTP_200_OK,
    summary="TRUNCATE the entire audit ledger (Development/Admin Utility)",
    description=(
        "WARNING: This endpoint permanently deletes all records in the "
        "AuditLog table. This is used to reset the global hash chain during "
        "development when the chain is fractured."
    ),
)
def reset_ledger(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(["admin"])),
):
    """
    Truncate the AuditLog table.
    """
    db.query(AuditLog).delete()
    db.commit()
    return {"message": "Audit ledger has been successfully truncated and reset to genesis state."}


# ── GET /verify-ledger/ ─────────────────────────────────────────────────────
# NOTE: Will be rewritten in Phase 3 for per-device verification.

@router.get(
    "/verify-ledger/",
    response_model=Union[LedgerVerificationSuccess, LedgerVerificationFailure],
    summary="Verify the integrity of the entire ledger",
    description=(
        "Walk the hash chain from genesis to the latest block. "
        "NOTE: This currently verifies ALL logs globally. "
        "Phase 3 will scope this per-device."
    ),
)
def verify_ledger(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(["auditor", "admin"])),
):
    """
    Cryptographic tamper-check engine (transitional — global chain).

    Will be rewritten in Phase 3 to verify per-device chains.
    """
    records = (
        db.query(AuditLog)
        .order_by(AuditLog.id.asc())
        .all()
    )

    if not records:
        return LedgerVerificationSuccess(
            status="valid",
            message="Ledger is empty. No blocks to verify.",
            blocks_verified=0,
        )

    expected_previous_hash = GENESIS_HASH

    for record in records:
        # ── Check 1: Chain linkage ────────────────────────────────────
        if record.previous_hash != expected_previous_hash:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=LedgerVerificationFailure(
                    status="tampered",
                    message=(
                        f"CRITICAL: Chain linkage broken at Block #{record.id}. "
                        f"The block's previous_hash does not match the "
                        f"preceding block's current_hash."
                    ),
                    tampered_block_id=record.id,
                    expected_hash=expected_previous_hash,
                    stored_hash=record.previous_hash,
                ).model_dump(),
            )

        # ── Check 2: Hash integrity ──────────────────────────────────
        utc_timestamp = record.timestamp.astimezone(timezone.utc)
        recalculated_hash = create_block_hash(
            operator_id=record.operator.employee_id if record.operator else "UNKNOWN",
            timestamp=utc_timestamp.isoformat(),
            action_type=record.action_type,
            payload=record.data_payload,
            previous_hash=record.previous_hash,
        )

        if recalculated_hash != record.current_hash:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=LedgerVerificationFailure(
                    status="tampered",
                    message=(
                        f"CRITICAL: Hash integrity violation at Block #{record.id}. "
                        f"The recalculated SHA3-256 digest does not match the "
                        f"stored current_hash. Data in this block has been altered."
                    ),
                    tampered_block_id=record.id,
                    expected_hash=recalculated_hash,
                    stored_hash=record.current_hash,
                ).model_dump(),
            )

        # This block is clean — advance the chain pointer.
        expected_previous_hash = record.current_hash

    return LedgerVerificationSuccess(
        status="valid",
        message=f"Ledger is 100% valid. All {len(records)} blocks verified.",
        blocks_verified=len(records),
    )


# ═════════════════════════════════════════════════════════════════════════════
# ACTIVE THREAT MONITORING — Honey-Token Decoy System
# ═════════════════════════════════════════════════════════════════════════════


# ── GET /system-configs-internal/ (HONEYPOT TRAP) ────────────────────────────

@router.get(
    "/system-configs-internal/",
    summary="[INTERNAL] System configuration export",
    description=(
        "Internal configuration dump for authorized maintenance tools. "
        "Do not expose publicly."
    ),
    # Intentionally vague tags to look like a real internal endpoint.
    tags=["internal"],
)
def honeypot_trap(db: Session = Depends(get_db)):
    """
    🍯 HONEYPOT — This endpoint is a trap.

    Any access is treated as hostile reconnaissance.  The system:
    1. Picks a random honey-token from the database.
    2. Increments its ``accessed_count``.
    3. Records the breach timestamp.
    4. Returns a fake JSON response that looks like a real config dump
       to keep the attacker engaged and buy time for the SOC team.
    """
    from sqlalchemy.sql.expression import func

    # Pick a random decoy to increment (distributes hits across nodes).
    token = (
        db.query(HoneyToken)
        .order_by(func.random())
        .first()
    )

    if not token:
        # Table is empty (seeder didn't run) — still return fake data.
        return {
            "service": "elogbook-core",
            "db_host": "prod-db-01.internal",
            "db_port": 5432,
            "cache_ttl": 3600,
            "debug_mode": False,
        }

    # ── Record the breach ─────────────────────────────────────────────
    token.accessed_count += 1
    token.last_breach_timestamp = datetime.now(timezone.utc)
    db.commit()
    db.refresh(token)

    # ── Return convincing fake response ───────────────────────────────
    return {
        "service": "elogbook-core",
        "version": "3.8.1-internal",
        "environment": "production",
        "database": {
            "host": "prod-db-01.internal",
            "port": 5432,
            "name": "elogbook_prod",
            "user": "svc_elogbook",
            "password_hash": "$2b$12$fakeHashThatLooksReal000000000000000000",
        },
        "jwt_secret": "eyJhbGciOiJIUzI1NiJ9.FAKE_SECRET_DO_NOT_USE",
        "redis": {
            "host": "cache-01.internal",
            "port": 6379,
            "password": "r3d1s_p@ss_FAKE",
        },
        "feature_flags": {
            "audit_mode": True,
            "maintenance_window": False,
        },
    }


# ── GET /threat-status/ (SOC DASHBOARD) ─────────────────────────────────────

@router.get(
    "/threat-status/",
    response_model=Union[ThreatStatusSecure, ThreatStatusBreached],
    summary="Threat monitoring console feed",
    description=(
        "Scans all honey-token decoy nodes.  Returns a secure status if "
        "no probes have been detected, or a critical alert listing every "
        "breached node with access counts and timestamps."
    ),
)
def threat_status(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(["admin"])),
):
    """
    SOC threat-status scanner.

    Queries every ``HoneyToken`` record and checks whether any
    ``accessed_count > 0``.  Computes an integrity percentage and
    returns either a clean bill or a critical breach alert.
    """
    all_tokens = db.query(HoneyToken).order_by(HoneyToken.id.asc()).all()
    total = len(all_tokens)

    if total == 0:
        return ThreatStatusSecure(
            status="secure",
            integrity="100%",
            message="No honey-token decoy nodes deployed yet.",
        )

    breached = [t for t in all_tokens if t.accessed_count > 0]
    breached_count = len(breached)
    intact_count = total - breached_count
    integrity_pct = f"{int((intact_count / total) * 100)}%"

    if breached_count == 0:
        return ThreatStatusSecure(
            status="secure",
            integrity="100%",
            message="All honey-token decoy nodes are intact. No intrusion detected.",
        )

    return ThreatStatusBreached(
        status="critical",
        integrity=integrity_pct,
        message=(
            f"⚠ ALERT: {breached_count} of {total} decoy nodes have been "
            f"probed. Possible unauthorized reconnaissance detected."
        ),
        total_decoys=total,
        breached_count=breached_count,
        breached_nodes=[
            BreachedDecoyDetail.model_validate(t) for t in breached
        ],
    )
