import pytest
from domain.entities.models import TaskStatus
from infrastructure.repositories.task_repository import TaskRepository

def test_add_task(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    task = task_repo.add_from_dict(sample_task)
    assert task.name == sample_task["name"]
    assert task.task_type == sample_task["task_type"]
    assert task.status == TaskStatus.PENDING

def test_get_task(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    added_task = task_repo.add_from_dict(sample_task)
    retrieved_task = task_repo.get_by_id(added_task.id)
    assert retrieved_task.id == added_task.id
    assert retrieved_task.name == added_task.name

def test_get_all_tasks(di_container, sample_task, sample_scheduled_task):
    task_repo = di_container.get_task_repository()
    task1 = task_repo.add_from_dict(sample_task)
    task2 = task_repo.add_from_dict(sample_scheduled_task)
    all_tasks = task_repo.get_all()
    assert len(all_tasks) >= 2
    task_ids = [t.id for t in all_tasks]
    assert task1.id in task_ids
    assert task2.id in task_ids

def test_get_by_status(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    task = task_repo.add_from_dict(sample_task)
    pending_tasks = task_repo.get_by_status(TaskStatus.PENDING)
    assert len(pending_tasks) > 0
    assert task.id in [t.id for t in pending_tasks]

def test_get_executed_tasks(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    task = task_repo.add_from_dict(sample_task)
    # Initially, no executed tasks
    executed_tasks = task_repo.get_executed_tasks()
    assert len(executed_tasks) == 0 