import logging
import time
from atlassian import Confluence
from bs4 import BeautifulSoup

class ConfluenceService:
    """
    Contains only the logic for interacting with the Confluence API:
    - get_page_xhtml
    - update_table_data
    - parse_table_cell, etc.
    No direct knowledge of business rules, which live in the domain layer.
    """
    def __init__(self, url: str, username: str, password: str):
        self.confluence = Confluence(
            url=url,
            username=username,
            password=password
        )

    def get_page_xhtml(self, page_id: str) -> dict:
        page_info = self.confluence.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version'
        )
        return page_info

    def parse_table_cell(self, cell_html: str) -> str:
        # This is unchanged from your version
        soup = BeautifulSoup(cell_html, 'html.parser')
        return soup.get_text(strip=True)

    # --------------------------------------------------
    # NEW HELPER 1: Fetch page, parse HTML, and return soup
    # --------------------------------------------------
    def _fetch_and_parse_page(self, page_id: str):
        """
        Fetch the page content, return:
         - page_info
         - current_version
         - soup (BeautifulSoup)
         - title
        Raises exception if page not found or other error.
        """
        page_info = self.get_page_xhtml(page_id)
        current_version = page_info['version']['number']
        xhtml = page_info['body']['storage']['value']
        title = page_info['title']

        soup = BeautifulSoup(xhtml, 'html.parser')
        return page_info, current_version, soup, title

    # --------------------------------------------------
    # NEW HELPER 2: Get the <table> by index
    # --------------------------------------------------
    def _get_table_by_index(self, soup: BeautifulSoup, page_id: str, table_index: int = 0):
        """
        Find the table at table_index in the page soup.
        Return the <table> element or None.
        """
        tables = soup.find_all('table')
        if not tables or table_index >= len(tables):
            logging.error("Page [%s] does not have table index=%d", page_id, table_index)
            return None
        return tables[table_index]

    # --------------------------------------------------
    # NEW HELPER 3: Build a new <tbody> from the new_data
    # --------------------------------------------------
    def _build_table_body(self, soup: BeautifulSoup, new_data: list) -> BeautifulSoup:
        """
        Given new_data (list of dict), build and return a new <tbody>.
        Each dict in new_data maps column_name -> cell_value.
        """
        new_tbody = soup.new_tag('tbody')

        if not new_data:
            # No data means an empty <tbody> is fine
            return new_tbody

        # Build header row
        headers = list(new_data[0].keys())
        header_tr = soup.new_tag('tr')
        for h in headers:
            th = soup.new_tag('th')
            th.string = h
            header_tr.append(th)
        new_tbody.append(header_tr)

        # Build data rows
        for row_item in new_data:
            row_tr = soup.new_tag('tr')
            for h in headers:
                td = soup.new_tag('td')
                td.string = str(row_item.get(h, ""))
                row_tr.append(td)
            new_tbody.append(row_tr)

        return new_tbody

    # --------------------------------------------------
    # NEW HELPER 4: Replace the old <tbody> with the new one
    # --------------------------------------------------
    def _replace_table_body(self, table, new_tbody):
        old_tbody = table.find('tbody')
        if old_tbody:
            old_tbody.replace_with(new_tbody)
        else:
            table.append(new_tbody)

    # --------------------------------------------------
    # NEW HELPER 5: Commit the update to Confluence
    # --------------------------------------------------
    def _commit_update(self, page_id: str, title: str, soup: BeautifulSoup, current_version: int) -> bool:
        """
        Convert the updated soup to a string and send to Confluence.
        Returns True if successful, False otherwise.
        """
        updated_body = str(soup)
        update_resp = self.confluence.update_page(
            page_id=page_id,
            title=title,
            body=updated_body,
            version=current_version + 1
        )
        if 'id' in update_resp:
            logging.info("Page [%s] updated successfully. Version: %d -> %d", 
                         page_id, current_version, current_version+1)
            return True
        else:
            logging.error("Failed to update page [%s]. Confluence returned: %s", page_id, update_resp)
            return False

    # --------------------------------------------------
    # REFACTORED MAIN METHOD: update_table_data
    # --------------------------------------------------
    def update_table_data(self, page_id: str,
                          new_data: list,
                          table_index: int = 0,
                          retry_on_conflict: bool = True) -> bool:
        """
        Update the specified table (table_index) in a Confluence page with new_data.
        If there's a version conflict and retry_on_conflict=True, it will retry once.
        """
        try:
            page_info, current_version, soup, title = self._fetch_and_parse_page(page_id)
            table = self._get_table_by_index(soup, page_id, table_index)
            if table is None:
                logging.error("Table index %d not found. Update aborted.", table_index)
                return False

            new_tbody = self._build_table_body(soup, new_data)
            self._replace_table_body(table, new_tbody)

            # Attempt to update Confluence
            success = self._commit_update(page_id, title, soup, current_version)
            return success

        except Exception as e:
            # Example conflict detection logic: 'conflict' in the error message
            if retry_on_conflict and "conflict" in str(e).lower():
                logging.warning("Version conflict detected for page [%s]. Retrying update...", page_id)
                # Retry once without further retries
                return self.update_table_data(
                    page_id=page_id,
                    new_data=new_data,
                    table_index=table_index,
                    retry_on_conflict=False
                )
            else:
                logging.error("Error updating page [%s] table [%d]: %s", page_id, table_index, e)
                return False
