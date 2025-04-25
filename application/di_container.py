# Updated core/di_container.py
from typing import Dict, Any
from domain.services.result_reporter import ResultReporter
from integration.external_clients.confluence_service import ConfluenceService
from integration.external_clients.jira_service import JiraService
from domain.services.confluence_data_processor import ConfluenceDataProcessor
from domain.services.jira_data_processor import JiraDataProcessor
from domain.services.mattermost_data_processor import MattermostDataProcessor
from application.error_handler import error_handler
from application.services.result_reporting_service import ResultReportingService

# Import new repositories
from infrastructure.repositories.task_repository import TaskRepository
from infrastructure.repositories.task_result_repository import TaskResultRepository
from infrastructure.repositories.confluence_repository import ConfluenceRepository
from infrastructure.persistence.persistence import TaskPersistenceManager

class DIContainer:
    """Dependency Injection container to manage service initialization."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._services = {}
        self._repositories = {}
    
    # Services
    
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
            self._services['result_reporter'] = ResultReporter(
                mattermost_processor=self.get_mattermost_data_processor()
            )
        return self._services['result_reporter']
    
    def get_error_handler(self):
        """Get the global error handler."""
        return error_handler
    
    def get_result_reporting_service(self) -> ResultReportingService:
        """Get or create the result reporting service."""
        if 'result_reporting_service' not in self._services:
            reporting_config = self.config.get('reporting', {})
            report_interval = reporting_config.get('interval', 30)
            
            self._services['result_reporting_service'] = ResultReportingService(
                task_result_repo=self.get_task_result_repository(),
                confluence_updater=self.get_confluence_repository(),
                report_interval=report_interval
            )
        return self._services['result_reporting_service']
    
    # Repositories
    
    def get_persistence_manager(self) -> TaskPersistenceManager:
        """Get or create the task persistence manager."""
        if 'persistence_manager' not in self._repositories:
            storage_path = self.config.get('storage', {}).get('path', 'task_storage')
            self._repositories['persistence_manager'] = TaskPersistenceManager(storage_path=storage_path)
        return self._repositories['persistence_manager']
    
    def get_task_repository(self) -> TaskRepository:
        """Get or create the task repository."""
        if 'task_repository' not in self._repositories:
            self._repositories['task_repository'] = TaskRepository(
                persistence_manager=self.get_persistence_manager()
            )
        return self._repositories['task_repository']
    
    def get_task_result_repository(self) -> TaskResultRepository:
        """Get or create the task result repository."""
        if 'task_result_repository' not in self._repositories:
            self._repositories['task_result_repository'] = TaskResultRepository()
        return self._repositories['task_result_repository']
    
    def get_confluence_repository(self) -> ConfluenceRepository:
        """Get or create the Confluence repository."""
        if 'confluence_repository' not in self._repositories:
            self._repositories['confluence_repository'] = ConfluenceRepository(
                confluence_service=self.get_confluence_service()
            )
        return self._repositories['confluence_repository']