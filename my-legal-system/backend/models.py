"""
Database models for Personal Legal Case Management System
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'legal_cases.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)


class Case(Base):
    """Main case/matter table"""
    __tablename__ = 'cases'

    id = Column(Integer, primary_key=True)
    case_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    case_type = Column(String(100))  # Employment Tribunal, Criminal, Regulatory, County Court
    status = Column(String(50))  # Preparation, Active Litigation, Awaiting Response, Closed
    priority = Column(String(20))  # Urgent, High, Medium, Low
    mission_statement = Column(Text)  # Primary objective for the case
    created_date = Column(DateTime, default=datetime.utcnow)
    closed_date = Column(DateTime, nullable=True)

    # Relationships
    milestones = relationship("Milestone", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="case", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="case", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="case", cascade="all, delete-orphan")
    parties = relationship("Party", back_populates="case", cascade="all, delete-orphan")
    critical_dates = relationship("CriticalDate", back_populates="case", cascade="all, delete-orphan")


class Milestone(Base):
    """Mission milestones for tracking case progress"""
    __tablename__ = 'milestones'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    title = Column(String(500), nullable=False)
    milestone_type = Column(String(100))  # Pre-action, Procedural, Evidence, Hearing, Outcome
    description = Column(Text)
    target_date = Column(Date, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    order_index = Column(Integer, default=0)  # For ordering milestones
    blocks_milestone_id = Column(Integer, ForeignKey('milestones.id'), nullable=True)  # Dependency

    # Relationships
    case = relationship("Case", back_populates="milestones")
    blocked_by = relationship("Milestone", remote_side=[id], backref="blocks")


class Task(Base):
    """Tasks and deadlines"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    milestone_id = Column(Integer, ForeignKey('milestones.id'), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    priority = Column(String(20))  # Urgent, Critical, Preparation, Administrative, Strategic
    status = Column(String(50), default='Pending')  # Pending, In Progress, Completed, Blocked
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    is_court_deadline = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    depends_on_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)

    # Relationships
    case = relationship("Case", back_populates="tasks")
    milestone = relationship("Milestone")
    depends_on = relationship("Task", remote_side=[id], backref="blocking_tasks")


class Document(Base):
    """Document management"""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    category = Column(String(100))  # Pleadings, Evidence, Correspondence, Orders, Research
    document_type = Column(String(100))
    status = Column(String(50))  # Draft, Final, Filed, Privileged
    upload_date = Column(DateTime, default=datetime.utcnow)
    document_date = Column(Date, nullable=True)
    description = Column(Text)
    file_size = Column(Integer)
    page_count = Column(Integer, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="documents")
    timeline_links = relationship("DocumentTimelineLink", back_populates="document", cascade="all, delete-orphan")


class TimelineEvent(Base):
    """Timeline and chronology entries"""
    __tablename__ = 'timeline_events'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_type = Column(String(100))  # Incident, Communication, Document, Court Action
    title = Column(String(500), nullable=False)
    description = Column(Text)
    party_involved = Column(String(200))
    is_key_event = Column(Boolean, default=False)  # Flag important events
    created_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="timeline_events")
    document_links = relationship("DocumentTimelineLink", back_populates="event", cascade="all, delete-orphan")


class DocumentTimelineLink(Base):
    """Link documents to timeline events"""
    __tablename__ = 'document_timeline_links'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    timeline_event_id = Column(Integer, ForeignKey('timeline_events.id'), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="timeline_links")
    event = relationship("TimelineEvent", back_populates="document_links")


class Contact(Base):
    """Contacts and parties"""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(100))  # Witness, Opposing Party, Legal Rep, Expert, Other
    organization = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    address = Column(Text)
    notes = Column(Text)

    # Relationships
    case = relationship("Case", back_populates="contacts")
    correspondence = relationship("Correspondence", back_populates="contact", cascade="all, delete-orphan")


class Correspondence(Base):
    """Correspondence log"""
    __tablename__ = 'correspondence'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    date = Column(DateTime, nullable=False)
    direction = Column(String(20))  # Sent, Received
    method = Column(String(50))  # Email, Letter, Phone, Meeting
    subject = Column(String(500))
    summary = Column(Text)
    response_status = Column(String(50))  # Sent, Awaiting Reply, Received, No Response Required
    response_due_date = Column(Date, nullable=True)

    # Relationships
    contact = relationship("Contact", back_populates="correspondence")
    document = relationship("Document")


class Note(Base):
    """Case notes and journal"""
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    note_type = Column(String(50))  # Journal, Strategy, Research, Meeting
    tags = Column(String(500))  # Comma-separated tags
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="notes")


class Party(Base):
    """Key parties in the case"""
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    name = Column(String(200), nullable=False)
    party_type = Column(String(100))  # Claimant, Respondent, Defendant, Witness, Legal Representative
    organization = Column(String(200))

    # Relationships
    case = relationship("Case", back_populates="parties")


class CriticalDate(Base):
    """Important case dates and deadlines"""
    __tablename__ = 'critical_dates'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    title = Column(String(500), nullable=False)
    date = Column(Date, nullable=False)
    date_type = Column(String(100))  # Hearing, Deadline, Filing Date, Trial Date
    description = Column(Text)
    is_court_imposed = Column(Boolean, default=False)

    # Relationships
    case = relationship("Case", back_populates="critical_dates")


def init_db():
    """Initialize the database"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)
    print(f"Database initialized at {DB_PATH}")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
