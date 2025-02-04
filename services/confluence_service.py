# -*- coding: utf-8 -*-

"""
Confluence service that orchestrates multiple calls to ConfluenceHandler.
All comments in English.
"""

from handlers.confluence_handler import ConfluenceHandler

class ConfluenceService:
    """
    This class provides high-level Confluence-related business logic.
    """

    def __init__(self, confluence_handler: ConfluenceHandler):
        """
        Initialize ConfluenceService with a ConfluenceHandler.
        """
        self.confluence_handler = confluence_handler

    def fetch_tasks_from_page(self, page_id: str) -> list:
        """
        Fetch and parse tasks from a given Confluence page.
        For demonstration, returns a mocked list or partial parse.
        """
        content = self.confluence_handler.get_page_content(page_id)
        # Here you might parse the HTML to find table rows or macros.
        # For now, we return a simple mock:
        tasks = [
            {"task_id": "cfx-1", "schedule_time": "10:00", "description": "Example from Confluence."},
            {"task_id": "cfx-2", "schedule_time": "11:00", "description": "Another example."}
        ]
        return tasks
