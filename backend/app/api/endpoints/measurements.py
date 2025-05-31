from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from app import models
from app.schemas import measurement as schemas
from app.db import get_db
from app.api.deps import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])


def map_phase_data(phase_num: int, phase: schemas.PhaseData) -> Dict[str, float]:
    """Map phase data to database columns."""
    return {
        f"v{phase_num}": phase.v,
        f"i{phase_num}": phase.i,
        f"p{phase_num}": phase.p,
        f"f{phase_num}": phase.f,
        f"pf{phase_num}": phase.pf
    }

@router.post(
    "/",
    response_model=schemas.Measurement,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new measurement",
    description="Store a new measurement with voltage, current, power, frequency, and power factor for each phase."
)
async def create_measurement(
    measurement: schemas.MeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new measurement entry with the following parameters per phase:
    - v: Voltage (V)
    - i: Current (A)
    - p: Power (W)
    - f: Frequency (Hz)
    - pf: Power Factor (0-1)
    """
    # Create a dictionary with all phase data
    data = {
        "device_id": measurement.device_id,
        "enqueued_time": measurement.enqueued_time
    }
    
    # Add phase data for each phase (up to 7 phases)
    for i, phase in enumerate(measurement.phases, 1):
        if i > 7:  # We only support up to 7 phases
            break
        data.update(map_phase_data(i, phase))
    
    try:
        # Create and save the measurement
        db_measurement = models.Measurement(**data)
        db.add(db_measurement)
        db.commit()
        db.refresh(db_measurement)
        
        # Convert the database model to a Pydantic model to include all fields
        measurement_dict = db_measurement.__dict__.copy()
        
        # Add phases to the response
        phases = []
        for i in range(1, 8):
            v = measurement_dict.get(f'v{i}')
            if v is not None:
                phase_data = {
                    'v': v,
                    'i': measurement_dict.get(f'i{i}'),
                    'p': measurement_dict.get(f'p{i}'),
                    'f': measurement_dict.get(f'f{i}'),
                    'pf': measurement_dict.get(f'pf{i}')
                }
                phases.append(phase_data)
        
        # Create the response with all fields
        response = {
            'id': measurement_dict['id'],
            'device_id': measurement_dict['device_id'],
            'enqueued_time': measurement_dict['enqueued_time'],
            'created_at': measurement_dict['created_at'],
            'phases': phases
        }
        
        return response
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving measurement: {str(e)}"
        )

@router.get(
    "/latest/{device_id}",
    response_model=schemas.Measurement,
    summary="Get latest measurement",
    description="Retrieve the most recent measurement for a specific device."
)
async def get_latest_measurement(
    device_id: str,
    db: Session = Depends(get_db)
):
    # Get the most recent measurement for the device
    measurement = db.query(models.Measurement)\
        .filter(models.Measurement.device_id == device_id)\
        .order_by(models.Measurement.enqueued_time.desc())\
        .first()
    
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No measurements found for device {device_id}"
        )
    
    # Convert the database model to a dictionary
    measurement_dict = measurement.__dict__.copy()
    
    # Add phases to the response
    phases = []
    for i in range(1, 8):
        v = measurement_dict.get(f'v{i}')
        if v is not None:
            phase_data = {
                'v': v,
                'i': measurement_dict.get(f'i{i}'),
                'p': measurement_dict.get(f'p{i}'),
                'f': measurement_dict.get(f'f{i}'),
                'pf': measurement_dict.get(f'pf{i}')
            }
            phases.append(phase_data)
    
    # Create the response with all fields
    response = {
        'id': measurement_dict['id'],
        'device_id': measurement_dict['device_id'],
        'enqueued_time': measurement_dict['enqueued_time'],
        'created_at': measurement_dict['created_at'],
        'phases': phases
    }
    
    return response

@router.get(
    "/recent/{device_id}",
    response_model=List[schemas.Measurement],
    summary="Get recent measurements",
    description="Get measurements from the last N hours for a specific device. Default is 2 hours if not specified."
)
async def get_recent_measurements(
    device_id: str,
    hours: int = 2,
    db: Session = Depends(get_db)
):
    """
    Get measurements from the last N hours for a specific device.
    Default is 2 hours if not specified.
    """
    if hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours parameter must be greater than 0"
        )
    # Calculate the time threshold
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Query measurements within the time threshold
    db_measurements = (
        db.query(models.Measurement)
        .filter(
            models.Measurement.device_id == device_id,
            models.Measurement.enqueued_time >= time_threshold
        )
        .order_by(models.Measurement.enqueued_time.desc())
        .all()
    )
    
    if not db_measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No measurements found for device {device_id} in the last {hours} hours"
        )
    
    # Convert database models to response format
    measurements = []
    for measurement in db_measurements:
        measurement_dict = measurement.__dict__.copy()
        
        # Add phases to the response
        phases = []
        for i in range(1, 8):
            v = measurement_dict.get(f'v{i}')
            if v is not None:
                phase_data = {
                    'v': v,
                    'i': measurement_dict.get(f'i{i}'),
                    'p': measurement_dict.get(f'p{i}'),
                    'f': measurement_dict.get(f'f{i}'),
                    'pf': measurement_dict.get(f'pf{i}')
                }
                phases.append(phase_data)
        
        # Create the response with all fields
        response = {
            'id': measurement_dict['id'],
            'device_id': measurement_dict['device_id'],
            'enqueued_time': measurement_dict['enqueued_time'],
            'created_at': measurement_dict['created_at'],
            'phases': phases
        }
        measurements.append(response)
    
    return measurements

@router.get(
    "/range/{device_id}",
    response_model=List[schemas.Measurement],
    summary="Get measurements in time range",
    description="Retrieve measurements within a specific time range for a specific device."
)
async def get_measurements_in_range(
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    """
    Get measurements within a specific time range for a specific device.
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Build and execute the query
    db_measurements = db.query(models.Measurement).filter(
        models.Measurement.device_id == device_id,
        models.Measurement.enqueued_time >= start_time,
        models.Measurement.enqueued_time <= end_time
    ).order_by(models.Measurement.enqueued_time.asc()).all()
    
    if not db_measurements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No measurements found for device {device_id} in the specified time range"
        )
    
    # Convert database models to response format
    measurements = []
    for measurement in db_measurements:
        measurement_dict = measurement.__dict__.copy()
        
        # Add phases to the response
        phases = []
        for i in range(1, 8):
            v = measurement_dict.get(f'v{i}')
            if v is not None:
                phase_data = {
                    'v': v,
                    'i': measurement_dict.get(f'i{i}'),
                    'p': measurement_dict.get(f'p{i}'),
                    'f': measurement_dict.get(f'f{i}'),
                    'pf': measurement_dict.get(f'pf{i}')
                }
                phases.append(phase_data)
        
        # Create the response with all fields
        response = {
            'id': measurement_dict['id'],
            'device_id': measurement_dict['device_id'],
            'enqueued_time': measurement_dict['enqueued_time'],
            'created_at': measurement_dict['created_at'],
            'phases': phases
        }
        measurements.append(response)
    
    return measurements
