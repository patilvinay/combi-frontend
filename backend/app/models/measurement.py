from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Measurement(Base):
    """
    SQLAlchemy model for storing time series measurements from IoT devices.
    Each measurement can have up to 7 phases, with each phase containing:
    - v: Voltage (V)
    - i: Current (A)
    - p: Power (W)
    - f: Frequency (Hz)
    - pf: Power Factor (0-1)
    """
    __tablename__ = "measurements"
    __table_args__ = (
        # Create indexes for common query patterns
        Index('idx_measurements_device_id', 'device_id'),
        Index('idx_measurements_enqueued_time', 'enqueued_time'),
        Index('idx_measurements_created_at', 'created_at'),
        {'comment': 'Stores time series measurements from IoT devices'}
    )

    id = Column(Integer, primary_key=True, index=True, comment="Unique identifier")
    device_id = Column(String(50), nullable=False, index=True, comment="Device identifier (e.g., MAC address)")
    enqueued_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="Timestamp when the measurement was taken")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp when the record was created in the database")
    
    # Phase 1 measurements
    v1 = Column(Float, nullable=True, comment="Voltage phase 1 (V)")
    i1 = Column(Float, nullable=True, comment="Current phase 1 (A)")
    p1 = Column(Float, nullable=True, comment="Power phase 1 (W)")
    f1 = Column(Float, nullable=True, comment="Frequency phase 1 (Hz)")
    pf1 = Column(Float, nullable=True, comment="Power Factor phase 1 (0-1)")
    
    # Phase 2 measurements
    v2 = Column(Float, nullable=True, comment="Voltage phase 2 (V)")
    i2 = Column(Float, nullable=True, comment="Current phase 2 (A)")
    p2 = Column(Float, nullable=True, comment="Power phase 2 (W)")
    f2 = Column(Float, nullable=True, comment="Frequency phase 2 (Hz)")
    pf2 = Column(Float, nullable=True, comment="Power Factor phase 2 (0-1)")
    
    # Phase 3 measurements
    v3 = Column(Float, nullable=True, comment="Voltage phase 3 (V)")
    i3 = Column(Float, nullable=True, comment="Current phase 3 (A)")
    p3 = Column(Float, nullable=True, comment="Power phase 3 (W)")
    f3 = Column(Float, nullable=True, comment="Frequency phase 3 (Hz)")
    pf3 = Column(Float, nullable=True, comment="Power Factor phase 3 (0-1)")
    
    # Phase 4 measurements
    v4 = Column(Float, nullable=True, comment="Voltage phase 4 (V)")
    i4 = Column(Float, nullable=True, comment="Current phase 4 (A)")
    p4 = Column(Float, nullable=True, comment="Power phase 4 (W)")
    f4 = Column(Float, nullable=True, comment="Frequency phase 4 (Hz)")
    pf4 = Column(Float, nullable=True, comment="Power Factor phase 4 (0-1)")
    
    # Phase 5 measurements
    v5 = Column(Float, nullable=True, comment="Voltage phase 5 (V)")
    i5 = Column(Float, nullable=True, comment="Current phase 5 (A)")
    p5 = Column(Float, nullable=True, comment="Power phase 5 (W)")
    f5 = Column(Float, nullable=True, comment="Frequency phase 5 (Hz)")
    pf5 = Column(Float, nullable=True, comment="Power Factor phase 5 (0-1)")
    
    # Phase 6 measurements
    v6 = Column(Float, nullable=True, comment="Voltage phase 6 (V)")
    i6 = Column(Float, nullable=True, comment="Current phase 6 (A)")
    p6 = Column(Float, nullable=True, comment="Power phase 6 (W)")
    f6 = Column(Float, nullable=True, comment="Frequency phase 6 (Hz)")
    pf6 = Column(Float, nullable=True, comment="Power Factor phase 6 (0-1)")
    
    # Phase 7 measurements
    v7 = Column(Float, nullable=True, comment="Voltage phase 7 (V)")
    i7 = Column(Float, nullable=True, comment="Current phase 7 (A)")
    p7 = Column(Float, nullable=True, comment="Power phase 7 (W)")
    f7 = Column(Float, nullable=True, comment="Frequency phase 7 (Hz)")
    pf7 = Column(Float, nullable=True, comment="Power Factor phase 7 (0-1)")
