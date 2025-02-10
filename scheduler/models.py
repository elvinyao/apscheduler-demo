"""
models.py
Defines the SQLAlchemy models (tables) in your application.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)  # e.g., 'scheduled' or 'immediate'
    cron_expr = Column(String, nullable=True)   # e.g., "*/5 * * * *" for scheduled tasks
    status = Column(String, default='PENDING')  # e.g., 'PENDING', 'RUNNING', 'DONE', 'FAILED'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TaskOut(BaseModel):
    id: int
    name: str
    task_type: str
    cron_expr: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
