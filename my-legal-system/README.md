# Personal Legal Case Management System

A comprehensive, single-user legal case management system designed for managing UK tribunal litigation, employment law cases, and regulatory investigations. Features intelligent "next step" recommendations, mission goal tracking, PDF bundle generation, full-text search, and advanced automation.

**Version 2.0.0** - Now with Phase 2 & 3 advanced features!

## 🎯 Key Features

### 1. **Intelligent Next Step Engine**
- Automatically analyzes case status and provides prioritized action recommendations
- Identifies urgent tasks, upcoming deadlines, and blocking dependencies
- Context-aware suggestions with time estimates and required resources
- Urgency levels: Urgent, Critical, Next Priority, Recommended

### 2. **Mission Goals & Milestones**
- Define case objectives with trackable milestones
- Visual progress indicators for each case
- Milestone types: Pre-action, Procedural, Evidence, Hearing, Outcome
- Automatic completion detection and celebration messages

### 3. **Case Management**
- Multiple case types: Employment Tribunal, Criminal, Regulatory, County Court
- Status tracking: Preparation, Active Litigation, Awaiting Response, Closed
- Priority levels: Urgent, High, Medium, Low
- Mission statements to keep focus on case objectives

### 4. **Task & Deadline Tracking**
- Court deadline tracking with countdown timers
- Task dependencies and sequencing
- Estimated duration tracking
- Automatic "Next Step" integration

### 5. **Document Management**
- Category-based organization (Pleadings, Evidence, Correspondence, Orders, Research)
- File upload with metadata tracking
- Document status tags (Draft, Final, Filed, Privileged)
- File size and upload date tracking

### 6. **Timeline & Chronology**
- Visual timeline of all case events
- Event types: Incident, Communication, Document, Court Action
- Key event flagging
- Document linking to timeline entries

### 7. **Contact Management**
- Contact database for witnesses, opposing parties, legal representatives
- Correspondence logging
- Role-based organization

### 8. **Case Notes & Journal**
- Free-form note-taking per case
- Note types: Journal, Strategy, Research, Meeting
- Tag-based organization

### ✨ **NEW - Phase 2 & 3 Features**

### 9. **PDF Bundle Generation** 📦
- Generate professional legal document bundles with automated cover page and TOC
- Automatic page numbering and exhibit references
- Multiple bundle types (hearing, disclosure, trial, chronological)
- Hyperlinked table of contents
- Paginated PDF output ready for tribunal submission

### 10. **Full-Text Search (SQLite FTS5)** 🔍
- Search across all documents, notes, and timeline events
- Advanced filtering by category, date range, and status
- Highlighted search snippets
- Relevance scoring
- Boolean operators and phrase searches

### 11. **Email Parsing & Auto-Logging** 📧
- Import .eml and .msg email files
- Auto-extract sender, recipient, subject, and dates
- Save email attachments as documents
- Automatically create correspondence log entries
- Auto-create timeline events for communications

### 12. **Template-Based Document Generation** 📝
- Generate legal documents from customizable templates
- Built-in templates: Witness Statements, Subject Access Requests, Disclosure Requests
- Jinja2 template engine with variable substitution
- Auto-populate case data into templates
- Export to Word (.docx) or text format

### 13. **Word/PDF Export** 📄
- Export case summaries to Word or PDF
- Export timeline/chronology for witness statements
- Export case notes with formatting
- Professional formatting ready for printing
- Share case data with legal advisors

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd my-legal-system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   cd backend
   python models.py
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

5. **Access the application:**
   - Main Dashboard: `http://localhost:8000/frontend/index.html`
   - API Documentation: `http://localhost:8000/docs`
   - API: `http://localhost:8000/api`

## 📖 Usage Guide

### Creating Your First Case

1. Open the dashboard at `http://localhost:8000/frontend/index.html`
2. Click "New Case" in the navigation
3. Fill in the case details:
   - **Case Number**: Unique identifier (e.g., ET-2025-001)
   - **Title**: Case name (e.g., Smith v. ESHT)
   - **Case Type**: Select from dropdown
   - **Priority**: Set urgency level
   - **Mission Statement**: Define your primary objective

### Adding Milestones

1. Navigate to the case view
2. Click the "Milestones" tab
3. Click "+ Add Milestone"
4. Define milestone details:
   - **Title**: What needs to be achieved
   - **Type**: Pre-action, Procedural, Evidence, Hearing, or Outcome
   - **Target Date**: When it should be completed
   - **Description**: Additional context

### Creating Tasks

1. Go to the "Tasks" tab in case view
2. Click "+ Add Task"
3. Enter task details:
   - **Title**: Task name
   - **Description**: What needs to be done
   - **Priority**: Urgency level
   - **Due Date**: Deadline
   - **Estimated Hours**: Time estimate

### Uploading Documents

1. Navigate to the "Documents" tab
2. Click "+ Upload Document"
3. Select document category
4. Choose file from your computer
5. Click "Upload"

Documents are stored in the `documents/[case_id]/` directory.

### Using the Next Step Engine

The Next Step Engine automatically analyzes your cases and provides recommendations:

1. **Dashboard View**: See next steps across all cases
2. **Case View**: See case-specific recommendations
3. **Recommendations include:**
   - Action to take
   - Estimated time required
   - Context and dependencies
   - Links to related items

### Tracking Progress

Monitor case progress through:
- **Overall Progress Bar**: Weighted average of milestone completion
- **Milestone Tracking**: Individual milestone progress
- **Statistics Dashboard**: Active cases, urgent tasks, upcoming deadlines

## 🏗️ Architecture

### Backend (Python/FastAPI)

```
backend/
├── models.py          # SQLAlchemy database models
├── api.py             # FastAPI REST API endpoints
├── goal_tracker.py    # Mission goal tracking system
├── next_step_engine.py # Intelligent recommendation engine
└── main.py            # Application entry point
```

### Frontend (HTML/CSS/JavaScript)

```
frontend/
├── index.html         # Main dashboard
├── case_view.html     # Case details page
├── style.css          # Comprehensive styling
└── app.js             # Frontend application logic
```

### Database (SQLite)

```
database/
└── legal_cases.db     # SQLite database file
```

Tables:
- `cases` - Main case records
- `milestones` - Mission milestones
- `tasks` - Tasks and deadlines
- `documents` - Document metadata
- `timeline_events` - Case chronology
- `contacts` - Contacts and parties
- `correspondence` - Communication log
- `notes` - Case notes and journal
- `parties` - Key case parties
- `critical_dates` - Important dates

## 🔌 API Endpoints

### Cases
- `POST /api/cases` - Create new case
- `GET /api/cases` - List all cases
- `GET /api/cases/{id}` - Get case details
- `PUT /api/cases/{id}` - Update case
- `DELETE /api/cases/{id}` - Delete case

### Milestones
- `POST /api/milestones` - Create milestone
- `GET /api/cases/{case_id}/milestones` - Get case milestones
- `PUT /api/milestones/{id}` - Update milestone
- `POST /api/milestones/{id}/complete` - Mark complete

### Next Steps
- `GET /api/next-steps` - Get next steps for all cases
- `GET /api/cases/{case_id}/next-steps` - Get case next steps

### Tasks
- `POST /api/tasks` - Create task
- `GET /api/cases/{case_id}/tasks` - Get case tasks
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/cases/{case_id}/documents` - Get case documents
- `GET /api/documents/{id}/download` - Download document

### Progress Tracking
- `GET /api/cases/{case_id}/progress` - Get case progress
- `GET /api/dashboard/summary` - Get dashboard summary

### ✨ NEW - Bundle Generation
- `POST /api/cases/{case_id}/generate-bundle` - Generate PDF bundle
- `POST /api/cases/{case_id}/generate-chronological-bundle` - Generate chronological bundle
- `GET /api/cases/{case_id}/bundle/documents` - Get documents for bundling

### ✨ NEW - Full-Text Search
- `GET /api/search/documents` - Search documents
- `GET /api/search/notes` - Search notes
- `GET /api/search/timeline` - Search timeline events
- `GET /api/search/all` - Search all content
- `POST /api/search/reindex` - Reindex all content
- `GET /api/search/statistics` - Get search statistics

### ✨ NEW - Email Parsing
- `POST /api/cases/{case_id}/import-email` - Import email file
- `POST /api/cases/{case_id}/parse-email` - Parse email (preview only)

### ✨ NEW - Templates
- `GET /api/templates` - Get available templates
- `POST /api/cases/{case_id}/generate-from-template` - Generate document from template
- `GET /api/cases/{case_id}/template-preview/{template_id}` - Preview template

### ✨ NEW - Export
- `GET /api/cases/{case_id}/export/summary-word` - Export case summary to Word
- `GET /api/cases/{case_id}/export/summary-pdf` - Export case summary to PDF
- `GET /api/cases/{case_id}/export/timeline-word` - Export timeline to Word
- `GET /api/cases/{case_id}/export/notes-word` - Export notes to Word

Full API documentation available at `http://localhost:8000/docs`

## 🎨 Customization

### Adding New Case Types

Edit the case type dropdown in `frontend/index.html` and `frontend/case_view.html`:

```html
<option value="Your New Type">Your New Type</option>
```

### Adding New Document Categories

Edit the document category dropdown:

```html
<option value="Your Category">Your Category</option>
```

### Modifying Next Step Logic

Edit `backend/next_step_engine.py` to customize recommendation rules.

## 📊 Example Workflow

### Employment Tribunal Case

1. **Create Case**
   - Case Number: ET-2025-001
   - Title: Smith v. East Sussex Healthcare Trust
   - Type: Employment Tribunal
   - Mission: "Secure maximum compensation for disability discrimination"

2. **Add Milestones**
   - ✅ Complete ACAS Early Conciliation
   - ✅ File ET1 claim
   - 🔄 Compile witness statements (60%)
   - ⬜ Complete disclosure
   - ⬜ Prepare hearing bundle
   - ⬜ Attend preliminary hearing
   - ⬜ Final hearing

3. **Create Tasks**
   - Draft witness statement for John Doe
   - Obtain medical records from GP
   - Review respondent's ET3 response
   - Compile disclosure documents

4. **Upload Documents**
   - ET1 claim form (Pleadings)
   - Medical reports (Evidence)
   - Email correspondence (Correspondence)
   - Tribunal orders (Orders)

5. **Track Progress**
   - Monitor milestone completion
   - Follow next step recommendations
   - Update timeline with events
   - Add case notes regularly

## 🔒 Data Privacy

This is a **single-user, local-first** system:
- No authentication required (local access only)
- All data stored locally in SQLite database
- Documents stored in local filesystem
- No cloud dependencies
- Database file portable for backup

**Backup Recommendations:**
- Regularly backup `database/legal_cases.db`
- Backup `documents/` directory
- Consider encrypted storage for sensitive data

## 🛠️ Troubleshooting

### Port Already in Use
If port 8000 is already in use, edit `backend/main.py`:
```python
uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
```

### Database Initialization Errors
Delete and recreate the database:
```bash
rm database/legal_cases.db
python backend/models.py
```

### CORS Errors
Ensure the frontend is accessed via the correct URL:
- Use `http://localhost:8000/frontend/index.html`
- Not `file:///path/to/index.html`

## ✅ Phase 2 & 3 - COMPLETED!

- [x] **PDF bundle generation** with hyperlinked index and pagination
- [x] **Full-text search** across documents (SQLite FTS5)
- [x] **Email parsing and auto-logging** (.eml and .msg support)
- [x] **Template-based document generation** with Jinja2 engine
- [x] **Word/PDF export capabilities** (case summaries, timeline, notes)
- [x] **Advanced timeline** visualization and export

See `UPGRADE_GUIDE.md` for full documentation of new features!

## 🚧 Future Enhancements (Phase 4+)

- [ ] Auto-detect deadlines from court orders using OCR/AI
- [ ] Smart notifications and email reminders
- [ ] Advanced bundle builder with drag-and-drop reordering
- [ ] OCR for scanned documents
- [ ] Mobile-responsive interface
- [ ] Case analytics and statistics
- [ ] Bulk operations (delete, move, update)
- [ ] Advanced reporting and dashboards

## 📝 License

This is a personal project for individual use. Modify as needed for your specific requirements.

## 🤝 Support

For issues or questions, refer to the API documentation at `http://localhost:8000/docs` or review the code comments in each module.

## ⚖️ Disclaimer

This software is designed as a personal organizational tool. It does not constitute legal advice and should not replace professional legal representation or counsel.

---

**Built with:**
- Python 3.x
- FastAPI
- SQLAlchemy
- SQLite (with FTS5 full-text search)
- ReportLab (PDF generation)
- python-docx (Word document generation)
- Jinja2 (template engine)
- PyPDF2 (PDF manipulation)
- Vanilla JavaScript
- HTML5/CSS3

**Version:** 2.0.0 (Phase 1, 2 & 3 Complete)
