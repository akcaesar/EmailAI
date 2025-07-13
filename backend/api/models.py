"""
Author: Akshay NS
Reorganized models for email account integration and AI-processed job emails.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAccount(models.Model):
    """Stores Gmail credentials for a user's IMAP/SMTP access."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts')
    email = models.EmailField()
    imap_server = models.CharField(max_length=255, default="imap.gmail.com")
    imap_port = models.IntegerField(default=993)
    smtp_server = models.CharField(max_length=255, default="smtp.gmail.com")
    smtp_port = models.IntegerField(default=587)
    password = models.CharField(max_length=255)  # Store encrypted in production
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'email')

    def __str__(self):
        return f"{self.user.username} <{self.email}>"


class ProcessedEmail(models.Model):
    """Represents a single fetched email, enriched with AI processing."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSED = 'processed', 'Processed'
        ERROR = 'error', 'Error'

    class Category(models.TextChoices):
        INTERVIEW = 'interview', 'Interview'
        REJECTION = 'rejection', 'Rejection'
        OFFER = 'offer', 'Offer'
        FOLLOW_UP = 'follow_up', 'Follow-Up Needed'
        NEWSLETTER = 'newsletter', 'Newsletter'
        SPAM = 'spam', 'Spam'
        OTHER = 'other', 'Other'

    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='emails')
    uid = models.CharField(max_length=255)  # IMAP UID (unique per account)
    subject = models.TextField()
    from_address = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True, null=True)
    to_address = models.EmailField(blank=True, null=True)
    received_at = models.DateTimeField()
    
    raw_body = models.TextField()
    cleaned_body = models.TextField(blank=True, null=True)  # For AI-friendly formatting
    
    summary = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=50, choices=Category.choices, blank=True, null=True
    )
    priority = models.IntegerField(default=0)
    needs_reply = models.BooleanField(default=False)
    suggested_reply = models.TextField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('account', 'uid')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['needs_reply']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.subject} [{self.status}]"


class FollowUpEmail(models.Model):
    """Stores follow-up messages generated and optionally sent for a processed email."""
    original_email = models.ForeignKey(
        ProcessedEmail,
        on_delete=models.CASCADE,
        related_name='followups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('error', 'Error')
        ],
        default='draft'
    )
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Follow-up ({self.status}) for: {self.original_email.subject[:50]}"
