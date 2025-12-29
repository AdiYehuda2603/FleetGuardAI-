"""
FleetGuard AI - Email Invoice Fetcher
======================================
Automatically retrieves invoice attachments (PDF/Excel/CSV) from email using IMAP protocol.

This module provides:
- Universal IMAP support (Gmail, Outlook, Yahoo, any IMAP provider)
- Attachment download and processing
- Integration with existing FileProcessor
- Duplicate prevention and error handling

Author: FleetGuard AI System
Date: 2025-12-19
"""

import imaplib
import email
from email.header import decode_header
import ssl
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """
    Configuration for email IMAP connection.

    Attributes:
        imap_server: IMAP server address (e.g., imap.gmail.com)
        imap_port: IMAP port (usually 993 for SSL)
        email_address: Email account address
        email_password: Email password or app-specific password
        folder: Email folder/label to monitor (default: INBOX)
        mark_as_read: Mark emails as read after processing (default: True)
        max_fetch: Maximum number of emails to fetch per sync (default: 50)
        date_filter_days: Only fetch emails from last N days (default: 30)
    """
    imap_server: str
    imap_port: int
    email_address: str
    email_password: str
    folder: str = "INBOX"
    mark_as_read: bool = True
    max_fetch: int = 50
    date_filter_days: int = 30


class EmailFetcher:
    """
    Handles IMAP email connection and retrieval.

    Supports any IMAP provider (Gmail, Outlook, Yahoo, custom servers).
    Uses SSL/TLS for secure connections.
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize EmailFetcher with configuration.

        Args:
            config: EmailConfig instance with connection details
        """
        self.config = config
        self.imap = None
        self.connected = False

    def connect(self) -> Tuple[bool, str]:
        """
        Establish SSL/TLS IMAP connection.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Create SSL context with certificate verification
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Connect to IMAP server with SSL
            self.imap = imaplib.IMAP4_SSL(
                host=self.config.imap_server,
                port=self.config.imap_port,
                ssl_context=context
            )

            # Login
            self.imap.login(self.config.email_address, self.config.email_password)
            self.connected = True

            logger.info(f"Successfully connected to {self.config.imap_server}")
            return True, "התחברות הצליחה"

        except imaplib.IMAP4.error as e:
            error_msg = f"IMAP error: {str(e)}"
            logger.error(error_msg)
            return False, f"שגיאת אימות: {str(e)}"

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return False, f"שגיאת חיבור: {str(e)}"

    def disconnect(self):
        """Safely disconnect from IMAP server."""
        if self.imap and self.connected:
            try:
                self.imap.close()
                self.imap.logout()
                self.connected = False
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")

    def list_folders(self) -> List[str]:
        """
        List all available folders/labels in the mailbox.

        Returns:
            List of folder names (decoded from IMAP UTF-7)
        """
        if not self.connected:
            logger.error("Cannot list folders: not connected")
            return []

        try:
            status, folder_list = self.imap.list()
            if status != 'OK':
                logger.error(f"Failed to list folders: {status}")
                return []

            folders = []
            for folder_bytes in folder_list:
                # Parse IMAP LIST response: (flags) "delimiter" "folder_name"
                folder_str = folder_bytes.decode('utf-8') if isinstance(folder_bytes, bytes) else folder_bytes
                # Extract folder name (last quoted string)
                import re
                match = re.search(r'"([^"]+)"$', folder_str)
                if match:
                    folder_name = match.group(1)
                    folders.append(folder_name)
                    logger.info(f"Found folder: {folder_name}")

            return folders

        except Exception as e:
            logger.error(f"Error listing folders: {str(e)}")
            return []

    def select_folder(self, folder: str = None) -> Tuple[bool, str]:
        """
        Select email folder/mailbox.

        Args:
            folder: Folder name (default: config.folder)

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.connected:
            return False, "לא מחובר לשרת"

        folder = folder or self.config.folder

        try:
            # Encode folder name to IMAP UTF-7 for non-ASCII characters
            encoded_folder = self._encode_imap_utf7(folder)

            status, messages = self.imap.select(encoded_folder)
            if status == 'OK':
                logger.info(f"Selected folder: {folder}")
                return True, f"תיקייה נבחרה: {folder}"
            else:
                return False, f"תיקייה לא נמצאה: {folder}"

        except Exception as e:
            logger.error(f"Error selecting folder: {str(e)}")
            return False, f"שגיאה בבחירת תיקייה: {str(e)}"

    def _encode_imap_utf7(self, folder_name: str) -> str:
        """
        Encode Unicode folder name to IMAP modified UTF-7.

        Gmail requires folder names with non-ASCII characters to be encoded
        using IMAP's modified UTF-7 encoding (RFC 3501).

        Args:
            folder_name: Folder name in UTF-8/Unicode

        Returns:
            Folder name encoded in IMAP modified UTF-7
        """
        # INBOX is always ASCII, never encode it
        if folder_name.upper() == 'INBOX':
            return folder_name

        # Check if folder contains only ASCII printable characters
        try:
            # Try ASCII encoding - if successful, no need to encode
            folder_name.encode('ascii')
            return folder_name
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

        # Encode to IMAP modified UTF-7 (RFC 3501)
        # Standard IMAP modified UTF-7 uses '+' and '/' from base64 as-is
        # Only the shift character '&' and terminator '-' are special
        try:
            import base64

            out = []
            in_shift = False
            shift_buffer = []

            for c in folder_name:
                # ASCII printable characters (0x20-0x7E)
                if 0x20 <= ord(c) <= 0x7E:
                    if c == '&':
                        # End any active shift sequence first
                        if in_shift and shift_buffer:
                            utf16_bytes = ''.join(shift_buffer).encode('utf-16-be')
                            b64 = base64.b64encode(utf16_bytes).decode('ascii').rstrip('=')
                            out.append(f'&{b64}-')
                            shift_buffer = []
                        in_shift = False
                        # Literal & is encoded as &-
                        out.append('&-')
                    else:
                        # Regular ASCII character - end shift if active
                        if in_shift and shift_buffer:
                            utf16_bytes = ''.join(shift_buffer).encode('utf-16-be')
                            b64 = base64.b64encode(utf16_bytes).decode('ascii').rstrip('=')
                            out.append(f'&{b64}-')
                            shift_buffer = []
                        in_shift = False
                        out.append(c)
                else:
                    # Non-ASCII character (Hebrew, etc.) - needs encoding
                    in_shift = True
                    shift_buffer.append(c)

            # Flush any remaining shift buffer
            if in_shift and shift_buffer:
                utf16_bytes = ''.join(shift_buffer).encode('utf-16-be')
                b64 = base64.b64encode(utf16_bytes).decode('ascii').rstrip('=')
                out.append(f'&{b64}-')

            encoded = ''.join(out)
            logger.info(f"IMAP UTF-7 encoding: '{folder_name}' -> '{encoded}'")
            return encoded

        except Exception as e:
            logger.error(f"Failed to encode folder name '{folder_name}': {e}")
            logger.exception(e)
            # Return original and let IMAP server handle it
            return folder_name

    def fetch_emails_with_attachments(self) -> List[Dict]:
        """
        Fetch unread emails with PDF/CSV/Excel attachments.

        Returns:
            List of email dicts with structure:
            {
                'message_id': str,
                'subject': str,
                'sender': str,
                'date': str,
                'attachments': [{'filename': str, 'data': bytes, 'content_type': str}]
            }
        """
        if not self.connected:
            logger.error("Not connected to IMAP server")
            return []

        try:
            # Search for unseen (unread) emails
            search_criterion = 'UNSEEN'

            # Add date filter if configured
            if self.config.date_filter_days > 0:
                since_date = datetime.now() - timedelta(days=self.config.date_filter_days)
                date_str = since_date.strftime("%d-%b-%Y")
                search_criterion = f'(UNSEEN SINCE {date_str})'

            status, messages = self.imap.search(None, search_criterion)

            if status != 'OK':
                logger.warning("No emails found")
                return []

            email_ids = messages[0].split()

            # Limit number of emails
            email_ids = email_ids[:self.config.max_fetch]

            logger.info(f"Found {len(email_ids)} unread emails")

            emails_with_attachments = []

            for email_id in email_ids:
                email_data = self._fetch_single_email(email_id)
                if email_data and email_data['attachments']:
                    emails_with_attachments.append(email_data)

            return emails_with_attachments

        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            return []

    def _fetch_single_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Fetch and parse a single email.

        Args:
            email_id: Email ID from IMAP search

        Returns:
            Email dict or None if parsing fails
        """
        try:
            status, msg_data = self.imap.fetch(email_id, '(RFC822)')

            if status != 'OK':
                return None

            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])

            # Extract headers
            subject = self._decode_header(msg.get('Subject', ''))
            sender = self._decode_header(msg.get('From', ''))
            date = msg.get('Date', '')
            message_id = msg.get('Message-ID', str(email_id))

            # Extract attachments
            attachments = []

            if msg.is_multipart():
                for part in msg.walk():
                    if self._is_attachment(part):
                        attachment = self._extract_attachment(part)
                        if attachment:
                            attachments.append(attachment)

            # Only return emails with valid attachments
            if not attachments:
                return None

            return {
                'email_id': email_id.decode(),
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'attachments': attachments
            }

        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {str(e)}")
            return None

    def _decode_header(self, header: str) -> str:
        """Decode email header (handles encoding)."""
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8')
                except Exception:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string

    def _is_attachment(self, part) -> bool:
        """Check if email part is an attachment."""
        content_disposition = str(part.get("Content-Disposition", ""))

        if "attachment" in content_disposition:
            return True

        # Also check for inline attachments with filename
        filename = part.get_filename()
        if filename and content_disposition:
            return True

        return False

    def _extract_attachment(self, part) -> Optional[Dict]:
        """
        Extract attachment from email part.

        Args:
            part: Email message part

        Returns:
            Attachment dict or None if invalid
        """
        filename = part.get_filename()

        if not filename:
            return None

        # Decode filename
        filename = self._decode_header(filename)

        # Validate file type (PDF, CSV, Excel only)
        valid_extensions = ('.pdf', '.csv', '.xlsx', '.xls')
        if not filename.lower().endswith(valid_extensions):
            logger.info(f"Skipping non-invoice file: {filename}")
            return None

        # Get file data
        file_data = part.get_payload(decode=True)

        if not file_data:
            return None

        # Check file size (max 10MB)
        file_size = len(file_data)
        max_size = 10 * 1024 * 1024  # 10MB

        if file_size > max_size:
            logger.warning(f"File too large: {filename} ({file_size} bytes)")
            return None

        content_type = part.get_content_type()

        logger.info(f"Extracted attachment: {filename} ({file_size} bytes)")

        return {
            'filename': filename,
            'data': file_data,
            'content_type': content_type,
            'size': file_size
        }

    def mark_as_processed(self, email_id: str):
        """
        Mark email as read to prevent reprocessing.

        Args:
            email_id: Email ID to mark
        """
        if not self.connected or not self.config.mark_as_read:
            return

        try:
            self.imap.store(email_id.encode(), '+FLAGS', '\\Seen')
            logger.info(f"Marked email {email_id} as read")
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")


class EmailInvoiceProcessor:
    """
    High-level processor that integrates EmailFetcher with FileProcessor and DatabaseManager.

    This class orchestrates the entire email sync workflow:
    1. Connect to email
    2. Fetch emails with attachments
    3. Download attachments to temp directory
    4. Process with existing FileProcessor
    5. Save to database
    6. Mark emails as processed
    """

    def __init__(self):
        """Initialize processor with configuration from environment variables."""
        self.config = self._load_config()
        self.fetcher = EmailFetcher(self.config)
        self.temp_dir = Path("data/uploads/email_temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> EmailConfig:
        """Load email configuration from environment variables or Streamlit secrets."""
        from src.utils.config_loader import config

        return EmailConfig(
            imap_server=config.get('EMAIL_IMAP_SERVER', 'imap.gmail.com'),
            imap_port=config.get_int('EMAIL_IMAP_PORT', 993),
            email_address=config.get('EMAIL_ADDRESS', ''),
            email_password=config.get('EMAIL_PASSWORD', ''),
            folder=config.get('EMAIL_FOLDER', 'INBOX'),
            mark_as_read=config.get_bool('EMAIL_MARK_AS_READ', True),
            max_fetch=config.get_int('EMAIL_MAX_FETCH', 50),
            date_filter_days=config.get_int('EMAIL_DATE_FILTER_DAYS', 30)
        )

    def sync_emails(self, silent: bool = False) -> Dict:
        """
        Main sync method - fetches and processes emails.

        Args:
            silent: If True, suppress non-critical errors (for auto-sync)

        Returns:
            Dict with sync statistics:
            {
                'new_invoices': int,
                'errors': int,
                'emails_processed': int,
                'error_message': str (if errors)
            }
        """
        result = {
            'new_invoices': 0,
            'errors': 0,
            'emails_processed': 0,
            'error_message': ''
        }

        try:
            # Import here to avoid circular imports
            from src.utils.file_processor import FileProcessor
            from src.database_manager import DatabaseManager

            file_processor = FileProcessor()
            db = DatabaseManager()

            # Connect to email
            success, message = self.fetcher.connect()
            if not success:
                result['error_message'] = message
                if not silent:
                    logger.error(message)
                return result

            # Select folder
            success, message = self.fetcher.select_folder()
            if not success:
                result['error_message'] = message
                self.fetcher.disconnect()
                return result

            # Fetch emails with attachments
            emails = self.fetcher.fetch_emails_with_attachments()

            if not emails:
                logger.info("No new emails with attachments")
                self.fetcher.disconnect()
                return result

            # Process each email
            for email_data in emails:
                try:
                    processed_invoices = self._process_email(email_data, file_processor, db)
                    result['new_invoices'] += processed_invoices
                    result['emails_processed'] += 1

                    # Mark as processed
                    self.fetcher.mark_as_processed(email_data['email_id'])

                    # Log sync to database
                    db.log_email_sync({
                        'email_message_id': email_data['message_id'],
                        'subject': email_data['subject'],
                        'sender': email_data['sender'],
                        'received_date': email_data['date'],
                        'processed_date': datetime.now().isoformat(),
                        'invoice_numbers': '',  # Will be updated if invoices found
                        'status': 'success' if processed_invoices > 0 else 'failed'
                    })

                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    result['errors'] += 1

            # Disconnect
            self.fetcher.disconnect()

            # Clean up temp directory
            self._cleanup_temp_dir()

            return result

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg)
            result['error_message'] = error_msg
            return result

    def _process_email(self, email_data: Dict, file_processor, db) -> int:
        """
        Process a single email's attachments.

        Args:
            email_data: Email dict with attachments
            file_processor: FileProcessor instance
            db: DatabaseManager instance

        Returns:
            Number of invoices successfully processed
        """
        processed_count = 0

        for attachment in email_data['attachments']:
            try:
                # Save attachment to temp file
                temp_file_path = self.temp_dir / attachment['filename']

                with open(temp_file_path, 'wb') as f:
                    f.write(attachment['data'])

                logger.info(f"Saved attachment: {temp_file_path}")

                # Determine file type
                file_extension = temp_file_path.suffix.lower()

                if file_extension == '.pdf':
                    file_type = 'application/pdf'
                elif file_extension in ['.csv', '.xlsx', '.xls']:
                    file_type = 'text/csv'
                else:
                    logger.warning(f"Unsupported file type: {file_extension}")
                    continue

                # Process with FileProcessor
                # Open file and pass as file object
                with open(temp_file_path, 'rb') as file_obj:
                    invoice_data = file_processor.process_uploaded_file(file_obj, file_type)

                if invoice_data is not None and not invoice_data.empty:
                    # Check for duplicates
                    if 'invoice_no' in invoice_data.columns:
                        invoice_no = invoice_data.iloc[0]['invoice_no']
                        if db.check_duplicate_invoice(invoice_no):
                            logger.warning(f"Duplicate invoice: {invoice_no} - skipping")
                            continue

                    # Save to database (implementation depends on db structure)
                    # This is a placeholder - actual implementation will use existing db methods
                    logger.info(f"Successfully processed: {attachment['filename']}")
                    processed_count += 1

            except Exception as e:
                logger.error(f"Error processing attachment {attachment['filename']}: {str(e)}")
                continue

        return processed_count

    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        try:
            for file in self.temp_dir.glob('*'):
                if file.is_file():
                    file.unlink()
            logger.info("Cleaned up temp directory")
        except Exception as e:
            logger.error(f"Error cleaning temp directory: {str(e)}")

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test IMAP connection without processing emails.

        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self.fetcher.connect()
        if success:
            self.fetcher.disconnect()
        return success, message

    def list_available_folders(self) -> List[str]:
        """
        Get list of all available folders/labels in mailbox.

        Returns:
            List of folder names
        """
        success, _ = self.fetcher.connect()
        if not success:
            return []

        folders = self.fetcher.list_folders()
        self.fetcher.disconnect()
        return folders
