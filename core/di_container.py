# Add a new file: core/di_container.py
from typing import Dict, Any
from domain.result_reporter import ResultReporter
from integration.confluence_service import ConfluenceService
from integration.jira_service import JiraService
from domain.confluence_data_processor import ConfluenceDataProcessor
from domain.jira_data_processor import JiraDataProcessor
from domain.mattermost_data_processor import MattermostDataProcessor

class DIContainer:
    """Dependency Injection container to manage service initialization."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._services = {}
        
    def get_confluence_service(self) -> ConfluenceService:
        if 'confluence_service' not in self._services:
            conf_config = self.config.get('confluence', {})
            self._services['confluence_service'] = ConfluenceService(
                url=conf_config.get('url'),
                username=conf_config.get('username'),
                password=conf_config.get('password')
            )
        return self._services['confluence_service']
    
    def get_jira_service(self) -> JiraService:
        if 'jira_service' not in self._services:
            jira_config = self.config.get('jira', {})
            self._services['jira_service'] = JiraService(
                url=jira_config.get('url'),
                username=jira_config.get('username'),
                password=jira_config.get('password')
            )
        return self._services['jira_service']
    
    def get_confluence_data_processor(self) -> ConfluenceDataProcessor:
        if 'confluence_data_processor' not in self._services:
            self._services['confluence_data_processor'] = ConfluenceDataProcessor(
                self.get_confluence_service()
            )
        return self._services['confluence_data_processor']
    
    def get_jira_data_processor(self) -> JiraDataProcessor:
        if 'jira_data_processor' not in self._services:
            self._services['jira_data_processor'] = JiraDataProcessor(
                self.get_jira_service()
            )
        return self._services['jira_data_processor']
    
    def get_mattermost_data_processor(self) -> MattermostDataProcessor:
        if 'mattermost_data_processor' not in self._services:
            self._services['mattermost_data_processor'] = MattermostDataProcessor()
        return self._services['mattermost_data_processor']
    
    def get_result_reporter(self) -> ResultReporter:
        if 'result_reporter' not in self._services:
            # 初始化 ResultReporter，同时注入 mattermost_processor
            self._services['result_reporter'] = ResultReporter(
                mattermost_processor=self.get_mattermost_data_processor()
            )
        return self._services['result_reporter']