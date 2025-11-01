# Quick Start Guide

Get up and running with the Legal Case Management System in 5 minutes!

## Installation

### Option 1: Using the Startup Script (Recommended)

1. Open a terminal and navigate to the project directory:
   ```bash
   cd my-legal-system
   ```

2. Run the startup script:
   ```bash
   ./start.sh
   ```

3. Open your browser and go to:
   ```
   http://localhost:8000/frontend/index.html
   ```

### Option 2: Manual Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```bash
   cd backend
   python3 models.py
   ```

3. Start the server:
   ```bash
   python3 main.py
   ```

4. Open your browser:
   ```
   http://localhost:8000/frontend/index.html
   ```

## First Steps

### 1. Create Your First Case

1. Click **"+ New Case"** in the navigation bar
2. Fill in the details:
   - **Case Number**: ET-2025-001
   - **Title**: Your case name
   - **Case Type**: Select from dropdown (e.g., Employment Tribunal)
   - **Priority**: Choose urgency level
   - **Mission Statement**: "Secure compensation for discrimination"
3. Click **"Create Case"**

### 2. Add Milestones

1. In the case view, go to the **"Milestones"** tab
2. Click **"+ Add Milestone"**
3. Example milestones:
   - Complete ACAS Early Conciliation (Pre-action)
   - File ET1 claim (Procedural)
   - Compile witness statements (Evidence)
   - Attend preliminary hearing (Hearing)

### 3. Create Tasks

1. Go to the **"Tasks"** tab
2. Click **"+ Add Task"**
3. Example tasks:
   - Draft witness statement for John Doe
   - Obtain medical records from GP
   - Review respondent's ET3 response
   - Due date: Set realistic deadlines
   - Estimated hours: 2-4 hours per task

### 4. Upload Documents

1. Navigate to **"Documents"** tab
2. Click **"+ Upload Document"**
3. Select category:
   - Pleadings (claim forms, responses)
   - Evidence (witness statements, documents)
   - Correspondence (letters, emails)
   - Orders (tribunal orders, judgments)

### 5. Check Your Next Steps

1. Return to the **Dashboard**
2. View the **"YOUR NEXT STEPS"** section
3. The system will automatically recommend:
   - Urgent tasks (overdue)
   - Critical tasks (deadline within 7 days)
   - Next priorities (logical next actions)
   - Recommended maintenance tasks

## Example Workflow

### Employment Tribunal Case

**Step 1: Create Case**
- Case: ET-2025-001
- Title: Smith v. ESHT
- Mission: "Secure maximum compensation for disability discrimination"

**Step 2: Add Milestones**
- ✅ Complete ACAS conciliation
- ✅ File ET1 claim
- 🔄 Compile witness statements (60%)
- ⬜ Complete disclosure
- ⬜ Hearing bundle
- ⬜ Preliminary hearing

**Step 3: Add Tasks**
- Draft witness statement (Due: 7 days)
- Obtain medical records (Due: 14 days)
- Review ET3 response (Due: 3 days)

**Step 4: Upload Documents**
- ET1 claim form → Pleadings
- Medical reports → Evidence
- Email correspondence → Correspondence

**Step 5: Follow Recommendations**
The Next Step Engine will now tell you:
- 🔴 **URGENT**: Review ET3 response (Due: 3 days)
- 🟠 **CRITICAL**: Draft witness statement (Due: 7 days)
- 🔵 **NEXT PRIORITY**: Obtain medical records

## Tips for Success

### 1. Set Realistic Deadlines
- Always work backwards from court deadlines
- Add buffer time for unexpected issues
- Mark court-imposed deadlines clearly

### 2. Update Progress Regularly
- Mark tasks as complete when done
- Update milestone progress percentages
- Add notes about important developments

### 3. Use the Mission Statement
- Keep it focused on the outcome you want
- Review it regularly to stay on track
- Update if your strategy changes

### 4. Leverage Next Steps
- Check the dashboard daily
- Work through recommendations in priority order
- Trust the urgency levels (red = do now!)

### 5. Organize Documents Well
- Use consistent naming conventions
- Choose the right category
- Upload documents as soon as you receive them

### 6. Track Everything
- Add timeline events as they happen
- Log all correspondence
- Keep detailed notes of meetings and calls

## Common Tasks

### Mark a Task Complete
Currently manual - update task status to "Completed" via the API or by editing the database

### Update Milestone Progress
Use the API endpoint:
```bash
PUT /api/milestones/{id}
{
  "completion_percentage": 75.0
}
```

### View All Deadlines
Go to Tasks tab - they're sorted by due date

### Export Case Information
Phase 2 feature - coming soon!

## Keyboard Shortcuts & Tips

- **Refresh Dashboard**: Reload page to see latest updates
- **Quick Navigation**: Use browser back/forward buttons
- **Multiple Tabs**: Open multiple cases in different browser tabs

## Troubleshooting

### Can't Access Dashboard
- Ensure server is running: `python3 backend/main.py`
- Check URL: `http://localhost:8000/frontend/index.html`
- Not: `file:///path/to/index.html`

### Documents Not Uploading
- Check file size (should be reasonable)
- Ensure documents directory exists
- Check browser console for errors

### Tasks Not Showing
- Verify task was created successfully
- Check API response in browser developer tools
- Reload the page

## Next Steps

Once you're comfortable with the basics:

1. **Explore All Tabs**: Timeline, Notes, Contacts
2. **Create Multiple Cases**: Track all your matters
3. **Set Up Regular Reviews**: Weekly case file review
4. **Customize Categories**: Add your own document types
5. **Review Progress**: Check milestone completion weekly

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Full README**: See README.md
- **Code Comments**: Check source files for detailed info

## Backup Your Data

**Important**: This is a local system. Back up regularly!

```bash
# Backup database
cp database/legal_cases.db database/legal_cases.db.backup

# Backup documents
cp -r documents documents.backup

# Or backup entire directory
tar -czf legal-system-backup.tar.gz my-legal-system/
```

---

**You're ready to go!** 🎉

Start by creating your first case and let the Next Step Engine guide you through your legal matters.
