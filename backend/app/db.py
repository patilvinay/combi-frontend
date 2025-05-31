from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from .config import settings
from .models import Base, Measurement

# Get database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine with connection pooling
engine: Engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=settings.DEBUG  # Enable SQL query logging in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.
    
    Yields:
        Session: A database session
        
    Example:
        ```python
        def some_endpoint(db: Session = Depends(get_db)):
            # Use the database session
            measurements = db.query(Measurement).all()
            return measurements
        ```
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize the database by creating all tables and indexes."""
    Base.metadata.create_all(bind=engine)
    
    # Create additional indexes if needed
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_measurements_device_enqueued 
            ON measurements(device_id, enqueued_time DESC)
        """))
        conn.commit()
