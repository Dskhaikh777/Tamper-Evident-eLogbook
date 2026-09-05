"""
Ed25519 digital-signature utilities for operator non-repudiation.

Uses the ``cryptography`` package (RFC 8032 Ed25519) to:
- Generate key pairs (hex-encoded for portability).
- Sign an arbitrary string payload.
- Verify a signature against a payload and public key.

The signed payload is the canonical concatenation of the three
client-supplied fields (operator_id, action_type, data_payload)
joined with the same ``\\x1f`` (ASCII Unit Separator) delimiter used
elsewhere in the system.
"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

# Same separator used in app.core.hashing for consistency.
_FIELD_SEPARATOR = "\x1f"


# ── Key generation ───────────────────────────────────────────────────────────

def generate_ed25519_keypair() -> tuple[str, str]:
    """
    Generate a fresh Ed25519 private/public key pair.

    Returns:
        A 2-tuple of **(private_key_hex, public_key_hex)**.
        Both values are lowercase hex-encoded raw key bytes
        (32 bytes each → 64 hex characters).
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_hex = private_key.private_bytes_raw().hex()
    public_hex = public_key.public_bytes_raw().hex()

    return private_hex, public_hex


# ── Canonical payload construction ───────────────────────────────────────────

def build_signing_payload(
    operator_id: str,
    action_type: str,
    data_payload: str,
) -> str:
    """
    Build the canonical string that operators must sign.

    The payload is ``operator_id ‖ \\x1f ‖ action_type ‖ \\x1f ‖ data_payload``.
    This must match **exactly** on both client and server side.

    Args:
        operator_id:  Unique operator identifier.
        action_type:  Category of the action performed.
        data_payload: Free-form description of the action.

    Returns:
        The canonical UTF-8 string to be signed.
    """
    return _FIELD_SEPARATOR.join([operator_id, action_type, data_payload])


# ── Signing ──────────────────────────────────────────────────────────────────

def sign_payload(private_key_hex: str, payload: str) -> str:
    """
    Sign *payload* with the Ed25519 private key.

    Args:
        private_key_hex: 64-character hex string of the 32-byte raw private key.
        payload:         The canonical string to sign.

    Returns:
        The 128-character hex-encoded Ed25519 signature (64 bytes).
    """
    private_key = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(private_key_hex)
    )
    signature = private_key.sign(payload.encode("utf-8"))
    return signature.hex()


# ── Verification ─────────────────────────────────────────────────────────────

def verify_signature(
    public_key_hex: str,
    payload: str,
    signature_hex: str,
) -> bool:
    """
    Verify an Ed25519 signature against a payload and public key.

    Args:
        public_key_hex: 64-character hex string of the 32-byte raw public key.
        payload:        The canonical signed string.
        signature_hex:  128-character hex-encoded signature.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(public_key_hex)
        )
        public_key.verify(
            bytes.fromhex(signature_hex),
            payload.encode("utf-8"),
        )
        return True
    except (InvalidSignature, ValueError, Exception):
        return False
