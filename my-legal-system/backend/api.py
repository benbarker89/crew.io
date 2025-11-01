"""
FastAPI REST API for Legal Case Management System
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import os
import shutil

from models import (
    get_db, Case, Milestone, Task, Document, TimelineEvent,
    Contact, Correspondence, Note, Party, CriticalDate
)
from goal_tracker import GoalTracker
from next_step_engine import NextStepEngine
from bundle_generator import BundleGenerator
from search import SearchEngine
from email_parser import EmailParser
from template_engine import TemplateEngine
from export import ExportEngine

app = FastAPI(title="Personal Legal Case Management System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class CaseCreate(BaseModel):
    case_number: str
    title: str
    case_type: str
    status: str = "Preparation"
    priority: str = "Medium"
    mission_statement: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    mission_statement: Optional[str] = None


class MilestoneCreate(BaseModel):
    case_id: int
    title: str
    milestone_type: str
    description: Optional[str] = None
    target_date: Optional[date] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    completion_percentage: Optional[float] = None
    is_completed: Optional[bool] = None
    target_date: Optional[date] = None


class TaskCreate(BaseModel):
    case_id: int
    milestone_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "Medium"
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    is_court_deadline: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None


class TimelineEventCreate(BaseModel):
    case_id: int
    event_date: datetime
    event_type: str
    title: str
    description: Optional[str] = None
    party_involved: Optional[str] = None
    is_key_event: bool = False


class ContactCreate(BaseModel):
    case_id: int
    name: str
    role: str
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class NoteCreate(BaseModel):
    case_id: int
    title: Optional[str] = None
    content: str
    note_type: str = "Journal"
    tags: Optional[str] = None


# ============ CASE ENDPOINTS ============

@app.post("/api/cases")
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    """Create a new case"""
    db_case = Case(**case.dict())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return {"success": True, "case_id": db_case.id, "case": db_case}


@app.get("/api/cases")
def list_cases(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all cases, optionally filtered by status"""
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    cases = query.all()
    return {"cases": cases, "total": len(cases)}


@app.get("/api/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get case details"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.put("/api/cases/{case_id}")
def update_case(case_id: int, case_update: CaseUpdate, db: Session = Depends(get_db)):
    """Update case details"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    for field, value in case_update.dict(exclude_unset=True).items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return {"success": True, "case": case}


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Delete a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    db.delete(case)
    db.commit()
    return {"success": True, "message": "Case deleted"}


# ============ MILESTONE ENDPOINTS ============

@app.post("/api/milestones")
def create_milestone(milestone: MilestoneCreate, db: Session = Depends(get_db)):
    """Create a new milestone"""
    tracker = GoalTracker(db)
    result = tracker.add_milestone(
        case_id=milestone.case_id,
        title=milestone.title,
        milestone_type=milestone.milestone_type,
        description=milestone.description,
        target_date=milestone.target_date
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/milestones/{milestone_id}")
def get_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Get milestone details"""
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone


@app.put("/api/milestones/{milestone_id}")
def update_milestone(milestone_id: int, milestone_update: MilestoneUpdate, db: Session = Depends(get_db)):
    """Update milestone"""
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    for field, value in milestone_update.dict(exclude_unset=True).items():
        setattr(milestone, field, value)

    if milestone.completion_percentage >= 100.0 and not milestone.is_completed:
        milestone.is_completed = True
        milestone.completed_date = datetime.utcnow()

    db.commit()
    db.refresh(milestone)
    return {"success": True, "milestone": milestone}


@app.post("/api/milestones/{milestone_id}/complete")
def complete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Mark milestone as complete"""
    tracker = GoalTracker(db)
    result = tracker.complete_milestone(milestone_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/cases/{case_id}/milestones")
def get_case_milestones(case_id: int, db: Session = Depends(get_db)):
    """Get all milestones for a case"""
    milestones = db.query(Milestone).filter(
        Milestone.case_id == case_id
    ).order_by(Milestone.order_index).all()
    return {"milestones": milestones, "total": len(milestones)}


# ============ GOAL TRACKING ENDPOINTS ============

@app.get("/api/cases/{case_id}/progress")
def get_case_progress(case_id: int, db: Session = Depends(get_db)):
    """Get case progress toward mission goals"""
    tracker = GoalTracker(db)
    return tracker.calculate_case_progress(case_id)


@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary of all cases"""
    tracker = GoalTracker(db)
    return tracker.get_dashboard_summary()


# ============ TASK ENDPOINTS ============

@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {"success": True, "task_id": db_task.id, "task": db_task}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)

    if task.status == "Completed" and not task.completed_date:
        task.completed_date = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return {"success": True, "task": task}


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"success": True, "message": "Task deleted"}


@app.get("/api/cases/{case_id}/tasks")
def get_case_tasks(case_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all tasks for a case"""
    query = db.query(Task).filter(Task.case_id == case_id)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.order_by(Task.due_date).all()
    return {"tasks": tasks, "total": len(tasks)}


# ============ NEXT STEP ENGINE ENDPOINTS ============

@app.get("/api/cases/{case_id}/next-steps")
def get_case_next_steps(case_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get prioritized next steps for a case"""
    engine = NextStepEngine(db)
    return engine.get_next_steps(case_id, limit)


@app.get("/api/next-steps")
def get_all_next_steps(limit: int = 15, db: Session = Depends(get_db)):
    """Get next steps across all active cases"""
    engine = NextStepEngine(db)
    return engine.get_all_next_steps(limit)


# ============ DOCUMENT ENDPOINTS ============

@app.post("/api/documents/upload")
async def upload_document(
    case_id: int,
    category: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Create case document directory
    doc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documents', str(case_id))
    os.makedirs(doc_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(doc_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document record
    document = Document(
        case_id=case_id,
        filename=file.filename,
        file_path=file_path,
        category=category,
        file_size=file_size
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {"success": True, "document_id": document.id, "document": document}


@app.get("/api/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    """Download a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(document.file_path, filename=document.filename)


@app.get("/api/cases/{case_id}/documents")
def get_case_documents(case_id: int, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all documents for a case"""
    query = db.query(Document).filter(Document.case_id == case_id)
    if category:
        query = query.filter(Document.category == category)
    documents = query.order_by(Document.upload_date.desc()).all()
    return {"documents": documents, "total": len(documents)}


# ============ TIMELINE ENDPOINTS ============

@app.post("/api/timeline")
def create_timeline_event(event: TimelineEventCreate, db: Session = Depends(get_db)):
    """Create a timeline event"""
    db_event = TimelineEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"success": True, "event_id": db_event.id, "event": db_event}


@app.get("/api/cases/{case_id}/timeline")
def get_case_timeline(case_id: int, db: Session = Depends(get_db)):
    """Get timeline for a case"""
    events = db.query(TimelineEvent).filter(
        TimelineEvent.case_id == case_id
    ).order_by(TimelineEvent.event_date.desc()).all()
    return {"events": events, "total": len(events)}


# ============ CONTACT ENDPOINTS ============

@app.post("/api/contacts")
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact"""
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return {"success": True, "contact_id": db_contact.id, "contact": db_contact}


@app.get("/api/cases/{case_id}/contacts")
def get_case_contacts(case_id: int, db: Session = Depends(get_db)):
    """Get all contacts for a case"""
    contacts = db.query(Contact).filter(Contact.case_id == case_id).all()
    return {"contacts": contacts, "total": len(contacts)}


# ============ NOTE ENDPOINTS ============

@app.post("/api/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note"""
    db_note = Note(**note.dict())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return {"success": True, "note_id": db_note.id, "note": db_note}


@app.get("/api/cases/{case_id}/notes")
def get_case_notes(case_id: int, db: Session = Depends(get_db)):
    """Get all notes for a case"""
    notes = db.query(Note).filter(
        Note.case_id == case_id
    ).order_by(Note.created_date.desc()).all()
    return {"notes": notes, "total": len(notes)}


# ============ PDF BUNDLE GENERATION ENDPOINTS ============

@app.post("/api/cases/{case_id}/generate-bundle")
def generate_bundle(
    case_id: int,
    document_ids: List[int],
    bundle_type: str = "hearing",
    start_page: int = 1,
    db: Session = Depends(get_db)
):
    """Generate PDF bundle from selected documents"""
    try:
        generator = BundleGenerator(db, case_id)
        result = generator.generate_bundle(
            document_ids=document_ids,
            bundle_type=bundle_type,
            start_page=start_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/bundle/documents")
def get_bundle_documents(case_id: int, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Get available documents for bundling"""
    try:
        generator = BundleGenerator(db, case_id)
        documents = generator.get_available_documents(category=category)
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cases/{case_id}/generate-chronological-bundle")
def generate_chronological_bundle(
    case_id: int,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate chronological bundle of all case documents"""
    try:
        generator = BundleGenerator(db, case_id)
        result = generator.generate_chronological_bundle(category=category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ SEARCH ENDPOINTS ============

@app.get("/api/search/documents")
def search_documents(
    query: str,
    case_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search documents with full-text search"""
    try:
        search_engine = SearchEngine(db)
        results = search_engine.search_documents(
            query=query,
            case_id=case_id,
            category=category,
            status=status,
            limit=limit
        )
        return {"results": results, "total": len(results), "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/notes")
def search_notes(
    query: str,
    case_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search notes with full-text search"""
    try:
        search_engine = SearchEngine(db)
        results = search_engine.search_notes(query=query, case_id=case_id, limit=limit)
        return {"results": results, "total": len(results), "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/timeline")
def search_timeline(
    query: str,
    case_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search timeline events with full-text search"""
    try:
        search_engine = SearchEngine(db)
        results = search_engine.search_timeline(query=query, case_id=case_id, limit=limit)
        return {"results": results, "total": len(results), "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/all")
def search_all(
    query: str,
    case_id: Optional[int] = None,
    limit_per_type: int = 20,
    db: Session = Depends(get_db)
):
    """Search across all content types"""
    try:
        search_engine = SearchEngine(db)
        results = search_engine.search_all(query=query, case_id=case_id, limit_per_type=limit_per_type)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/reindex")
def reindex_all_content(db: Session = Depends(get_db)):
    """Reindex all searchable content"""
    try:
        search_engine = SearchEngine(db)
        doc_result = search_engine.reindex_all_documents()
        note_result = search_engine.reindex_all_notes()
        timeline_result = search_engine.reindex_all_timeline()

        return {
            "success": True,
            "documents": doc_result,
            "notes": note_result,
            "timeline": timeline_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/statistics")
def get_search_statistics(db: Session = Depends(get_db)):
    """Get search index statistics"""
    try:
        search_engine = SearchEngine(db)
        return search_engine.get_search_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ EMAIL PARSING ENDPOINTS ============

@app.post("/api/cases/{case_id}/import-email")
async def import_email(
    case_id: int,
    file: UploadFile = File(...),
    direction: str = "Received",
    save_attachments: bool = True,
    db: Session = Depends(get_db)
):
    """Import email file (.eml or .msg) into case"""
    try:
        # Save uploaded email file temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse and import email
        parser = EmailParser(db, case_id)
        result = parser.import_email_to_case(
            file_path=temp_path,
            direction=direction,
            save_attachments=save_attachments
        )

        # Clean up temp file
        os.remove(temp_path)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cases/{case_id}/parse-email")
async def parse_email(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parse email file and return metadata without importing"""
    try:
        # Save uploaded email file temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse email
        parser = EmailParser(db, case_id)
        result = parser.parse_email_file(temp_path)

        # Clean up temp file
        os.remove(temp_path)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ TEMPLATE ENGINE ENDPOINTS ============

@app.get("/api/templates")
def get_templates(db: Session = Depends(get_db)):
    """Get available document templates"""
    try:
        # Use a dummy case_id for listing templates
        engine = TemplateEngine(db, 1)
        templates = engine.get_available_templates()
        return {"templates": templates, "total": len(templates)}
    except Exception as e:
        # If no cases exist, return empty list
        return {"templates": [], "total": 0}


@app.post("/api/cases/{case_id}/generate-from-template")
def generate_from_template(
    case_id: int,
    template_id: str,
    variables: Dict,
    output_format: str = "docx",
    db: Session = Depends(get_db)
):
    """Generate document from template"""
    try:
        engine = TemplateEngine(db, case_id)
        result = engine.generate_document_from_template(
            template_id=template_id,
            variables=variables,
            output_format=output_format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/template-preview/{template_id}")
def get_template_preview(
    case_id: int,
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get template preview with case variables"""
    try:
        engine = TemplateEngine(db, case_id)
        result = engine.get_template_preview(template_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ EXPORT ENDPOINTS ============

@app.get("/api/cases/{case_id}/export/summary-word")
def export_summary_word(case_id: int, db: Session = Depends(get_db)):
    """Export case summary to Word document"""
    try:
        exporter = ExportEngine(db, case_id)
        result = exporter.export_case_summary_word()

        if result.get('success'):
            return FileResponse(
                result['file_path'],
                filename=result['filename'],
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/export/summary-pdf")
def export_summary_pdf(case_id: int, db: Session = Depends(get_db)):
    """Export case summary to PDF"""
    try:
        exporter = ExportEngine(db, case_id)
        result = exporter.export_case_summary_pdf()

        if result.get('success'):
            return FileResponse(
                result['file_path'],
                filename=result['filename'],
                media_type='application/pdf'
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/export/timeline-word")
def export_timeline_word(case_id: int, db: Session = Depends(get_db)):
    """Export timeline/chronology to Word document"""
    try:
        exporter = ExportEngine(db, case_id)
        result = exporter.export_timeline_word()

        if result.get('success'):
            return FileResponse(
                result['file_path'],
                filename=result['filename'],
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/export/notes-word")
def export_notes_word(case_id: int, db: Session = Depends(get_db)):
    """Export case notes to Word document"""
    try:
        exporter = ExportEngine(db, case_id)
        result = exporter.export_notes_word()

        if result.get('success'):
            return FileResponse(
                result['file_path'],
                filename=result['filename'],
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH CHECK ============

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Legal Case Management System"}


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Legal Case Management System API", "version": "2.0.0 - Phase 2 & 3"}
