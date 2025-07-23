# EmailAI API Documentation

**Author:** Akshay NS

## Overview
EmailAI is a comprehensive Django-based system for automated job application email processing. It uses Ollama AI models for email classification, reply generation, and follow-up automation.

## API Architecture
The API is built using Django REST Framework with two approaches:
1. **ViewSet-based API** (Recommended) - Modern, organized approach
2. **Function-based views** - Backward compatibility

## ViewSet-based API (Recommended)
Base URL: `http://localhost:8000/api/v1/`

## Authentication
All endpoints (except auth endpoints) require JWT authentication.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

## Base URL
```
http://localhost:8000/api/
```

## Endpoints

## ViewSet Endpoints

### 1. Email Accounts (`/api/v1/accounts/`)

#### List User Accounts
```
GET /api/v1/accounts/
```

#### Add New Account
```
POST /api/v1/accounts/
```
**Body:**
```json
{
  "email": "your-email@gmail.com",
  "password": "app-password",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

#### Fetch Emails from Account
```
POST /api/v1/accounts/{id}/fetch_emails/
```
**Body:**
```json
{
  "max_emails": 20
}
```

### 2. Email Processing (`/api/v1/processing/`)

#### Process Single Email
```
POST /api/v1/processing/process_comprehensive/
```
**Body:**
```json
{
  "subject": "Interview Invitation",
  "body": "Dear Akshay, we would like to invite you for an interview...",
  "sender_name": "HR Manager"
}
```

#### Batch Process Emails
```
POST /api/v1/processing/batch_process/
```
**Body:**
```json
{
  "emails": [
    {
      "subject": "Application Confirmation",
      "body": "Thank you for your application...",
      "sender_name": "Hiring Team"
    }
  ]
}
```

#### Get Processing Statistics
```
GET /api/v1/processing/statistics/
```

### 3. Follow-ups (`/api/v1/follow-ups/`)

#### Get Follow-up Candidates
```
GET /api/v1/follow-ups/candidates/
```

#### Create Follow-up Draft
```
POST /api/v1/follow-ups/create_draft/
```
**Body:**
```json
{
  "email_id": 1
}
```

#### Send Follow-up Email
```
POST /api/v1/follow-ups/{id}/send/
```

#### Process Automated Follow-ups
```
POST /api/v1/follow-ups/process_automated/
```

#### Get Follow-up Statistics
```
GET /api/v1/follow-ups/statistics/
```

### 4. Dashboard (`/api/v1/dashboard/`)

#### Get User Dashboard
```
GET /api/v1/dashboard/
```

### 5. System (`/api/v1/system/`)

#### Health Check
```
GET /api/v1/system/health/
```

## Authentication Endpoints

### Register User
```
POST /auth/register/
```
**Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login
```
POST /auth/login/
```
**Body:**
```json
{
  "username": "johndoe",
  "password": "secure_password"
}
```

#### Get User Profile
```
GET /auth/profile/
```

#### Update Profile
```
PUT /auth/profile/update/
```
**Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "newemail@example.com"
}
```

### 2. Email Account Management

#### Get User Email Accounts
```
GET /user/accounts/
```

#### Add Email Account
```
POST /user/accounts/add/
```
**Body:**
```json
{
  "email": "your-email@gmail.com",
  "password": "app-password",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

#### Fetch Emails
```
POST /accounts/fetch/
```
**Body:**
```json
{
  "account_id": 1,
  "max_emails": 20
}
```

### 3. Email Processing

#### Process Email Comprehensively
```
POST /emails/process-comprehensive/
```
**Body:**
```json
{
  "subject": "Interview Invitation",
  "body": "Dear John, we would like to invite you for an interview...",
  "sender_name": "HR Manager"
}
```

#### Batch Process Emails
```
POST /emails/batch-process/
```
**Body:**
```json
{
  "emails": [
    {
      "subject": "Application Confirmation",
      "body": "Thank you for your application...",
      "sender_name": "Hiring Team"
    },
    {
      "subject": "Interview Invitation",
      "body": "We would like to schedule an interview...",
      "sender_name": "HR Manager"
    }
  ]
}
```

#### Generate Reply
```
POST /emails/generate-reply/
```
**Body:**
```json
{
  "email_id": 1,
  "model": "deepseek-r1:1.5b"
}
```

### 4. Dashboard

#### Get User Dashboard
```
GET /user/dashboard/
```

#### Get Email Statistics
```
GET /emails/stats/
```

### 5. Follow-up Automation

#### Get Follow-up Candidates
```
GET /follow-ups/candidates/
```

#### Create Follow-up Draft
```
POST /follow-ups/create-draft/
```
**Body:**
```json
{
  "email_id": 1
}
```

#### Send Follow-up Email
```
POST /follow-ups/send/
```
**Body:**
```json
{
  "follow_up_id": 1
}
```

#### Process Automated Follow-ups
```
POST /follow-ups/process-automated/
```

#### Get Follow-up Statistics
```
GET /follow-ups/statistics/
```

### 6. System Health

#### Health Check
```
GET /health/
```

## Email Categories

The system classifies emails into 4 categories:

1. **confirmation** - Application receipt acknowledgment
2. **rejection** - Application rejection
3. **interview** - Interview invitation or scheduling
4. **query** - Request for additional information

## Priority Levels

- **1** - Urgent (Interview invitations)
- **2** - High (Information requests)
- **3** - Medium (Rejections)
- **4** - Low (Confirmations)

## Response Format

All API responses follow this format:

```json
{
  "status": "success|error",
  "message": "Human readable message",
  "data": { ... },
  "errors": [ ... ]
}
```

## Error Handling

Common HTTP status codes:
- **200** - Success
- **400** - Bad Request
- **401** - Unauthorized
- **404** - Not Found
- **500** - Internal Server Error

## Environment Setup

### Required Services
1. **Django**: `python manage.py runserver`
2. **Celery**: `celery -A emailai worker --loglevel=info`
3. **Redis**: `redis-server`
4. **Ollama**: `ollama serve`

### Environment Variables
```bash
OLLAMA_HOST=http://172.23.112.1:11434
OLLAMA_DEFAULT_MODEL=deepseek-r1:1.5b
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

## Models Available

- **llava:latest** - Good for general email processing
- **deepseek-r1:1.5b** - Faster, good for classification
- **gemma3:1b** - Lightweight option

## Usage Examples

### 1. Complete Email Processing Workflow

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/auth/register/ \
-H "Content-Type: application/json" \
-d '{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{
  "username": "johndoe",
  "password": "secure_password"
}'

# 3. Add email account
curl -X POST http://localhost:8000/api/user/accounts/add/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{
  "email": "your-email@gmail.com",
  "password": "app-password"
}'

# 4. Fetch emails
curl -X POST http://localhost:8000/api/accounts/fetch/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{
  "account_id": 1,
  "max_emails": 10
}'

# 5. Get dashboard
curl -X GET http://localhost:8000/api/user/dashboard/ \
-H "Authorization: Bearer <token>"
```

### 2. Follow-up Automation

```bash
# Get follow-up candidates
curl -X GET http://localhost:8000/api/follow-ups/candidates/ \
-H "Authorization: Bearer <token>"

# Create follow-up draft
curl -X POST http://localhost:8000/api/follow-ups/create-draft/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{"email_id": 1}'

# Send follow-up
curl -X POST http://localhost:8000/api/follow-ups/send/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{"follow_up_id": 1}'
```

## Features Implemented

✅ **Core Features**
- Email fetching from real accounts (Gmail, Outlook)
- AI-powered email classification (4 categories)
- Intelligent reply generation
- Background processing with Celery
- Multi-user support with JWT authentication

✅ **Advanced Features**
- Comprehensive email processing service
- Follow-up automation system
- User-specific dashboards
- Quality assessment for generated replies
- Batch email processing
- Statistics and analytics

✅ **Quality Improvements**
- Enhanced reply generation (no double greetings)
- Better email classification accuracy
- Improved error handling
- Comprehensive logging

## What to do next

1. **Test the system** with your email accounts
2. **Configure email settings** in your email provider
3. **Set up automated tasks** using Celery Beat
4. **Monitor system health** using `/health/` endpoint
5. **Create frontend** to interact with the API
6. **Add more email providers** if needed
7. **Fine-tune AI models** for better accuracy
8. **Add email templates** for different scenarios
9. **Implement scheduled follow-ups** with Celery Beat
10. **Add email search and filtering** capabilities