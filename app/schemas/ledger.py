"""
Pydantic schemas for the AuditLog (per-device tamper-evident hash chain).

Replaces the former ``LogRecord`` schemas to align with the asset-centric
ledger architecture.  Key changes:

  - ``LogCreate`` now requires a ``device_id`` to target a specific chain.
  - ``LogResponse`` includes both ``device_id`` and ``operator_id`` as
    typed foreign-key references.
  - Verification schemas are updated for per-device chain verification.

Threat-monitoring schemas (HoneyToken) are preserved unchanged.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ═════════════════════════════════════════════════════════════════════════════
# AUDIT LOG — INPUT SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class LogCreate(BaseModel):
    """
    Schema for appending a new entry to a device's hash chain.

    The client provides:
      - ``device_id`` — which device's chain to append to.
      - ``action_type`` / ``data_payload`` — the operational record.
      - ``public_key`` / ``signature`` — Ed25519 non-repudiation proof.

    The server injects the authenticated ``operator_id`` from the JWT,
    generates the timestamp, computes hashes, and persists the block.
    """

    device_id: UUID = Field(
        ...,
        description="UUID of the target device (from the QR sticker).",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    action_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the action performed.",
        examples=["PM", "Calibration", "Inspection", "Cleaning"],
    )
    data_payload: str = Field(
        ...,
        min_length=1,
        description="Free-form text describing the action details.",
        examples=["Replaced pressure sensor on Line 3."],
    )
    public_key: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description=(
            "Hex-encoded 32-byte Ed25519 public key of the signing operator."
        ),
        examples=["a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"],
    )
    signature: str = Field(
        ...,
        min_length=128,
        max_length=128,
        description=(
            "Hex-encoded 64-byte Ed25519 signature over the canonical "
            "payload: employee_id || \\x1f || action_type || \\x1f || data_payload."
        ),
        examples=["deadbeef0123" + "0" * 116],
    )


# ═════════════════════════════════════════════════════════════════════════════
# AUDIT LOG — OUTPUT / RESPONSE SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class LogResponse(BaseModel):
    """
    Full audit-log entry as returned to the client.

    Includes all server-generated fields (id, timestamp, hashes)
    alongside the original input data and cryptographic proof.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: UUID
    operator_id: int
    timestamp: datetime
    action_type: str
    data_payload: str
    public_key: str
    signature: str
    previous_hash: str
    current_hash: str


# ═════════════════════════════════════════════════════════════════════════════
# LEDGER VERIFICATION SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class LedgerVerificationSuccess(BaseModel):
    """Response schema when a device's hash chain is fully intact."""

    status: str = Field(
        default="valid",
        description="Overall verification result.",
        examples=["valid"],
    )
    message: str = Field(
        ...,
        description="Human-readable verification summary.",
        examples=["Device chain is 100% valid. All 42 blocks verified."],
    )
    blocks_verified: int = Field(
        ...,
        ge=0,
        description="Total number of blocks that passed verification.",
    )


class LedgerVerificationFailure(BaseModel):
    """Response schema when tamper evidence is detected in a device chain."""

    status: str = Field(
        default="tampered",
        description="Overall verification result.",
        examples=["tampered"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the integrity violation.",
    )
    tampered_block_id: int = Field(
        ...,
        description="ID of the first block where tampering was detected.",
    )
    expected_hash: str = Field(
        ...,
        description="The hash value that was expected (recalculated).",
    )
    stored_hash: str = Field(
        ...,
        description="The hash value currently stored in the database.",
    )


# ═════════════════════════════════════════════════════════════════════════════
# KEY GENERATION (Development Utility)
# ═════════════════════════════════════════════════════════════════════════════


class KeyPairResponse(BaseModel):
    """Response schema for the key generation utility endpoint."""

    private_key: str = Field(
        ..., description="Hex-encoded 32-byte Ed25519 private key."
    )
    public_key: str = Field(
        ..., description="Hex-encoded 32-byte Ed25519 public key."
    )
    sample_payload: str = Field(
        ..., description="The canonical string that was signed."
    )
    sample_signature: str = Field(
        ..., description="Hex-encoded Ed25519 signature of the sample payload."
    )


# ═════════════════════════════════════════════════════════════════════════════
# THREAT MONITORING — Honey-Token Schemas (Preserved)
# ═════════════════════════════════════════════════════════════════════════════


class BreachedDecoyDetail(BaseModel):
    """Detail of a single breached honey-token."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    decoy_name: str
    accessed_count: int
    last_breach_timestamp: datetime | None


class ThreatStatusSecure(BaseModel):
    """Response when all honey-tokens are untouched."""

    status: str = Field(
        default="secure",
        description="Overall threat assessment.",
        examples=["secure"],
    )
    integrity: str = Field(
        default="100%",
        description="Percentage of unbreached decoy nodes.",
    )
    message: str = Field(
        default="All honey-token decoy nodes are intact. No intrusion detected.",
        description="Human-readable summary.",
    )


class ThreatStatusBreached(BaseModel):
    """Response when one or more honey-tokens have been accessed."""

    status: str = Field(
        default="critical",
        description="Overall threat assessment.",
        examples=["critical"],
    )
    integrity: str = Field(
        ...,
        description="Percentage of unbreached decoy nodes.",
        examples=["60%"],
    )
    message: str = Field(
        ...,
        description="Human-readable alert summary.",
    )
    total_decoys: int = Field(
        ..., description="Total number of honey-token decoy nodes."
    )
    breached_count: int = Field(
        ..., description="Number of decoy nodes that have been probed."
    )
    breached_nodes: list[BreachedDecoyDetail] = Field(
        ..., description="Details of each breached decoy node."
    )
