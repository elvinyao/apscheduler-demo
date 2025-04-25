import pytest
from fastapi.testclient import TestClient
from app import create_app
from domain.entities.models import TaskStatus, TaskScheduleType
from application.di_container import DIContainer
from infrastructure.config.config import load_config
from settings import get_settings

@pytest.fixture
def test_config():
    return load_config("./config.yaml")

@pytest.fixture
def di_container():
    """Provide DIContainer built with global Settings."""
    return DIContainer(get_settings())

@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def sample_task():
    return {
        "name": "Test Task",
        "task_type": TaskScheduleType.IMMEDIATE,
        "tags": ["TEST"],
        "parameters": {
            "test_param": "value"
        }
    }

@pytest.fixture
def sample_scheduled_task():
    return {
        "name": "Scheduled Test Task",
        "task_type": TaskScheduleType.SCHEDULED,
        "cron_expr": "0 0 * * *",
        "tags": ["TEST"],
        "parameters": {
            "test_param": "value"
        }
    }
