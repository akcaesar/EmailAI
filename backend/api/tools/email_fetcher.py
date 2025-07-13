"""
Author: Akshay NS
Contains: Email fetching tool for IMAP servers with enhanced error handling and configuration options

"""

# backend/api/tools/email_fetcher.py
from typing import Any, Optional, List, Dict
import imaplib
import email
from datetime import datetime
from dataclasses import dataclass
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

@dataclass
class EmailFetchConfig:
    imap_server: str
    username: str
    password: str
    port: int = 993  # Default IMAPS port
    ssl: bool = True
    mailbox: str = "INBOX"

@dataclass
class EmailFetchInputs:
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    max_emails: int = 10  # Added for safety
    mark_as_read: bool = False  # Added as config option

@dataclass
class EmailMessage:
    subject: str
    date: datetime
    sender: str
    text: str
    uid: str  # Added for tracking
    headers: Dict[str, str]  # Added for full headers

class EmailFetchTool:
    def __init__(self, config: EmailFetchConfig):
        self.config = config
        self.imap = None

    async def connect(self):
        """Establish IMAP connection"""
        try:
            if self.config.ssl:
                self.imap = imaplib.IMAP4_SSL(
                    self.config.imap_server, 
                    self.config.port
                )
            else:
                self.imap = imaplib.IMAP4(
                    self.config.imap_server, 
                    self.config.port
                )
            self.imap.login(self.config.username, self.config.password)
            self.imap.select(self.config.mailbox)
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {str(e)}")
            raise

    async def disconnect(self):
        """Close IMAP connection"""
        try:
            if self.imap:
                self.imap.close()
                self.imap.logout()
        except Exception as e:
            logger.warning(f"Error disconnecting IMAP: {str(e)}")

    def validate_date_format(self, date_str: str):
        """Validate date format (DD-Mon-YYYY)"""
        try:
            datetime.strptime(date_str, '%d-%b-%Y')
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_str}. "
                "Expected format is DD-Mon-YYYY. Example: 10-Jan-2025"
            )

    def build_search_criteria(self, inputs: EmailFetchInputs) -> str:
        """Construct IMAP search query"""
        criteria = []
        if inputs.from_date:
            self.validate_date_format(inputs.from_date)
            criteria.append(f'SINCE "{inputs.from_date}"')
        if inputs.to_date:
            self.validate_date_format(inputs.to_date)
            criteria.append(f'BEFORE "{inputs.to_date}"')
        return ' '.join(criteria) if criteria else 'ALL'

    async def fetch_emails(self, inputs: EmailFetchInputs) -> List[EmailMessage]:
        """Main method to fetch emails"""
        if not self.imap:
            await self.connect()

        try:
            # Build and execute search
            criteria = self.build_search_criteria(inputs)
            status, data = self.imap.search(None, criteria)
            if status != 'OK':
                raise Exception(f"IMAP search failed: {data}")

            mail_ids = data[0].split()[:inputs.max_emails]
            emails = []

            for mail_id in mail_ids:
                email_data = await self._fetch_single_email(mail_id)
                if email_data:
                    emails.append(email_data)
                    if inputs.mark_as_read:
                        self.imap.store(mail_id, '+FLAGS', '\\Seen')

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise

    async def _fetch_single_email(self, mail_id: str) -> Optional[EmailMessage]:
        """Fetch and parse a single email"""
        try:
            status, data = self.imap.fetch(mail_id, '(RFC822 UID)')
            if status != 'OK':
                return None

            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract UID from response
            uid = data[0][0].split()[2].decode('utf-8')  # Adjust based on your IMAP server response

            return EmailMessage(
                subject=email_message.get('Subject', ''),
                sender=email_message.get('From', ''),
                date=self._parse_email_date(email_message),
                text=self._extract_email_body(email_message),
                uid=uid,
                headers=dict(email_message.items())
            )
        except Exception as e:
            logger.warning(f"Error processing email {mail_id}: {str(e)}")
            return None

    def _parse_email_date(self, email_message) -> Optional[datetime]:
        """Parse email date with fallback"""
        date_str = email_message.get('Date')
        if not date_str:
            return None
            
        try:
            # Try common email date formats
            for fmt in (
                '%a, %d %b %Y %H:%M:%S %z',
                '%d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S'
            ):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode(errors='replace')
                    except Exception as e:
                        logger.debug(f"Error decoding part: {str(e)}")
        else:
            try:
                body = email_message.get_payload(decode=True).decode(errors='replace')
            except Exception as e:
                logger.debug(f"Error decoding payload: {str(e)}")
        
        return body