# Barker v ESHT - Deployment Guide

Complete deployment and configuration guide for the ESHT case management system.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Service Setup](#service-setup)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Database Initialization](#database-initialization)
6. [Verification](#verification)
7. [Production Deployment](#production-deployment)
8. [Monitoring Setup](#monitoring-setup)

---

## Prerequisites

### System Requirements
- **OS:** Linux, macOS, or Windows with WSL
- **Python:** 3.9 or higher
- **Memory:** 2GB minimum
- **Disk:** 10GB minimum for logs and cache
- **Network:** Stable internet connection

### Required Accounts & Services
- Google Cloud Platform (GCP) account
- Slack workspace
- Notion workspace
- Supabase account
- Todoist account (optional)
- PDF.co account (optional)

---

## Service Setup

### 1. Google Cloud Platform

**Create Service Account:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable Google Drive API
4. Create service account:
   - IAM & Admin → Service Accounts → Create
   - Name: `esht-automation`
   - Role: `Editor` or custom with Drive access
5. Create JSON key:
   - Click on service account
   - Keys → Add Key → JSON
   - Download and save as `config/google_credentials.json`

**Share Drive Folder:**
1. Create root folder in Google Drive
2. Share with service account email
3. Grant edit permissions

### 2. Slack

**Create Slack App:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create New App → From Scratch
3. Name: `ESHT Case Manager`
4. Select workspace

**Configure Permissions:**
Add these OAuth scopes:
- `chat:write`
- `files:write`
- `channels:read`
- `groups:read`

**Install to Workspace:**
1. Install App to workspace
2. Copy Bot User OAuth Token
3. Save as `SLACK_BOT_TOKEN` in `.env`

**Create Channel:**
1. Create `#all-ben` channel in Slack
2. Invite bot to channel: `/invite @ESHT Case Manager`

### 3. Notion

**Create Integration:**
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. New Integration → Name: `ESHT Automation`
3. Copy Internal Integration Token
4. Save as `NOTION_TOKEN` in `.env`

**Create Command Centre:**
1. Create page: "Barker v ESHT — Command Centre"
2. Share with integration
3. Note page ID from URL

**Database Setup:**
- Databases will be created automatically by setup script
- Or create manually in Notion and note database IDs

### 4. Supabase

**Create Project:**
1. Go to [supabase.com](https://supabase.com)
2. New Project
3. Name: `esht-case-management`
4. Region: Select closest to UK
5. Database password: Strong password

**Get Credentials:**
1. Project Settings → API
2. Copy:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`

**Database Setup:**
1. SQL Editor → New Query
2. Paste contents of `scripts/database_setup.sql`
3. Run query

### 5. PDF.co (Optional)

**Get API Key:**
1. Sign up at [pdf.co](https://pdf.co)
2. Get API key from dashboard
3. Save as `PDFCO_API_KEY` in `.env`

### 6. Todoist (Optional)

**Get API Token:**
1. Todoist Settings → Integrations
2. API Token → Copy
3. Save as `TODOIST_API_TOKEN` in `.env`

**Create Project:**
1. Create project: "Barker v ESHT"
2. Note project name

---

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd barker-esht-orchestration
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.template .env
```

Edit `.env` with your credentials:
```bash
nano .env  # or use your preferred editor
```

### 5. Add Google Credentials
```bash
# Place Google service account JSON
cp /path/to/downloaded/key.json config/google_credentials.json
```

### 6. Verify File Structure
```bash
tree -L 2
```

Should show:
```
barker-esht-orchestration/
├── config/
│   ├── system_config.yaml
│   └── google_credentials.json
├── src/
├── scripts/
├── .env
└── requirements.txt
```

---

## Configuration

### Environment Variables

**Minimal `.env` Configuration:**
```bash
# Google
GOOGLE_DRIVE_CREDENTIALS_PATH=./config/google_credentials.json
GOOGLE_CALENDAR_ID=primary
GOOGLE_TIMEZONE=Europe/London

# Slack
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL_ALL_BEN=#all-ben

# Notion
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_EVIDENCE_ID=
NOTION_DATABASE_ISSUES_ID=
NOTION_DATABASE_TIMELINE_ID=
NOTION_DATABASE_TASKS_ID=

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Case Config
CASE_NAME=Barker v ESHT
CASE_ROOT_FOLDER=EvidenceVault/ESHT

# Logging
LOG_LEVEL=INFO
```

### System Configuration

Edit `config/system_config.yaml` to customize:
- Folder structure
- Automation schedules
- Database schema
- Integration settings

---

## Database Initialization

### Option 1: Automatic (via setup script)
```bash
python scripts/setup.py
```

### Option 2: Manual (Supabase)
1. Open Supabase SQL Editor
2. Copy `scripts/database_setup.sql`
3. Paste and execute

### Option 3: Manual (Notion)
Databases created automatically by setup script, or:
1. Run setup: `python scripts/setup.py`
2. Note database IDs from output
3. Update `.env` with database IDs

---

## Verification

### 1. Run Setup Script
```bash
python scripts/setup.py
```

**Expected Output:**
```
✅ Configuration validated
✅ Google Drive connected
✅ Slack connected
✅ Notion connected
✅ Supabase connected
📁 Folder structure created: 9 folders
🗄️  Database tables created: 4 tables
✅ Setup completed successfully!
```

### 2. Test Connections
```python
from src.orchestrator import ESHTOrchestrator

orchestrator = ESHTOrchestrator()
status = orchestrator.initialize_connections()
print(status)
# Should show all True
```

### 3. Run Test Automation
```bash
# Run delta sweep with 1 hour lookback
python scripts/run_automation.py sweep --hours 1
```

### 4. Check Slack
Verify notification appeared in #all-ben channel

### 5. Check Drive
Verify folder structure created in Google Drive

### 6. Check Database
```sql
-- In Supabase SQL Editor
SELECT * FROM evidence LIMIT 5;
SELECT * FROM issues LIMIT 5;
```

---

## Production Deployment

### Option 1: Systemd Service (Linux)

**Create service file:**
```bash
sudo nano /etc/systemd/system/esht-scheduler.service
```

**Service configuration:**
```ini
[Unit]
Description=ESHT Case Management Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/barker-esht-orchestration
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python scripts/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable esht-scheduler
sudo systemctl start esht-scheduler
sudo systemctl status esht-scheduler
```

**View logs:**
```bash
sudo journalctl -u esht-scheduler -f
```

### Option 2: Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "scripts/scheduler.py"]
```

**Build and run:**
```bash
docker build -t esht-orchestration .
docker run -d --name esht-scheduler \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  esht-orchestration
```

### Option 3: Cloud Deployment (AWS/GCP/Azure)

**Using Cloud Functions/Lambda:**
1. Package application
2. Deploy each automation as separate function
3. Use cloud scheduler for cron triggers
4. Configure environment variables in cloud

### Option 4: Supervisor (Alternative)

**Install supervisor:**
```bash
sudo apt-get install supervisor
```

**Create config:**
```bash
sudo nano /etc/supervisor/conf.d/esht-scheduler.conf
```

```ini
[program:esht-scheduler]
command=/path/to/venv/bin/python /path/to/scripts/scheduler.py
directory=/path/to/barker-esht-orchestration
user=your-user
autostart=true
autorestart=true
stderr_logfile=/var/log/esht-scheduler.err.log
stdout_logfile=/var/log/esht-scheduler.out.log
```

**Start:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start esht-scheduler
```

---

## Monitoring Setup

### 1. Log Monitoring

**Install log monitoring tool:**
```bash
# Option A: Logwatch
sudo apt-get install logwatch

# Option B: GoAccess for real-time
tail -f logs/automation.log | grep ERROR
```

### 2. Slack Alerts

Already configured! All automations post to Slack.

**Custom alerts:**
```python
# In your automation code
if error_count > 5:
    slack.post_message(
        ":rotating_light: High error rate detected!",
        channel="#alerts"
    )
```

### 3. Health Check Endpoint

**Create health check script:**
```python
# scripts/health_check.py
from src.orchestrator import ESHTOrchestrator

def health_check():
    orchestrator = ESHTOrchestrator()
    status = orchestrator.get_system_status()

    # Check all connections
    all_ok = all(status['connections'].values())

    if all_ok:
        print("OK")
        return 0
    else:
        print("FAILED")
        return 1

if __name__ == '__main__':
    exit(health_check())
```

**Add to cron:**
```bash
crontab -e

# Run health check every 15 minutes
*/15 * * * * cd /path/to/barker-esht-orchestration && /path/to/venv/bin/python scripts/health_check.py
```

### 4. External Monitoring

**UptimeRobot / Pingdom:**
- Create HTTP monitor for health check endpoint
- Alert on failures

**Slack Webhooks:**
- Send status updates to dedicated channel
- Configure alerts for failures

---

## Backup & Recovery

### Database Backups

**Supabase:**
- Automatic daily backups included
- Manual backup via dashboard
- Export to SQL file

**Export Evidence:**
```bash
python -c "
from src.orchestrator import ESHTOrchestrator
o = ESHTOrchestrator()
o.initialize_connections()
evidence = o.supabase.query_evidence()
import json
with open('backup_evidence.json', 'w') as f:
    json.dump(evidence, f, default=str)
"
```

### Drive Backups

Google Drive has built-in versioning and recovery.

### Configuration Backups

```bash
# Backup config (excluding secrets)
tar -czf backup_config_$(date +%Y%m%d).tar.gz \
  config/system_config.yaml \
  requirements.txt \
  README.md
```

---

## Security Hardening

### 1. File Permissions
```bash
chmod 600 .env
chmod 600 config/google_credentials.json
chmod 755 scripts/*.py
```

### 2. Firewall Rules
```bash
# Allow only necessary outbound connections
# Block inbound except SSH (if applicable)
```

### 3. API Key Rotation
- Rotate every 90 days
- Update in `.env`
- Restart services

### 4. Audit Logging
All operations logged automatically to:
- `logs/system.log`
- `logs/automation.log`
- `logs/error.log`

---

## Troubleshooting

### Common Issues

**1. Google Auth Fails**
```bash
# Check credentials file
cat config/google_credentials.json | jq .

# Verify service account email
# Verify Drive folder shared with service account
```

**2. Slack Messages Not Sending**
```bash
# Test token
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test

# Check bot invited to channel
```

**3. Database Connection Fails**
```bash
# Test Supabase connection
curl $SUPABASE_URL/rest/v1/ \
  -H "apikey: $SUPABASE_KEY"
```

**4. Scheduler Not Running**
```bash
# Check process
ps aux | grep scheduler

# Check logs
tail -f logs/system.log
```

---

## Rollback Procedures

**If deployment fails:**

1. Stop services
```bash
sudo systemctl stop esht-scheduler
# or
docker stop esht-scheduler
```

2. Restore previous version
```bash
git checkout <previous-commit>
```

3. Restore configuration
```bash
tar -xzf backup_config_20241030.tar.gz
```

4. Restart services
```bash
sudo systemctl start esht-scheduler
```

---

## Next Steps

After successful deployment:

1. ✅ Monitor first automation run
2. ✅ Review Slack notifications
3. ✅ Check evidence indexing
4. ✅ Verify KPI reports
5. ✅ Setup regular backups
6. ✅ Document any customizations

---

## Support Contacts

- **Technical Issues:** System administrator
- **Service Outages:** Check service status pages
- **Emergency:** [Contact information]

---

**Deployment Checklist:**
- [ ] All prerequisites met
- [ ] Services configured
- [ ] Environment variables set
- [ ] Google credentials added
- [ ] Database initialized
- [ ] Setup script run successfully
- [ ] Test automation executed
- [ ] Slack notifications received
- [ ] Production service deployed
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Documentation updated
