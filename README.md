# My Scheduler App - README

Welcome to **My Scheduler App**, a flexible and extensible framework for task scheduling and asynchronous execution in Python. This system integrates **APScheduler**, **FastAPI**, and a custom repository/executor design to manage tasks, either from a database or in-memory, with support for dynamic addition of tasks via REST APIs, Confluence pages, or external REST endpoints.

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Repository Structure](#repository-structure)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Usage](#usage)
   - [FastAPI Endpoints](#fastapi-endpoints)
   - [Scheduler Internals](#scheduler-internals)
8. [Extending the System](#extending-the-system)
   - [Custom Repository](#custom-repository)
   - [Custom Task Fetching](#custom-task-fetching)
9. [Technical Notes & Best Practices](#technical-notes--best-practices)
10. [Security & Privacy](#security--privacy)
11. [License](#license)

---

## 1. Overview
**My Scheduler App** is designed as a lightweight but powerful task scheduling solution leveraging APScheduler for flexible cron or interval-based execution, and FastAPI for a simple REST interface to manage and observe tasks.

Use Cases:
- Periodic tasks (cron-based) for data ingestion, backups, or other time-based jobs.
- On-demand tasks that must be triggered immediately.
- Multithreaded, concurrent execution with robust scheduling logic.
- Optionally fetch tasks from external sources (e.g., Confluence, custom REST APIs) and push them into an in-memory store or DB.

---

## 2. Features
1. **APScheduler Integration**: Run tasks in parallel with thread pools, schedule recurring jobs with cron strings, or trigger immediate tasks.
2. **FastAPI**: A simple REST API to list or eventually manipulate tasks.
3. **Repository Pattern**: A `TaskRepository` interface storing tasks in memory, easily replaced or extended (SQLAlchemy, Redis, etc.).
4. **Executor Abstraction**: `TaskExecutor` that simulates or implements real task logic, e.g., reading external data.
5. **Fetch Service**: Example `ExternalTaskFetcher` that demonstrates how to retrieve tasks from Confluence or REST APIs.
6. **Demo Data**: Automatic seeding of test tasks on startup for demonstration.

---

## 3. Repository Structure

```
scheduler/
├── __init__.py            # Package init
├── executor.py            # TaskExecutor class
├── fetch_service.py       # Example external data fetcher (Confluence, REST)
├── models.py              # Pydantic-based Task model (Task, TaskOut)
├── repository.py          # In-memory implementation of TaskRepository
├── service.py             # SchedulerService with APScheduler logic
.gitignore                 # Ignore file
app.py                     # Main FastAPI application
requirements.txt           # Python dependencies
```

Key files:
- **`app.py`**: Defines a FastAPI server, sets up endpoints, and starts the scheduler.
- **`scheduler/service.py`**: The core scheduling logic using APScheduler.
- **`scheduler/executor.py`**: Contains the logic to execute tasks (simulated in this example).
- **`scheduler/fetch_service.py`**: Example of pulling tasks from external sources.
- **`scheduler/repository.py`** & **`scheduler/models.py`**: Provide an in-memory data store for tasks.

---

## 4. Installation
1. Clone this repository:

```bash
git clone <your-repo-url> my-scheduler-app
cd my-scheduler-app
```

2. (Optional) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 5. Configuration
Currently, the system has no centralized config file. Instead, you configure:
- **In-memory or DB approach**: By default, we use an in-memory repository (`TaskRepository`) in `scheduler/repository.py`. You can integrate a custom storage (SQLAlchemy, Redis, etc.) by implementing a similar pattern.
- **APScheduler Settings**: In `scheduler/service.py`, the concurrency, interval, etc. are partially hardcoded. Modify them as needed or pass them from environment variables.
- **FastAPI**: Host and port settings can be changed in `app.py` where `uvicorn.run(...)` is called.

For more advanced usage, consider adding a YAML or JSON config file, as discussed in prior architecture references.

---

## 6. Running the Application

1. **Start the FastAPI server** (which also initializes the APScheduler background jobs):

```bash
python app.py
```

2. **Access the REST endpoint** in your browser or a tool like curl:

- `GET /tasks` to see the list of tasks (JSON array of tasks).

You will see logs on the console about tasks being seeded (the default two tasks), scheduler starting, etc.

---

## 7. Usage

### 7.1 FastAPI Endpoints
- **`GET /tasks`**: Returns the array of tasks currently stored (whether scheduled or immediate). For each task, you get `id`, `name`, `task_type`, `cron_expr`, `status`, `created_at`, `updated_at`.

### 7.2 Scheduler Internals
- **Periodic Poll**: Every 30 seconds, `SchedulerService` polls for tasks with `status='PENDING'`. If it detects a `task_type='scheduled'` with a valid `cron_expr`, it sets up a recurring APScheduler job. If `task_type='immediate'`, it schedules a one-off job to run immediately.
- **Executing a Task**: The job calls `task_executor.execute_task(task_id)`. Inside `TaskExecutor`, we mark the task as `RUNNING`, simulate some work (`time.sleep(3)`), then set it to `DONE`.
- **read_data**: Another job (`read_data`) is scheduled every minute to simulate data ingestion.
- **fetch_from_confluence**: A demonstration job that fetches tasks from a Confluence or REST endpoint every minute. (It’s currently commented or set to `*/1 * * * *`. Adjust as needed.)

---

## 8. Extending the System

### 8.1 Custom Repository
The `scheduler/repository.py` file uses an **in-memory** list of tasks. You can create a new repository class implementing the same interface (e.g., `add_task`, `get_pending_tasks`, `update_task_status`, etc.) but storing tasks in a real database:

```python
class SQLAlchemyTaskRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        # ...
    # etc...
```

Then swap it in `app.py`:

```python
# Instead of TaskRepository()
# task_repo = SQLAlchemyTaskRepository(SessionLocal)
```

### 8.2 Custom Task Fetching
For more complex logic retrieving tasks from external systems, see `scheduler/fetch_service.py`. You can schedule a job that calls `fetcher.fetch_from_confluence()` at some desired interval.

```python
self.scheduler.add_job(
    func=self.fetcher.fetch_from_confluence,
    trigger=CronTrigger.from_crontab('0 * * * *'),  # every hour
    id='fetch_confluence_job'
)
```

Adjust the data transformation in `_save_tasks()` to match your table schema or repository.

---

## 9. Technical Notes & Best Practices
1. **Concurrency**: By default, APScheduler is configured with a thread pool (`ThreadPoolExecutor`) of size 5. Increase or decrease in `service.py`.
2. **APScheduler**: We use a `BackgroundScheduler`. If you want persistent scheduling (keeping job definitions across restarts), consider using job stores (e.g., SQLAlchemyJobStore).
3. **Task Identification**: The example uses integer IDs, but you can adapt to UUIDs or any unique ID scheme.
4. **Logging**: This demo uses `print()`. For production, consider Python’s `logging` library with levels and handlers.
5. **Error Handling**: On task exceptions, we set the status to `FAILED`. You can extend to add retries or error notifications.
6. **Security**: If fetching tasks or data from an external system, secure your credentials (not shown in these code examples). Also, ensure your FastAPI endpoints are protected if necessary.

---

## 10. Security & Privacy
- Treat all credentials (database, Confluence auth, etc.) as private. Use environment variables or a secure vault in production.
- If tasks contain sensitive data, ensure your repository (in-memory or DB) is handled accordingly, e.g., encryption at rest, restricted access.
- Rate limit or authenticate your FastAPI endpoints to prevent unauthorized usage in production.

---

## 11. License
This code base is provided for demonstration and internal usage. Please consult your organization’s guidelines on licensing if you plan to distribute or open-source it.

---

### Final Remarks

`My Scheduler App` provides a modular, easily extensible blueprint for scheduling tasks in Python. By combining APScheduler’s flexibility, FastAPI’s simplicity, and a well-defined repository/executor pattern, you can quickly integrate scheduling into your application. Feel free to adapt the code to your environment—switching from in-memory storage to a production database, hooking into external APIs, and customizing concurrency settings.

Enjoy building with `My Scheduler App`!

