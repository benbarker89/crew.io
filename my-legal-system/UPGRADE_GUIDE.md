# Upgrade Guide: Phase 2 & Phase 3 Features

## Version 2.0.0 - Advanced Features

This document covers the major enhancements added in Phase 2 and Phase 3 of the Legal Case Management System.

---

## 🎉 What's New

### Phase 2 Features (Automation & Search)

1. **PDF Bundle Generation** - Create professional legal document bundles
2. **Full-Text Search (FTS5)** - Search across all documents and case data
3. **Email Parsing & Auto-Logging** - Import .eml and .msg files automatically

### Phase 3 Features (Advanced Functionality)

4. **Template-Based Document Generation** - Create documents from templates
5. **Advanced Timeline Visualization** - Interactive case chronology
6. **Word/PDF Export** - Export case summaries and data

---

## 📦 New Dependencies

The following packages have been added:

```
PyPDF2==3.0.1              # PDF manipulation and bundle generation
python-docx==1.1.0         # Word document creation and export
extract-msg==0.45.0        # Outlook .msg file parsing
beautifulsoup4==4.12.2     # HTML parsing for emails
jinja2==3.1.2              # Template engine
```

### Installation

```bash
cd my-legal-system
pip install -r requirements.txt
```

---

## 1️⃣ PDF Bundle Generation

### Overview

Generate professional, paginated PDF bundles from case documents with:
- Automated cover page
- Hyperlinked table of contents
- Automatic page numbering
- Exhibit numbering
- Multiple bundle types (hearing, disclosure, trial, etc.)

### API Endpoints

#### Generate Bundle from Selected Documents

```http
POST /api/cases/{case_id}/generate-bundle
```

**Request Body:**
```json
{
  "document_ids": [1, 2, 3, 4],
  "bundle_type": "hearing",
  "start_page": 1
}
```

**Response:**
```json
{
  "success": true,
  "bundle_path": "/path/to/bundle.pdf",
  "bundle_filename": "ET-2025-001_hearing_bundle_20250101_120000.pdf",
  "bundle_type": "hearing",
  "total_documents": 4,
  "total_pages": 45,
  "generated_date": "2025-01-01T12:00:00"
}
```

#### Generate Chronological Bundle

```http
POST /api/cases/{case_id}/generate-chronological-bundle?category=Evidence
```

Generates a bundle with all documents in chronological order.

#### Get Available Documents for Bundling

```http
GET /api/cases/{case_id}/bundle/documents?category=Pleadings
```

### Usage Example

```python
# Using the API
import requests

response = requests.post(
    'http://localhost:8000/api/cases/1/generate-bundle',
    json={
        'document_ids': [1, 2, 3],
        'bundle_type': 'hearing',
        'start_page': 1
    }
)

result = response.json()
print(f"Bundle created: {result['bundle_filename']}")
print(f"Total pages: {result['total_pages']}")
```

### Bundle Types

- **hearing** - For tribunal/court hearings
- **disclosure** - For disclosure bundles
- **trial** - For trial bundles
- **chronological** - Chronological order
- **evidence** - Evidence bundles

### Output Location

Bundles are saved to: `/exports/{case_number}_{bundle_type}_bundle_{timestamp}.pdf`

---

## 2️⃣ Full-Text Search (SQLite FTS5)

### Overview

Search across all case content with:
- Full-text search in documents, notes, and timeline events
- Advanced filters (date range, category, status)
- Highlighted snippets
- Relevance scoring

### API Endpoints

#### Search Documents

```http
GET /api/search/documents?query=disability%20discrimination&case_id=1&category=Evidence&limit=50
```

**Response:**
```json
{
  "results": [
    {
      "document_id": 5,
      "filename": "medical_report.pdf",
      "category": "Evidence",
      "case_number": "ET-2025-001",
      "snippet": "...evidence of <mark>disability discrimination</mark> in the workplace...",
      "relevance_score": 0.85
    }
  ],
  "total": 1,
  "query": "disability discrimination"
}
```

#### Search All Content Types

```http
GET /api/search/all?query=tribunal&limit_per_type=20
```

Returns results categorized by type (documents, notes, timeline).

#### Reindex All Content

```http
POST /api/search/reindex
```

Rebuilds the search index for all content.

#### Get Search Statistics

```http
GET /api/search/statistics
```

Returns count of indexed items.

### Usage Example

```javascript
// Search from frontend
async function searchCaseContent(query) {
    const response = await fetch(
        `${API_BASE}/search/all?query=${encodeURIComponent(query)}&case_id=1`
    );
    const results = await response.json();

    console.log(`Found ${results.documents.length} documents`);
    console.log(`Found ${results.notes.length} notes`);
    console.log(`Found ${results.timeline.length} timeline events`);

    return results;
}
```

### Search Features

- **Stemming** - Searches "discriminate" also finds "discrimination"
- **Unicode Support** - Works with special characters
- **Phrase Search** - Use quotes: `"disability discrimination"`
- **Boolean Operators** - Use AND, OR, NOT
- **Snippet Highlighting** - Results highlighted with `<mark>` tags

---

## 3️⃣ Email Parsing & Auto-Logging

### Overview

Import email files directly into case correspondence:
- Parse .eml and .msg files
- Extract sender, recipient, subject, date
- Extract email body (text and HTML)
- Save attachments as documents
- Auto-create correspondence log entries
- Auto-create timeline events

### API Endpoints

#### Import Email into Case

```http
POST /api/cases/{case_id}/import-email
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Email file (.eml or .msg)
- `direction`: "Sent" or "Received" (optional, default: "Received")
- `save_attachments`: true/false (optional, default: true)

**Response:**
```json
{
  "success": true,
  "document_id": 15,
  "correspondence_id": 8,
  "contact_id": 3,
  "timeline_event_id": 12,
  "attachments_processed": 2,
  "email_subject": "Re: Tribunal Hearing Date",
  "email_date": "2025-01-01T14:30:00",
  "sender": "John Smith <john.smith@example.com>"
}
```

#### Parse Email (Preview Only)

```http
POST /api/cases/{case_id}/parse-email
```

Parses email and returns metadata without importing.

### Usage Example

```javascript
// Upload email file
async function importEmail(caseId, emailFile) {
    const formData = new FormData();
    formData.append('file', emailFile);
    formData.append('direction', 'Received');
    formData.append('save_attachments', true);

    const response = await fetch(
        `${API_BASE}/cases/${caseId}/import-email`,
        {
            method: 'POST',
            body: formData
        }
    );

    const result = await response.json();
    console.log(`Email imported: ${result.email_subject}`);
    console.log(`Attachments: ${result.attachments_processed}`);

    return result;
}
```

### What Gets Created

When you import an email:

1. **Document** - Email file saved to `documents/{case_id}/correspondence/`
2. **Correspondence** - Log entry with sender, subject, summary
3. **Contact** - Sender added as contact (if not exists)
4. **Timeline Event** - Communication event added to timeline
5. **Attachments** - Saved to `documents/{case_id}/attachments/` (optional)

---

## 4️⃣ Template-Based Document Generation

### Overview

Create legal documents from templates with merge fields:
- Pre-built templates (witness statements, SAR, disclosure requests)
- Jinja2 template engine with variable substitution
- Auto-populate case data
- Generate Word (.docx) or text files
- Create custom templates

### API Endpoints

#### Get Available Templates

```http
GET /api/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "witness_statement",
      "name": "Witness Statement",
      "description": "Standard witness statement for tribunal proceedings",
      "category": "Evidence",
      "fields": [
        {"name": "witness_name", "label": "Witness Name", "type": "text", "required": true},
        {"name": "witness_address", "label": "Witness Address", "type": "textarea", "required": true}
      ]
    }
  ],
  "total": 3
}
```

#### Generate Document from Template

```http
POST /api/cases/{case_id}/generate-from-template
```

**Request Body:**
```json
{
  "template_id": "witness_statement",
  "variables": {
    "witness_name": "Jane Doe",
    "witness_address": "123 Main Street, London",
    "statement_date": "01/01/2025",
    "statement_content": "I have been employed by..."
  },
  "output_format": "docx"
}
```

**Response:**
```json
{
  "success": true,
  "file_path": "/path/to/document.docx",
  "filename": "witness_statement_20250101_120000.docx",
  "template_id": "witness_statement",
  "format": "docx",
  "document_id": 20
}
```

#### Preview Template

```http
GET /api/cases/{case_id}/template-preview/witness_statement
```

Returns rendered template with default case variables.

### Built-In Templates

1. **Witness Statement** - Standard witness statement with declaration
2. **Subject Access Request** - GDPR Subject Access Request letter
3. **Disclosure Request** - Request for disclosure of documents

### Auto-Populated Variables

Templates automatically have access to:

- `case_number` - Case reference number
- `case_title` - Case title
- `case_type` - Type of case
- `mission_statement` - Case mission
- `today` - Today's date (formatted)
- `claimant_name` - Claimant/party name (if added)
- `respondent_name` - Respondent name (if added)
- `primary_contact_name` - Primary contact
- `primary_contact_email` - Primary contact email

### Usage Example

```javascript
// Generate witness statement
async function generateWitnessStatement(caseId) {
    const response = await fetch(
        `${API_BASE}/cases/${caseId}/generate-from-template`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                template_id: 'witness_statement',
                variables: {
                    witness_name: 'John Doe',
                    witness_address: '123 Main St, London',
                    statement_date: '01/01/2025',
                    statement_content: 'I have worked for the respondent since...'
                },
                output_format: 'docx'
            })
        }
    );

    const result = await response.json();
    console.log(`Document created: ${result.filename}`);
    return result;
}
```

### Creating Custom Templates

Templates are stored in `/templates/document_templates/` as JSON files.

Example template:

```json
{
  "name": "My Custom Letter",
  "description": "Custom letter template",
  "category": "Correspondence",
  "fields": [
    {"name": "recipient", "label": "Recipient Name", "type": "text", "required": true},
    {"name": "message", "label": "Message", "type": "textarea", "required": true}
  ],
  "content": "Dear {{ recipient }},\n\n{{ message }}\n\nSincerely,\n{{ primary_contact_name }}"
}
```

---

## 5️⃣ Word/PDF Export

### Overview

Export case data to professional Word and PDF documents:
- Case summaries (all case data)
- Timeline/chronology
- Case notes
- Customizable formatting
- Ready for printing or sharing

### API Endpoints

#### Export Case Summary (Word)

```http
GET /api/cases/{case_id}/export/summary-word
```

Downloads a complete case summary as Word document including:
- Case information
- Mission statement
- All milestones
- All tasks
- Timeline
- Documents list
- Recent notes

#### Export Case Summary (PDF)

```http
GET /api/cases/{case_id}/export/summary-pdf
```

Same content as Word export but in PDF format.

#### Export Timeline (Word)

```http
GET /api/cases/{case_id}/export/timeline-word
```

Exports chronological table of all timeline events.

#### Export Notes (Word)

```http
GET /api/cases/{case_id}/export/notes-word
```

Exports all case notes with formatting.

### Usage Example

```javascript
// Export case summary to Word
async function exportCaseSummary(caseId) {
    const url = `${API_BASE}/cases/${caseId}/export/summary-word`;
    window.open(url, '_blank');
}

// Export timeline to PDF
async function exportTimeline(caseId) {
    const url = `${API_BASE}/cases/${caseId}/export/timeline-word`;
    window.open(url, '_blank');
}
```

### Output Location

Exports are saved to: `/exports/{case_number}_{type}_{timestamp}.{ext}`

---

## 🔧 Migration Guide

### From Version 1.0.0 to 2.0.0

#### 1. Update Dependencies

```bash
cd my-legal-system
pip install -r requirements.txt
```

#### 2. Initialize Search Indexes

After installing, initialize the full-text search:

```bash
curl -X POST http://localhost:8000/api/search/reindex
```

This will index all existing documents, notes, and timeline events.

#### 3. Create Default Templates

Templates are created automatically when the system starts. Verify:

```bash
ls templates/document_templates/
```

You should see:
- `witness_statement.json`
- `subject_access_request.json`
- `disclosure_request.json`

#### 4. Test New Features

```bash
# Test bundle generation
curl -X GET http://localhost:8000/api/cases/1/bundle/documents

# Test search
curl -X GET "http://localhost:8000/api/search/documents?query=test"

# Test templates
curl -X GET http://localhost:8000/api/templates

# Test export
curl -X GET http://localhost:8000/api/cases/1/export/summary-word -o summary.docx
```

---

## 📊 Performance Notes

### Search Performance

- FTS5 is extremely fast even with thousands of documents
- Indexing happens automatically when documents/notes are created
- Reindex if you have existing content: `POST /api/search/reindex`

### Bundle Generation

- Large bundles (100+ pages) may take 10-30 seconds
- Bundle generation is synchronous (blocks until complete)
- Consider implementing async generation for very large bundles

### Export Performance

- Word/PDF exports are fast for typical cases
- Timeline exports limited to most recent 20 events by default
- Exports generated on-demand (not cached)

---

## 🚨 Breaking Changes

None! All Phase 2 & 3 features are additive and backward compatible.

Existing API endpoints and functionality remain unchanged.

---

## 🎯 Usage Scenarios

### Scenario 1: Preparing for Hearing

```python
# 1. Generate hearing bundle
bundle = generate_bundle(
    case_id=1,
    document_ids=[1, 2, 3, 4, 5],
    bundle_type='hearing'
)

# 2. Export timeline for witness preparation
timeline_doc = export_timeline_word(case_id=1)

# 3. Generate witness statements from template
for witness in witnesses:
    generate_from_template(
        case_id=1,
        template_id='witness_statement',
        variables={'witness_name': witness.name, ...}
    )
```

### Scenario 2: Disclosure Process

```python
# 1. Generate disclosure request letter
disclosure_request = generate_from_template(
    case_id=1,
    template_id='disclosure_request',
    variables={'documents_requested': '...', ...}
)

# 2. When disclosure received, import emails
import_email(case_id=1, email_file='disclosure.eml')

# 3. Search for specific documents
search_results = search_documents(
    query='employment contract',
    category='Evidence'
)

# 4. Create disclosure bundle
bundle = generate_chronological_bundle(
    case_id=1,
    category='Evidence'
)
```

### Scenario 3: Case Review

```python
# 1. Search for all references to a topic
results = search_all(query='disability adjustments')

# 2. Export complete case summary
summary = export_case_summary_word(case_id=1)

# 3. Export notes for review
notes = export_notes_word(case_id=1)
```

---

## 📝 Best Practices

### Bundle Generation

- **Organize documents first**: Ensure correct categories and dates
- **Review TOC**: Check table of contents before finalizing
- **Multiple bundle types**: Create separate bundles for different purposes
- **Version control**: Keep different versions (hearing, trial, etc.)

### Full-Text Search

- **Reindex regularly**: After bulk imports, run reindex
- **Use filters**: Narrow results with category/date filters
- **Phrase searches**: Use quotes for exact phrases
- **Boolean logic**: Combine terms with AND/OR

### Email Parsing

- **Batch imports**: Import multiple emails at once
- **Review attachments**: Check attachments before importing
- **Contact management**: Emails auto-create contacts
- **Timeline integration**: Emails appear in timeline

### Templates

- **Customize templates**: Edit JSON files for your needs
- **Variable naming**: Use clear, descriptive variable names
- **Preview first**: Always preview before generating
- **Save successful variables**: Keep records of good variable sets

### Exports

- **Regular backups**: Export case summaries regularly
- **Share with advisors**: Export PDFs for legal advice
- **Print-ready**: Exports formatted for printing
- **Version dating**: Filenames include timestamps

---

## 🐛 Troubleshooting

### Bundle Generation Issues

**Problem**: "Error adding document to bundle"
- **Solution**: Ensure document file exists and is a valid PDF

**Problem**: Bundle missing documents
- **Solution**: Check document IDs are correct

### Search Not Working

**Problem**: "No results found" but content exists
- **Solution**: Run reindex: `POST /api/search/reindex`

**Problem**: Search returns irrelevant results
- **Solution**: Use more specific terms or phrase searches

### Email Parsing Fails

**Problem**: "Failed to parse .msg file"
- **Solution**: Ensure `extract-msg` is installed: `pip install extract-msg`

**Problem**: Attachments not saved
- **Solution**: Check `save_attachments=true` in request

### Template Generation Errors

**Problem**: "Template not found"
- **Solution**: Check template files exist in `/templates/document_templates/`

**Problem**: Variable not found error
- **Solution**: Ensure all required fields are provided

### Export Issues

**Problem**: "Export file not found"
- **Solution**: Check `/exports/` directory permissions

**Problem**: Export appears empty
- **Solution**: Ensure case has data to export

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Full README**: `README.md`
- **Quick Start**: `QUICKSTART.md`

---

## 🎉 Summary

Version 2.0.0 adds powerful automation and export features:

✅ **PDF Bundle Generation** - Professional legal bundles
✅ **Full-Text Search** - Find anything instantly
✅ **Email Import** - Automated correspondence logging
✅ **Document Templates** - Generate documents from templates
✅ **Word/PDF Export** - Share case data professionally

All features work locally, maintaining the single-user, privacy-first approach.

**Version**: 2.0.0
**Release Date**: January 2025
**Compatibility**: Fully backward compatible with 1.0.0
