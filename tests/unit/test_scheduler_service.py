import pytest
from unittest.mock import Mock, patch
from application.schedulers.scheduler_service import SchedulerService
from domain.entities.models import TaskStatus, TaskScheduleType

@pytest.fixture
def scheduler_service(di_container):
    task_repo = di_container.get_task_repository()
    task_executor = di_container.get_task_executor()
    result_repo = di_container.get_task_result_repository()
    confluence_repo = di_container.get_confluence_repository()
    
    return SchedulerService(
        task_repository=task_repo,
        task_executor=task_executor,
        task_result_repo=result_repo,
        confluence_updater=confluence_repo,
        poll_interval=1,
        max_concurrent_jobs=2,
        coalesce=True,
        max_instances=3
    )

def test_scheduler_initialization(scheduler_service):
    assert scheduler_service.poll_interval == 1
    assert scheduler_service.max_concurrent_jobs == 2
    assert scheduler_service.coalesce is True
    assert scheduler_service.max_instances == 3

def test_scheduler_start_stop(scheduler_service):
    scheduler_service.start()
    assert scheduler_service.scheduler.running is True
    
    scheduler_service.shutdown()
    assert scheduler_service.scheduler.running is False

def test_schedule_task(scheduler_service, sample_task):
    task = scheduler_service.task_repository.add_from_dict(sample_task)
    scheduler_service.schedule_task(task)
    
    # Verify task is scheduled
    scheduled_tasks = scheduler_service.scheduler.get_jobs()
    assert len(scheduled_tasks) > 0
    assert any(job.id == f"task_{task.id}" for job in scheduled_tasks)

def test_schedule_immediate_task(scheduler_service, sample_task):
    task = scheduler_service.task_repository.add_from_dict(sample_task)
    scheduler_service.schedule_task(task)
    
    # Verify immediate task is executed
    scheduled_tasks = scheduler_service.scheduler.get_jobs()
    assert len(scheduled_tasks) == 0  # Immediate tasks are not scheduled

def test_schedule_scheduled_task(scheduler_service, sample_scheduled_task):
    task = scheduler_service.task_repository.add_from_dict(sample_scheduled_task)
    scheduler_service.schedule_task(task)
    
    # Verify scheduled task is in scheduler
    scheduled_tasks = scheduler_service.scheduler.get_jobs()
    assert len(scheduled_tasks) > 0
    assert any(job.id == f"task_{task.id}" for job in scheduled_tasks)

def test_handle_task_execution_error(scheduler_service, sample_task):
    with patch.object(scheduler_service.task_executor, 'execute_task') as mock_execute:
        mock_execute.side_effect = Exception("Task execution failed")
        
        task = scheduler_service.task_repository.add_from_dict(sample_task)
        scheduler_service.schedule_task(task)
        
        # Verify error is handled and task status is updated
        updated_task = scheduler_service.task_repository.get_by_id(task.id)
        assert updated_task.status == TaskStatus.FAILED

def test_max_concurrent_jobs_limit(scheduler_service, sample_task):
    # Create multiple tasks
    tasks = []
    for i in range(5):  # More than max_concurrent_jobs
        task_dict = sample_task.copy()
        task_dict["name"] = f"Task {i}"
        task = scheduler_service.task_repository.add_from_dict(task_dict)
        tasks.append(task)
        scheduler_service.schedule_task(task)
    
    # Verify only max_concurrent_jobs are running
    running_tasks = [t for t in tasks if t.status == TaskStatus.RUNNING]
    assert len(running_tasks) <= scheduler_service.max_concurrent_jobs 