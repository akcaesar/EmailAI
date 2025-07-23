"""
Service to fetch emails from real email accounts and save them to database.
"""

import asyncio
from typing import List, Dict, Any
from django.utils import timezone
from ..models import EmailAccount, ProcessedEmail
from ..tools.email_fetcher import EmailFetchTool, EmailFetchConfig, EmailFetchInputs
from .email_processor import process_email_batch
import logging
from asgiref.sync import sync_to_async
from django.db import transaction

logger = logging.getLogger(__name__)


class EmailFetchingService:
    def __init__(self):
        pass

    async def fetch_and_store_emails(self, account_id: int, max_emails: int = 50) -> Dict[str, Any]:
        """Fetch emails from account and store in database."""

        try:
            # Get account using sync_to_async
            account = await sync_to_async(EmailAccount.objects.get)(id=account_id)

            # Configure email fetcher
            config = EmailFetchConfig(
                imap_server=account.imap_server,
                username=account.email,
                password=account.password,
                port=account.imap_port,
                ssl=True
            )

            fetcher = EmailFetchTool(config)

            # Fetch recent emails (last 7 days)
            from datetime import datetime, timedelta
            from_date = (datetime.now() - timedelta(days=7)).strftime('%d-%b-%Y')

            inputs = EmailFetchInputs(
                from_date=from_date,
                max_emails=max_emails,
                mark_as_read=False
            )

            emails = await fetcher.fetch_emails(inputs)
            await fetcher.disconnect()

            # Store emails in database using sync operations
            result = await self._store_emails_sync(account, emails, account_id)

            return result

        except Exception as e:
            logger.error(f"Email account {account_id} not found or error: {e}")
            return {'error': str(e)}

    @sync_to_async
    def _store_emails_sync(self, account, emails, account_id):
        """Store emails synchronously in database."""
        new_emails = []
        processed_count = 0

        with transaction.atomic():
            for email_msg in emails:
                # Check if email already exists
                if ProcessedEmail.objects.filter(
                    account=account,
                    uid=email_msg.uid
                ).exists():
                    continue

                # Create new email record
                processed_email = ProcessedEmail.objects.create(
                    account=account,
                    uid=email_msg.uid,
                    subject=email_msg.subject or 'No Subject',
                    from_address=self._extract_email_address(email_msg.sender),
                    from_name=self._extract_sender_name(email_msg.sender),
                    received_at=email_msg.date or timezone.now(),
                    raw_body=email_msg.text,
                    status=ProcessedEmail.Status.PENDING
                )

                new_emails.append(processed_email.uid)
                processed_count += 1

        # Trigger background processing for new emails
        if new_emails:
            process_email_batch.delay(account_id, new_emails)

        return {
            'account_id': account_id,
            'fetched': len(emails),
            'new_emails': processed_count,
            'duplicate_emails': len(emails) - processed_count,
            'processing_started': len(new_emails) > 0
        }

    def _extract_email_address(self, sender: str) -> str:
        """Extract email address from sender string."""
        import re
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)

        # If no angle brackets, assume the whole string is the email
        match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', sender)
        if match:
            return match.group(1)

        return sender.strip()

    def _extract_sender_name(self, sender: str) -> str:
        """Extract sender name from sender string."""
        import re
        # Check for "Name <email>" format
        match = re.search(r'^(.+?)\s*<.+?>$', sender)
        if match:
            return match.group(1).strip(' "\'')

        # If no name found, return empty string
        return ''


# Sync wrapper for Django views
def fetch_emails_sync(account_id: int, max_emails: int = 50) -> Dict[str, Any]:
    """Synchronous wrapper for email fetching."""
    import asyncio

    async def _fetch():
        service = EmailFetchingService()
        return await service.fetch_and_store_emails(account_id, max_emails)

    # Create new event loop for this thread
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_fetch())
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return {'error': str(e)}
    finally:
        loop.close()
