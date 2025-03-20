import pytest
from unittest.mock import Mock, patch
from application.services.result_reporting_service import ResultReportingService
from domain.entities.models import TaskStatus

@pytest.fixture
def result_reporting_service(di_container):
    result_repo = di_container.get_task_result_repository()
    confluence_repo = di_container.get_confluence_repository()
    return ResultReportingService(result_repo, confluence_repo)

def test_report_task_result(result_reporting_service, sample_task):
    # Create a task result
    task = result_reporting_service.result_repo.add_from_dict(sample_task)
    result = result_reporting_service.result_repo.create_result(
        task_id=task.id,
        status=TaskStatus.DONE,
        output={"message": "Task completed successfully"}
    )
    
    # Report the result
    result_reporting_service.report_result(result)
    
    # Verify result was reported
    reported_results = result_reporting_service.result_repo.get_by_task_id(task.id)
    assert len(reported_results) > 0
    assert reported_results[0].status == TaskStatus.DONE

def test_report_failed_task(result_reporting_service, sample_task):
    # Create a failed task result
    task = result_reporting_service.result_repo.add_from_dict(sample_task)
    result = result_reporting_service.result_repo.create_result(
        task_id=task.id,
        status=TaskStatus.FAILED,
        output={"error": "Task failed"}
    )
    
    # Report the result
    result_reporting_service.report_result(result)
    
    # Verify failure was reported
    reported_results = result_reporting_service.result_repo.get_by_task_id(task.id)
    assert len(reported_results) > 0
    assert reported_results[0].status == TaskStatus.FAILED

def test_update_confluence_report(result_reporting_service, sample_task):
    with patch.object(result_reporting_service.confluence_repo, 'update_report') as mock_update:
        # Create a task result
        task = result_reporting_service.result_repo.add_from_dict(sample_task)
        result = result_reporting_service.result_repo.create_result(
            task_id=task.id,
            status=TaskStatus.DONE,
            output={"message": "Task completed"}
        )
        
        # Update Confluence report
        result_reporting_service.update_confluence_report(result)
        
        # Verify Confluence was updated
        mock_update.assert_called_once()

def test_handle_reporting_error(result_reporting_service, sample_task):
    with patch.object(result_reporting_service.confluence_repo, 'update_report') as mock_update:
        mock_update.side_effect = Exception("Confluence update failed")
        
        # Create a task result
        task = result_reporting_service.result_repo.add_from_dict(sample_task)
        result = result_reporting_service.result_repo.create_result(
            task_id=task.id,
            status=TaskStatus.DONE,
            output={"message": "Task completed"}
        )
        
        # Attempt to update Confluence report
        result_reporting_service.update_confluence_report(result)
        
        # Verify error was handled gracefully
        reported_results = result_reporting_service.result_repo.get_by_task_id(task.id)
        assert len(reported_results) > 0
        assert reported_results[0].status == TaskStatus.DONE

def test_get_task_history(result_reporting_service, sample_task):
    # Create multiple results for the same task
    task = result_reporting_service.result_repo.add_from_dict(sample_task)
    result1 = result_reporting_service.result_repo.create_result(
        task_id=task.id,
        status=TaskStatus.DONE,
        output={"message": "First run"}
    )
    result2 = result_reporting_service.result_repo.create_result(
        task_id=task.id,
        status=TaskStatus.FAILED,
        output={"error": "Second run failed"}
    )
    
    # Get task history
    history = result_reporting_service.get_task_history(task.id)
    assert len(history) == 2
    assert history[0].status == TaskStatus.DONE
    assert history[1].status == TaskStatus.FAILED 