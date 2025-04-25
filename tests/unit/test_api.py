import pytest
from domain.entities.models import TaskStatus
from fastapi.testclient import TestClient

def test_list_tasks(test_client, sample_task):
    # First add a task
    task_repo = test_client.app.dependency_overrides["get_task_repository"]()
    task_repo.add_from_dict(sample_task)
    
    # Test the endpoint
    response = test_client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "data" in data
    assert len(data["data"]) > 0

def test_list_tasks_by_status(test_client, sample_task):
    # First add a task
    task_repo = test_client.app.dependency_overrides["get_task_repository"]()
    task = task_repo.add_from_dict(sample_task)
    
    # Test the endpoint
    response = test_client.get(f"/tasks/status/{TaskStatus.PENDING}")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "data" in data
    assert len(data["data"]) > 0
    assert any(t["id"] == task.id for t in data["data"])

def test_get_task_history(test_client, sample_task):
    # First add a task
    task_repo = test_client.app.dependency_overrides["get_task_repository"]()
    task = task_repo.add_from_dict(sample_task)
    
    # Execute the task to create history
    task_executor = test_client.app.dependency_overrides["get_task_executor"]()
    task_executor.execute_task(task.id)
    
    # Test the endpoint
    response = test_client.get("/task_history")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "data" in data
    assert len(data["data"]) > 0
    assert any(t["id"] == task.id for t in data["data"])

def test_invalid_status(test_client):
    response = test_client.get("/tasks/status/invalid_status")
    assert response.status_code == 422  # Validation error 