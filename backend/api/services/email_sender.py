"""
  Email sending service using SMTP for outgoing emails.
  """

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import EmailAccount, ProcessedEmail, FollowUpEmail

logger = logging.getLogger(__name__)

class EmailSender:
      def __init__(self, account: EmailAccount):
          self.account = account
          self.smtp_connection = None

      def connect(self) -> bool:
          """Establish SMTP connection."""
          try:
              self.smtp_connection = smtplib.SMTP(self.account.smtp_server, self.account.smtp_port)
              self.smtp_connection.starttls()
              self.smtp_connection.login(self.account.email, self.account.password)
              logger.info(f"SMTP connection established for {self.account.email}")
              return True
          except Exception as e:
              logger.error(f"SMTP connection failed: {e}")
              return False

      def disconnect(self):
          """Close SMTP connection."""
          try:
              if self.smtp_connection:
                  self.smtp_connection.quit()
          except Exception as e:
              logger.warning(f"Error disconnecting SMTP: {e}")

      def send_reply(self, original_email: ProcessedEmail, reply_content: str,
                     subject_override: Optional[str] = None) -> Dict[str, Any]:
          """Send a reply to an original email."""

          try:
              if not self.connect():
                  return {'success': False, 'error': 'SMTP connection failed'}

              # Create email message
              msg = MIMEMultipart()
              msg['From'] = self.account.email
              msg['To'] = original_email.from_address

              # Generate reply subject
              if subject_override:
                  msg['Subject'] = subject_override
              else:
                  original_subject = original_email.subject
                  if not original_subject.lower().startswith('re:'):
                      msg['Subject'] = f"Re: {original_subject}"
                  else:
                      msg['Subject'] = original_subject

              # Add reply content
              msg.attach(MIMEText(reply_content, 'plain'))

              # Send email
              text = msg.as_string()
              self.smtp_connection.sendmail(self.account.email, original_email.from_address, text)

              self.disconnect()

              # Create follow-up record
              follow_up = FollowUpEmail.objects.create(
                  original_email=original_email,
                  content=reply_content,
                  status='sent',
                  sent_at=timezone.now()
              )

              logger.info(f"Reply sent successfully to {original_email.from_address}")

              return {
                  'success': True,
                  'message': 'Reply sent successfully',
                  'follow_up_id': follow_up.id,
                  'sent_to': original_email.from_address,
                  'subject': msg['Subject']
              }

          except Exception as e:
              logger.error(f"Error sending reply: {e}")

              # Create failed follow-up record
              FollowUpEmail.objects.create(
                  original_email=original_email,
                  content=reply_content,
                  status='error',
                  error_message=str(e)
              )

              return {'success': False, 'error': str(e)}

      def send_custom_email(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
          """Send a custom email."""

          try:
              if not self.connect():
                  return {'success': False, 'error': 'SMTP connection failed'}

              msg = MIMEMultipart()
              msg['From'] = self.account.email
              msg['To'] = to_email
              msg['Subject'] = subject

              msg.attach(MIMEText(content, 'plain'))

              text = msg.as_string()
              self.smtp_connection.sendmail(self.account.email, to_email, text)

              self.disconnect()

              logger.info(f"Custom email sent to {to_email}")

              return {
                  'success': True,
                  'message': 'Email sent successfully',
                  'sent_to': to_email,
                  'subject': subject
              }

          except Exception as e:
              logger.error(f"Error sending custom email: {e}")
              return {'success': False, 'error': str(e)}