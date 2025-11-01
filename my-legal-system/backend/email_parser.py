"""
Email Parser - Extract metadata and content from .eml and .msg files
"""
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime
from typing import Dict, List, Optional
import os
import shutil
from sqlalchemy.orm import Session
from models import Document, Correspondence, Contact, TimelineEvent
try:
    import extract_msg
    MSG_SUPPORT = True
except ImportError:
    MSG_SUPPORT = False


class EmailParser:
    """Parse and extract information from email files"""

    def __init__(self, db: Session, case_id: int):
        self.db = db
        self.case_id = case_id

    def parse_eml_file(self, file_path: str) -> Dict:
        """
        Parse .eml file and extract metadata

        Args:
            file_path: Path to .eml file

        Returns:
            Dict with extracted email data
        """
        try:
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)

            # Extract basic metadata
            email_data = {
                'subject': msg.get('subject', ''),
                'from': msg.get('from', ''),
                'to': msg.get('to', ''),
                'cc': msg.get('cc', ''),
                'date': self._parse_email_date(msg.get('date')),
                'message_id': msg.get('message-id', ''),
                'body_text': '',
                'body_html': '',
                'attachments': [],
                'headers': dict(msg.items())
            }

            # Extract body content
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    # Get text body
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        try:
                            email_data['body_text'] = part.get_content()
                        except:
                            pass

                    # Get HTML body
                    elif content_type == 'text/html' and 'attachment' not in content_disposition:
                        try:
                            email_data['body_html'] = part.get_content()
                        except:
                            pass

                    # Get attachments
                    elif 'attachment' in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            email_data['attachments'].append({
                                'filename': filename,
                                'content_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
            else:
                # Non-multipart message
                content_type = msg.get_content_type()
                if content_type == 'text/plain':
                    email_data['body_text'] = msg.get_content()
                elif content_type == 'text/html':
                    email_data['body_html'] = msg.get_content()

            return {
                'success': True,
                'email_data': email_data,
                'file_type': 'eml'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def parse_msg_file(self, file_path: str) -> Dict:
        """
        Parse .msg file and extract metadata

        Args:
            file_path: Path to .msg file

        Returns:
            Dict with extracted email data
        """
        if not MSG_SUPPORT:
            return {
                'success': False,
                'error': 'MSG file support not available. Install extract-msg package.'
            }

        try:
            msg = extract_msg.Message(file_path)

            email_data = {
                'subject': msg.subject or '',
                'from': msg.sender or '',
                'to': msg.to or '',
                'cc': msg.cc or '',
                'date': msg.date,
                'message_id': msg.message_id or '',
                'body_text': msg.body or '',
                'body_html': msg.htmlBody or '',
                'attachments': [],
                'headers': {}
            }

            # Extract attachments
            for attachment in msg.attachments:
                email_data['attachments'].append({
                    'filename': attachment.longFilename or attachment.shortFilename,
                    'content_type': attachment.mimetype or 'application/octet-stream',
                    'size': len(attachment.data) if hasattr(attachment, 'data') else 0
                })

            msg.close()

            return {
                'success': True,
                'email_data': email_data,
                'file_type': 'msg'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def parse_email_file(self, file_path: str) -> Dict:
        """
        Parse email file (auto-detect .eml or .msg)

        Args:
            file_path: Path to email file

        Returns:
            Dict with extracted email data
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.eml':
            return self.parse_eml_file(file_path)
        elif file_ext == '.msg':
            return self.parse_msg_file(file_path)
        else:
            return {
                'success': False,
                'error': f'Unsupported file type: {file_ext}'
            }

    def import_email_to_case(
        self,
        file_path: str,
        direction: str = 'Received',
        save_attachments: bool = True
    ) -> Dict:
        """
        Import email file into case correspondence and documents

        Args:
            file_path: Path to email file
            direction: 'Sent' or 'Received'
            save_attachments: Whether to save attachments as separate documents

        Returns:
            Dict with import results
        """
        # Parse email
        parse_result = self.parse_email_file(file_path)

        if not parse_result.get('success'):
            return parse_result

        email_data = parse_result['email_data']

        # Extract sender/recipient info
        sender_email = self._extract_email_address(email_data['from'])
        sender_name = self._extract_name(email_data['from'])

        # Find or create contact
        contact = self._find_or_create_contact(sender_name, sender_email)

        # Save email as document
        doc_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'documents',
            str(self.case_id),
            'correspondence'
        )
        os.makedirs(doc_dir, exist_ok=True)

        # Copy email file to documents directory
        email_filename = os.path.basename(file_path)
        new_email_path = os.path.join(doc_dir, email_filename)
        shutil.copy2(file_path, new_email_path)

        # Create document record
        document = Document(
            case_id=self.case_id,
            filename=email_filename,
            file_path=new_email_path,
            category='Correspondence',
            document_type='Email',
            status='Final',
            document_date=email_data['date'],
            description=f"Email: {email_data['subject']}",
            file_size=os.path.getsize(new_email_path)
        )

        self.db.add(document)
        self.db.flush()

        # Create correspondence record
        correspondence = Correspondence(
            contact_id=contact.id,
            document_id=document.id,
            date=email_data['date'],
            direction=direction,
            method='Email',
            subject=email_data['subject'],
            summary=self._create_email_summary(email_data),
            response_status='Received' if direction == 'Received' else 'Sent'
        )

        self.db.add(correspondence)

        # Create timeline event
        timeline_event = TimelineEvent(
            case_id=self.case_id,
            event_date=email_data['date'],
            event_type='Communication',
            title=f"Email: {email_data['subject'][:50]}",
            description=f"{direction} email from/to {sender_name or sender_email}",
            party_involved=sender_name or sender_email
        )

        self.db.add(timeline_event)

        # Process attachments
        attachment_results = []
        if save_attachments and email_data['attachments']:
            # TODO: Extract and save attachments
            # This would require extracting attachment content from the email
            attachment_results = self._process_attachments(
                file_path,
                email_data['attachments'],
                parse_result['file_type']
            )

        self.db.commit()

        return {
            'success': True,
            'document_id': document.id,
            'correspondence_id': correspondence.id,
            'contact_id': contact.id,
            'timeline_event_id': timeline_event.id,
            'attachments_processed': len(attachment_results),
            'email_subject': email_data['subject'],
            'email_date': email_data['date'].isoformat() if email_data['date'] else None,
            'sender': f"{sender_name} <{sender_email}>" if sender_name else sender_email
        }

    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string to datetime"""
        if not date_str:
            return None

        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return None

    def _extract_email_address(self, from_str: str) -> str:
        """Extract email address from 'From' string"""
        if not from_str:
            return ''

        # Handle format: "Name <email@example.com>" or just "email@example.com"
        if '<' in from_str and '>' in from_str:
            start = from_str.index('<') + 1
            end = from_str.index('>')
            return from_str[start:end].strip()
        else:
            return from_str.strip()

    def _extract_name(self, from_str: str) -> Optional[str]:
        """Extract name from 'From' string"""
        if not from_str:
            return None

        # Handle format: "Name <email@example.com>"
        if '<' in from_str:
            name = from_str[:from_str.index('<')].strip()
            # Remove quotes if present
            name = name.strip('"').strip("'")
            return name if name else None
        else:
            return None

    def _find_or_create_contact(
        self,
        name: Optional[str],
        email: str
    ) -> Contact:
        """Find existing contact or create new one"""
        # Try to find by email
        contact = self.db.query(Contact).filter(
            Contact.case_id == self.case_id,
            Contact.email == email
        ).first()

        if contact:
            return contact

        # Create new contact
        contact = Contact(
            case_id=self.case_id,
            name=name or email,
            role='Correspondent',
            email=email
        )

        self.db.add(contact)
        self.db.flush()

        return contact

    def _create_email_summary(self, email_data: Dict) -> str:
        """Create a summary of the email"""
        body = email_data['body_text'] or email_data['body_html']

        # Take first 500 characters of body
        if body:
            summary = body[:500]
            if len(body) > 500:
                summary += '...'
            return summary
        else:
            return f"Email with subject: {email_data['subject']}"

    def _process_attachments(
        self,
        email_file_path: str,
        attachments: List[Dict],
        file_type: str
    ) -> List[Dict]:
        """
        Process and save email attachments

        Args:
            email_file_path: Path to email file
            attachments: List of attachment metadata
            file_type: 'eml' or 'msg'

        Returns:
            List of processed attachment results
        """
        results = []

        try:
            if file_type == 'eml':
                results = self._extract_eml_attachments(email_file_path, attachments)
            elif file_type == 'msg' and MSG_SUPPORT:
                results = self._extract_msg_attachments(email_file_path, attachments)
        except Exception as e:
            print(f"Error processing attachments: {e}")

        return results

    def _extract_eml_attachments(
        self,
        email_file_path: str,
        attachment_metadata: List[Dict]
    ) -> List[Dict]:
        """Extract attachments from .eml file"""
        results = []

        try:
            with open(email_file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)

            attachment_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'documents',
                str(self.case_id),
                'attachments'
            )
            os.makedirs(attachment_dir, exist_ok=True)

            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition', ''))

                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Save attachment
                        attachment_path = os.path.join(attachment_dir, filename)
                        with open(attachment_path, 'wb') as af:
                            af.write(part.get_payload(decode=True))

                        # Create document record
                        document = Document(
                            case_id=self.case_id,
                            filename=filename,
                            file_path=attachment_path,
                            category='Evidence',
                            document_type='Email Attachment',
                            status='Final',
                            file_size=os.path.getsize(attachment_path)
                        )

                        self.db.add(document)
                        self.db.flush()

                        results.append({
                            'filename': filename,
                            'document_id': document.id,
                            'success': True
                        })

        except Exception as e:
            print(f"Error extracting .eml attachments: {e}")

        return results

    def _extract_msg_attachments(
        self,
        email_file_path: str,
        attachment_metadata: List[Dict]
    ) -> List[Dict]:
        """Extract attachments from .msg file"""
        results = []

        if not MSG_SUPPORT:
            return results

        try:
            msg = extract_msg.Message(email_file_path)

            attachment_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'documents',
                str(self.case_id),
                'attachments'
            )
            os.makedirs(attachment_dir, exist_ok=True)

            for attachment in msg.attachments:
                filename = attachment.longFilename or attachment.shortFilename

                # Save attachment
                attachment_path = os.path.join(attachment_dir, filename)
                with open(attachment_path, 'wb') as af:
                    af.write(attachment.data)

                # Create document record
                document = Document(
                    case_id=self.case_id,
                    filename=filename,
                    file_path=attachment_path,
                    category='Evidence',
                    document_type='Email Attachment',
                    status='Final',
                    file_size=os.path.getsize(attachment_path)
                )

                self.db.add(document)
                self.db.flush()

                results.append({
                    'filename': filename,
                    'document_id': document.id,
                    'success': True
                })

            msg.close()

        except Exception as e:
            print(f"Error extracting .msg attachments: {e}")

        return results

    def get_email_thread(self, message_id: str) -> List[Dict]:
        """
        Get email thread based on message ID or subject

        Args:
            message_id: Email message ID

        Returns:
            List of emails in the thread
        """
        # This is a simplified implementation
        # A full implementation would parse In-Reply-To and References headers

        correspondences = self.db.query(Correspondence).filter(
            Correspondence.subject.like(f"%{message_id}%")
        ).order_by(Correspondence.date).all()

        return [{
            'id': corr.id,
            'subject': corr.subject,
            'date': corr.date.isoformat() if corr.date else None,
            'direction': corr.direction,
            'contact_id': corr.contact_id
        } for corr in correspondences]
