"""
Barker v ESHT - Notion Integration
Handles database operations for Evidence, Issues, Timeline, and Tasks
"""

from typing import List, Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError
import logging

logger = logging.getLogger(__name__)


class NotionClient:
    """Notion API client for case databases"""

    def __init__(self, token: str):
        """Initialize Notion client

        Args:
            token: Notion integration token
        """
        self.client = Client(auth=token)
        self.databases = {}
        logger.info("Initialized Notion client")

    def set_database_id(self, name: str, database_id: str):
        """Set database ID for a specific database

        Args:
            name: Database name (evidence, issues, timeline, tasks)
            database_id: Notion database ID
        """
        self.databases[name] = database_id
        logger.info(f"Set {name} database ID: {database_id}")

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any]
    ) -> Optional[str]:
        """Create a new Notion database

        Args:
            parent_page_id: Parent page ID
            title: Database title
            properties: Database properties schema

        Returns:
            Database ID if successful
        """
        try:
            response = self.client.databases.create(
                parent={'page_id': parent_page_id},
                title=[{'type': 'text', 'text': {'content': title}}],
                properties=properties
            )

            database_id = response['id']
            logger.info(f"Created Notion database '{title}': {database_id}")
            return database_id

        except APIResponseError as e:
            logger.error(f"Error creating Notion database: {e}")
            return None

    def create_evidence_database(self, parent_page_id: str) -> Optional[str]:
        """Create Evidence database

        Args:
            parent_page_id: Parent page ID

        Returns:
            Database ID
        """
        properties = {
            'Exhibit Code': {'title': {}},
            'Document Type': {'select': {}},
            'Source Path': {'url': {}},
            'Normalised Path': {'url': {}},
            'SHA256': {'rich_text': {}},
            'File Size': {'number': {'format': 'number'}},
            'Page Count': {'number': {'format': 'number'}},
            'Tags': {'multi_select': {}},
            'Used In': {'rich_text': {}},
            'Notes': {'rich_text': {}},
            'Date Created': {'date': {}},
            'Date Modified': {'date': {}}
        }

        return self.create_database(parent_page_id, 'Evidence', properties)

    def create_issues_database(self, parent_page_id: str) -> Optional[str]:
        """Create Issues database

        Args:
            parent_page_id: Parent page ID

        Returns:
            Database ID
        """
        properties = {
            'Issue Code': {'title': {}},
            'Title': {'rich_text': {}},
            'Category': {'select': {}},
            'Priority': {'select': {}},
            'Status': {
                'select': {
                    'options': [
                        {'name': 'Open', 'color': 'blue'},
                        {'name': 'In Progress', 'color': 'yellow'},
                        {'name': 'Resolved', 'color': 'green'},
                        {'name': 'Closed', 'color': 'gray'}
                    ]
                }
            },
            'Description': {'rich_text': {}},
            'Evidence': {'relation': {'database_id': ''}},
            'Created': {'created_time': {}},
            'Updated': {'last_edited_time': {}}
        }

        return self.create_database(parent_page_id, 'Issues', properties)

    def create_timeline_database(self, parent_page_id: str) -> Optional[str]:
        """Create Timeline database

        Args:
            parent_page_id: Parent page ID

        Returns:
            Database ID
        """
        properties = {
            'Title': {'title': {}},
            'Event Date': {'date': {}},
            'Category': {'select': {}},
            'Description': {'rich_text': {}},
            'Participants': {'multi_select': {}},
            'Location': {'rich_text': {}},
            'Evidence': {'relation': {'database_id': ''}},
            'Issues': {'relation': {'database_id': ''}},
            'Created': {'created_time': {}}
        }

        return self.create_database(parent_page_id, 'Timeline', properties)

    def create_tasks_database(self, parent_page_id: str) -> Optional[str]:
        """Create Tasks database

        Args:
            parent_page_id: Parent page ID

        Returns:
            Database ID
        """
        properties = {
            'Title': {'title': {}},
            'Workstream': {'select': {}},
            'Priority': {
                'select': {
                    'options': [
                        {'name': 'High', 'color': 'red'},
                        {'name': 'Medium', 'color': 'yellow'},
                        {'name': 'Low', 'color': 'green'}
                    ]
                }
            },
            'Status': {
                'select': {
                    'options': [
                        {'name': 'To Do', 'color': 'gray'},
                        {'name': 'In Progress', 'color': 'blue'},
                        {'name': 'Done', 'color': 'green'}
                    ]
                }
            },
            'Due Date': {'date': {}},
            'Assigned To': {'people': {}},
            'Description': {'rich_text': {}},
            'Evidence': {'relation': {'database_id': ''}},
            'Issues': {'relation': {'database_id': ''}},
            'Todoist ID': {'rich_text': {}},
            'Created': {'created_time': {}},
            'Updated': {'last_edited_time': {}}
        }

        return self.create_database(parent_page_id, 'Tasks', properties)

    def query_database(
        self,
        database_name: str,
        filter_params: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Query a Notion database

        Args:
            database_name: Database name (evidence, issues, timeline, tasks)
            filter_params: Optional filter parameters
            sorts: Optional sort parameters

        Returns:
            List of database items
        """
        if database_name not in self.databases:
            logger.error(f"Database '{database_name}' not configured")
            return []

        try:
            database_id = self.databases[database_name]
            results = []
            has_more = True
            start_cursor = None

            while has_more:
                response = self.client.databases.query(
                    database_id=database_id,
                    filter=filter_params,
                    sorts=sorts,
                    start_cursor=start_cursor
                )

                results.extend(response['results'])
                has_more = response['has_more']
                start_cursor = response.get('next_cursor')

            logger.info(f"Queried {database_name} database: {len(results)} items")
            return results

        except APIResponseError as e:
            logger.error(f"Error querying Notion database: {e}")
            return []

    def create_page(
        self,
        database_name: str,
        properties: Dict[str, Any]
    ) -> Optional[str]:
        """Create a page in a Notion database

        Args:
            database_name: Database name
            properties: Page properties

        Returns:
            Page ID if successful
        """
        if database_name not in self.databases:
            logger.error(f"Database '{database_name}' not configured")
            return None

        try:
            database_id = self.databases[database_name]

            response = self.client.pages.create(
                parent={'database_id': database_id},
                properties=properties
            )

            page_id = response['id']
            logger.info(f"Created page in {database_name} database: {page_id}")
            return page_id

        except APIResponseError as e:
            logger.error(f"Error creating Notion page: {e}")
            return None

    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update a Notion page

        Args:
            page_id: Page ID
            properties: Properties to update

        Returns:
            True if successful
        """
        try:
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            logger.info(f"Updated Notion page: {page_id}")
            return True

        except APIResponseError as e:
            logger.error(f"Error updating Notion page: {e}")
            return False

    def add_evidence_entry(
        self,
        exhibit_code: str,
        document_type: str,
        source_path: str,
        sha256: str,
        **kwargs
    ) -> Optional[str]:
        """Add an evidence entry

        Args:
            exhibit_code: Exhibit code
            document_type: Document type
            source_path: Source file path
            sha256: SHA256 hash
            **kwargs: Additional properties

        Returns:
            Page ID if successful
        """
        properties = {
            'Exhibit Code': {'title': [{'text': {'content': exhibit_code}}]},
            'Document Type': {'select': {'name': document_type}},
            'Source Path': {'url': source_path} if source_path.startswith('http') else {'rich_text': [{'text': {'content': source_path}}]},
            'SHA256': {'rich_text': [{'text': {'content': sha256}}]}
        }

        # Add optional properties
        if 'file_size' in kwargs:
            properties['File Size'] = {'number': kwargs['file_size']}
        if 'page_count' in kwargs:
            properties['Page Count'] = {'number': kwargs['page_count']}
        if 'tags' in kwargs:
            properties['Tags'] = {'multi_select': [{'name': tag} for tag in kwargs['tags']]}
        if 'notes' in kwargs:
            properties['Notes'] = {'rich_text': [{'text': {'content': kwargs['notes']}}]}

        return self.create_page('evidence', properties)

    def export_timeline_to_csv(self) -> List[Dict[str, Any]]:
        """Export timeline database to CSV format

        Returns:
            List of timeline events
        """
        events = self.query_database(
            'timeline',
            sorts=[{'property': 'Event Date', 'direction': 'ascending'}]
        )

        csv_data = []
        for event in events:
            props = event['properties']
            csv_data.append({
                'date': props.get('Event Date', {}).get('date', {}).get('start', ''),
                'title': self._extract_text(props.get('Title', {})),
                'description': self._extract_text(props.get('Description', {})),
                'category': props.get('Category', {}).get('select', {}).get('name', ''),
                'location': self._extract_text(props.get('Location', {}))
            })

        return csv_data

    def _extract_text(self, property_value: Dict) -> str:
        """Extract text from Notion property

        Args:
            property_value: Property value dictionary

        Returns:
            Extracted text
        """
        if 'title' in property_value:
            texts = property_value['title']
        elif 'rich_text' in property_value:
            texts = property_value['rich_text']
        else:
            return ''

        return ''.join([t.get('plain_text', '') for t in texts])
