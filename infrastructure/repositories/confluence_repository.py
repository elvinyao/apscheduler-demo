"""
Repository implementation for Confluence updates.
"""
import logging
import time
from typing import List, Dict, Any

from domain.exceptions import IntegrationException, ApiResponseError

class ConfluenceRepository:
    """
    Repository for updating Confluence with task results.
    This encapsulates the Confluence update logic.
    """
    
    def __init__(self, confluence_service=None):
        """
        Initialize the repository.
        
        Args:
            confluence_service: The Confluence service to use for updates
        """
        self.logger = logging.getLogger(__name__)
        self.confluence_service = confluence_service
    
    def update_with_results(self, results: List[Dict[str, Any]], page_id: str = None) -> bool:
        """
        Update Confluence with aggregated task results.
        
        Args:
            results: List of task results to update
            page_id: Optional page ID to update. If not provided, uses a default page.
            
        Returns:
            bool: True if the update succeeded, False otherwise
        """
        try:
            if not results:
                self.logger.info("No results to update in Confluence")
                return True
            
            data_preview = str(results)[:50] + "..." if len(str(results)) > 50 else str(results)
            self.logger.info("Updating Confluence with aggregated data: %s", data_preview)
            
            # Call the Confluence service if available, otherwise just simulate
            if self.confluence_service and page_id:
                # Transform results to a format suitable for Confluence
                table_data = self._transform_results_to_table(results)
                return self.confluence_service.update_table_data(page_id, table_data)
            else:
                # Simulate an update
                time.sleep(1)
                self.logger.info("Confluence update simulation done.")
                return True
                
        except Exception as e:
            self.logger.error("Failed to update Confluence: %s", str(e))
            raise ApiResponseError("Confluence", details={"message": str(e)})
    
    def _transform_results_to_table(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Transform task results into a format suitable for a Confluence table.
        
        Args:
            results: List of task results
            
        Returns:
            List of dictionaries representing table rows
        """
        table_data = []
        
        for result in results:
            # Extract the relevant information from the result
            task_id = result.get('task_id', 'Unknown')
            status = result.get('execution_details', {}).get('success', False)
            status_str = "Success" if status else "Failed"
            error = result.get('execution_details', {}).get('error', '')
            timestamp = result.get('timestamp', '')
            
            # Create a row for the table
            row = {
                "Task ID": str(task_id),
                "Status": status_str,
                "Error": error if error else "None",
                "Timestamp": str(timestamp)
            }
            
            table_data.append(row)
        
        return table_data