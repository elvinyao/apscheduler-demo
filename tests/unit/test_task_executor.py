import pytest
from domain.entities.models import TaskStatus
from application.use_cases.executor import TaskExecutor

def test_execute_task(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    result_repo = di_container.get_task_result_repository()
    task_executor = TaskExecutor(task_repo, result_repo, di_container)
    
    task = task_repo.add_from_dict(sample_task)
    result = task_executor.execute_task(task.id)
    
    assert result is not None
    assert result.task_id == task.id
    assert result.status in [TaskStatus.DONE, TaskStatus.FAILED]

def test_execute_nonexistent_task(di_container):
    task_repo = di_container.get_task_repository()
    result_repo = di_container.get_task_result_repository()
    task_executor = TaskExecutor(task_repo, result_repo, di_container)
    
    with pytest.raises(ValueError):
        task_executor.execute_task("nonexistent_id")

def test_execute_scheduled_task(di_container, sample_scheduled_task):
    task_repo = di_container.get_task_repository()
    result_repo = di_container.get_task_result_repository()
    task_executor = TaskExecutor(task_repo, result_repo, di_container)
    
    task = task_repo.add_from_dict(sample_scheduled_task)
    result = task_executor.execute_task(task.id)
    
    assert result is not None
    assert result.task_id == task.id
    assert result.status in [TaskStatus.DONE, TaskStatus.FAILED]

def test_task_execution_status_update(di_container, sample_task):
    task_repo = di_container.get_task_repository()
    result_repo = di_container.get_task_result_repository()
    task_executor = TaskExecutor(task_repo, result_repo, di_container)
    
    task = task_repo.add_from_dict(sample_task)
    task_executor.execute_task(task.id)
    
    updated_task = task_repo.get_by_id(task.id)
    assert updated_task.status in [TaskStatus.DONE, TaskStatus.FAILED] 