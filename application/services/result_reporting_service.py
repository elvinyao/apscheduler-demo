import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

class ResultReportingService:
    """
    Handles reporting of task execution results through various channels,
    including updating Confluence pages with aggregated results.
    """
    def __init__(self, task_result_repo, confluence_updater, report_interval=30):
        """
        Initialize the ResultReportingService.
        
        Args:
            task_result_repo: Repository for accessing task results
            confluence_updater: Service to update Confluence pages
            report_interval: Interval in seconds between result updates
        """
        self.task_result_repo = task_result_repo
        self.confluence_updater = confluence_updater
        self.report_interval = report_interval
        self.scheduler = None
    
    def start(self, scheduler=None):
        """
        Start the result reporting service.
        
        Args:
            scheduler: An existing scheduler to use, or create a new one if None
        """
        # Use provided scheduler or create our own
        if scheduler:
            self.scheduler = scheduler
            self._schedule_updates(self.scheduler)
        else:
            self.scheduler = BackgroundScheduler()
            self._schedule_updates(self.scheduler)
            self.scheduler.start()
            logging.info("ResultReportingService started with dedicated scheduler")
    
    def _schedule_updates(self, scheduler):
        """Schedule the regular update job in the provided scheduler."""
        scheduler.add_job(
            func=self.update_confluence_page,
            trigger=IntervalTrigger(seconds=self.report_interval),
            id='update_confluence_job',
            replace_existing=True
        )
        logging.info(f"Scheduled Confluence updates every {self.report_interval} seconds")
    
    def update_confluence_page(self):
        """Update Confluence page with task results."""
        results = self.task_result_repo.get_all()
        if not results:
            logging.info("ResultReportingService: no new results to update.")
            return

        logging.info("ResultReportingService: found %d results, updating Confluence...", len(results))
        self.confluence_updater.update_with_results(results)
        self.task_result_repo.clear_all()
        logging.info("ResultReportingService: done updating Confluence and clearing results.")
    
    def report_single_result(self, task_id, result):
        """
        Report a single task result immediately.
        
        Args:
            task_id: ID of the task
            result: Result data to report
        """
        logging.info(f"Reporting single result for task {task_id}")
        self.confluence_updater.update_single_result(task_id, result)
    
    def shutdown(self):
        """Shutdown the service."""
        if self.scheduler and self.scheduler._standalone:
            self.scheduler.shutdown()
            logging.info("ResultReportingService scheduler shutdown") 