#!/usr/bin/env python3
"""
Barker v ESHT - Automation Scheduler
Runs automations on schedule according to system configuration
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import schedule

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from orchestrator import ESHTOrchestrator
from core import setup_logging, get_logger

setup_logging(log_level='INFO')
logger = get_logger(__name__)

# Global orchestrator
orchestrator = None


def run_nightly_sweep():
    """Scheduled nightly delta sweep"""
    try:
        logger.info("Scheduled: Running nightly delta sweep")
        orchestrator.run_nightly_sweep(since_hours=24)
    except Exception as e:
        logger.error(f"Scheduled nightly sweep failed: {e}", exc_info=True)


def run_weekly_export():
    """Scheduled weekly AEON export"""
    try:
        logger.info("Scheduled: Running weekly AEON export")
        orchestrator.run_weekly_export()
    except Exception as e:
        logger.error(f"Scheduled weekly export failed: {e}", exc_info=True)


def run_weekly_kpi():
    """Scheduled weekly KPI report"""
    try:
        logger.info("Scheduled: Running weekly KPI report")
        orchestrator.run_kpi_report()
    except Exception as e:
        logger.error(f"Scheduled weekly KPI failed: {e}", exc_info=True)


def main():
    """Main scheduler loop"""
    global orchestrator

    print("""
╔═══════════════════════════════════════════════════════════╗
║   BARKER v ESHT - AUTOMATION SCHEDULER                   ║
║   Running automations on schedule...                      ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    orchestrator = ESHTOrchestrator()
    orchestrator.initialize_connections()

    # Get automation config
    config = orchestrator.config

    # Schedule nightly delta sweep
    nightly_sweep_config = config.get('automations.nightly_delta_sweep', {})
    if nightly_sweep_config.get('enabled', True):
        # Schedule at 02:00 daily
        schedule.every().day.at("02:00").do(run_nightly_sweep)
        logger.info("Scheduled: Nightly Delta Sweep at 02:00 daily")
        print("✅ Nightly Delta Sweep: 02:00 daily")

    # Schedule weekly AEON export
    aeon_config = config.get('automations.weekly_aeon_export', {})
    if aeon_config.get('enabled', True):
        # Schedule Friday at 18:00
        schedule.every().friday.at("18:00").do(run_weekly_export)
        logger.info("Scheduled: Weekly AEON Export Friday at 18:00")
        print("✅ Weekly AEON Export: Friday 18:00")

    # Schedule weekly KPI report
    kpi_config = config.get('automations.weekly_kpi_report', {})
    if kpi_config.get('enabled', True):
        # Schedule Friday at 18:15
        schedule.every().friday.at("18:15").do(run_weekly_kpi)
        logger.info("Scheduled: Weekly KPI Report Friday at 18:15")
        print("✅ Weekly KPI Report: Friday 18:15")

    print(f"\n🕐 Scheduler started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to stop\n")

    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped by user")
        logger.info("Scheduler stopped")
        return 0

    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        print(f"\n❌ Scheduler error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
