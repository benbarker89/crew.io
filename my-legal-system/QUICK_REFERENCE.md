# Quick Reference - Phase 2 & 3 Features

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
cd backend && python3 main.py

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## 📦 Bundle Generation

### Generate Hearing Bundle
```bash
curl -X POST "http://localhost:8000/api/cases/1/generate-bundle" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": [1,2,3], "bundle_type": "hearing"}'
```

### Generate Chronological Bundle
```bash
curl -X POST "http://localhost:8000/api/cases/1/generate-chronological-bundle"
```

**Output:** `/exports/{case_number}_{bundle_type}_bundle_{timestamp}.pdf`

---

## 🔍 Full-Text Search

### Search Documents
```bash
curl "http://localhost:8000/api/search/documents?query=discrimination&case_id=1"
```

### Search Everything
```bash
curl "http://localhost:8000/api/search/all?query=tribunal"
```

### Reindex Content
```bash
curl -X POST "http://localhost:8000/api/search/reindex"
```

**Search Operators:**
- Phrase: `"exact phrase"`
- Boolean: `term1 AND term2`
- Exclude: `term1 NOT term2`

---

## 📧 Email Import

### Import Email
```bash
curl -X POST "http://localhost:8000/api/cases/1/import-email" \
  -F "file=@email.eml" \
  -F "direction=Received" \
  -F "save_attachments=true"
```

**Supported:** `.eml` and `.msg` files

**Creates:**
- Document record
- Correspondence entry
- Timeline event
- Contact (if new)
- Attachments (optional)

---

## 📝 Templates

### List Templates
```bash
curl "http://localhost:8000/api/templates"
```

### Generate from Template
```bash
curl -X POST "http://localhost:8000/api/cases/1/generate-from-template" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "witness_statement",
    "variables": {
      "witness_name": "John Doe",
      "witness_address": "123 Main St",
      "statement_date": "01/01/2025",
      "statement_content": "I have worked for..."
    },
    "output_format": "docx"
  }'
```

**Built-In Templates:**
- `witness_statement`
- `subject_access_request`
- `disclosure_request`

**Output:** `/documents/{case_id}/generated/{template}_{timestamp}.docx`

---

## 📄 Export

### Export Case Summary (Word)
```bash
curl "http://localhost:8000/api/cases/1/export/summary-word" -o summary.docx
```

### Export Case Summary (PDF)
```bash
curl "http://localhost:8000/api/cases/1/export/summary-pdf" -o summary.pdf
```

### Export Timeline
```bash
curl "http://localhost:8000/api/cases/1/export/timeline-word" -o timeline.docx
```

### Export Notes
```bash
curl "http://localhost:8000/api/cases/1/export/notes-word" -o notes.docx
```

**Output:** `/exports/{case_number}_{type}_{timestamp}.{ext}`

---

## 📁 File Locations

| Type | Location |
|------|----------|
| Bundles | `/exports/` |
| Exports | `/exports/` |
| Documents | `/documents/{case_id}/` |
| Emails | `/documents/{case_id}/correspondence/` |
| Attachments | `/documents/{case_id}/attachments/` |
| Generated Docs | `/documents/{case_id}/generated/` |
| Templates | `/templates/document_templates/` |

---

## 🎯 Common Workflows

### Preparing for Hearing
```bash
# 1. Generate bundle
curl -X POST ".../generate-bundle" -d '{"document_ids":[...]}'

# 2. Export timeline
curl ".../export/timeline-word" -o timeline.docx

# 3. Generate witness statements
curl -X POST ".../generate-from-template" -d '{"template_id":"witness_statement",...}'
```

### Processing Disclosure
```bash
# 1. Import disclosure email
curl -X POST ".../import-email" -F "file=@disclosure.eml"

# 2. Search for relevant docs
curl ".../search/documents?query=contract"

# 3. Generate disclosure bundle
curl -X POST ".../generate-chronological-bundle?category=Evidence"
```

### Case Review
```bash
# 1. Search all content
curl ".../search/all?query=disability"

# 2. Export case summary
curl ".../export/summary-word" -o review.docx

# 3. Export notes
curl ".../export/notes-word" -o notes.docx
```

---

## ⚡ Performance Tips

### Search
- Run reindex after bulk imports: `POST /api/search/reindex`
- Use filters to narrow results
- Use phrase searches for exact matches

### Bundles
- Pre-organize documents by category
- Use chronological bundles for evidence
- Custom bundles for specific purposes

### Templates
- Preview templates before generating
- Save successful variable sets for reuse
- Customize templates in `/templates/document_templates/`

### Export
- Export regularly for backups
- Use Word format for editing
- Use PDF format for sharing

---

## 🐛 Troubleshooting

### Search returns no results
```bash
# Reindex all content
curl -X POST "http://localhost:8000/api/search/reindex"
```

### Bundle missing documents
- Check document IDs are correct
- Verify documents exist and are PDFs
- Check bundle generation response for errors

### Email import fails
- Ensure file is .eml or .msg format
- Check file is not corrupted
- Verify extract-msg is installed for .msg files

### Template generation errors
- Verify all required fields are provided
- Check template exists in `/templates/document_templates/`
- Preview template first to test variables

---

## 📚 Documentation

- **Full Guide:** `UPGRADE_GUIDE.md`
- **README:** `README.md`
- **Quick Start:** `QUICKSTART.md`
- **API Docs:** `http://localhost:8000/docs`
- **Summary:** `PHASE2_3_SUMMARY.md`

---

## 🎓 Tips & Best Practices

### General
✅ Reindex search after bulk operations
✅ Use consistent document naming
✅ Tag documents with correct categories
✅ Keep case numbers unique and descriptive

### Bundles
✅ Review TOC before finalizing
✅ Use different bundle types for different purposes
✅ Keep multiple versions (hearing, trial, etc.)
✅ Check page numbers are sequential

### Search
✅ Use specific terms for better results
✅ Combine with filters for precision
✅ Use phrase searches for exact text
✅ Check search statistics regularly

### Templates
✅ Customize templates for your needs
✅ Use consistent variable naming
✅ Preview before generating
✅ Keep template library organized

### Export
✅ Export regularly for backups
✅ Use descriptive filenames
✅ Review exports before sharing
✅ Keep exports organized by date

---

## 🔑 Keyboard Shortcuts

### API Testing (via browser)
- **F12** - Open developer console
- **Ctrl+Shift+I** - Inspect network tab
- **Ctrl+R** - Refresh page

### Document Navigation
- **Browser back/forward** - Navigate between pages
- **Ctrl+F** - Find in page
- **Ctrl+Click** - Open link in new tab

---

## 🎯 Quick Checklist

Before Tribunal Hearing:
- [ ] Generate hearing bundle
- [ ] Export timeline
- [ ] Generate witness statements
- [ ] Review all documents
- [ ] Export case summary for advisor

Before Disclosure:
- [ ] Import all disclosure emails
- [ ] Search for relevant documents
- [ ] Generate disclosure bundle
- [ ] Export disclosure list

Weekly Maintenance:
- [ ] Import new emails
- [ ] Update timeline
- [ ] Reindex search
- [ ] Export case summary (backup)
- [ ] Review next steps

---

## 📞 Getting Help

1. Check API documentation: `http://localhost:8000/docs`
2. Review `UPGRADE_GUIDE.md` for detailed examples
3. Check `TROUBLESHOOTING` sections in README
4. Review code comments in source files

---

**Version:** 2.0.0
**Last Updated:** January 2025
**Status:** Production Ready ✅
