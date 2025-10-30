#!/usr/bin/env python3
"""
Barker v ESHT - Run Automation Script
Execute individual automations on-demand
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from orchestrator import ESHTOrchestrator
from core import setup_logging, get_logger

setup_logging(log_level='INFO')
logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Run ESHT case management automations'
    )

    parser.add_argument(
        'automation',
        choices=['sweep', 'export', 'bundle', 'kpi', 'all'],
        help='Automation to run'
    )

    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Hours to look back for delta sweep (default: 24)'
    )

    parser.add_argument(
        '--bundle-name',
        type=str,
        help='Custom bundle name for bundle builder'
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"ESHT AUTOMATION: {args.automation.upper()}")
    print(f"{'='*60}\n")

    # Initialize orchestrator
    orchestrator = ESHTOrchestrator()
    orchestrator.initialize_connections()

    try:
        if args.automation == 'sweep' or args.automation == 'all':
            print("\n🔍 Running Nightly Delta Sweep...")
            result = orchestrator.run_nightly_sweep(args.hours)
            print(f"\n✅ Delta Sweep Complete:")
            print(f"   • New files: {result.get('new_files', 0)}")
            print(f"   • Modified: {result.get('modified_files', 0)}")
            print(f"   • Duplicates: {result.get('duplicates', 0)}")
            print(f"   • Errors: {result.get('errors', 0)}")

        if args.automation == 'export' or args.automation == 'all':
            print("\n📊 Running Weekly AEON Export...")
            result = orchestrator.run_weekly_export()
            print(f"\n✅ AEON Export Complete:")
            print(f"   • Events: {result.get('event_count', 0)}")
            print(f"   • Categories: {len(result.get('categories', {}))}")

        if args.automation == 'bundle' or args.automation == 'all':
            print("\n📚 Running Bundle Builder...")
            result = orchestrator.run_bundle_builder(args.bundle_name)
            print(f"\n✅ Bundle Complete:")
            print(f"   • Bundle: {result.get('bundle_name', 'N/A')}")
            print(f"   • Exhibits: {result.get('exhibit_count', 0)}")
            print(f"   • Pages: {result.get('page_count', 0)}")

        if args.automation == 'kpi' or args.automation == 'all':
            print("\n📈 Running KPI Report...")
            result = orchestrator.run_kpi_report()
            print(f"\n✅ KPI Report Complete:")
            print(f"   • Evidence with codes: {result.get('evidence_with_codes_pct', '0%')}")
            print(f"   • Total evidence: {result.get('total_evidence_items', 0)}")
            print(f"   • Open tasks: {result.get('total_open_tasks', 0)}")

        print(f"\n{'='*60}")
        print("✅ All automations completed successfully!")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        print(f"\n❌ Automation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
