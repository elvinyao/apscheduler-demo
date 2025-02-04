# -*- coding: utf-8 -*-

"""
This class encapsulates low-level JIRA operations using the atlassian-python-api library.
It provides methods to retrieve JIRA issues, search for issues using JQL, and add comments to issues.
"""

from atlassian import Jira

class JiraHandler:
    """
    This class encapsulates low-level JIRA operations using atlassian-python-api.
    """

    def __init__(self, jira_url: str, username: str = None, password: str = None, token: str = None):
        """
        Initialize JiraHandler with credentials or token.
        """
        self.client = Jira(
            url=jira_url,
            username=username,
            password=password,
            token=token
        )

    def get_issue(self, issue_key: str) -> dict:
        """
        Retrieve detailed issue info by issue_key.
        """
        return self.client.issue(issue_key)

    def search_issues(self, jql: str) -> list:
        """
        Search for issues matching the provided JQL.
        Returns a list of issues.
        """
        result = self.client.jql(jql)
        return result.get('issues', [])

    def add_comment(self, issue_key: str, comment: str) -> None:
        """
        Add a comment to a JIRA issue.
        """
        self.client.issue_add_comment(issue_key, comment)
