"""
examples/demo_tasks.py

Provides a helper that returns a list of demo task dictionaries
which can be used to seed the TaskRepository during development
or unit tests. Moving the verbose sample-data out of *app.py*
keeps application boot code clean and focused on wiring.
"""

from domain.entities.models import TaskScheduleType, TaskTags


def get_demo_tasks() -> list[dict]:
    """Return a list of demo task definitions."""

    # 1) Root ticket extraction
    root_ticket_task = {
        "name": "JIRA Extraction - Root Ticket",
        "task_type": TaskScheduleType.IMMEDIATE,
        "tags": [TaskTags.JIRA_TASK_EXP],
        "parameters": {
            "jira_envs": ["env1.jira.com", "env2.jira.com"],
            "key_type": "root_ticket",
            "key_value": "PROJ-123",
            "user": "johndoe",
        },
    }

    # 2) Project extraction
    project_task = {
        "name": "JIRA Extraction - Project",
        "task_type": TaskScheduleType.IMMEDIATE,
        "cron_expr": "0 0 * * *",  # Every day at midnight
        "tags": [TaskTags.JIRA_TASK_EXP],
        "parameters": {
            "jira_envs": ["env1.jira.com"],
            "key_type": "project",
            "key_value": "PROJ",
            "user": "johndoe",
        },
    }

    # 3) Bulk create Jira tickets
    bulk_jira_task = {
        "name": "批量创建Jira tickets",
        "task_type": TaskScheduleType.IMMEDIATE,
        "tags": [TaskTags.BULK_JIRA_TASK],
        "parameters": {
            "operation_type": "create",
            "max_workers": 4,
            "tickets_data": [
                {
                    "fields": {
                        "project": {"key": "PROJ"},
                        "issuetype": {"name": "Task"},
                        "summary": "示例任务1",
                        "description": "这是示例任务1的描述",
                        "priority": {"name": "Medium"},
                    }
                },
                {
                    "fields": {
                        "project": {"key": "PROJ"},
                        "issuetype": {"name": "Task"},
                        "summary": "示例任务2",
                        "description": "这是示例任务2的描述",
                        "priority": {"name": "High"},
                    }
                },
                {
                    "fields": {
                        "project": {"key": "PROJ"},
                        "issuetype": {"name": "Bug"},
                        "summary": "示例Bug1",
                        "description": "这是示例Bug1的描述",
                        "priority": {"name": "High"},
                    }
                },
            ],
        },
    }

    # 4) Linked Jira tickets (hierarchical)
    linked_jira_task = {
        "name": "创建层级结构Jira tickets",
        "task_type": TaskScheduleType.IMMEDIATE,
        "tags": [TaskTags.BULK_JIRA_TASK],
        "parameters": {
            "operation_type": "create",
            "max_workers": 3,
            "is_linked": True,  # hierarchical task flag
            "tickets_data": {
                "root": {
                    "fields": {
                        "project": {"key": "PROJ"},
                        "issuetype": {"name": "Epic"},
                        "summary": "根Epic任务",
                        "description": "这是一个根Epic任务",
                        "priority": {"name": "High"},
                    }
                },
                "children": [
                    {
                        "fields": {
                            "project": {"key": "PROJ"},
                            "issuetype": {"name": "Task"},
                            "summary": "子任务1",
                            "description": "这是子任务1的描述",
                            "priority": {"name": "Medium"},
                        }
                    },
                    {
                        "fields": {
                            "project": {"key": "PROJ"},
                            "issuetype": {"name": "Task"},
                            "summary": "子任务2",
                            "description": "这是子任务2的描述",
                            "priority": {"name": "Medium"},
                        }
                    },
                    {
                        "fields": {
                            "project": {"key": "PROJ"},
                            "issuetype": {"name": "Bug"},
                            "summary": "相关Bug",
                            "description": "这是相关Bug的描述",
                            "priority": {"name": "High"},
                        }
                    },
                ],
            },
        },
    }

    return [
        root_ticket_task,
        project_task,
        bulk_jira_task,
        linked_jira_task,
    ]
