"""
API routes for the tamper-evident eLogbook.

Provides endpoints for creating log records with automatic hash-chain
integrity.  Each new record's hash is derived from its own fields plus
the preceding record's hash, forming an append-only ledger.

Ed25519 digital signatures are required on every new entry for
operator non-repudiation.

Includes active threat monitoring via honey-token decoy endpoints.
"""

from datetime import datetime, timezone
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import create_block_hash
from app.models.ledger import LogRecord
from app.models.honey_token import HoneyToken
from app.schemas.ledger import (
    LogRecordCreate,
    LogRecordResponse,
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

# Genesis hash – used as `previous_hash` for the very first record.
GENESIS_HASH = "0" * 64

router = APIRouter()


# ── POST /logs/ ──────────────────────────────────────────────────────────────

@router.post(
    "/logs/",
    response_model=LogRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new log record",
    description=(
        "Append a new entry to the tamper-evident logbook. "
        "The client must include a valid Ed25519 signature over the "
        "canonical payload (operator_id || action_type || data_payload) "
        "for non-repudiation. The server verifies the signature before "
        "accepting the record."
    ),
)
def create_log(entry: LogRecordCreate, db: Session = Depends(get_db)):
    """
    Create and persist a new log record in the hash chain.

    0. **Verify the Ed25519 signature** — reconstruct the canonical
       signing payload from the submitted fields, then verify the
       ``signature`` against the ``public_key``.  Reject with
       HTTP 401 if invalid.
    1. Fetch the most recent record's ``current_hash`` to use as this
       record's ``previous_hash``.  If the ledger is empty the genesis
       hash (64 zeros) is used instead.
    2. Generate the current UTC timestamp.
    3. Compute ``current_hash`` via SHA3-256 over all record fields plus
       the ``previous_hash``.
    4. Persist the new ``LogRecord`` and return it.
    """

    # --- 0. Verify the Ed25519 digital signature --------------------------
    canonical_payload = build_signing_payload(
        operator_id=entry.operator_id,
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
    sample_operator = "OP-TEST"
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
    response_model=List[LogRecordResponse],
    summary="Retrieve the complete ledger history",
    description=(
        "Return every log record in the ledger, ordered by block ID in "
        "ascending order (genesis → latest)."
    ),
)
def get_all_logs(db: Session = Depends(get_db)):
    """
    Fetch and return the full, ordered ledger for display or audit.
    """
    records = (
        db.query(LogRecord)
        .order_by(LogRecord.id.asc())
        .all()
    )
    return records


# ── GET /verify-ledger/ ─────────────────────────────────────────────────────

@router.get(
    "/verify-ledger/",
    response_model=Union[LedgerVerificationSuccess, LedgerVerificationFailure],
    summary="Verify the integrity of the entire ledger",
    description=(
        "Walk the hash chain from genesis to the latest block.  "
        "For every block, recalculate the SHA3-256 digest using the same "
        "field order and delimiter used during creation, then verify that "
        "(a) the recalculated hash matches the stored current_hash, and "
        "(b) the block's previous_hash matches the preceding block's "
        "current_hash.  Halts immediately on the first discrepancy."
    ),
)
def verify_ledger(db: Session = Depends(get_db)):
    """
    Cryptographic tamper-check engine.

    Iterates every record in ascending ID order and performs two checks
    per block:

    1. **Hash integrity** – recompute the hash from the stored fields
       (operator_id, timestamp ISO string, action_type, data_payload,
       previous_hash) using the same ``\\x1f``-delimited concatenation
       and SHA3-256 algorithm.  Compare to ``current_hash``.
    2. **Chain linkage** – confirm ``record.previous_hash`` equals the
       ``current_hash`` of the immediately preceding record (or the
       genesis hash for the first block).

    Returns 200 with a success payload if the chain is intact, or 200
    with a failure payload (including the tampered block ID) on the
    first mismatch.
    """

    records = (
        db.query(LogRecord)
        .order_by(LogRecord.id.asc())
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
        # Recompute the hash using the EXACT same inputs as creation.
        # The timestamp was originally hashed via
        #   datetime.now(timezone.utc).isoformat()
        # which produces a string with "+00:00".  PostgreSQL may return
        # the timestamp in the server's local timezone (e.g. "+05:30"),
        # so we must normalize back to UTC before calling .isoformat().
        utc_timestamp = record.timestamp.astimezone(timezone.utc)
        recalculated_hash = create_block_hash(
            operator_id=record.operator_id,
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
def threat_status(db: Session = Depends(get_db)):
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


