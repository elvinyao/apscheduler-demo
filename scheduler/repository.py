"""
repository.py
Encapsulates all database operations for Task entities.
"""

from scheduler.models import Task
from scheduler.database import SessionLocal

class TaskRepository:
    """
    Encapsulates all database-related operations for Task.
    """
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def get_task_by_id(self, task_id):
        session = self.session_factory()
        try:
            return session.query(Task).filter(Task.id == task_id).one_or_none()
        finally:
            session.close()

    def get_pending_tasks(self):
        session = self.session_factory()
        try:
            return session.query(Task).filter(Task.status == 'PENDING').all()
        finally:
            session.close()

    def update_task_status(self, task_id, new_status):
        session = self.session_factory()
        try:
            task = session.query(Task).filter(Task.id == task_id).one_or_none()
            if task:
                task.status = new_status
                session.commit()
        finally:
            session.close()

    def seed_demo_data(self):
        """
        Populate the database with example tasks for demonstration.
        """
        # Ensure the DB has the tables created
        from scheduler.models import Base
        from scheduler.database import engine
        Base.metadata.create_all(engine)

        session = self.session_factory()
        try:
            # Add only if table is empty
            if not session.query(Task).first():
                scheduled_task = Task(
                    name="Scheduled DB Cleanup",
                    task_type="scheduled",
                    cron_expr="* * * * *"  # runs every minute for demo
                )
                immediate_task = Task(
                    name="One-off Job",
                    task_type="immediate"
                )
                session.add_all([scheduled_task, immediate_task])
                session.commit()
        finally:
            session.close()
