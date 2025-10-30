"""
Barker v ESHT - Google Drive Integration
Handles folder structure, file operations, and evidence management
"""

import os
import io
from pathlib import Path
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)


class GoogleDriveClient:
    """Google Drive API client for case management"""

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, credentials_path: str):
        """Initialize Google Drive client

        Args:
            credentials_path: Path to Google service account JSON or OAuth credentials
        """
        self.credentials_path = credentials_path
        self.service = None
        self.folder_cache = {}
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Try service account first
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Authenticated with Google Drive using service account")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            raise

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder in Google Drive

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)

        Returns:
            Created folder ID
        """
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()

            folder_id = folder.get('id')
            logger.info(f"Created folder '{name}' with ID: {folder_id}")
            return folder_id

        except HttpError as e:
            logger.error(f"Error creating folder '{name}': {e}")
            raise

    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Find a folder by name

        Args:
            name: Folder name
            parent_id: Parent folder ID to search within

        Returns:
            Folder ID if found, None otherwise
        """
        try:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()

            items = results.get('files', [])
            if items:
                folder_id = items[0]['id']
                logger.info(f"Found folder '{name}' with ID: {folder_id}")
                return folder_id

            return None

        except HttpError as e:
            logger.error(f"Error finding folder '{name}': {e}")
            return None

    def get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Get existing folder or create if it doesn't exist

        Args:
            name: Folder name
            parent_id: Parent folder ID

        Returns:
            Folder ID
        """
        folder_id = self.find_folder(name, parent_id)
        if folder_id:
            return folder_id
        return self.create_folder(name, parent_id)

    def create_folder_structure(self, root_name: str, subfolders: List[str]) -> Dict[str, str]:
        """Create complete folder structure

        Args:
            root_name: Root folder name (e.g., 'EvidenceVault/ESHT')
            subfolders: List of subfolder names

        Returns:
            Dictionary mapping folder names to IDs
        """
        folder_ids = {}

        # Create root folder structure
        root_parts = root_name.split('/')
        parent_id = None

        for part in root_parts:
            parent_id = self.get_or_create_folder(part, parent_id)
            folder_ids[part] = parent_id

        # Store root ID
        folder_ids['_root'] = parent_id

        # Create subfolders
        for subfolder in subfolders:
            folder_id = self.get_or_create_folder(subfolder, parent_id)
            folder_ids[subfolder] = folder_id

        logger.info(f"Created folder structure: {len(folder_ids)} folders")
        return folder_ids

    def search_files(self, query: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for files matching query

        Args:
            query: Search query (e.g., 'ESHT' or '@nhs.net')
            folder_id: Folder ID to search within (None for all)

        Returns:
            List of matching files with metadata
        """
        try:
            search_query = f"fullText contains '{query}' and trashed=false"
            if folder_id:
                search_query += f" and '{folder_id}' in parents"

            files = []
            page_token = None

            while True:
                results = self.service.files().list(
                    q=search_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, md5Checksum, parents)',
                    pageSize=100,
                    pageToken=page_token
                ).execute()

                files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')

                if not page_token:
                    break

            logger.info(f"Found {len(files)} files matching '{query}'")
            return files

        except HttpError as e:
            logger.error(f"Error searching files: {e}")
            return []

    def get_modified_files(self, folder_id: str, since: str) -> List[Dict[str, Any]]:
        """Get files modified since a specific date

        Args:
            folder_id: Folder ID to search
            since: ISO 8601 datetime string

        Returns:
            List of modified files
        """
        try:
            query = f"modifiedTime > '{since}' and trashed=false and '{folder_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime, createdTime, md5Checksum)',
                pageSize=1000
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} files modified since {since}")
            return files

        except HttpError as e:
            logger.error(f"Error getting modified files: {e}")
            return []

    def download_file(self, file_id: str, destination: Path) -> bool:
        """Download a file from Google Drive

        Args:
            file_id: File ID to download
            destination: Local destination path

        Returns:
            True if successful
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            destination.parent.mkdir(parents=True, exist_ok=True)

            with io.FileIO(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download {int(status.progress() * 100)}%")

            logger.info(f"Downloaded file {file_id} to {destination}")
            return True

        except HttpError as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return False

    def upload_file(self, file_path: Path, folder_id: str, name: Optional[str] = None) -> Optional[str]:
        """Upload a file to Google Drive

        Args:
            file_path: Local file path
            folder_id: Destination folder ID
            name: Optional custom name (defaults to file_path.name)

        Returns:
            Uploaded file ID if successful
        """
        try:
            file_name = name or file_path.name
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(
                str(file_path),
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get('id')
            logger.info(f"Uploaded {file_name} with ID: {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"Error uploading {file_path}: {e}")
            return None

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata

        Args:
            file_id: File ID

        Returns:
            File metadata dictionary
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, createdTime, md5Checksum, parents'
            ).execute()
            return file

        except HttpError as e:
            logger.error(f"Error getting file metadata: {e}")
            return None

    def move_file(self, file_id: str, new_parent_id: str) -> bool:
        """Move a file to a different folder

        Args:
            file_id: File ID to move
            new_parent_id: New parent folder ID

        Returns:
            True if successful
        """
        try:
            # Get current parents
            file = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()

            previous_parents = ','.join(file.get('parents', []))

            # Move file
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            logger.info(f"Moved file {file_id} to {new_parent_id}")
            return True

        except HttpError as e:
            logger.error(f"Error moving file: {e}")
            return False
