# -*- coding: utf-8 -*-

"""
TaskReader module that fetches tasks from ConfluenceService or other sources.
All comments in English.
"""

from services.confluence_service import ConfluenceService
import datetime

class TaskReader:
    """
    Reads tasks from Confluence or other data sources on a scheduled basis.
    """

    def __init__(self, confluence_service: ConfluenceService):
        """
        Initialize TaskReader with a ConfluenceService.
        """
        self.confluence_service = confluence_service

    def read_tasks_from_confluence(self, page_id: str) -> list:
        """
        Read tasks from a given Confluence page (via confluence_service).
        Returns a list of tasks with schedule_time, etc.
        """
        tasks = self.confluence_service.fetch_tasks_from_page(page_id)
        # Optionally process or filter tasks. For now, just return them.
        return tasks
