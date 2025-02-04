# -*- coding: utf-8 -*-

"""
The `ScheduledTask` class is an ORM model for storing scheduled tasks in the database. It has the following fields:

- `id`: An auto-incrementing integer primary key.
- `task_id`: A unique string identifier for the task.
- `schedule_time`: A string representing the scheduled time for the task, in the format "HH:MM".
- `payload`: A text field for storing serialized data related to the task.
- `status`: A string representing the status of the task, defaulting to "pending".
- `created_at`: A datetime field representing the time the task was created.
- `updated_at`: A datetime field representing the last time the task was updated.

The `get_db_url()` function returns the database URL, which is set to use a local SQLite file by default.

The `init_db()` function creates the necessary database tables if they don't already exist.

The `add_or_update_tasks()` function inserts or updates tasks in the database, based on a list of dictionaries containing task information.

The `fetch_due_tasks()` function returns a list of `ScheduledTask` objects that have a `schedule_time` matching the provided `now_str` and a status of "pending".

The `mark_task_done()` function updates the status of a task with the given `task_id` to either "done" or "failed".
"""

import os
import datetime
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ScheduledTask(Base):
    """
    ORM model for storing scheduled tasks in the database.
    """
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, unique=True, index=True)
    # "HH:MM" format or use DateTime if you prefer
    schedule_time = Column(String)
    payload = Column(Text)          # store JSON or other serialized data
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


def get_db_url() -> str:
    """
    Return the database URL, here we use local SQLite by default.
    Could also parse from environment or config if needed.
    """
    return "sqlite:///./database/tasks.db"


engine = create_engine(get_db_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Create tables if not exist. Called once at startup.
    """
    Base.metadata.create_all(bind=engine)


def add_or_update_tasks(tasks: List[Dict]) -> None:
    """
    Insert or update tasks read from Confluence.
    :param tasks: A list of dicts, e.g. [{"task_id": "...", "schedule_time": "HH:MM", "description": "..."}]
    We store the entire dict in payload, and keep schedule_time for easy querying.
    """
    session = SessionLocal()
    try:
        for t in tasks:
            # Convert 't' to string (JSON, for example) or handle in a more robust way
            import json
            payload_json = json.dumps(t, ensure_ascii=False)

            existing = session.query(ScheduledTask).filter_by(
                task_id=t["task_id"]).first()
            if existing:
                existing.schedule_time = t["schedule_time"]
                existing.payload = payload_json
                existing.status = "pending"
            else:
                new_task = ScheduledTask(
                    task_id=t["task_id"],
                    schedule_time=t["schedule_time"],
                    payload=payload_json,
                    status="pending"
                )
                session.add(new_task)
        session.commit()
    finally:
        session.close()


def fetch_due_tasks(now_str: str) -> List[ScheduledTask]:
    """
    Return tasks that match schedule_time == now_str and status == 'pending'.
    """
    session = SessionLocal()
    try:
        results = session.query(ScheduledTask).filter_by(
            schedule_time=now_str,
            status="pending"
        ).all()
        return results
    finally:
        session.close()


def mark_task_done(task_id: str, status: str = "done") -> None:
    """
    Update the status of the given task_id to 'done' (or 'failed').
    """
    session = SessionLocal()
    try:
        task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
        if task:
            task.status = status
            session.commit()
    finally:
        session.close()
