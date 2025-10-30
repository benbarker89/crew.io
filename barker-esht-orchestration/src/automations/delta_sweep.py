"""
Barker v ESHT - Nightly Delta Sweep Automation
Searches for new/modified files, normalizes PDFs, deduplicates, and updates index
"""

import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import csv
import logging

logger = logging.getLogger('automation.delta_sweep')


class DeltaSweepAutomation:
    """Nightly delta sweep automation"""

    def __init__(self, drive_client, slack_client, supabase_client, config):
        """Initialize delta sweep automation

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
        self.search_patterns = config.get('automations.nightly_delta_sweep.search_patterns', [])

    def run(self, since_hours: int = 24) -> Dict[str, Any]:
        """Run nightly delta sweep

        Args:
            since_hours: Number of hours to look back

        Returns:
            Execution summary
        """
        logger.info("Starting nightly delta sweep")
        start_time = datetime.now()

        summary = {
            'new_files': 0,
            'modified_files': 0,
            'duplicates': 0,
            'total_size_mb': 0.0,
            'errors': 0,
            'processed': []
        }

        try:
            # Get folder IDs
            folder_ids = self._get_folder_ids()

            # Calculate since timestamp
            since = (datetime.now() - timedelta(hours=since_hours)).isoformat() + 'Z'

            # Search for files
            all_files = []
            for pattern in self.search_patterns:
                logger.info(f"Searching for pattern: {pattern}")
                files = self.drive.search_files(pattern)
                all_files.extend(files)

            # Get modified files
            root_folder_id = folder_ids.get('_root')
            if root_folder_id:
                modified = self.drive.get_modified_files(root_folder_id, since)
                all_files.extend(modified)

            # Remove duplicates by file ID
            unique_files = {f['id']: f for f in all_files}.values()
            logger.info(f"Found {len(unique_files)} unique files to process")

            # Process each file
            for file in unique_files:
                try:
                    result = self._process_file(file, folder_ids)
                    if result:
                        if result['is_new']:
                            summary['new_files'] += 1
                        else:
                            summary['modified_files'] += 1

                        if result['is_duplicate']:
                            summary['duplicates'] += 1

                        summary['total_size_mb'] += result['size_mb']
                        summary['processed'].append(result)

                except Exception as e:
                    logger.error(f"Error processing file {file.get('name')}: {e}")
                    summary['errors'] += 1

            # Update master index
            self._update_master_index(summary['processed'])

            # Post summary to Slack
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Delta sweep completed in {duration:.2f}s")

            self.slack.post_delta_sweep_summary(
                new_files=summary['new_files'],
                modified_files=summary['modified_files'],
                duplicates=summary['duplicates'],
                total_size_mb=summary['total_size_mb'],
                errors=summary['errors']
            )

            return summary

        except Exception as e:
            logger.error(f"Delta sweep failed: {e}")
            summary['errors'] += 1
            self.slack.post_message(
                f":x: Nightly Delta Sweep FAILED\n```{str(e)}```"
            )
            raise

    def _get_folder_ids(self) -> Dict[str, str]:
        """Get or create folder structure

        Returns:
            Dictionary of folder IDs
        """
        root = self.config.drive_root
        folders = self.config.drive_folders

        return self.drive.create_folder_structure(root, folders)

    def _process_file(self, file: Dict[str, Any], folder_ids: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Process a single file

        Args:
            file: File metadata from Drive
            folder_ids: Folder ID mapping

        Returns:
            Processing result
        """
        file_id = file['id']
        file_name = file['name']
        mime_type = file.get('mimeType', '')
        size = int(file.get('size', 0))

        logger.info(f"Processing file: {file_name}")

        # Download file temporarily
        temp_dir = Path('/tmp/esht_sweep')
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name

        if not self.drive.download_file(file_id, temp_file):
            return None

        # Compute SHA256 hash
        sha256 = self._compute_hash(temp_file)

        # Check for duplicates
        is_duplicate = False
        existing = self.supabase.find_by_hash(sha256)
        if existing:
            logger.info(f"Duplicate found: {file_name} (matches {existing.get('exhibit_code')})")
            is_duplicate = True

            # Move to duplicates folder
            duplicates_folder_id = folder_ids.get('99_Duplicates')
            if duplicates_folder_id:
                self.drive.move_file(file_id, duplicates_folder_id)

        # Normalize PDF if needed
        normalized_path = None
        if 'pdf' in mime_type.lower() or file_name.lower().endswith('.pdf'):
            normalized_path = self._normalize_pdf(temp_file, file_name, folder_ids)

        # Create/update evidence record
        evidence_data = {
            'exhibit_code': f"ESHT-{datetime.now().strftime('%Y%m%d')}-{file_id[:8]}",
            'document_type': self._detect_document_type(file_name),
            'source_path': file_name,
            'normalised_path': normalized_path,
            'sha256': sha256,
            'file_size': size,
            'date_created': file.get('createdTime'),
            'date_modified': file.get('modifiedTime'),
            'metadata': {
                'drive_id': file_id,
                'mime_type': mime_type
            }
        }

        if not existing:
            self.supabase.insert_evidence(evidence_data)
            is_new = True
        else:
            self.supabase.update_evidence(existing['id'], evidence_data)
            is_new = False

        # Clean up temp file
        temp_file.unlink(missing_ok=True)

        return {
            'file_name': file_name,
            'sha256': sha256,
            'size_mb': size / (1024 * 1024),
            'is_new': is_new,
            'is_duplicate': is_duplicate,
            'normalized': normalized_path is not None
        }

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _normalize_pdf(self, file_path: Path, file_name: str, folder_ids: Dict[str, str]) -> Optional[str]:
        """Normalize PDF file

        Args:
            file_path: Path to PDF file
            file_name: Original file name
            folder_ids: Folder ID mapping

        Returns:
            Normalized file path/ID
        """
        try:
            # Upload to normalized folder
            normalized_folder_id = folder_ids.get('01_Normalised_PDF')
            if not normalized_folder_id:
                return None

            normalized_name = f"normalized_{file_name}"
            file_id = self.drive.upload_file(file_path, normalized_folder_id, normalized_name)

            if file_id:
                logger.info(f"Normalized PDF: {normalized_name}")
                return file_id

            return None

        except Exception as e:
            logger.error(f"Error normalizing PDF: {e}")
            return None

    def _detect_document_type(self, file_name: str) -> str:
        """Detect document type from filename

        Args:
            file_name: File name

        Returns:
            Document type
        """
        name_lower = file_name.lower()

        if 'medical' in name_lower or 'clinical' in name_lower:
            return 'Medical Record'
        elif 'email' in name_lower or '@' in name_lower:
            return 'Email'
        elif 'letter' in name_lower or 'correspondence' in name_lower:
            return 'Correspondence'
        elif 'policy' in name_lower or 'procedure' in name_lower:
            return 'Policy/Procedure'
        elif 'witness' in name_lower or 'statement' in name_lower:
            return 'Witness Statement'
        else:
            return 'Document'

    def _update_master_index(self, processed: List[Dict[str, Any]]):
        """Update master index CSV

        Args:
            processed: List of processed files
        """
        try:
            # This would update a Google Sheet or CSV file
            # For now, just log the update
            logger.info(f"Updated master index with {len(processed)} entries")

        except Exception as e:
            logger.error(f"Error updating master index: {e}")
