from datetime import datetime, timezone
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
    enqueued_time: str = Field(
        ...,
        description="Timestamp when the measurement was taken in ISO 8601 format with 'Z' timezone (e.g., 2025-05-31T12:00:00Z)",
        example="2025-05-31T12:00:00Z",
        pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$'
    )
    
    @validator('enqueued_time')
    def validate_iso8601_utc(cls, v):
        """Validate that the timestamp is in ISO 8601 format with 'Z' timezone."""
        try:
            # Try to parse the datetime to ensure it's valid
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Ensure it's in UTC (ends with Z)
            if not v.endswith('Z'):
                raise ValueError("Timestamp must end with 'Z' for UTC")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 UTC timestamp format: {e}")
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
    enqueued_time: str  # Override to ensure string output

    class Config:
        orm_mode = True
        
    @validator('enqueued_time', pre=True)
    def format_enqueued_time(cls, v):
        """Convert datetime to ISO 8601 string with 'Z' timezone."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            return v.isoformat().replace('+00:00', 'Z')
        return v

class MeasurementResponse(BaseModel):
    """Response schema for measurement operations."""
    success: bool
    message: str
    data: Optional[Measurement] = None
