"""
Barker v ESHT - Configuration Manager
Handles system configuration, credentials, and environment setup
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Central configuration manager for the ESHT case management system"""

    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """Initialize configuration

        Args:
            config_path: Path to system_config.yaml
            env_path: Path to .env file
        """
        self.base_dir = Path(__file__).parent.parent.parent

        # Load environment variables
        env_file = env_path or self.base_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
        else:
            logger.warning(f".env file not found at {env_file}")

        # Load YAML configuration
        config_file = config_path or self.base_dir / 'config' / 'system_config.yaml'
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Loaded system configuration from {config_file}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'case.name')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value
        """
        return os.getenv(key, default)

    @property
    def case_name(self) -> str:
        return self.get('case.name', 'Barker v ESHT')

    @property
    def case_reference(self) -> str:
        return self.get('case.reference', 'BB_ESHT')

    @property
    def timezone(self) -> str:
        return self.get('case.timezone', 'Europe/London')

    @property
    def drive_root(self) -> str:
        return self.get('drive_structure.root', 'EvidenceVault/ESHT')

    @property
    def drive_folders(self) -> list:
        return self.get('drive_structure.folders', [])

    @property
    def database_schema(self) -> Dict[str, Any]:
        return self.get('database_schema', {})

    @property
    def automations(self) -> Dict[str, Any]:
        return self.get('automations', {})

    @property
    def integrations(self) -> Dict[str, Any]:
        return self.get('integrations', {})

    # Google credentials
    @property
    def google_credentials_path(self) -> str:
        return self.get_env('GOOGLE_DRIVE_CREDENTIALS_PATH', './config/google_credentials.json')

    @property
    def google_calendar_id(self) -> str:
        return self.get_env('GOOGLE_CALENDAR_ID', 'primary')

    # Slack
    @property
    def slack_token(self) -> Optional[str]:
        return self.get_env('SLACK_BOT_TOKEN')

    @property
    def slack_channel(self) -> str:
        return self.get_env('SLACK_CHANNEL_ALL_BEN', '#all-ben')

    # Notion
    @property
    def notion_token(self) -> Optional[str]:
        return self.get_env('NOTION_TOKEN')

    @property
    def notion_database_evidence_id(self) -> Optional[str]:
        return self.get_env('NOTION_DATABASE_EVIDENCE_ID')

    @property
    def notion_database_issues_id(self) -> Optional[str]:
        return self.get_env('NOTION_DATABASE_ISSUES_ID')

    @property
    def notion_database_timeline_id(self) -> Optional[str]:
        return self.get_env('NOTION_DATABASE_TIMELINE_ID')

    @property
    def notion_database_tasks_id(self) -> Optional[str]:
        return self.get_env('NOTION_DATABASE_TASKS_ID')

    # Todoist
    @property
    def todoist_token(self) -> Optional[str]:
        return self.get_env('TODOIST_API_TOKEN')

    @property
    def todoist_project(self) -> str:
        return self.get_env('TODOIST_PROJECT_NAME', 'Barker v ESHT')

    # PDF.co
    @property
    def pdfco_api_key(self) -> Optional[str]:
        return self.get_env('PDFCO_API_KEY')

    # Supabase
    @property
    def supabase_url(self) -> Optional[str]:
        return self.get_env('SUPABASE_URL')

    @property
    def supabase_key(self) -> Optional[str]:
        return self.get_env('SUPABASE_KEY')

    @property
    def supabase_service_key(self) -> Optional[str]:
        return self.get_env('SUPABASE_SERVICE_KEY')

    @property
    def log_level(self) -> str:
        return self.get_env('LOG_LEVEL', 'INFO')

    def validate(self) -> tuple[bool, list]:
        """Validate configuration and credentials

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check critical paths
        if not Path(self.google_credentials_path).exists():
            errors.append(f"Google credentials not found: {self.google_credentials_path}")

        # Check required tokens
        if not self.slack_token:
            errors.append("SLACK_BOT_TOKEN not set")

        if not self.notion_token:
            errors.append("NOTION_TOKEN not set")

        if not self.supabase_url or not self.supabase_key:
            errors.append("Supabase configuration incomplete")

        return len(errors) == 0, errors


# Singleton instance
_config_instance = None


def get_config() -> Config:
    """Get or create singleton configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
