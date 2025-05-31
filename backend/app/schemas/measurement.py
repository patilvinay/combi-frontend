from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from typing_extensions import Annotated

class PhaseData(BaseModel):
    """Schema for phase measurement data."""
    v: Optional[float] = Field(
        None,
        description="Voltage in volts (V)",
        example=220.5,
        ge=0,
        le=1000
    )
    i: Optional[float] = Field(
        None,
        description="Current in amperes (A)",
        example=5.2,
        ge=0,
        le=1000
    )
    p: Optional[float] = Field(
        None,
        description="Power in watts (W)",
        example=1144.5,
        ge=0
    )
    f: Optional[float] = Field(
        None,
        description="Frequency in hertz (Hz)",
        example=50.0,
        ge=0,
        le=100
    )
    pf: Optional[float] = Field(
        None,
        description="Power factor (0-1)",
        example=0.99,
        ge=0,
        le=1
    )

class MeasurementBase(BaseModel):
    """Base schema for measurement data."""
    device_id: str = Field(
        ...,
        description="Unique identifier for the IoT device",
        example="48:CA:43:36:71:04"
    )
    enqueued_time: datetime = Field(
        ...,
        description="Timestamp when the measurement was taken",
        example="2025-05-31T12:00:00Z"
    )
    phases: List[PhaseData] = Field(
        ...,
        description="List of phase measurements (up to 7 phases)",
        min_items=1,
        max_items=7
    )

class MeasurementCreate(MeasurementBase):
    """Schema for creating a new measurement."""
    pass

class Measurement(MeasurementBase):
    """Schema for returning measurement data."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MeasurementResponse(BaseModel):
    """Response schema for measurement operations."""
    success: bool
    message: str
    data: Optional[Measurement] = None
