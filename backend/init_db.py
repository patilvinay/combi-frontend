import sys
import os
from sqlalchemy import create_engine
from app.db import Base, SQLALCHEMY_DATABASE_URL

def init_db():
    print("Initializing database...")
    # Create all tables
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
