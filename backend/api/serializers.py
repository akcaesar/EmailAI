"""
Django REST Framework Serializers for EmailAI models.
Provides clean data serialization and validation.

Author: Akshay NS
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import EmailAccount, ProcessedEmail, FollowUpEmail


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

# serializers.py
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class DeleteUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
class DeleteAllUsersSerializer(serializers.Serializer):
    confirm = serializers.CharField()
    
    def validate_confirm(self, value):
        if value != "DELETE_ALL_USERS":
            raise serializers.ValidationError("Must confirm with exact phrase: DELETE_ALL_USERS")
        return value

class EmailAccountSerializer(serializers.ModelSerializer):
    """Serializer for EmailAccount model."""
    
    statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAccount
        fields = ['id', 'email', 'imap_server', 'imap_port', 'smtp_server', 'smtp_port', 
                 'created_at', 'statistics']
        read_only_fields = ['id', 'created_at', 'statistics']
    
    def get_statistics(self, obj):
        """Get email statistics for the account."""
        return {
            'total_emails': obj.emails.count(),
            'pending_emails': obj.emails.filter(status='pending').count(),
            'processed_emails': obj.emails.filter(status='processed').count(),
            'error_emails': obj.emails.filter(status='error').count(),
        }


class EmailAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating EmailAccount."""
    
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = EmailAccount
        fields = ['email', 'password', 'imap_server', 'imap_port', 'smtp_server', 'smtp_port']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProcessedEmailSerializer(serializers.ModelSerializer):
    """Serializer for ProcessedEmail model."""
    
    account_email = serializers.CharField(source='account.email', read_only=True)
    
    class Meta:
        model = ProcessedEmail
        fields = ['id', 'uid', 'subject', 'from_address', 'from_name', 'to_address', 
                 'received_at', 'raw_body', 'cleaned_body', 'summary', 'category', 
                 'priority', 'needs_reply', 'suggested_reply', 'status', 'processed_at',
                 'reprocessed_at', 'reprocessing_count', 'account_email']
        read_only_fields = ['id', 'processed_at', 'reprocessed_at', 'reprocessing_count', 'account_email']


class FollowUpEmailSerializer(serializers.ModelSerializer):
    """Serializer for FollowUpEmail model."""
    
    original_email_subject = serializers.CharField(source='original_email.subject', read_only=True)
    original_email_from = serializers.CharField(source='original_email.from_address', read_only=True)
    
    class Meta:
        model = FollowUpEmail
        fields = ['id', 'content', 'status', 'created_at', 'sent_at', 'error_message',
                 'original_email_subject', 'original_email_from']
        read_only_fields = ['id', 'created_at', 'sent_at', 'original_email_subject', 'original_email_from']


class EmailProcessingSerializer(serializers.Serializer):
    """Serializer for email processing requests."""
    
    subject = serializers.CharField(max_length=500)
    body = serializers.CharField()
    sender_name = serializers.CharField(max_length=255, required=False, default='')
    
    def validate_body(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Email body too short")
        return value


class BatchEmailProcessingSerializer(serializers.Serializer):
    """Serializer for batch email processing."""
    
    emails = EmailProcessingSerializer(many=True)
    
    def validate_emails(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 emails allowed per batch")
        return value


class FetchEmailsSerializer(serializers.Serializer):
    """Serializer for fetching emails request."""
    
    max_emails = serializers.IntegerField(min_value=1, max_value=100, default=20)


class FollowUpDraftSerializer(serializers.Serializer):
    """Serializer for creating follow-up drafts."""
    
    email_id = serializers.IntegerField()
    
    def validate_email_id(self, value):
        user = self.context['request'].user
        if not ProcessedEmail.objects.filter(id=value, account__user=user).exists():
            raise serializers.ValidationError("Email not found or access denied")
        return value


class ReplyGenerationSerializer(serializers.Serializer):
    """Serializer for reply generation requests."""
    
    email_id = serializers.IntegerField()
    model = serializers.CharField(max_length=50, required=False, default='deepseek-r1:1.5b')
    
    def validate_email_id(self, value):
        user = self.context['request'].user
        if not ProcessedEmail.objects.filter(id=value, account__user=user).exists():
            raise serializers.ValidationError("Email not found or access denied")
        return value


class EmailReprocessingSerializer(serializers.Serializer):
    """Serializer for email reprocessing requests."""
    
    model = serializers.CharField(max_length=50, required=False, default='deepseek-r1:1.5b')
    force = serializers.BooleanField(default=False)
    
    def validate_model(self, value):
        """Validate that the model name is reasonable."""
        if not value or len(value) > 50:
            raise serializers.ValidationError("Invalid model name")
        return value


class BatchReprocessingSerializer(serializers.Serializer):
    """Serializer for batch email reprocessing."""
    
    email_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    model = serializers.CharField(max_length=50, required=False, default='deepseek-r1:1.5b')
    
    def validate_email_ids(self, value):
        """Validate that all email IDs belong to the authenticated user."""
        user = self.context['request'].user
        user_email_ids = set(
            ProcessedEmail.objects.filter(account__user=user).values_list('id', flat=True)
        )
        
        invalid_ids = set(value) - user_email_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid email IDs or access denied: {list(invalid_ids)}"
            )
        return value


class SummaryRewriteSerializer(serializers.Serializer):
    """Serializer for summary rewriting requests."""
    
    model = serializers.CharField(max_length=50, required=False, default='deepseek-r1:1.5b')


class SuperuserCreationSerializer(serializers.ModelSerializer):
    """Serializer for creating superusers."""
    
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value


class AdminUserListSerializer(serializers.Serializer):
    """Serializer for admin user list response."""
    
    users = serializers.ListSerializer(child=serializers.DictField())
    statistics = serializers.DictField()