# -*- coding: utf-8 -*-

"""
Confluence handler for basic Confluence API interactions.
This class encapsulates low-level Confluence operations using the atlassian-python-api library. It provides methods to retrieve and update the content of Confluence pages.
The `get_page_content` method retrieves the 'body.storage.value' from a Confluence page specified by the `page_id` parameter. If the page is found, the method returns the content, otherwise it returns an empty string.
The `update_page_content` method updates the content of a Confluence page specified by the `page_id` parameter. It takes the new content as the `new_content` parameter, and an optional `version_comment` parameter to provide a comment for the update. The method first retrieves the current version of the page, and then updates the page with the new content, incrementing the version number.
"""
from atlassian import Confluence

class ConfluenceHandler:
    """
    This class encapsulates low-level Confluence operations using atlassian-python-api.
    """

    def __init__(self, confluence_url: str, username: str = None, password: str = None, token: str = None):
        """
        Initialize ConfluenceHandler with credentials or token.
        """
        self.client = Confluence(
            url=confluence_url,
            username=username,
            password=password,
            token=token
        )

    def get_page_content(self, page_id: str) -> str:
        """
        Retrieve the 'body.storage.value' from a Confluence page.
        """
        page = self.client.get_page_by_id(page_id, expand='body.storage')
        if page:
            return page.get('body', {}).get('storage', {}).get('value', '')
        return ''

    def update_page_content(self, page_id: str, new_content: str, version_comment: str = "Update content") -> None:
        """
        Update Confluence page content.
        """
        page_info = self.client.get_page_by_id(page_id)
        if page_info:
            current_version = page_info['version']['number']
            self.client.update_page(
                page_id=page_id,
                title=page_info['title'],
                body=new_content,
                parent_id=None,
                type='page',
                representation='storage',
                minor_edit=False,
                version_comment=version_comment,
                version=current_version + 1
            )
