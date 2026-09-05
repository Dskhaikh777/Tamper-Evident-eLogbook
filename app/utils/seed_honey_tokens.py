"""
Honey-token seeder — plants decoy records on first startup.

Called from ``app.main`` during application initialization.  If the
``honey_tokens`` table is empty, five enticing fake records are
inserted.  Subsequent startups are no-ops.
"""

from sqlalchemy.orm import Session

from app.models.honey_token import HoneyToken

# ── Seed data ────────────────────────────────────────────────────────────────
# Each tuple: (decoy_name, fake_secret_data)
# Designed to look irresistible to an attacker performing reconnaissance.

_SEED_DECOYS = [
    (
        "admin_passwords",
        "admin:$2b$12$LJ3m9X9Z8Kq7r5TfNz.RheYZ7GdGp0vKQ||root:hunter2",
    ),
    (
        "jwt_master_secret",
        "HMAC-SECRET=9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    ),
    (
        "pharma_formula_x",
        "Compound-X: C21H30O2 | Ratio 3:1:0.5 | Yield 98.7% | CLASSIFIED",
    ),
    (
        "database_master_credentials",
        "host=prod-db-01.internal port=5432 user=superadmin password=P@ssw0rd!2026",
    ),
    (
        "api_stripe_live_key",
        "fake_stripe_key_for_honeypot_999",
    ),
]


def seed_honey_tokens(db: Session) -> int:
    """
    Insert seed decoy records if the ``honey_tokens`` table is empty.

    Args:
        db: An active SQLAlchemy session.

    Returns:
        The number of records inserted (0 if the table was already seeded).
    """
    existing_count = db.query(HoneyToken).count()
    if existing_count > 0:
        return 0

    tokens = [
        HoneyToken(decoy_name=name, fake_secret_data=data)
        for name, data in _SEED_DECOYS
    ]

    db.add_all(tokens)
    db.commit()
    return len(tokens)
