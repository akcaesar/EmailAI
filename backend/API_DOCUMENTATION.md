# EmailAI API Documentation

**Version**: 1.0  
**Base URL**: `http://localhost:8000/api/`  
**Authentication**: JWT Bearer Token  
**Author**: Akshay NS

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Email Account Management](#email-account-management)
4. [Email Processing](#email-processing)
5. [System Health](#system-health)
6. [Error Handling](#error-handling)
7. [Testing Guide](#testing-guide)

---

## Overview

EmailAI provides a streamlined API for AI-powered email processing. The system automatically fetches, classifies, and generates replies for job application emails using local Ollama AI models.

### Core Features
- User authentication with JWT tokens
- Email account management (Gmail, Outlook, etc.)
- AI-powered email classification and reply generation
- System health monitoring

### Email Categories
The system classifies emails into 4 categories:
1. **confirmation** - Application receipt acknowledgment
2. **rejection** - Application rejection
3. **interview** - Interview invitation or scheduling
4. **query** - Request for additional information

### Priority Levels
- **1-3** - Low (Confirmations)
- **4-6** - Medium (General inquiries)
- **7-8** - High (Rejections, important updates)
- **9-10** - Critical (Interview invitations)

---

## Authentication

All endpoints except authentication require a valid JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### 1. Register User

**Endpoint**: `POST /v1/auth/register/`

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "status": 201
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login

**Endpoint**: `POST /v1/auth/login/`

**Request Body**:
```json
{
  "username": "johndoe",
  "password": "securePassword123"
}
```

**Response**:
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "status": 200
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 3. Logout

**Endpoint**: `POST /v1/auth/logout/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response**:
```json
{
  "message": "Logout successful",
  "status": 200
}
```

---

## Email Account Management

### 1. List Email Accounts

**Endpoint**: `GET /v1/accounts/`

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
[
  {
    "id": 1,
    "email": "john@gmail.com",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

**Test with curl**:
```bash
curl -X GET http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer <your_access_token>"
```

### 2. Create Email Account

**Endpoint**: `POST /v1/accounts/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "email": "john@gmail.com",
  "password": "app_password_here",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

**Response**:
```json
{
  "id": 1,
  "email": "john@gmail.com",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "password": "your_app_password",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
  }'
```

### 3. Fetch Emails from Account

**Endpoint**: `POST /v1/accounts/{account_id}/fetch_emails/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "max_emails": 20
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Fetched 15 emails",
  "data": {
    "fetched_count": 15,
    "new_emails": 12,
    "existing_emails": 3,
    "errors": []
  }
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts/1/fetch_emails/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"max_emails": 10}'
```

**Note**: This endpoint automatically processes fetched emails using either:
- **Background processing** (if Celery is running) - Recommended for production
- **Synchronous processing** (fallback) - If Celery is not available

### 4. Update Email Account

**Endpoint**: `PUT /v1/accounts/{account_id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**: Same as create account

### 5. Delete Email Account

**Endpoint**: `DELETE /v1/accounts/{account_id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
{
  "message": "Account deleted successfully"
}
```

---

## Fetched Emails Management

### 1. List All User Emails

**Endpoint**: `GET /v1/emails/`

**Headers**: `Authorization: Bearer <access_token>`

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `category` (optional): Filter by category (confirmation, rejection, interview, query)
- `status` (optional): Filter by status (pending, processed, error)
- `needs_reply` (optional): Filter by needs_reply (true/false)
- `account_id` (optional): Filter by specific email account

**Response**:
```json
{
  "status": "success",
  "data": {
    "emails": [
      {
        "id": 1,
        "uid": "12345",
        "subject": "Application for Software Engineer Position",
        "from_address": "hr@company.com",
        "from_name": "HR Team",
        "to_address": "john@example.com",
        "received_at": "2024-01-15T10:30:00Z",
        "raw_body": "Dear John, Thank you for your application...",
        "cleaned_body": "Thank you for your application...",
        "summary": "Application acknowledgment with next steps",
        "category": "confirmation",
        "priority": 5,
        "needs_reply": false,
        "suggested_reply": null,
        "status": "processed",
        "processed_at": "2024-01-15T10:32:00Z",
        "account_email": "john@gmail.com"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 45,
      "total_pages": 3
    },
    "filters": {
      "category": null,
      "status": null,
      "needs_reply": null,
      "account_id": null
    }
  }
}
```

**Test with curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/emails/?category=interview&page=1&page_size=10" \
  -H "Authorization: Bearer <your_access_token>"
```

### 2. Get Specific Email Details

**Endpoint**: `GET /v1/emails/{email_id}/`

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "uid": "12345",
    "subject": "Application for Software Engineer Position",
    "from_address": "hr@company.com",
    "from_name": "HR Team",
    "to_address": "john@example.com",
    "received_at": "2024-01-15T10:30:00Z",
    "raw_body": "Dear John, Thank you for your application...",
    "cleaned_body": "Thank you for your application...",
    "summary": "Application acknowledgment with next steps",
    "category": "confirmation",
    "priority": 5,
    "needs_reply": false,
    "suggested_reply": "Thank you for considering my application...",
    "status": "processed",
    "processed_at": "2024-01-15T10:32:00Z",
    "account_email": "john@gmail.com"
  }
}
```

**Test with curl**:
```bash
curl -X GET http://localhost:8000/api/v1/emails/1/ \
  -H "Authorization: Bearer <your_access_token>"
```

### 3. List Emails for Specific Account

**Endpoint**: `GET /v1/accounts/{account_id}/emails/`

**Headers**: `Authorization: Bearer <access_token>`

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `category` (optional): Filter by category
- `status` (optional): Filter by status
- `needs_reply` (optional): Filter by needs_reply (true/false)

**Response**: Same format as "List All User Emails" but filtered to specific account

**Test with curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/accounts/1/emails/?category=interview" \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Email Processing

### 1. Process Email Comprehensively

**Endpoint**: `POST /v1/processing/process_comprehensive/`

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "subject": "Application for Software Engineer Position",
  "body": "Dear John, Thank you for your application. We would like to schedule an interview...",
  "from_address": "hr@company.com",
  "from_name": "HR Team"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Email processed successfully",
  "data": {
    "classification": {
      "category": "interview",
      "confidence": 0.95,
      "priority": 8
    },
    "analysis": {
      "company_name": "TechCorp",
      "position": "Software Engineer",
      "key_points": ["Interview scheduled", "Next steps provided"],
      "sentiment": "positive"
    },
    "suggested_reply": "Thank you for considering my application. I'm excited about the opportunity...",
    "needs_reply": true
  }
}
```

**Test with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/processing/process_comprehensive/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Job Application Update",
    "body": "Dear candidate, We received your application and will review it shortly.",
    "from_address": "hr@company.com",
    "from_name": "HR Department"
  }'
```

### 2. Get Processing Statistics

**Endpoint**: `GET /v1/processing/statistics/`

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_emails": 150,
    "pending_emails": 5,
    "processed_emails": 140,
    "error_emails": 5,
    "category_distribution": {
      "confirmation": 45,
      "rejection": 60,
      "interview": 25,
      "query": 20
    }
  }
}
```

**Test with curl**:
```bash
curl -X GET http://localhost:8000/api/v1/processing/statistics/ \
  -H "Authorization: Bearer <your_access_token>"
```

---

## System Health

### Health Check

**Endpoint**: `GET /v1/system/health/`

**No authentication required**

**Response**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "overall_status": "healthy",
  "services": {
    "ollama": {
      "status": "healthy",
      "test_response": "Hello! How can I help you today?..."
    },
    "database": {
      "status": "healthy",
      "email_count": 150,
      "account_count": 5
    }
  }
}
```

**Test with curl**:
```bash
curl -X GET http://localhost:8000/api/v1/system/health/
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error description",
  "status": 400
}
```

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully  
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Field Validation Errors

```json
{
  "username": ["This field is required."],
  "email": ["Enter a valid email address."]
}
```

---

## Testing Guide

### Prerequisites - Setup Development Environment

1. **Start the Django server**:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ollama pull deepseek-r1:1.5b
   ```

3. **Start Redis** (for background tasks):
   ```bash
   redis-server
   ```

4. **Environment Variables**:
   ```bash
   export OLLAMA_HOST=http://localhost:11434
   export OLLAMA_DEFAULT_MODEL=deepseek-r1:1.5b
   export DEBUG=True
   ```

### Complete Frontend Integration Flow

#### 1. User Registration & Login

```javascript
// Register a new user
const registerUser = async (userData) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/register/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  return response.json();
};

// Login user
const loginUser = async (credentials) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });
  return response.json();
};
```

#### 2. Email Account Management

```javascript
// Add email account
const addEmailAccount = async (accountData, accessToken) => {
  const response = await fetch('http://localhost:8000/api/v1/accounts/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(accountData),
  });
  return response.json();
};

// Fetch emails
const fetchEmails = async (accountId, maxEmails, accessToken) => {
  const response = await fetch(`http://localhost:8000/api/v1/accounts/${accountId}/fetch_emails/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ max_emails: maxEmails }),
  });
  return response.json();
};

// Get all user emails with filtering and pagination
const getAllEmails = async (filters = {}, accessToken) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      queryParams.append(key, value);
    }
  });
  
  const response = await fetch(`http://localhost:8000/api/v1/emails/?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  return response.json();
};

// Get specific email details
const getEmailDetails = async (emailId, accessToken) => {
  const response = await fetch(`http://localhost:8000/api/v1/emails/${emailId}/`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  return response.json();
};

// Get emails for specific account
const getAccountEmails = async (accountId, filters = {}, accessToken) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      queryParams.append(key, value);
    }
  });
  
  const response = await fetch(`http://localhost:8000/api/v1/accounts/${accountId}/emails/?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  return response.json();
};
```

#### 3. Email Processing

```javascript
// Process single email
const processEmail = async (emailData, accessToken) => {
  const response = await fetch('http://localhost:8000/api/v1/processing/process_comprehensive/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(emailData),
  });
  return response.json();
};

// Get statistics
const getStatistics = async (accessToken) => {
  const response = await fetch('http://localhost:8000/api/v1/processing/statistics/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  return response.json();
};
```

#### 4. System Health Check

```javascript
// Check system health (no auth required)
const checkSystemHealth = async () => {
  const response = await fetch('http://localhost:8000/api/v1/system/health/');
  return response.json();
};
```

### Testing Checklist for Frontend Developers

#### Authentication Flow
- [ ] User can register successfully with valid data
- [ ] Registration validates required fields and email format
- [ ] User can login and receive JWT tokens
- [ ] Invalid credentials return appropriate error
- [ ] Protected routes require authentication

#### Email Account Management
- [ ] User can view their email accounts
- [ ] User can add email accounts with proper validation  
- [ ] Email fetching works with real email credentials
- [ ] User can update and delete email accounts
- [ ] Only user's own accounts are accessible

#### Fetched Emails Viewing
- [ ] User can list all their fetched emails with pagination
- [ ] Filtering works correctly (category, status, needs_reply, account_id)
- [ ] User can view detailed information for specific emails
- [ ] User can list emails for a specific account
- [ ] Pagination works correctly for large email lists
- [ ] Only user's own emails are accessible

#### Email Processing
- [ ] Email processing returns classification and analysis
- [ ] Different email types are classified correctly
- [ ] Reply suggestions are generated appropriately
- [ ] Statistics endpoint provides meaningful data
- [ ] Processing handles various email formats

#### System Health
- [ ] System health check works without authentication
- [ ] Health status reflects actual service states
- [ ] Database and Ollama service status are reported

#### Error Handling
- [ ] Error handling works for invalid requests
- [ ] Field validation errors are properly formatted
- [ ] HTTP status codes are appropriate
- [ ] Error messages are helpful for debugging

### Sample Test Data

#### User Registration
```json
{
  "username": "frontend_tester",
  "email": "tester@example.com",
  "password": "SecurePass123!",
  "first_name": "Frontend",
  "last_name": "Tester"
}
```

#### Email Account (Gmail)
```json
{
  "email": "your.test.email@gmail.com",
  "password": "your_app_password",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

#### Sample Email for Processing
```json
{
  "subject": "Thank you for your application - Software Engineer",
  "body": "Dear John,\n\nThank you for applying for the Software Engineer position at TechCorp. We have received your application and our team will review it shortly.\n\nWe will get back to you within 5 business days.\n\nBest regards,\nHR Team",
  "from_address": "hr@techcorp.com",
  "from_name": "TechCorp HR"
}
```

### Gmail App Password Setup

For testing with real Gmail accounts:

1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account settings → Security → App passwords
3. Generate an app password for "Mail"
4. Use this app password instead of your regular Gmail password

### Common Provider Settings

#### Gmail
```json
{
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_ssl": true
}
```

#### Outlook/Hotmail
```json
{
  "imap_server": "outlook.office365.com",
  "imap_port": 993,
  "smtp_server": "smtp-mail.outlook.com", 
  "smtp_port": 587,
  "use_ssl": true
}
```

### Expected API Response Times

- **Authentication**: < 500ms
- **Email Account CRUD**: < 200ms
- **Email Fetching**: 2-10 seconds (depends on email count)
- **Email Processing**: 3-15 seconds (depends on AI model)
- **Statistics**: < 500ms
- **System Health**: < 1 second

This documentation provides everything needed for frontend developers to integrate with the EmailAI API effectively. The streamlined endpoints focus on core functionality while maintaining all essential features for a complete email processing application.