"""
Author: Akshay NS
Contains: Django models for email account management and processed emails

"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailAccount(models.Model):
    """Stores user email account credentials"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    imap_server = models.CharField(max_length=255)
    imap_port = models.IntegerField(default=993)
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.IntegerField(default=587)
    password = models.CharField(max_length=255)  # Encrypted in production
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'email')

class ProcessedEmail(models.Model):
    """Tracks processed emails and their AI-generated content"""
    PENDING = 'pending'
    PROCESSED = 'processed'
    ERROR = 'error'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    ]
    
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE)
    uid = models.CharField(max_length=255)  # IMAP UID
    subject = models.TextField()
    from_address = models.EmailField()
    received_at = models.DateTimeField()
    raw_body = models.TextField()
    summary = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    priority = models.IntegerField(default=0)
    needs_reply = models.BooleanField(default=False)
    suggested_reply = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('account', 'uid')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['needs_reply']),
        ]