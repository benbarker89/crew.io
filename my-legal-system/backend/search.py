"""
Full-Text Search Engine using SQLite FTS5
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, date
from models import Document, Case, Note, TimelineEvent, Task
import os


class SearchEngine:
    """Full-text search across documents and case data"""

    def __init__(self, db: Session):
        self.db = db
        self._initialize_fts()

    def _initialize_fts(self):
        """Initialize FTS5 virtual tables"""
        # Create FTS5 table for documents if not exists
        self.db.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                document_id UNINDEXED,
                case_id UNINDEXED,
                filename,
                content,
                category,
                description,
                tokenize='porter unicode61'
            )
        """))

        # Create FTS5 table for notes
        self.db.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                note_id UNINDEXED,
                case_id UNINDEXED,
                title,
                content,
                tags,
                tokenize='porter unicode61'
            )
        """))

        # Create FTS5 table for timeline events
        self.db.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS timeline_fts USING fts5(
                event_id UNINDEXED,
                case_id UNINDEXED,
                title,
                description,
                party_involved,
                tokenize='porter unicode61'
            )
        """))

        self.db.commit()

    def index_document(self, document_id: int, content: Optional[str] = None) -> bool:
        """
        Index a document for full-text search

        Args:
            document_id: Document ID to index
            content: Optional extracted text content from document

        Returns:
            Success status
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False

        # If no content provided, try to extract from file
        if not content and document.file_path:
            content = self._extract_text_from_file(document.file_path)

        # Delete existing entry
        self.db.execute(
            text("DELETE FROM documents_fts WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )

        # Insert into FTS table
        self.db.execute(text("""
            INSERT INTO documents_fts (document_id, case_id, filename, content, category, description)
            VALUES (:doc_id, :case_id, :filename, :content, :category, :description)
        """), {
            "doc_id": document.id,
            "case_id": document.case_id,
            "filename": document.filename,
            "content": content or "",
            "category": document.category or "",
            "description": document.description or ""
        })

        self.db.commit()
        return True

    def index_note(self, note_id: int) -> bool:
        """Index a note for full-text search"""
        note = self.db.query(Note).filter(Note.id == note_id).first()
        if not note:
            return False

        # Delete existing entry
        self.db.execute(
            text("DELETE FROM notes_fts WHERE note_id = :note_id"),
            {"note_id": note_id}
        )

        # Insert into FTS table
        self.db.execute(text("""
            INSERT INTO notes_fts (note_id, case_id, title, content, tags)
            VALUES (:note_id, :case_id, :title, :content, :tags)
        """), {
            "note_id": note.id,
            "case_id": note.case_id,
            "title": note.title or "",
            "content": note.content or "",
            "tags": note.tags or ""
        })

        self.db.commit()
        return True

    def index_timeline_event(self, event_id: int) -> bool:
        """Index a timeline event for full-text search"""
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            return False

        # Delete existing entry
        self.db.execute(
            text("DELETE FROM timeline_fts WHERE event_id = :event_id"),
            {"event_id": event_id}
        )

        # Insert into FTS table
        self.db.execute(text("""
            INSERT INTO timeline_fts (event_id, case_id, title, description, party_involved)
            VALUES (:event_id, :case_id, :title, :description, :party)
        """), {
            "event_id": event.id,
            "case_id": event.case_id,
            "title": event.title or "",
            "description": event.description or "",
            "party": event.party_involved or ""
        })

        self.db.commit()
        return True

    def search_documents(
        self,
        query: str,
        case_id: Optional[int] = None,
        category: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search documents with full-text search and filters

        Args:
            query: Search query string
            case_id: Filter by case ID
            category: Filter by document category
            date_from: Filter by start date
            date_to: Filter by end date
            status: Filter by document status
            limit: Maximum results

        Returns:
            List of matching documents with snippets
        """
        # Build FTS query
        fts_query = query

        # Search in FTS table
        fts_results = self.db.execute(text("""
            SELECT
                document_id,
                case_id,
                filename,
                category,
                snippet(documents_fts, 2, '<mark>', '</mark>', '...', 64) as snippet,
                rank
            FROM documents_fts
            WHERE documents_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """), {"query": fts_query, "limit": limit}).fetchall()

        # Get full document details
        results = []
        for row in fts_results:
            document = self.db.query(Document).filter(
                Document.id == row.document_id
            ).first()

            if not document:
                continue

            # Apply additional filters
            if case_id and document.case_id != case_id:
                continue
            if category and document.category != category:
                continue
            if status and document.status != status:
                continue
            if date_from and document.document_date and document.document_date < date_from:
                continue
            if date_to and document.document_date and document.document_date > date_to:
                continue

            # Get case info
            case = self.db.query(Case).filter(Case.id == document.case_id).first()

            results.append({
                'document_id': document.id,
                'filename': document.filename,
                'category': document.category,
                'status': document.status,
                'document_date': document.document_date.isoformat() if document.document_date else None,
                'upload_date': document.upload_date.isoformat() if document.upload_date else None,
                'case_id': document.case_id,
                'case_number': case.case_number if case else None,
                'case_title': case.title if case else None,
                'snippet': row.snippet,
                'relevance_score': abs(row.rank)
            })

        return results

    def search_notes(
        self,
        query: str,
        case_id: Optional[int] = None,
        note_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Search notes with full-text search"""
        fts_results = self.db.execute(text("""
            SELECT
                note_id,
                case_id,
                title,
                snippet(notes_fts, 1, '<mark>', '</mark>', '...', 64) as snippet,
                rank
            FROM notes_fts
            WHERE notes_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """), {"query": query, "limit": limit}).fetchall()

        results = []
        for row in fts_results:
            note = self.db.query(Note).filter(Note.id == row.note_id).first()

            if not note:
                continue

            # Apply filters
            if case_id and note.case_id != case_id:
                continue
            if note_type and note.note_type != note_type:
                continue

            # Get case info
            case = self.db.query(Case).filter(Case.id == note.case_id).first()

            results.append({
                'note_id': note.id,
                'title': note.title,
                'note_type': note.note_type,
                'created_date': note.created_date.isoformat() if note.created_date else None,
                'tags': note.tags,
                'case_id': note.case_id,
                'case_number': case.case_number if case else None,
                'snippet': row.snippet,
                'relevance_score': abs(row.rank)
            })

        return results

    def search_timeline(
        self,
        query: str,
        case_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Search timeline events"""
        fts_results = self.db.execute(text("""
            SELECT
                event_id,
                case_id,
                title,
                snippet(timeline_fts, 1, '<mark>', '</mark>', '...', 64) as snippet,
                rank
            FROM timeline_fts
            WHERE timeline_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """), {"query": query, "limit": limit}).fetchall()

        results = []
        for row in fts_results:
            event = self.db.query(TimelineEvent).filter(
                TimelineEvent.id == row.event_id
            ).first()

            if not event:
                continue

            # Apply filters
            if case_id and event.case_id != case_id:
                continue
            if event_type and event.event_type != event_type:
                continue

            # Get case info
            case = self.db.query(Case).filter(Case.id == event.case_id).first()

            results.append({
                'event_id': event.id,
                'title': event.title,
                'event_type': event.event_type,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'is_key_event': event.is_key_event,
                'case_id': event.case_id,
                'case_number': case.case_number if case else None,
                'snippet': row.snippet,
                'relevance_score': abs(row.rank)
            })

        return results

    def search_all(
        self,
        query: str,
        case_id: Optional[int] = None,
        limit_per_type: int = 20
    ) -> Dict:
        """
        Search across all indexed content

        Returns:
            Dict with results categorized by type
        """
        return {
            'documents': self.search_documents(query, case_id=case_id, limit=limit_per_type),
            'notes': self.search_notes(query, case_id=case_id, limit=limit_per_type),
            'timeline': self.search_timeline(query, case_id=case_id, limit=limit_per_type),
            'query': query,
            'case_id': case_id
        }

    def reindex_all_documents(self) -> Dict:
        """Reindex all documents in the system"""
        documents = self.db.query(Document).all()
        indexed = 0
        failed = 0

        for doc in documents:
            try:
                self.index_document(doc.id)
                indexed += 1
            except Exception as e:
                print(f"Failed to index document {doc.id}: {e}")
                failed += 1

        return {
            'indexed': indexed,
            'failed': failed,
            'total': len(documents)
        }

    def reindex_all_notes(self) -> Dict:
        """Reindex all notes in the system"""
        notes = self.db.query(Note).all()
        indexed = 0

        for note in notes:
            self.index_note(note.id)
            indexed += 1

        return {'indexed': indexed}

    def reindex_all_timeline(self) -> Dict:
        """Reindex all timeline events in the system"""
        events = self.db.query(TimelineEvent).all()
        indexed = 0

        for event in events:
            self.index_timeline_event(event.id)
            indexed += 1

        return {'indexed': indexed}

    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from file (basic implementation)

        For Phase 2, this is a placeholder. Can be enhanced with:
        - PDF text extraction (PyPDF2, pdfplumber)
        - Word document extraction (python-docx)
        - OCR for scanned documents (pytesseract)
        """
        try:
            # For now, just return empty string
            # In production, implement proper extraction based on file type
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            elif file_path.endswith('.pdf'):
                # TODO: Implement PDF text extraction
                from PyPDF2 import PdfReader
                try:
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except:
                    return ""
            else:
                return ""
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    def get_search_statistics(self) -> Dict:
        """Get statistics about indexed content"""
        doc_count = self.db.execute(
            text("SELECT COUNT(*) FROM documents_fts")
        ).scalar()

        note_count = self.db.execute(
            text("SELECT COUNT(*) FROM notes_fts")
        ).scalar()

        timeline_count = self.db.execute(
            text("SELECT COUNT(*) FROM timeline_fts")
        ).scalar()

        return {
            'indexed_documents': doc_count,
            'indexed_notes': note_count,
            'indexed_timeline_events': timeline_count,
            'total_indexed': doc_count + note_count + timeline_count
        }
