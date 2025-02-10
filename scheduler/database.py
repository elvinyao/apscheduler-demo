"""
database.py
Handles the creation of the SQLAlchemy engine and session maker.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# For demo, use an in-memory SQLite database.
# Replace with your real database connection string in production.
DATABASE_URL = "sqlite+pysqlite:///:memory:"

# Create the engine
engine = create_engine(DATABASE_URL, echo=False)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(bind=engine)
