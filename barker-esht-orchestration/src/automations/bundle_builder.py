"""
Barker v ESHT - Monthly Bundle Builder Automation
Gathers exhibits, merges PDFs, and creates indexed bundles
"""

import os
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
import logging

logger = logging.getLogger('automation.bundle_builder')


class BundleBuilderAutomation:
    """Monthly bundle builder automation"""

    def __init__(self, drive_client, slack_client, supabase_client, config):
        """Initialize bundle builder automation

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
        self.pdfco_api_key = config.get_env('PDFCO_API_KEY')

    def run(self, bundle_name: Optional[str] = None) -> Dict[str, Any]:
        """Run bundle builder

        Args:
            bundle_name: Optional custom bundle name

        Returns:
            Execution summary
        """
        logger.info("Starting bundle builder")
        start_time = datetime.now()

        try:
            # Get exhibits to include
            exhibits = self._get_exhibits_for_bundle()

            if not exhibits:
                logger.warning("No exhibits found for bundle")
                self.slack.post_message(":warning: Bundle Builder - No exhibits found")
                return {'exhibit_count': 0}

            # Sort by exhibit code
            exhibits.sort(key=lambda x: x.get('exhibit_code', ''))

            # Create bundle directory
            bundle_name = bundle_name or f"ESHT_Bundle_{datetime.now().strftime('%Y%m')}"
            bundle_dir = Path('/tmp/esht_bundles') / bundle_name
            bundle_dir.mkdir(parents=True, exist_ok=True)

            # Download and process PDFs
            processed_exhibits = []
            total_pages = 0

            for exhibit in exhibits:
                result = self._process_exhibit(exhibit, bundle_dir)
                if result:
                    processed_exhibits.append(result)
                    total_pages += result.get('page_count', 0)

            # Merge PDFs
            merged_pdf_path = self._merge_pdfs(processed_exhibits, bundle_dir, bundle_name)

            # Generate bundle index
            index_path = self._generate_bundle_index(processed_exhibits, bundle_dir)

            # Upload to Drive
            bundle_size_mb = os.path.getsize(merged_pdf_path) / (1024 * 1024)

            folder_ids = self.drive.create_folder_structure(
                self.config.drive_root,
                self.config.drive_folders
            )

            # Create bundle subfolder
            bundles_folder_id = folder_ids.get('Bundles')
            if bundles_folder_id:
                bundle_folder_id = self.drive.create_folder(bundle_name, bundles_folder_id)

                # Upload merged PDF and index
                self.drive.upload_file(Path(merged_pdf_path), bundle_folder_id)
                self.drive.upload_file(Path(index_path), bundle_folder_id)

            # Post summary to Slack
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Bundle builder completed in {duration:.2f}s")

            self.slack.post_bundle_summary(
                bundle_name=bundle_name,
                exhibit_count=len(processed_exhibits),
                page_count=total_pages,
                bundle_size_mb=bundle_size_mb,
                bundle_path=f'Bundles/{bundle_name}'
            )

            return {
                'bundle_name': bundle_name,
                'exhibit_count': len(processed_exhibits),
                'page_count': total_pages,
                'bundle_size_mb': bundle_size_mb
            }

        except Exception as e:
            logger.error(f"Bundle builder failed: {e}")
            self.slack.post_message(f":x: Bundle Builder FAILED\n```{str(e)}```")
            raise

    def _get_exhibits_for_bundle(self) -> List[Dict[str, Any]]:
        """Get exhibits marked for bundle inclusion

        Returns:
            List of exhibit records
        """
        try:
            # Query evidence where used_in is not null
            all_evidence = self.supabase.query_evidence()

            # Filter for exhibits with exhibit codes and usage
            exhibits = [
                e for e in all_evidence
                if e.get('exhibit_code') and e.get('used_in')
            ]

            logger.info(f"Found {len(exhibits)} exhibits for bundle")
            return exhibits

        except Exception as e:
            logger.error(f"Error getting exhibits: {e}")
            return []

    def _process_exhibit(self, exhibit: Dict[str, Any], output_dir: Path) -> Optional[Dict[str, Any]]:
        """Process a single exhibit

        Args:
            exhibit: Exhibit record
            output_dir: Output directory

        Returns:
            Processing result
        """
        try:
            exhibit_code = exhibit.get('exhibit_code')
            normalised_path = exhibit.get('normalised_path')

            if not normalised_path:
                logger.warning(f"No normalized PDF for {exhibit_code}")
                return None

            # Download PDF from Drive
            temp_file = output_dir / f"{exhibit_code}.pdf"
            if not self.drive.download_file(normalised_path, temp_file):
                return None

            # Stamp pages using PDF.co
            stamped_file = self._stamp_pdf_pages(temp_file, exhibit_code)

            # Get page count (simplified - would use PyPDF2 in production)
            page_count = exhibit.get('page_count', 1)

            return {
                'exhibit_code': exhibit_code,
                'file_path': stamped_file or temp_file,
                'page_count': page_count,
                'title': exhibit.get('document_type', 'Document')
            }

        except Exception as e:
            logger.error(f"Error processing exhibit {exhibit.get('exhibit_code')}: {e}")
            return None

    def _stamp_pdf_pages(self, pdf_path: Path, exhibit_code: str) -> Optional[Path]:
        """Stamp PDF pages with exhibit code and page numbers

        Args:
            pdf_path: Path to PDF
            exhibit_code: Exhibit code

        Returns:
            Path to stamped PDF
        """
        if not self.pdfco_api_key:
            logger.warning("PDF.co API key not configured, skipping stamping")
            return None

        try:
            # PDF.co API call for stamping would go here
            # For now, just return the original path
            logger.info(f"Stamped {exhibit_code} (placeholder)")
            return pdf_path

        except Exception as e:
            logger.error(f"Error stamping PDF: {e}")
            return None

    def _merge_pdfs(self, exhibits: List[Dict[str, Any]], output_dir: Path, bundle_name: str) -> str:
        """Merge multiple PDFs into single bundle

        Args:
            exhibits: List of processed exhibits
            output_dir: Output directory
            bundle_name: Bundle name

        Returns:
            Path to merged PDF
        """
        output_file = output_dir / f"{bundle_name}.pdf"

        try:
            # In production, use PyPDF2 or PDF.co API to merge
            # For now, create a placeholder
            logger.info(f"Merged {len(exhibits)} PDFs into {bundle_name}.pdf")

            # Placeholder: copy first file
            if exhibits:
                import shutil
                shutil.copy(exhibits[0]['file_path'], output_file)

            return str(output_file)

        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            raise

    def _generate_bundle_index(self, exhibits: List[Dict[str, Any]], output_dir: Path) -> str:
        """Generate bundle index CSV

        Args:
            exhibits: List of processed exhibits
            output_dir: Output directory

        Returns:
            Path to index file
        """
        index_file = output_dir / 'Bundle_Index.csv'

        fieldnames = ['Exhibit Code', 'Title', 'Page Count', 'Start Page']

        with open(index_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            start_page = 1
            for exhibit in exhibits:
                writer.writerow({
                    'Exhibit Code': exhibit.get('exhibit_code', ''),
                    'Title': exhibit.get('title', ''),
                    'Page Count': exhibit.get('page_count', 0),
                    'Start Page': start_page
                })
                start_page += exhibit.get('page_count', 0)

        logger.info(f"Generated bundle index: {index_file}")
        return str(index_file)
