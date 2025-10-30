"""
Barker v ESHT - Main Orchestrator
Coordinates all automations and system operations
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Config, get_config, setup_logging, get_logger
from integrations import GoogleDriveClient, SlackClient, NotionClient, SupabaseClient
from automations import (
    DeltaSweepAutomation,
    AeonExportAutomation,
    BundleBuilderAutomation,
    KPIReporterAutomation
)

logger = get_logger(__name__)


class ESHTOrchestrator:
    """Main orchestrator for ESHT case management system"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize orchestrator

        Args:
            config_path: Optional path to config file
        """
        self.config = Config(config_path) if config_path else get_config()

        # Setup logging
        setup_logging(
            log_level=self.config.log_level,
            console_output=True
        )

        logger.info("Initializing ESHT Orchestrator")

        # Initialize integrations
        self.drive = None
        self.slack = None
        self.notion = None
        self.supabase = None

        # Initialize automations (will be set after connections)
        self.delta_sweep = None
        self.aeon_export = None
        self.bundle_builder = None
        self.kpi_reporter = None

    def initialize_connections(self) -> Dict[str, bool]:
        """Initialize all service connections

        Returns:
            Dictionary of connection status
        """
        status = {}

        # Google Drive
        try:
            if self.config.google_credentials_path:
                self.drive = GoogleDriveClient(self.config.google_credentials_path)
                status['google_drive'] = True
                logger.info("Google Drive connected")
            else:
                status['google_drive'] = False
                logger.warning("Google Drive credentials not configured")
        except Exception as e:
            logger.error(f"Failed to connect to Google Drive: {e}")
            status['google_drive'] = False

        # Slack
        try:
            if self.config.slack_token:
                self.slack = SlackClient(
                    self.config.slack_token,
                    self.config.slack_channel
                )
                status['slack'] = True
                logger.info("Slack connected")
            else:
                status['slack'] = False
                logger.warning("Slack token not configured")
        except Exception as e:
            logger.error(f"Failed to connect to Slack: {e}")
            status['slack'] = False

        # Notion
        try:
            if self.config.notion_token:
                self.notion = NotionClient(self.config.notion_token)

                # Set database IDs if configured
                if self.config.notion_database_evidence_id:
                    self.notion.set_database_id('evidence', self.config.notion_database_evidence_id)
                if self.config.notion_database_issues_id:
                    self.notion.set_database_id('issues', self.config.notion_database_issues_id)
                if self.config.notion_database_timeline_id:
                    self.notion.set_database_id('timeline', self.config.notion_database_timeline_id)
                if self.config.notion_database_tasks_id:
                    self.notion.set_database_id('tasks', self.config.notion_database_tasks_id)

                status['notion'] = True
                logger.info("Notion connected")
            else:
                status['notion'] = False
                logger.warning("Notion token not configured")
        except Exception as e:
            logger.error(f"Failed to connect to Notion: {e}")
            status['notion'] = False

        # Supabase
        try:
            if self.config.supabase_url and self.config.supabase_key:
                self.supabase = SupabaseClient(
                    self.config.supabase_url,
                    self.config.supabase_key,
                    self.config.supabase_service_key
                )
                status['supabase'] = True
                logger.info("Supabase connected")
            else:
                status['supabase'] = False
                logger.warning("Supabase credentials not configured")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            status['supabase'] = False

        # Initialize automations if we have required connections
        if status.get('google_drive') and status.get('slack') and status.get('supabase'):
            self._initialize_automations()

        return status

    def _initialize_automations(self):
        """Initialize automation modules"""
        self.delta_sweep = DeltaSweepAutomation(
            self.drive, self.slack, self.supabase, self.config
        )
        self.aeon_export = AeonExportAutomation(
            self.drive, self.slack, self.supabase, self.notion, self.config
        )
        self.bundle_builder = BundleBuilderAutomation(
            self.drive, self.slack, self.supabase, self.config
        )
        self.kpi_reporter = KPIReporterAutomation(
            self.drive, self.slack, self.supabase, self.config
        )
        logger.info("Automations initialized")

    def setup_system(self) -> Dict[str, Any]:
        """Run Phase 1: Discovery & Setup

        Returns:
            Setup summary
        """
        logger.info("=== PHASE 1: DISCOVERY & SETUP ===")

        summary = {
            'connections': {},
            'folders': {},
            'databases': {},
            'errors': []
        }

        # Initialize connections
        logger.info("Initializing connections...")
        summary['connections'] = self.initialize_connections()

        # Create folder structure
        if self.drive:
            logger.info("Creating folder structure...")
            try:
                folder_ids = self.drive.create_folder_structure(
                    self.config.drive_root,
                    self.config.drive_folders
                )
                summary['folders'] = folder_ids
                logger.info(f"Created {len(folder_ids)} folders")
            except Exception as e:
                error_msg = f"Failed to create folder structure: {e}"
                logger.error(error_msg)
                summary['errors'].append(error_msg)

        # Create database tables
        if self.supabase:
            logger.info("Creating database tables...")
            try:
                schema = self.config.database_schema
                table_results = self.supabase.create_tables(schema)
                summary['databases'] = table_results
                logger.info(f"Database setup: {table_results}")
            except Exception as e:
                error_msg = f"Failed to create database tables: {e}"
                logger.error(error_msg)
                summary['errors'].append(error_msg)

        logger.info("Phase 1 complete")
        return summary

    def run_nightly_sweep(self, since_hours: int = 24) -> Dict[str, Any]:
        """Run nightly delta sweep automation

        Args:
            since_hours: Hours to look back

        Returns:
            Execution summary
        """
        if not self.delta_sweep:
            raise RuntimeError("Automations not initialized. Run setup_system() first.")

        logger.info("=== RUNNING NIGHTLY DELTA SWEEP ===")
        return self.delta_sweep.run(since_hours)

    def run_weekly_export(self) -> Dict[str, Any]:
        """Run weekly AEON export automation

        Returns:
            Execution summary
        """
        if not self.aeon_export:
            raise RuntimeError("Automations not initialized. Run setup_system() first.")

        logger.info("=== RUNNING WEEKLY AEON EXPORT ===")
        return self.aeon_export.run()

    def run_bundle_builder(self, bundle_name: Optional[str] = None) -> Dict[str, Any]:
        """Run monthly bundle builder automation

        Args:
            bundle_name: Optional bundle name

        Returns:
            Execution summary
        """
        if not self.bundle_builder:
            raise RuntimeError("Automations not initialized. Run setup_system() first.")

        logger.info("=== RUNNING BUNDLE BUILDER ===")
        return self.bundle_builder.run(bundle_name)

    def run_kpi_report(self) -> Dict[str, Any]:
        """Run weekly KPI report automation

        Returns:
            Execution summary
        """
        if not self.kpi_reporter:
            raise RuntimeError("Automations not initialized. Run setup_system() first.")

        logger.info("=== RUNNING KPI REPORT ===")
        return self.kpi_reporter.run()

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status

        Returns:
            System status summary
        """
        return {
            'connections': {
                'google_drive': self.drive is not None,
                'slack': self.slack is not None,
                'notion': self.notion is not None,
                'supabase': self.supabase is not None
            },
            'automations': {
                'delta_sweep': self.delta_sweep is not None,
                'aeon_export': self.aeon_export is not None,
                'bundle_builder': self.bundle_builder is not None,
                'kpi_reporter': self.kpi_reporter is not None
            },
            'config': {
                'case_name': self.config.case_name,
                'case_reference': self.config.case_reference,
                'timezone': self.config.timezone,
                'drive_root': self.config.drive_root
            }
        }


def main():
    """Main entry point"""
    orchestrator = ESHTOrchestrator()

    # Run setup
    setup_summary = orchestrator.setup_system()

    print("\n=== ESHT CASE MANAGEMENT SYSTEM ===")
    print(f"\nConnections: {setup_summary['connections']}")
    print(f"Folders: {len(setup_summary.get('folders', {}))} created")
    print(f"Databases: {setup_summary.get('databases', {})}")

    if setup_summary.get('errors'):
        print(f"\nErrors: {len(setup_summary['errors'])}")
        for error in setup_summary['errors']:
            print(f"  - {error}")

    return orchestrator


if __name__ == '__main__':
    main()
