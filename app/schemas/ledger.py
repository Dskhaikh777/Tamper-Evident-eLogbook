"""
Pydantic schemas for LogRecord input validation and response serialization.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LogRecordCreate(BaseModel):
    """
    Schema for creating a new log record.

    The client supplies only the operational fields; the server
    generates the timestamp, hashes, and ID automatically.
    """

    operator_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier of the operator creating the entry.",
        examples=["OP-4521"],
    )
    action_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the action performed.",
        examples=["PM", "Calibration", "Inspection"],
    )
    data_payload: str = Field(
        ...,
        min_length=1,
        description="Free-form text describing the action details.",
        examples=["Replaced pressure sensor on Line 3."],
    )


class LogRecordResponse(BaseModel):
    """
    Schema for returning a log record to the client.

    Includes all server-generated fields (id, timestamp, hashes)
    alongside the original input data.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    operator_id: str
    timestamp: datetime
    action_type: str
    data_payload: str
    previous_hash: str
    current_hash: str
