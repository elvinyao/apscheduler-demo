import logging
import time
from integration.jira_service import JiraService

class JiraDataProcessor:
    """
    Contains business logic to interpret and respond to JIRA data.
    Delegates real JIRA calls to JiraService (integration).
    """
    def __init__(self, jira_service: JiraService):
        self.jira_service = jira_service

    def check_and_process_tickets(self, jql: str) -> bool:
        """
        Example domain logic: run a JQL, parse results,
        and decide if further action is needed.
        """
        logging.info("Checking JIRA tickets with JQL: %s", jql)
        issues = self.jira_service.search_issues(jql, fetch_all=True)

        if not issues:
            logging.info("No matching issues for JQL: %s", jql)
            return False

        logging.info("Found %d issues. Checking last comments...", len(issues))
        time.sleep(0.5)  # domain-level logic or transformations

        # Suppose we find we need post-processing if any issue has a special marker
        need_post_process = any("SPECIAL_MARKER" in i.get('fields', {}).get('description', '')
                                for i in issues)
        return need_post_process
