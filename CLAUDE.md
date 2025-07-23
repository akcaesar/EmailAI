# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmailAI is an AI-powered job application email processing system built with Django REST Framework backend and Next.js frontend. The system automatically fetches, classifies, and generates replies for job application emails using local Ollama AI models.

## Architecture

### Backend (Django)
- **Framework**: Django 5.0.6 with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Integration**: Local Ollama service for email classification and reply generation
- **Background Tasks**: Celery with Redis for async processing
- **Authentication**: JWT-based authentication

### Frontend (Next.js)
- **Framework**: Next.js 15.4.1 with React 19.1.0
- **Styling**: Tailwind CSS v4
- **Language**: TypeScript
- **State Management**: React Context API

### Key Services
- `EmailProcessingService`: Comprehensive email analysis pipeline
- `EmailClassifier`: AI-powered email classification (confirmation, rejection, interview, query)
- `ReplyGenerator`: Professional reply generation with quality assessment
- `FollowUpAutomationService`: Automated follow-up management
- `OllamaService`: Local AI model integration

## Development Commands

### Backend Setup
```bash
# Create virtual environment
python -m venv emailai-env
source emailai-env/bin/activate  # Linux/Mac
# or
emailai-env\Scripts\activate  # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Development server with turbopack
npm run build  # Production build
npm run start  # Production server
npm run lint  # ESLint
```

### Background Services
```bash
# Start Redis (required for Celery)
redis-server

# Start Celery worker
cd backend
celery -A emailai worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A emailai beat --loglevel=info
```

### AI Models Setup
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models
ollama pull llava:latest
ollama pull deepseek-r1:1.5b
ollama pull gemma3:1b
```

## Testing

### Backend Tests
```bash
cd backend
python manage.py test  # Run all tests
python manage.py test api  # Run specific app tests

# Individual test files
python test_classifier_standalone.py
python test_reply_generator.py
python test_reply_simple.py
```

### Frontend Tests
```bash
cd frontend
npm test  # Run Jest tests (if configured)
```

## Key Models

### EmailAccount
- Stores user email credentials for IMAP/SMTP access
- Supports Gmail, Outlook, and other providers
- Encrypted password storage (production)

### ProcessedEmail
- Represents fetched emails with AI processing results
- Fields: subject, body, classification, priority, suggested_reply
- Categories: confirmation, rejection, interview, query
- Status: pending, processed, error

### FollowUpEmail
- Manages automated follow-up emails
- Status: draft, sent, error
- Linked to original ProcessedEmail

## API Endpoints

### Authentication
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `GET /auth/profile/` - Get user profile

### Email Management (ViewSet-based)
- `GET /api/v1/accounts/` - List user email accounts
- `POST /api/v1/accounts/` - Add new email account
- `POST /api/v1/accounts/{id}/fetch_emails/` - Fetch emails

### Email Processing
- `POST /api/v1/processing/process_comprehensive/` - Process single email
- `POST /api/v1/processing/batch_process/` - Process multiple emails
- `GET /api/v1/processing/statistics/` - Get processing statistics

### Follow-ups
- `GET /api/v1/follow-ups/candidates/` - Get follow-up candidates
- `POST /api/v1/follow-ups/create_draft/` - Create follow-up draft
- `POST /api/v1/follow-ups/{id}/send/` - Send follow-up email

### System
- `GET /api/v1/system/health/` - System health check
- `GET /api/v1/dashboard/` - User dashboard

## Configuration

### Environment Variables
```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=deepseek-r1:1.5b

# Database
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# Redis (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### CORS Configuration
- Frontend (Next.js): `http://localhost:3000`
- Backend API: `http://localhost:8000`

## File Structure

```
├── backend/
│   ├── api/
│   │   ├── models.py              # Database models
│   │   ├── views.py               # Function-based views
│   │   ├── viewsets.py            # ViewSet-based API
│   │   ├── serializers.py         # DRF serializers
│   │   ├── authentication.py      # JWT authentication
│   │   ├── urls.py                # URL routing
│   │   └── services/              # Business logic layer
│   │       ├── email_processing_service.py
│   │       ├── email_classifier.py
│   │       ├── reply_generator.py
│   │       ├── follow_up_automation.py
│   │       └── ollama_service.py
│   ├── emailai/
│   │   ├── settings.py            # Django configuration
│   │   ├── urls.py                # Main URL configuration
│   │   └── celery.py              # Celery configuration
│   ├── tests/                     # Test files
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js app directory
│   │   ├── components/            # React components
│   │   ├── contexts/              # React contexts
│   │   ├── services/              # API services
│   │   └── types/                 # TypeScript types
│   ├── package.json               # Node.js dependencies
│   └── tsconfig.json              # TypeScript configuration
└── README.md                      # Project documentation
```

## Development Workflow

1. **Start all services**: Django server, Celery worker, Redis, Ollama
2. **Test API endpoints**: Use the health check endpoint to verify system status
3. **Email processing**: Test with real email accounts (Gmail app passwords recommended)
4. **Frontend development**: Run Next.js dev server with hot reloading
5. **Database migrations**: Run after model changes
6. **AI model testing**: Use test scripts to verify classification accuracy

## Common Issues

- **Ollama connection**: Ensure Ollama service is running on correct port
- **Email authentication**: Use app passwords for Gmail/Outlook
- **Redis connection**: Verify Redis server is running for Celery
- **CORS issues**: Check CORS_ALLOWED_ORIGINS in Django settings
- **Model performance**: Different Ollama models have varying accuracy/speed tradeoffs

## Security Notes

- JWT tokens for authentication
- Email passwords should be encrypted in production
- CORS properly configured for frontend-backend communication
- No hardcoded secrets in code

## AI Models

- **llava:latest**: General email processing (slower, more accurate)
- **deepseek-r1:1.5b**: Fast classification and reply generation
- **gemma3:1b**: Lightweight option for resource-constrained environments
#