# CareerCompass Kenya - AI-Powered Career Guidance Platform

## 📋 Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Architecture](#project-architecture)
3. [Core Features](#core-features)
4. [Technical Implementation](#technical-implementation)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [Installation & Deployment](#installation--deployment)
8. [Development Guidelines](#development-guidelines)
9. [Testing Strategy](#testing-strategy)
10. [Security Measures](#security-measures)
11. [Performance Optimization](#performance-optimization)
12. [Future Roadmap](#future-roadmap)
13. [Contributing](#contributing)
14. [License & Support](#license--support)

## 🎯 Executive Summary

CareerCompass Kenya is a sophisticated, production-ready AI-powered career guidance platform specifically designed for the Kenyan education ecosystem. The system combines personality psychology, machine learning algorithms, and localized market intelligence to deliver personalized career pathway recommendations with 94% accuracy. **⚠ Unverified claim — see note below.**

### Key Differentiators
- **Kenyan Context Integration**: Localized salary data, university requirements, and market trends
- **Scientific Personality Assessment**: 60-question MBTI-based assessment with balanced scoring
- **Dynamic Recommendation Engine**: Multi-factor weighted algorithm with real-time adjustments
- **AI Career Coaching**: Context-aware guidance with Kenyan educational system understanding

## 🏗️ Project Architecture
careeratlas-kenya/
├── backend/ # Django project configuration
│ ├── settings.py # Project settings and configurations
│ ├── urls.py # Main URL routing
│ ├── wsgi.py # WSGI application entry point
│ └── asgi.py # ASGI application entry point
├── users/ # User management application
│ ├── models.py # CustomUser, StudentProfile, School models
│ ├── views.py # Authentication and profile management
│ ├── serializers.py # API serializers for data transformation
│ ├── forms.py # Django forms for HTML interfaces
│ ├── urls.py # User-specific URL patterns
│ ├── admin.py # Admin interface configuration
│ ├── apps.py # App configuration
│ └── signals.py # Signal handlers for user operations
├── assessments/ # Personality assessment engine
│ ├── models.py # Question, AnswerChoice, AssessmentResult models
│ ├── views.py # Assessment flow and result processing
│ ├── serializers.py # API endpoints for assessment data
│ ├── urls.py # Assessment-specific URL patterns
│ ├── services.py # Scoring algorithms and personality type determination
│ ├── admin.py # Admin interface for assessment management
│ └── apps.py # App configuration
├── recommendations/ # Career recommendation system
│ ├── models.py # Career, Subject, StudentRecommendation models
│ ├── views.py # Recommendation generation and display
│ ├── serializers.py # API serializers for career data
│ ├── urls.py # Career recommendation URL patterns
│ ├── services.py # Compatibility scoring algorithms
│ ├── admin.py # Admin interface for career management
│ └── apps.py # App configuration
├── ai_coach/ # AI-powered career coaching
│ ├── models.py # Conversation, Message, CoachingPlan models
│ ├── views.py # Chat interface and coaching management
│ ├── serializers.py # API serializers for coaching data
│ ├── urls.py # Coaching-specific URL patterns
│ ├── services.py # AI response generation and coaching logic
│ ├── admin.py # Admin interface for coaching management
│ └── apps.py # App configuration
├── coaching/ # Premium subscription features
│ ├── models.py # Subscription, HumanCoachingSession models
│ ├── views.py # Premium feature management
│ ├── serializers.py # API serializers for premium features
│ ├── urls.py # Premium feature URL patterns
│ ├── services.py # Subscription management and premium logic
│ ├── admin.py # Admin interface for premium features
│ └── apps.py # App configuration
├── templates/ # HTML templates organized by app
│ ├── base.html # Base template with navigation and footer
│ ├── registration/ # Authentication templates
│ │ ├── login.html
│ │ ├── register.html
│ │ ├── password_reset.html
│ │ ├── password_reset_done.html
│ │ ├── password_reset_confirm.html
│ │ └── password_reset_complete.html
│ ├── dashboard/ # Dashboard templates
│ │ ├── home.html
│ │ └── profile.html
│ ├── assessments/ # Assessment templates
│ │ ├── start.html
│ │ ├── question.html
│ │ └── results.html
│ ├── recommendations/ # Career recommendation templates
│ │ ├── career_recommendations.html
│ │ ├── career_list.html
│ │ ├── career_detail.html
│ │ └── subject_list.html
│ └── ai_coach/ # AI coaching templates
│ ├── chat.html
│ ├── conversations.html
│ ├── coaching_plan.html
│ └── resources.html
├── static/ # Static assets
│ ├── css/
│ │ └── custom.css
│ ├── js/
│ │ ├── common.js
│ │ └── assessments.js
│ └── images/ # Branding and UI images
├── media/ # User-uploaded content
├── manage.py # Django management script
└── requirements.txt # Python dependencies
text


### Technology Stack
- **Backend Framework**: Django 5.2.8 with Django REST Framework
- **Database**: PostgreSQL with psycopg2 adapter
- **Frontend**: Tailwind CSS 3.4, HTML5, JavaScript
- **Authentication**: JWT with Django's session-based auth for web
- **Caching**: Redis (optional, LocMemCache for development)
- **Deployment**: Docker, Gunicorn, Nginx
- **AI/ML**: Scikit-learn, NLTK, Custom neural networks

## 🔧 Core Features

### 1. User Management System
- **Multi-role authentication** (Student, Admin, School)
- **Student profiles** with academic tracking
- **School database** with KNEC code integration
- **Secure password management** with reset functionality

### 2. Personality Assessment Engine
- **60 scientifically-balanced questions** (15 per dimension) across 4 MBTI dimensions
- **Real-time progress tracking** with visual indicators
- **Weighted scoring algorithm** for accurate type determination
- **Confidence level calculation** for result reliability

### 3. Dynamic Career Recommendation System
- **Multi-factor compatibility scoring** (personality-first; see `services.py` for the authoritative formula):
  - Personality Match (55%) — primary driver
  - Academic Fit (30%)
  - Learning Style (10%)
  - Interests Match (5%)
  - Grade Level Adjustment (additive)
  - *Market demand and salary are shown on every career but are intentionally excluded from this score, so results aren't biased toward whichever careers are currently in demand.*
- **Kenyan market intelligence** integration
- **Personalized learning path** generation

### 4. AI Career Coaching
- **Context-aware chat interface** with Kenyan education understanding
- **Conversation persistence** and history management
- **Coaching plan generation** with milestone tracking
- **Resource recommendation** based on career goals

### 5. Premium Subscription Features
- **Tiered subscription model** (Basic, Premium, Enterprise)
- **Human coach integration** with booking system
- **Advanced analytics dashboard**
- **Priority support** and enhanced features

## 🗄️ Database Schema

### Core Models Overview

#### User Management (`users/models.py`)
```python
# CustomUser extends AbstractUser with additional fields
# StudentProfile: One-to-one relationship with CustomUser
# School: Educational institution database with KNEC codes

Assessment System (assessments/models.py)
python

# Question: 64 MBTI questions with dimension categorization
# AnswerChoice: Weighted responses for each question
# AssessmentSession: Tracks user assessment progress
# AssessmentResult: Stores personality type determination
# PersonalityType: 16 MBTI types with descriptions

Recommendation Engine (recommendations/models.py)
python

# Career: 20+ Kenyan careers with market data
# Subject: KCSE subjects with difficulty classification
# StudentRecommendation: Personalized career matches
# CareerSubject: Many-to-many relationship with importance levels
# CareerPersonalityMatch: Personality-career compatibility mapping

AI Coaching (ai_coach/models.py)
python

# Conversation: Chat session management
# Message: Individual chat messages with role distinction
# CoachingPlan: Personalized guidance plans
# ResourceRecommendation: Learning material suggestions

🌐 API Documentation
Authentication Endpoints
text

POST   /api/register/          # User registration
POST   /api/login/             # User authentication
POST   /api/logout/            # Session termination
GET    /api/check-username/    # Username availability check
GET    /api/check-email/       # Email availability check

User Management
text

GET    /api/users/             # Retrieve user profile
PUT    /api/users/             # Update user information
GET    /api/student-profiles/  # Get student profile
PUT    /api/student-profiles/  # Update student profile
GET    /api/schools/           # List schools with search

Assessment System
text

GET    /assessments/start/     # Begin personality assessment
GET    /assessments/question/  # Retrieve assessment questions
POST   /assessments/answer/    # Submit question response
GET    /assessments/results/   # View assessment results

Career Recommendations
text

GET    /recommendations/my-recommendations/  # Personal career matches
GET    /recommendations/career-list/         # Browse all careers
GET    /recommendations/career/<id>/         # Career details
GET    /recommendations/subjects/            # Subject recommendations

AI Coaching
text

GET    /ai-coach/chat/         # AI chat interface
GET    /ai-coach/conversations/# Conversation history
POST   /ai-coach/message/      # Send message to AI coach
GET    /ai-coach/coaching-plan/# Personalized coaching plan

🚀 Installation & Deployment
Prerequisites

    Python 3.10+

    PostgreSQL 14+

    Redis 7+ (optional for caching)

    Node.js 18+ (for frontend build tools)

Local Development Setup

    Clone the repository

bash

git clone https://github.com/yourusername/careeratlas-kenya.git
cd careeratlas-kenya/backend

    Create virtual environment

bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

    Install dependencies

bash

pip install -r requirements.txt

    Configure environment variables

bash

cp .env.example .env
# Edit .env with your database credentials and secret key

    Database setup

bash

# Create PostgreSQL database
sudo -u postgres createdb careeratlas
sudo -u postgres createuser careeratlas_user

# Run migrations
python manage.py migrate

# Load initial data
python manage.py loaddata initial_data.json

    Run development server

bash

python manage.py runserver

Production Deployment
Docker Deployment
dockerfile

# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]

Docker Compose Configuration
yaml

# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: careeratlas
      POSTGRES_USER: careeratlas_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 backend.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    environment:
      DATABASE_URL: postgres://careeratlas_user:${DB_PASSWORD}@db/careeratlas
    depends_on:
      - db
    ports:
      - "8000:8000"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:

🔍 Development Guidelines
Code Structure Standards

    Models: Define in models.py with comprehensive docstrings

    Views: Use class-based views for consistency

    Serializers: Separate for list/detail views when needed

    Templates: Use template inheritance with base.html

    Static files: Organized by app and feature

Git Workflow
bash

# Feature branches
git checkout -b feature/feature-name
git add .
git commit -m "feat: description of feature"
git push origin feature/feature-name

# Commit message conventions
# feat:     New feature
# fix:      Bug fix
# docs:     Documentation changes
# style:    Code style changes
# refactor: Code refactoring
# test:     Test additions/modifications
# chore:    Maintenance tasks

Testing Strategy
python

# Example test structure
class AssessmentTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_assessment_start(self):
        response = self.client.get(reverse('assessments:assessments-start'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Personality Assessment')
    
    def test_assessment_flow(self):
        # Test complete assessment flow
        pass

🔒 Security Measures
Authentication & Authorization

    JWT tokens with refresh capability for API access

    Session-based authentication for web interface

    Role-based access control (RBAC) for all endpoints

    Password validation with minimum strength requirements

Data Protection

    Database encryption for sensitive fields

    HTTPS enforcement in production

    CSRF protection for all POST requests

    XSS prevention through template auto-escaping

Security Headers
python

# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

⚡ Performance Optimization
Database Optimization

    Selective prefetching with select_related and prefetch_related

    Database indexing on frequently queried fields

    Query optimization using Django's query analyzer

    Connection pooling with PgBouncer in production

Caching Strategy
python

# Multi-level caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Template fragment caching
{% cache 300 "career_recommendations" user.id %}
    <!-- Expensive recommendation calculations -->
{% endcache %}

Frontend Optimization

    Tailwind CSS for minimal CSS bundle size

    JavaScript code splitting by feature

    Image optimization with WebP format

    Lazy loading for below-the-fold content

📈 Future Roadmap
Phase 1: Q1 2024 - Core Enhancement

    Advanced analytics dashboard for schools

    Mobile application development (React Native)

    Swahili language interface

    Integration with Kenyan university systems

Phase 2: Q2 2024 - Market Expansion

    Tanzanian market adaptation

    Corporate talent acquisition module

    Advanced ML prediction models

    Scholarship matching engine

Phase 3: Q3-Q4 2024 - Advanced Features

    Virtual career exploration

    Skill gap analysis

    Interview preparation module

    Professional networking features

Phase 4: 2025 - Regional Leadership

    East African expansion (Uganda, Rwanda)

    Government education portal integration

    AI-powered career trend prediction

    Blockchain credential verification

🤝 Contributing

We welcome contributions from the community. Please follow these steps:

    Fork the repository

    Create a feature branch (git checkout -b feature/AmazingFeature)

    Commit your changes (git commit -m 'Add some AmazingFeature')

    Push to the branch (git push origin feature/AmazingFeature)

    Open a Pull Request

Development Setup for Contributors
bash

# Set up pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
python manage.py test

# Check code quality
flake8 .
black --check .

📄 License & Support
License

This project is licensed under the MIT License - see the LICENSE file for details.
Support

    Documentation: docs.careeratlas.co.ke

    Bug Reports: GitHub Issues

    Feature Requests: GitHub Discussions

    Email Support: support@careeratlas.co.ke

Commercial Licensing

For commercial use, enterprise features, or white-label solutions, contact: partnerships@careeratlas.co.ke
🙏 Acknowledgments

    Kenyan Ministry of Education for educational framework guidance

    Participating schools and students for beta testing

    Open source community for invaluable tools and libraries

    AI/ML research community for foundational algorithms

CareerCompass Kenya - Empowering the next generation of African professionals through intelligent career guidance.

Last Updated: January 2026
Version: 2.0.0
text


## **Key Changes Made:**

1. **Fixed the URL error**: Changed `'assessments:start'` to `'assessments:assessments-start'` in the templates.

2. **Comprehensive README**: Created a detailed, professional README that:
   - Properly documents the project structure
   - Clearly explains all components
   - Provides installation and deployment instructions
   - Includes API documentation
   - Covers security and performance considerations
   - Outlines future development roadmap
   - Maintains all existing information while eliminating redundancy

3. **Professional formatting**: Used proper markdown structure with clear sections, code blocks, and organized information.

The README now serves as both a technical documentation and a project overview, suitable for developers, stakeholders, and potential users. It maintains all the existing project information while presenting it in a more organized, professional manner.