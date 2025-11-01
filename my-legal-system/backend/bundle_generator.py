"""
PDF Bundle Generator - Create paginated, indexed legal document bundles
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Document, Case
import io


class BundleGenerator:
    """Generate professional legal document bundles"""

    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id
        self.case = db.query(Case).filter(Case.id == case_id).first()
        if not self.case:
            raise ValueError(f"Case {case_id} not found")

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='BundleTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='BundleSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=6
        ))

    def generate_bundle(
        self,
        document_ids: List[int],
        bundle_type: str = "hearing",
        output_filename: Optional[str] = None,
        start_page: int = 1
    ) -> Dict:
        """
        Generate a complete PDF bundle

        Args:
            document_ids: List of document IDs to include
            bundle_type: Type of bundle (hearing, disclosure, trial, etc.)
            output_filename: Custom filename (auto-generated if None)
            start_page: Starting page number

        Returns:
            Dict with bundle information
        """
        # Get documents
        documents = self.db.query(Document).filter(
            Document.id.in_(document_ids)
        ).order_by(Document.document_date).all()

        if not documents:
            return {"error": "No documents found"}

        # Generate filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{self.case.case_number}_{bundle_type}_bundle_{timestamp}.pdf"

        # Create exports directory
        exports_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'exports'
        )
        os.makedirs(exports_dir, exist_ok=True)

        output_path = os.path.join(exports_dir, output_filename)

        # Generate bundle
        bundle_info = self._create_bundle(
            documents,
            output_path,
            bundle_type,
            start_page
        )

        return {
            "success": True,
            "bundle_path": output_path,
            "bundle_filename": output_filename,
            "bundle_type": bundle_type,
            "total_documents": len(documents),
            "total_pages": bundle_info.get('total_pages', 0),
            "generated_date": datetime.now().isoformat()
        }

    def _create_bundle(
        self,
        documents: List[Document],
        output_path: str,
        bundle_type: str,
        start_page: int
    ) -> Dict:
        """Create the actual PDF bundle"""

        # Create temporary PDF for cover and TOC
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Add cover page
        story.extend(self._generate_cover_page(bundle_type))
        story.append(PageBreak())

        # Add table of contents
        toc_entries = self._generate_toc(documents, start_page)
        story.extend(toc_entries['content'])
        story.append(PageBreak())

        # Build the cover/TOC PDF
        doc.build(story)
        buffer.seek(0)

        # Merge with actual documents
        final_pdf = PdfWriter()

        # Add cover and TOC
        cover_pdf = PdfReader(buffer)
        for page in cover_pdf.pages:
            final_pdf.add_page(page)

        current_page = start_page + len(cover_pdf.pages)

        # Add each document with page numbers
        for doc_info in documents:
            if os.path.exists(doc_info.file_path):
                try:
                    doc_pdf = PdfReader(doc_info.file_path)
                    for page_num, page in enumerate(doc_pdf.pages):
                        # Add page number
                        page_with_number = self._add_page_number(
                            page,
                            current_page + page_num
                        )
                        final_pdf.add_page(page_with_number)

                    current_page += len(doc_pdf.pages)
                except Exception as e:
                    print(f"Error adding document {doc_info.filename}: {e}")

        # Write final bundle
        with open(output_path, 'wb') as output_file:
            final_pdf.write(output_file)

        return {
            'total_pages': current_page - start_page,
            'documents_included': len(documents)
        }

    def _generate_cover_page(self, bundle_type: str) -> List:
        """Generate bundle cover page"""
        story = []

        # Title
        title = Paragraph(
            f"{bundle_type.upper()} BUNDLE",
            self.styles['BundleTitle']
        )
        story.append(Spacer(1, 1*inch))
        story.append(title)
        story.append(Spacer(1, 0.5*inch))

        # Case information
        case_info = [
            f"<b>Case Number:</b> {self.case.case_number}",
            f"<b>Case Title:</b> {self.case.title}",
            f"<b>Case Type:</b> {self.case.case_type}",
            f"<b>Bundle Generated:</b> {datetime.now().strftime('%d %B %Y at %H:%M')}",
        ]

        for info in case_info:
            p = Paragraph(info, self.styles['BundleSubtitle'])
            story.append(p)
            story.append(Spacer(1, 0.2*inch))

        story.append(Spacer(1, 1*inch))

        # Mission statement if available
        if self.case.mission_statement:
            story.append(Paragraph(
                "<b>Case Mission:</b>",
                self.styles['BundleSubtitle']
            ))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                self.case.mission_statement,
                self.styles['Normal']
            ))

        return story

    def _generate_toc(self, documents: List[Document], start_page: int) -> Dict:
        """Generate table of contents"""
        story = []

        # TOC Title
        toc_title = Paragraph("TABLE OF CONTENTS", self.styles['Heading1'])
        story.append(toc_title)
        story.append(Spacer(1, 0.3*inch))

        # Build TOC table
        toc_data = [['Exhibit', 'Document', 'Date', 'Page']]

        current_page = start_page + 2  # Account for cover and TOC pages
        exhibit_num = 1

        for doc in documents:
            # Try to get page count
            page_count = 1
            if os.path.exists(doc.file_path):
                try:
                    pdf = PdfReader(doc.file_path)
                    page_count = len(pdf.pages)
                except:
                    pass

            doc_date = doc.document_date.strftime('%d/%m/%Y') if doc.document_date else 'N/A'

            toc_data.append([
                f"Ex {exhibit_num}",
                doc.filename[:40] + ('...' if len(doc.filename) > 40 else ''),
                doc_date,
                str(current_page)
            ])

            current_page += page_count
            exhibit_num += 1

        # Create TOC table
        toc_table = Table(toc_data, colWidths=[1*inch, 3.5*inch, 1.2*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(toc_table)

        return {
            'content': story,
            'entries': len(documents)
        }

    def _add_page_number(self, page, page_num: int):
        """Add page number to a PDF page"""
        # Create a new PDF with just the page number
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # Add page number at bottom center
        can.setFont('Helvetica', 10)
        can.drawCentredString(
            A4[0] / 2,
            30,
            f"Page {page_num}"
        )
        can.save()

        # Move to the beginning of the StringIO buffer
        packet.seek(0)

        # Merge with original page
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])

        return page

    def get_available_documents(self, category: Optional[str] = None) -> List[Dict]:
        """Get list of documents available for bundling"""
        query = self.db.query(Document).filter(Document.case_id == self.case_id)

        if category:
            query = query.filter(Document.category == category)

        documents = query.order_by(Document.document_date).all()

        return [{
            'id': doc.id,
            'filename': doc.filename,
            'category': doc.category,
            'date': doc.document_date.isoformat() if doc.document_date else None,
            'status': doc.status,
            'file_size': doc.file_size
        } for doc in documents]

    def generate_chronological_bundle(
        self,
        category: Optional[str] = None,
        bundle_type: str = "chronological"
    ) -> Dict:
        """Generate a bundle with all documents in chronological order"""
        documents = self.db.query(Document).filter(
            Document.case_id == self.case_id
        )

        if category:
            documents = documents.filter(Document.category == category)

        documents = documents.order_by(Document.document_date).all()

        document_ids = [doc.id for doc in documents]

        return self.generate_bundle(
            document_ids=document_ids,
            bundle_type=bundle_type
        )

    def generate_category_bundle(self, category: str) -> Dict:
        """Generate a bundle for a specific document category"""
        documents = self.db.query(Document).filter(
            Document.case_id == self.case_id,
            Document.category == category
        ).order_by(Document.document_date).all()

        document_ids = [doc.id for doc in documents]

        return self.generate_bundle(
            document_ids=document_ids,
            bundle_type=f"{category.lower()}_bundle"
        )
