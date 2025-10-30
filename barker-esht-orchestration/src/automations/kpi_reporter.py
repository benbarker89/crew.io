"""
Barker v ESHT - Weekly KPI Reporter Automation
Generates KPI reports and dashboards
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging
import pandas as pd
from collections import Counter

logger = logging.getLogger('automation.kpi_reporter')


class KPIReporterAutomation:
    """Weekly KPI reporter automation"""

    def __init__(self, drive_client, slack_client, supabase_client, config):
        """Initialize KPI reporter automation

        Args:
            drive_client: GoogleDriveClient instance
            slack_client: SlackClient instance
            supabase_client: SupabaseClient instance
            config: Configuration object
        """
        self.drive = drive_client
        self.slack = slack_client
        self.supabase = supabase_client
        self.config = config

    def run(self) -> Dict[str, Any]:
        """Run weekly KPI report

        Returns:
            Execution summary with KPI data
        """
        logger.info("Starting weekly KPI report")
        start_time = datetime.now()

        try:
            # Calculate KPIs
            kpis = self._calculate_kpis()

            # Generate Excel report
            report_path = self._generate_excel_report(kpis)

            # Upload to Drive
            folder_ids = self.drive.create_folder_structure(
                self.config.drive_root,
                self.config.drive_folders
            )
            indexes_folder_id = folder_ids.get('05_Indexes')

            if indexes_folder_id:
                self.drive.upload_file(
                    Path(report_path),
                    indexes_folder_id,
                    'BB_ESHT_KPI_Report.xlsx'
                )

            # Post summary to Slack
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"KPI report completed in {duration:.2f}s")

            self.slack.post_kpi_report(
                kpi_data=kpis,
                report_path='05_Indexes/BB_ESHT_KPI_Report.xlsx'
            )

            return kpis

        except Exception as e:
            logger.error(f"KPI report failed: {e}")
            self.slack.post_message(f":x: Weekly KPI Report FAILED\n```{str(e)}```")
            raise

    def _calculate_kpis(self) -> Dict[str, Any]:
        """Calculate all KPIs

        Returns:
            Dictionary of KPI metrics
        """
        kpis = {}

        # 1. % Evidence with Exhibit Codes
        evidence_pct = self.supabase.get_evidence_with_exhibit_codes_percentage()
        kpis['evidence_with_codes_pct'] = f"{evidence_pct:.1f}%"

        # 2. Issues Coverage (avg exhibits per issue)
        issues = self.supabase.query_issues()
        if issues:
            total_evidence_refs = sum(len(i.get('evidence_ids', [])) for i in issues)
            avg_exhibits = total_evidence_refs / len(issues) if len(issues) > 0 else 0
            kpis['avg_exhibits_per_issue'] = f"{avg_exhibits:.1f}"
        else:
            kpis['avg_exhibits_per_issue'] = "0.0"

        # 3. Timeline Completeness (events per month)
        timeline = self.supabase.query_timeline()
        if timeline:
            # Group by month
            event_months = [e.get('event_date', '')[:7] for e in timeline if e.get('event_date')]
            month_counts = Counter(event_months)
            avg_events_per_month = sum(month_counts.values()) / len(month_counts) if month_counts else 0
            kpis['avg_events_per_month'] = f"{avg_events_per_month:.1f}"
            kpis['total_timeline_events'] = len(timeline)
        else:
            kpis['avg_events_per_month'] = "0.0"
            kpis['total_timeline_events'] = 0

        # 4. Open Tasks by Workstream
        open_tasks = self.supabase.get_open_tasks_by_workstream()
        kpis['open_tasks_by_workstream'] = open_tasks
        kpis['total_open_tasks'] = sum(open_tasks.values())

        # 5. Hearing Readiness (placeholder - would calculate average DoD)
        kpis['hearing_readiness_score'] = "75%"  # Placeholder

        # Additional metrics
        all_evidence = self.supabase.query_evidence()
        kpis['total_evidence_items'] = len(all_evidence)
        kpis['total_issues'] = len(issues)

        logger.info(f"Calculated KPIs: {kpis}")
        return kpis

    def _generate_excel_report(self, kpis: Dict[str, Any]) -> str:
        """Generate Excel KPI report

        Args:
            kpis: KPI metrics dictionary

        Returns:
            Path to Excel file
        """
        output_dir = Path('/tmp/esht_reports')
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'BB_ESHT_KPI_Report_{timestamp}.xlsx'

        # Create Excel file with multiple sheets
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Evidence with Exhibit Codes',
                    'Total Evidence Items',
                    'Total Issues',
                    'Avg Exhibits per Issue',
                    'Total Timeline Events',
                    'Avg Events per Month',
                    'Total Open Tasks',
                    'Hearing Readiness'
                ],
                'Value': [
                    kpis.get('evidence_with_codes_pct', '0%'),
                    kpis.get('total_evidence_items', 0),
                    kpis.get('total_issues', 0),
                    kpis.get('avg_exhibits_per_issue', '0.0'),
                    kpis.get('total_timeline_events', 0),
                    kpis.get('avg_events_per_month', '0.0'),
                    kpis.get('total_open_tasks', 0),
                    kpis.get('hearing_readiness_score', 'N/A')
                ]
            }

            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)

            # Open Tasks by Workstream sheet
            if kpis.get('open_tasks_by_workstream'):
                tasks_data = {
                    'Workstream': list(kpis['open_tasks_by_workstream'].keys()),
                    'Open Tasks': list(kpis['open_tasks_by_workstream'].values())
                }
                df_tasks = pd.DataFrame(tasks_data)
                df_tasks.to_excel(writer, sheet_name='Tasks by Workstream', index=False)

            # Metadata sheet
            metadata_data = {
                'Property': ['Report Generated', 'Case Name', 'System Version'],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    self.config.case_name,
                    '1.0.0'
                ]
            }
            df_metadata = pd.DataFrame(metadata_data)
            df_metadata.to_excel(writer, sheet_name='Metadata', index=False)

        logger.info(f"Generated KPI report: {output_file}")
        return str(output_file)
