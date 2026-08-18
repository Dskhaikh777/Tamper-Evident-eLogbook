"""
Cryptographic hashing utilities for the tamper-evident eLogbook.

Uses SHA3-256 from PyCryptodome to produce hash digests that form
the integrity chain across log records.
"""

from Crypto.Hash import SHA3_256

# Delimiter used to separate fields before hashing.
# A non-printable character prevents accidental collisions when
# field values are concatenated (e.g., "ab" + "cd" vs "a" + "bcd").
_FIELD_SEPARATOR = "\x1f"  # ASCII Unit Separator


def generate_sha3_hash(data: str) -> str:
    """
    Compute the SHA3-256 hex digest of a UTF-8 encoded string.

    Args:
        data: The input string to hash.

    Returns:
        A 64-character lowercase hexadecimal digest string.
    """
    h = SHA3_256.new()
    h.update(data.encode("utf-8"))
    return h.hexdigest()


def create_block_hash(
    operator_id: str,
    timestamp: str,
    action_type: str,
    payload: str,
    previous_hash: str,
) -> str:
    """
    Build a tamper-evident hash for a single log record.

    All fields are joined with a non-printable delimiter to avoid
    ambiguity, then hashed with SHA3-256.

    Args:
        operator_id:   The ID of the operator creating the entry.
        timestamp:      ISO-8601 formatted timestamp of the action.
        action_type:    Category of the action (e.g. "PM", "Calibration").
        payload:        Free-form text describing the action details.
        previous_hash:  The current_hash of the preceding log record
                        (use a known genesis value for the first record).

    Returns:
        A 64-character lowercase hexadecimal SHA3-256 digest.
    """
    combined = _FIELD_SEPARATOR.join([
        operator_id,
        timestamp,
        action_type,
        payload,
        previous_hash,
    ])
    return generate_sha3_hash(combined)
