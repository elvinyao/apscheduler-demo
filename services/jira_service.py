# -*- coding: utf-8 -*-

"""
JIRA service that orchestrates multiple calls to JiraHandler, for business logic.
All comments in English.
"""

from handlers.jira_handler import JiraHandler

class JiraService:
    """
    This class provides high-level JIRA-related business logic
    by orchestrating multiple calls to JiraHandler if needed.
    """

    def __init__(self, jira_handler: JiraHandler):
        """
        Initialize JiraService with a JiraHandler.
        """
        self.jira_handler = jira_handler

    def fetch_issues(self, jql: str) -> list:
        """
        Fetch issues matching the given JQL, return a simplified list of data for further processing.
        """
        issues = self.jira_handler.search_issues(jql)
        # You might parse each issue to get only the fields you need:
        simplified = []
        for i in issues:
            simplified.append({
                "key": i["key"],
                "summary": i["fields"].get("summary"),
                "status": i["fields"].get("status", {}).get("name", "N/A")
            })
        return simplified

    def add_comment_to_issue(self, issue_key: str, comment_text: str) -> None:
        """
        Add a comment to a given issue key.
        """
        self.jira_handler.add_comment(issue_key, comment_text)
