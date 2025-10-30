#!/usr/bin/env python3
"""
Barker v ESHT - System Setup Script
Performs initial system setup and validation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from orchestrator import ESHTOrchestrator
from core import setup_logging, get_logger

setup_logging(log_level='INFO')
logger = get_logger(__name__)


def main():
    """Run system setup"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   BARKER v ESHT - CASE MANAGEMENT SYSTEM SETUP           ║
║   Version 1.0.0                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    orchestrator = ESHTOrchestrator()

    # Validate configuration
    logger.info("Validating configuration...")
    is_valid, errors = orchestrator.config.validate()

    if not is_valid:
        print("\n❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"   • {error}")
        print("\nPlease fix configuration errors before continuing.")
        print("Check .env file and config/system_config.yaml")
        return 1

    print("\n✅ Configuration validated")

    # Run setup
    print("\n📦 Running system setup...")
    summary = orchestrator.setup_system()

    # Display results
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)

    print("\n🔌 CONNECTIONS:")
    for service, status in summary['connections'].items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {service.replace('_', ' ').title()}")

    if summary.get('folders'):
        print(f"\n📁 FOLDER STRUCTURE:")
        print(f"   Root folder ID: {summary['folders'].get('_root', 'N/A')}")
        print(f"   Total folders created: {len(summary['folders'])}")
        for folder_name, folder_id in summary['folders'].items():
            if folder_name != '_root':
                print(f"      • {folder_name}: {folder_id}")

    if summary.get('databases'):
        print(f"\n🗄️  DATABASE TABLES:")
        for table_name, status in summary['databases'].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {table_name}")

    if summary.get('errors'):
        print(f"\n⚠️  ERRORS ({len(summary['errors'])}):")
        for error in summary['errors']:
            print(f"   • {error}")

    # System status
    status = orchestrator.get_system_status()
    print(f"\n📊 SYSTEM STATUS:")
    print(f"   Case: {status['config']['case_name']}")
    print(f"   Reference: {status['config']['case_reference']}")
    print(f"   Timezone: {status['config']['timezone']}")
    print(f"   Drive Root: {status['config']['drive_root']}")

    print("\n" + "="*60)

    if not summary.get('errors'):
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("   1. Run automations: python scripts/run_automation.py --help")
        print("   2. Start scheduler: python scripts/scheduler.py")
        print("   3. View status: python scripts/status.py")
    else:
        print("\n⚠️  Setup completed with errors. Check logs for details.")

    return 0 if not summary.get('errors') else 1


if __name__ == '__main__':
    sys.exit(main())
