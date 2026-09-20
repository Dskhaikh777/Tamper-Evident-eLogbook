"""
Pydantic schemas for User input validation and response serialization.

Designed for the enterprise pivot:
  - Authentication uses ``employee_id`` (not username).
  - ``UserCreate`` enforces strict field validation for admin provisioning.
  - ``UserResponse`` never exposes the password hash.
  - ``UserLogin`` is the lightweight schema for the OAuth2 password flow.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ═════════════════════════════════════════════════════════════════════════════
# INPUT SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class UserCreate(BaseModel):
    """
    Schema for admin-provisioned user creation.

    The admin provides the identity fields and a raw password.
    The API hashes the password before persistence — plain text never
    touches the database.
    """

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Full legal name as per corporate HR records.",
        examples=["Dr. Aisha Khan"],
    )
    employee_id: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z0-9\-_]+$",
        description=(
            "Unique corporate employee identifier. "
            "Alphanumeric, hyphens, and underscores only."
        ),
        examples=["EMP-0042"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Raw password (will be bcrypt-hashed server-side).",
        examples=["S3cure!Pass#2026"],
    )
    role: Literal["admin", "operator", "auditor"] = Field(
        ...,
        description="RBAC role to assign to this user.",
        examples=["operator"],
    )


class UserLogin(BaseModel):
    """
    Schema for the login / token-issuance flow.

    Maps to the OAuth2PasswordRequestForm but typed for clarity
    in internal usage.  The actual endpoint still uses the standard
    OAuth2 form dependency.
    """

    employee_id: str = Field(
        ...,
        min_length=2,
        description="Corporate employee ID used as the login identifier.",
        examples=["EMP-0042"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Plain-text password for verification.",
    )


# ═════════════════════════════════════════════════════════════════════════════
# OUTPUT / RESPONSE SCHEMAS
# ═════════════════════════════════════════════════════════════════════════════


class UserResponse(BaseModel):
    """
    Public-facing user representation — never exposes ``hashed_password``.

    Returned by provisioning endpoints and user-list queries.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    employee_id: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token response returned after successful authentication."""

    access_token: str = Field(
        ..., description="Signed JWT bearer token."
    )
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')."
    )
    role: str = Field(
        ..., description="The authenticated user's RBAC role."
    )
    employee_id: str = Field(
        ..., description="The authenticated user's corporate ID."
    )
    full_name: str = Field(
        ..., description="The authenticated user's full name."
    )
