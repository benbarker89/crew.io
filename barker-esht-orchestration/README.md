# Barker v ESHT - Legal Case Management System

**Version:** 1.0.0
**Case:** Barker v East Sussex Healthcare NHS Trust
**Purpose:** Integrated, automated case management orchestration platform

---

## Overview

This system provides a comprehensive, automated case management platform for the Barker v ESHT legal case. It integrates with multiple services (Google Drive, Slack, Notion, Todoist, Supabase, PDF.co) to create a single source of truth for all case data, automations, and analytics.

## Features

### Phase 1: Discovery & Setup
- ✅ Automated folder structure creation in Google Drive
- ✅ Database schema deployment (Supabase/Notion)
- ✅ Connection validation and health checks
- ✅ Idempotent setup (safe to run multiple times)

### Phase 2: Automations
- ✅ **Nightly Delta Sweep** (02:00 UK) - Finds new/modified files, normalizes PDFs, deduplicates
- ✅ **Weekly AEON Export** (Fri 18:00) - Exports timeline to AEON-compatible CSV
- ✅ **Monthly Bundle Builder** (Manual trigger) - Creates exhibit bundles with stamped pages
- ✅ **Weekly KPI Report** (Fri 18:15) - Generates comprehensive analytics

### Phase 3: Reporting & Dashboards
- ✅ KPI metrics tracking
- ✅ Evidence coverage analysis
- ✅ Timeline completeness
- ✅ Task management insights
- ✅ Automated Slack notifications

### Phase 4: LLM Tools
- ✅ Issue Mapper - Links evidence to legal issues
- ✅ Quote Extractor - Extracts key quotes from documents
- ✅ JSON/CSV exports for external tools

---

## Architecture

```
barker-esht-orchestration/
├── config/
│   ├── system_config.yaml      # System configuration
│   └── google_credentials.json # Google service account (not in git)
├── src/
│   ├── core/
│   │   ├── config.py           # Configuration manager
│   │   └── logger.py           # Structured logging
│   ├── integrations/
│   │   ├── google_drive.py     # Drive API client
│   │   ├── slack_client.py     # Slack notifications
│   │   ├── notion_client.py    # Notion databases
│   │   └── supabase_client.py  # PostgreSQL operations
│   ├── automations/
│   │   ├── delta_sweep.py      # Nightly file sweep
│   │   ├── aeon_export.py      # Timeline export
│   │   ├── bundle_builder.py   # Evidence bundling
│   │   └── kpi_reporter.py     # Analytics
│   ├── utils/
│   │   └── llm_tools.py        # LLM analysis tools
│   └── orchestrator.py         # Main orchestration engine
├── scripts/
│   ├── setup.py                # Initial setup
│   ├── run_automation.py       # Run automations on-demand
│   ├── scheduler.py            # Automated scheduler
│   └── database_setup.sql      # Database schema
├── logs/                       # Log files (auto-created)
├── data/                       # Local data cache
├── .env                        # Environment variables (not in git)
├── .env.template               # Template for credentials
└── requirements.txt            # Python dependencies
```

---

## Installation

### Prerequisites
- Python 3.9+
- Google Cloud service account with Drive API access
- Slack workspace with bot token
- Notion integration token
- Supabase project
- PDF.co API key (optional, for PDF stamping)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd barker-esht-orchestration
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
cp .env.template .env
# Edit .env with your credentials
```

### Step 4: Add Google Credentials
Place your Google service account JSON file at:
```
config/google_credentials.json
```

### Step 5: Setup Database
If using Supabase, run the setup SQL:
```bash
# Copy scripts/database_setup.sql to Supabase SQL Editor and execute
```

### Step 6: Run Initial Setup
```bash
python scripts/setup.py
```

This will:
- Validate all credentials
- Create Google Drive folder structure
- Initialize database tables
- Test all connections

---

## Usage

### Run Automations On-Demand

**Nightly Delta Sweep:**
```bash
python scripts/run_automation.py sweep --hours 24
```

**Weekly AEON Export:**
```bash
python scripts/run_automation.py export
```

**Bundle Builder:**
```bash
python scripts/run_automation.py bundle --bundle-name "ESHT_Bundle_202410"
```

**KPI Report:**
```bash
python scripts/run_automation.py kpi
```

**Run All:**
```bash
python scripts/run_automation.py all
```

### Start Automated Scheduler

For continuous operation with scheduled automations:
```bash
python scripts/scheduler.py
```

This runs automations on schedule:
- Delta Sweep: Daily at 02:00 UK time
- AEON Export: Friday at 18:00 UK time
- KPI Report: Friday at 18:15 UK time

### Using the Orchestrator Programmatically

```python
from src.orchestrator import ESHTOrchestrator

# Initialize
orchestrator = ESHTOrchestrator()

# Run setup
setup_summary = orchestrator.setup_system()

# Run specific automation
result = orchestrator.run_nightly_sweep(since_hours=24)

# Get system status
status = orchestrator.get_system_status()
```

---

## Configuration

### System Configuration (`config/system_config.yaml`)

Key settings:
- **Case details:** Name, reference, timezone
- **Folder structure:** Drive folder hierarchy
- **Database schema:** Table definitions
- **Automation schedules:** Cron expressions and settings
- **Integration rate limits:** API throttling

### Environment Variables (`.env`)

Required:
```bash
# Google
GOOGLE_DRIVE_CREDENTIALS_PATH=./config/google_credentials.json

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ALL_BEN=#all-ben

# Notion
NOTION_TOKEN=secret_your_token
NOTION_DATABASE_EVIDENCE_ID=database_id
NOTION_DATABASE_ISSUES_ID=database_id
NOTION_DATABASE_TIMELINE_ID=database_id
NOTION_DATABASE_TASKS_ID=database_id

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# PDF.co (optional)
PDFCO_API_KEY=your_api_key
```

---

## Database Schema

### Evidence Table
Stores all evidence items with metadata, hashes, and exhibit codes.

### Issues Table
Legal issues with categorization and evidence linkage.

### Timeline Table
Chronological events with multi-dimensional categorization.

### Tasks Table
Action items with workstream tracking and Todoist integration.

See `scripts/database_setup.sql` for full schema.

---

## Automations

### 1. Nightly Delta Sweep
**Schedule:** Daily 02:00 UK
**Purpose:** Discover and process new/modified evidence

**Process:**
1. Search Drive for files matching patterns (ESHT, @nhs.net)
2. Compute SHA256 hashes for deduplication
3. Normalize PDFs to standard format
4. Update master index
5. Post summary to Slack

**Output:**
- Normalized PDFs in `01_Normalised_PDF/`
- Duplicates moved to `99_Duplicates/`
- Log files in `97_Logs/run-{timestamp}/`

### 2. Weekly AEON Export
**Schedule:** Friday 18:00 UK
**Purpose:** Export timeline for AEON Timeline software

**Process:**
1. Query all timeline events from database
2. Generate category histogram
3. Export to AEON-compatible CSV format
4. Upload to `05_Indexes/`
5. Post summary to Slack

**Output:**
- `05_Indexes/AEON_Timeline_Export.csv`

### 3. Monthly Bundle Builder
**Schedule:** Manual trigger
**Purpose:** Create exhibit bundles for court submission

**Process:**
1. Gather all exhibits marked with `used_in`
2. Sort by exhibit code
3. Merge PDFs with page stamping
4. Generate bundle index
5. Upload to `Bundles/{bundle_name}/`
6. Post summary to Slack

**Output:**
- `Bundles/ESHT_Bundle_{YYYYMM}/{bundle}.pdf`
- `Bundles/ESHT_Bundle_{YYYYMM}/Bundle_Index.csv`

### 4. Weekly KPI Report
**Schedule:** Friday 18:15 UK
**Purpose:** Generate case analytics and metrics

**Metrics:**
- % Evidence with exhibit codes
- Average exhibits per issue
- Timeline completeness (events/month)
- Open tasks by workstream
- Hearing readiness score

**Output:**
- `05_Indexes/BB_ESHT_KPI_Report.xlsx`

---

## LLM Analysis Tools

### Issue Mapper
Maps evidence to legal issues using LLM analysis.

```python
from src.utils.llm_tools import IssueMapper

mapper = IssueMapper(supabase_client, config)

# Analyze single evidence item
result = mapper.analyze_evidence(evidence_id)

# Batch analysis
results = mapper.batch_analyze([id1, id2, id3])

# Export to JSON
mapper.export_to_json('05_Indexes/BB_ESHT_IssueMapping.json')
```

### Quote Extractor
Extracts key quotes from evidence documents.

```python
from src.utils.llm_tools import QuoteExtractor

extractor = QuoteExtractor(drive_client, supabase_client, config)

# Extract quotes
quotes = extractor.extract_quotes(evidence_id, context="Medical negligence")

# Batch extraction
all_quotes = extractor.batch_extract([id1, id2, id3])
```

---

## Logging

All operations are logged with structured JSON format:

**Log Files:**
- `logs/system.log` - All operations
- `logs/error.log` - Errors only
- `logs/automation.log` - Automation runs

**Log Rotation:**
- Daily rotation
- 90-day retention

**Log Format:**
```json
{
  "timestamp": "2024-10-30T10:30:00Z",
  "level": "INFO",
  "logger": "automation.delta_sweep",
  "message": "Delta sweep completed",
  "module": "delta_sweep",
  "function": "run"
}
```

---

## Monitoring & Notifications

All automations post summaries to Slack (#all-ben) with:
- Execution status (Success/Warning/Error)
- Key metrics
- Error details (if any)
- Links to outputs

---

## Security

### Credentials
- Never commit `.env` or Google credentials to git
- Use environment variables for all secrets
- Rotate API keys regularly

### Database
- Row-level security enabled in Supabase
- Service key required for admin operations
- Audit logs for all modifications

### API Rate Limiting
- Configured per integration in `system_config.yaml`
- Automatic retry with exponential backoff
- Graceful degradation on failures

---

## Troubleshooting

### Setup Fails
1. Check `.env` file has all required variables
2. Verify Google credentials file exists
3. Test network connectivity to services
4. Check logs in `logs/system.log`

### Automation Errors
1. Check Slack for error notifications
2. Review `logs/automation.log`
3. Verify service quotas not exceeded
4. Check file permissions

### Database Issues
1. Verify Supabase connection
2. Check RLS policies
3. Ensure tables created correctly
4. Review `logs/error.log`

---

## Maintenance

### Daily
- Monitor Slack notifications
- Check automation execution

### Weekly
- Review KPI reports
- Verify evidence indexing
- Check disk space

### Monthly
- Review logs and errors
- Update dependencies
- Rotate API keys
- Archive old logs

---

## Development

### Adding New Automations

1. Create automation class in `src/automations/`
2. Implement `run()` method
3. Add to orchestrator in `src/orchestrator.py`
4. Update configuration in `config/system_config.yaml`
5. Add CLI command in `scripts/run_automation.py`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

---

## Support

For issues or questions:
1. Check logs first
2. Review this documentation
3. Contact system administrator
4. Raise issue in project tracker

---

## License

Proprietary - Barker v ESHT Case Management
© 2024 All Rights Reserved

---

## Changelog

### Version 1.0.0 (2024-10-30)
- Initial release
- All Phase 1-4 features implemented
- Full automation suite operational
- Comprehensive documentation
