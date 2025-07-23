# EmailAI - AI-Powered Job Application Email Processing System

**Author:** Akshay NS

## Project Overview

EmailAI is a comprehensive Django-based system that automates job application email processing using AI. The system can fetch emails from real email accounts, classify them intelligently, generate professional replies, and manage follow-up communications automatically.

## Key Features

### 🔐 **Authentication & Multi-User Support**
- JWT-based authentication system
- User registration and login
- Multi-user support with data isolation
- Profile management

### 📧 **Email Processing**
- Real-time email fetching from Gmail, Outlook, and other providers
- AI-powered email classification (4 categories: confirmation, rejection, interview, query)
- Intelligent reply generation with quality assessment
- Batch processing capabilities
- Background processing with Celery

### 🤖 **AI Integration**
- Local Ollama AI integration (no external API keys needed)
- Multiple model support (llava:latest, deepseek-r1:1.5b, gemma3:1b)
- Enhanced prompts for better classification accuracy
- Quality assessment for AI-generated responses

### 📊 **Dashboard & Analytics**
- User-specific dashboards
- Email processing statistics
- Category and priority distribution
- Recent email summaries

### 🔄 **Follow-up Automation**
- Intelligent follow-up scheduling based on email types
- Automated draft creation
- Follow-up statistics and management
- Time-based follow-up recommendations

### 🛠 **API Architecture**
- RESTful API with Django REST Framework
- ViewSet-based architecture for clean, maintainable code
- Comprehensive error handling
- API documentation with examples

## Technical Architecture

### **Backend Stack**
- **Django 5.0.6** - Web framework
- **Django REST Framework** - API development
- **PostgreSQL/SQLite** - Database
- **Celery + Redis** - Background task processing
- **Ollama** - Local AI processing
- **JWT** - Authentication

### **AI Models**
- **llava:latest** - General email processing
- **deepseek-r1:1.5b** - Fast classification
- **gemma3:1b** - Lightweight processing

### **Key Services**
- `EmailProcessingService` - Comprehensive email analysis
- `EmailClassifier` - AI-powered classification
- `ReplyGenerator` - Professional reply generation
- `FollowUpAutomationService` - Automated follow-up management
- `OllamaService` - AI model integration

## Project Structure

```
backend/
├── api/
│   ├── models.py              # Database models
│   ├── views.py               # Function-based views
│   ├── viewsets.py            # ViewSet-based API (new)
│   ├── urls.py                # URL routing
│   ├── urls_viewsets.py       # ViewSet routing (new)
│   ├── authentication.py     # JWT authentication
│   └── services/
│       ├── email_processing_service.py
│       ├── email_classifier.py
│       ├── reply_generator.py
│       ├── follow_up_automation.py
│       ├── ollama_service.py
│       ├── email_fetching_service.py
│       └── email_sender.py
├── emailai/
│   ├── settings.py           # Django configuration
│   ├── urls.py               # Main URL configuration
│   └── celery.py             # Celery configuration
├── requirements.txt          # Python dependencies
└── API_DOCUMENTATION.md      # Complete API docs
```

## API Endpoints (ViewSet-based)

### **Authentication**
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `GET /auth/profile/` - Get user profile
- `PUT /auth/profile/update/` - Update profile

### **Email Accounts**
- `GET /api/v1/accounts/` - List user accounts
- `POST /api/v1/accounts/` - Add new account
- `POST /api/v1/accounts/{id}/fetch_emails/` - Fetch emails

### **Email Processing**
- `POST /api/v1/processing/process_comprehensive/` - Process single email
- `POST /api/v1/processing/batch_process/` - Process multiple emails
- `GET /api/v1/processing/statistics/` - Get processing stats

### **Follow-ups**
- `GET /api/v1/follow-ups/candidates/` - Get follow-up candidates
- `POST /api/v1/follow-ups/create_draft/` - Create follow-up draft
- `POST /api/v1/follow-ups/{id}/send/` - Send follow-up
- `GET /api/v1/follow-ups/statistics/` - Get follow-up stats

### **Dashboard**
- `GET /api/v1/dashboard/` - Get user dashboard

### **System**
- `GET /api/v1/system/health/` - System health check

## Database Models

### **EmailAccount**
- User association
- IMAP/SMTP configuration
- Account statistics

### **ProcessedEmail**
- Email content and metadata
- AI classification results
- Processing status
- Reply suggestions

### **FollowUpEmail**
- Follow-up email drafts
- Sending status
- Error tracking

## Quality Improvements Made

### **Reply Generation**
- ✅ Fixed double greetings
- ✅ Eliminated incomplete sentences
- ✅ Improved AI response cleaning
- ✅ Enhanced quality assessment

### **Email Classification**
- ✅ Better prompt engineering
- ✅ Improved fallback classification
- ✅ Enhanced multilingual support
- ✅ Score-based keyword matching

### **Code Architecture**
- ✅ ViewSet-based API design
- ✅ Service layer separation
- ✅ Comprehensive error handling
- ✅ Professional logging

## Setup Instructions

### **1. System Requirements**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install and start Redis
sudo apt-get install redis-server
redis-server

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llava:latest
ollama pull deepseek-r1:1.5b
```

### **2. Configuration**
```bash
# Environment variables (.env)
OLLAMA_HOST=http://172.23.112.1:11434
OLLAMA_DEFAULT_MODEL=deepseek-r1:1.5b
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

### **3. Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### **4. Start Services**
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A emailai worker --loglevel=info

# Terminal 3: Celery Beat (for scheduled tasks)
celery -A emailai beat --loglevel=info
```

## Usage Examples

### **1. User Registration & Login**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
-H "Content-Type: application/json" \
-d '{"username": "akshay", "email": "akshay@example.com", "password": "secure123", "first_name": "Akshay", "last_name": "NS"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{"username": "akshay", "password": "secure123"}'
```

### **2. Email Processing**
```bash
# Add email account
curl -X POST http://localhost:8000/api/v1/accounts/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{"email": "your@gmail.com", "password": "app-password"}'

# Process email
curl -X POST http://localhost:8000/api/v1/processing/process_comprehensive/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{"subject": "Interview Invitation", "body": "Dear Akshay, we would like to invite you for an interview..."}'
```

### **3. Follow-up Management**
```bash
# Get follow-up candidates
curl -X GET http://localhost:8000/api/v1/follow-ups/candidates/ \
-H "Authorization: Bearer <token>"

# Create follow-up draft
curl -X POST http://localhost:8000/api/v1/follow-ups/create_draft/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <token>" \
-d '{"email_id": 1}'
```

## What's Next

### **Immediate Steps**
1. **Test the system** with your email accounts
2. **Configure email providers** (Gmail app passwords)
3. **Set up automated tasks** with Celery Beat
4. **Monitor system health** using health endpoints

### **Future Enhancements**
1. **Frontend Development** - React/Vue.js web interface
2. **Email Templates** - Customizable reply templates
3. **Advanced Analytics** - Detailed reporting and insights
4. **Mobile App** - iOS/Android applications
5. **Integration APIs** - Connect with job boards and CRM systems

## Technical Achievements

- **Clean Architecture** - Separation of concerns with service layers
- **Scalable Design** - Multi-user support with proper data isolation
- **Professional APIs** - RESTful design with comprehensive documentation
- **AI Integration** - Local AI processing without external dependencies
- **Quality Assurance** - Comprehensive testing and error handling
- **Security** - JWT authentication with proper authorization

## Author

**Akshay NS** - Full-stack developer specializing in AI-powered applications and Django backend development.

This project demonstrates advanced Django development, AI integration, and professional software architecture principles.