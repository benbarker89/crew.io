"""
Barker v ESHT - Slack Integration
Handles notifications and status updates
"""

from typing import Optional, Dict, Any, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)


class SlackClient:
    """Slack API client for notifications"""

    def __init__(self, token: str, default_channel: str = '#all-ben'):
        """Initialize Slack client

        Args:
            token: Slack bot token
            default_channel: Default channel for messages
        """
        self.client = WebClient(token=token)
        self.default_channel = default_channel
        self.bot_id = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate and get bot info"""
        try:
            response = self.client.auth_test()
            self.bot_id = response['user_id']
            logger.info(f"Authenticated with Slack as {response['user']}")
        except SlackApiError as e:
            logger.error(f"Failed to authenticate with Slack: {e}")
            raise

    def post_message(
        self,
        text: str,
        channel: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None
    ) -> Optional[str]:
        """Post a message to Slack

        Args:
            text: Message text
            channel: Channel name or ID (uses default if None)
            blocks: Optional Block Kit blocks
            thread_ts: Optional thread timestamp for replies

        Returns:
            Message timestamp if successful
        """
        try:
            channel = channel or self.default_channel

            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts
            )

            ts = response['ts']
            logger.info(f"Posted message to {channel}")
            return ts

        except SlackApiError as e:
            logger.error(f"Error posting message to Slack: {e}")
            return None

    def post_automation_summary(
        self,
        automation_name: str,
        status: str,
        metrics: Dict[str, Any],
        channel: Optional[str] = None
    ) -> Optional[str]:
        """Post automation summary to Slack

        Args:
            automation_name: Name of the automation
            status: Status (SUCCESS, WARNING, ERROR)
            metrics: Dictionary of metrics to display
            channel: Channel to post to

        Returns:
            Message timestamp if successful
        """
        # Determine emoji and color based on status
        emoji_map = {
            'SUCCESS': ':white_check_mark:',
            'WARNING': ':warning:',
            'ERROR': ':x:'
        }
        color_map = {
            'SUCCESS': '#36a64f',
            'WARNING': '#ff9900',
            'ERROR': '#ff0000'
        }

        emoji = emoji_map.get(status, ':information_source:')
        color = color_map.get(status, '#0066cc')

        # Build metrics fields
        fields = []
        for key, value in metrics.items():
            fields.append({
                'type': 'mrkdwn',
                'text': f'*{key}:*\n{value}'
            })

        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f'{emoji} {automation_name}'
                }
            },
            {
                'type': 'section',
                'fields': fields
            },
            {
                'type': 'context',
                'elements': [
                    {
                        'type': 'mrkdwn',
                        'text': f'Status: *{status}*'
                    }
                ]
            }
        ]

        text = f"{automation_name} - {status}"
        return self.post_message(text, channel=channel, blocks=blocks)

    def post_delta_sweep_summary(
        self,
        new_files: int,
        modified_files: int,
        duplicates: int,
        total_size_mb: float,
        errors: int = 0,
        channel: Optional[str] = None
    ) -> Optional[str]:
        """Post nightly delta sweep summary

        Args:
            new_files: Number of new files
            modified_files: Number of modified files
            duplicates: Number of duplicates found
            total_size_mb: Total size in MB
            errors: Number of errors
            channel: Channel to post to

        Returns:
            Message timestamp
        """
        status = 'SUCCESS' if errors == 0 else 'WARNING' if errors < 5 else 'ERROR'

        metrics = {
            'New Files': new_files,
            'Modified Files': modified_files,
            'Duplicates': duplicates,
            'Total Size': f'{total_size_mb:.2f} MB',
            'Errors': errors
        }

        return self.post_automation_summary(
            'Nightly Delta Sweep',
            status,
            metrics,
            channel
        )

    def post_aeon_export_summary(
        self,
        event_count: int,
        categories: Dict[str, int],
        export_path: str,
        channel: Optional[str] = None
    ) -> Optional[str]:
        """Post weekly AEON export summary

        Args:
            event_count: Total number of events
            categories: Category histogram
            export_path: Path to export file
            channel: Channel to post to

        Returns:
            Message timestamp
        """
        category_text = '\n'.join([f'• {k}: {v}' for k, v in sorted(categories.items())])

        metrics = {
            'Total Events': event_count,
            'Categories': category_text,
            'Export Path': export_path
        }

        return self.post_automation_summary(
            'Weekly AEON Timeline Export',
            'SUCCESS',
            metrics,
            channel
        )

    def post_bundle_summary(
        self,
        bundle_name: str,
        exhibit_count: int,
        page_count: int,
        bundle_size_mb: float,
        bundle_path: str,
        channel: Optional[str] = None
    ) -> Optional[str]:
        """Post bundle builder summary

        Args:
            bundle_name: Bundle name
            exhibit_count: Number of exhibits
            page_count: Total pages
            bundle_size_mb: Bundle size in MB
            bundle_path: Path to bundle
            channel: Channel to post to

        Returns:
            Message timestamp
        """
        metrics = {
            'Bundle': bundle_name,
            'Exhibits': exhibit_count,
            'Pages': page_count,
            'Size': f'{bundle_size_mb:.2f} MB',
            'Path': bundle_path
        }

        return self.post_automation_summary(
            'Evidence Bundle Created',
            'SUCCESS',
            metrics,
            channel
        )

    def post_kpi_report(
        self,
        kpi_data: Dict[str, Any],
        report_path: str,
        channel: Optional[str] = None
    ) -> Optional[str]:
        """Post KPI report summary

        Args:
            kpi_data: Dictionary of KPI metrics
            report_path: Path to report file
            channel: Channel to post to

        Returns:
            Message timestamp
        """
        metrics = {
            'Report Path': report_path,
            **kpi_data
        }

        return self.post_automation_summary(
            'Weekly KPI Report',
            'SUCCESS',
            metrics,
            channel
        )

    def upload_file(
        self,
        file_path: str,
        channel: Optional[str] = None,
        title: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """Upload a file to Slack

        Args:
            file_path: Path to file
            channel: Channel to upload to
            title: File title
            comment: Optional comment

        Returns:
            True if successful
        """
        try:
            channel = channel or self.default_channel

            response = self.client.files_upload_v2(
                channel=channel,
                file=file_path,
                title=title,
                initial_comment=comment
            )

            logger.info(f"Uploaded file {file_path} to {channel}")
            return True

        except SlackApiError as e:
            logger.error(f"Error uploading file to Slack: {e}")
            return False
