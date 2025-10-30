"""
Barker v ESHT - Weekly AEON Timeline Export Automation
Exports timeline database to AEON-compatible CSV format
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter
import logging

logger = logging.getLogger('automation.aeon_export')


class AeonExportAutomation:
    """Weekly AEON timeline export automation"""

    def __init__(self, drive_client, slack_client, supabase_client, notion_client, config):
        """Initialize AEON export automation

        Args:
            drive_client: GoogleDriveClient instance
            slack_client: SlackClient instance
            supabase_client: SupabaseClient instance
            notion_client: NotionClient instance
            config: Configuration object
        """
        self.drive = drive_client
        self.slack = slack_client
        self.supabase = supabase_client
        self.notion = notion_client
        self.config = config

    def run(self) -> Dict[str, Any]:
        """Run weekly AEON export

        Returns:
            Execution summary
        """
        logger.info("Starting weekly AEON export")
        start_time = datetime.now()

        try:
            # Query timeline events from Supabase or Notion
            events = self._get_timeline_events()

            if not events:
                logger.warning("No timeline events found")
                self.slack.post_message(":warning: Weekly AEON Export - No events found")
                return {'event_count': 0, 'categories': {}}

            # Generate category histogram
            categories = Counter([e.get('category', 'Unknown') for e in events])

            # Export to CSV
            export_path = self._export_to_csv(events)

            # Upload to Drive
            folder_ids = self.drive.create_folder_structure(
                self.config.drive_root,
                self.config.drive_folders
            )
            indexes_folder_id = folder_ids.get('05_Indexes')

            if indexes_folder_id:
                self.drive.upload_file(
                    Path(export_path),
                    indexes_folder_id,
                    'AEON_Timeline_Export.csv'
                )

            # Post summary to Slack
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"AEON export completed in {duration:.2f}s")

            self.slack.post_aeon_export_summary(
                event_count=len(events),
                categories=dict(categories),
                export_path='05_Indexes/AEON_Timeline_Export.csv'
            )

            return {
                'event_count': len(events),
                'categories': dict(categories),
                'export_path': export_path
            }

        except Exception as e:
            logger.error(f"AEON export failed: {e}")
            self.slack.post_message(f":x: Weekly AEON Export FAILED\n```{str(e)}```")
            raise

    def _get_timeline_events(self) -> List[Dict[str, Any]]:
        """Get timeline events from database

        Returns:
            List of timeline events
        """
        try:
            # Try Supabase first
            events = self.supabase.query_timeline()
            if events:
                return events

            # Fall back to Notion
            logger.info("Falling back to Notion for timeline events")
            return self.notion.export_timeline_to_csv()

        except Exception as e:
            logger.error(f"Error getting timeline events: {e}")
            return []

    def _export_to_csv(self, events: List[Dict[str, Any]]) -> str:
        """Export events to AEON-compatible CSV

        Args:
            events: List of timeline events

        Returns:
            Path to exported CSV file
        """
        output_dir = Path('/tmp/esht_exports')
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'AEON_Timeline_Export_{timestamp}.csv'

        # AEON Timeline CSV format
        fieldnames = [
            'Date',
            'Time',
            'Title',
            'Description',
            'Category',
            'Participants',
            'Location',
            'Evidence IDs'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for event in events:
                # Format date and time
                event_date = event.get('event_date', '')
                event_time = event.get('event_time', '')

                # Format participants
                participants = event.get('participants', [])
                if isinstance(participants, list):
                    participants = ', '.join(participants)

                # Format evidence IDs
                evidence_ids = event.get('evidence_ids', [])
                if isinstance(evidence_ids, list):
                    evidence_ids = ', '.join(evidence_ids)

                writer.writerow({
                    'Date': event_date,
                    'Time': event_time,
                    'Title': event.get('title', ''),
                    'Description': event.get('description', ''),
                    'Category': event.get('category', ''),
                    'Participants': participants,
                    'Location': event.get('location', ''),
                    'Evidence IDs': evidence_ids
                })

        logger.info(f"Exported {len(events)} events to {output_file}")
        return str(output_file)
