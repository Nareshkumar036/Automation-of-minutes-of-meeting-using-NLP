# 🎙️ Meeting Minutes AI - Automated Transcription and Summarization System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)

*Transform your meetings into actionable insights with AI-powered transcription and intelligent summarization*

</div>

## 🌟 Overview

Meeting Minutes AI is a comprehensive solution that automates the entire process of meeting documentation. Upload audio or video files, and get professionally formatted meeting minutes with transcripts, summaries, action items, and speaker analytics—all powered by advanced AI.

## ✨ Key Features

### 🎯 Core Functionality
- **🎤 Multi-format Audio Processing** - Supports WAV, MP3, FLAC, M4A, OGG, WebM
- **🧠 AI-Powered Transcription** - Using OpenAI Whisper models for high accuracy
- **👥 Speaker Diarization** - Identifies and separates different speakers
- **📝 Intelligent Summarization** - GPT-powered or local transformer models
- **🎯 Action Item Extraction** - Automatically identifies tasks and assignments
- **🔍 Advanced Search** - Full-text search with highlighting and keyword extraction

### 📊 Analytics & Reporting
- **📈 Meeting Analytics** - Duration, word count, speaker statistics
- **🎨 Interactive Dashboards** - Visual insights into meeting patterns
- **📋 Export Options** - Professional PDF and DOCX reports
- **🗂️ Data Export** - JSON and CSV formats for further analysis

### 🔐 Security & Management
- **🔒 User Authentication** - JWT-based secure authentication
- **👤 Multi-user Support** - Individual user workspaces
- **🌍 Multi-language Support** - 19+ languages supported
- **☁️ Scalable Architecture** - Microservices with Docker deployment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM (for AI models)
- 10GB+ storage space

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/meeting-minutes-ai.git
cd meeting-minutes-ai
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (add your API keys)
nano .env
```

### 3. Launch with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### 4. Access the Application
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost/docs
- **Health Check**: http://localhost/health

## 📋 API Documentation

### Authentication
```bash
# Register new user
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password"}'

# Login
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password"
```

### Meeting Upload
```bash
# Upload meeting file
curl -X POST "http://localhost/api/v1/meetings/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@meeting.mp3" \
  -F "title=Team Standup" \
  -F "description=Daily team meeting"
```

### Export Meeting
```bash
# Export as PDF
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/export/pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o meeting_report.pdf

# Export as DOCX
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/export/docx" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o meeting_report.docx
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Frontend    │    │      Nginx      │    │    Backend      │
│   (React SPA)   │◄──►│  (Load Balancer │◄──►│   (FastAPI)     │
│                 │    │   Static Files) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐              │
                       │     Redis       │◄─────────────┤
                       │   (Caching &    │              │
                       │   Task Queue)   │              │
                       └─────────────────┘              │
                                                        │
                       ┌─────────────────┐              │
                       │   PostgreSQL    │◄─────────────┘
                       │   (Database)    │
                       └─────────────────┘

                       ┌─────────────────┐
                       │ Celery Workers  │
                       │ (Background     │
                       │  Processing)    │
                       └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Celery** - Background task processing
- **Redis** - Caching and task queue
- **PostgreSQL** - Primary database

### AI & Machine Learning
- **OpenAI Whisper** - Speech-to-text transcription
- **Transformers** - Hugging Face models
- **pyannote.audio** - Speaker diarization
- **OpenAI GPT** - Text summarization
- **librosa** - Audio processing

### Document Generation
- **ReportLab** - PDF generation
- **python-docx** - DOCX generation
- **Jinja2** - Template rendering

### Deployment
- **Docker** - Containerization
- **Nginx** - Reverse proxy and static files
- **Docker Compose** - Multi-service orchestration

## 📁 Project Structure

```
meeting-minutes-ai/
├── backend/                 # FastAPI backend application
│   ├── core/               # Core configuration and utilities
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic and AI services
│   └── main.py            # Application entry point
├── frontend/               # React frontend (to be implemented)
├── docker-compose.yml      # Multi-service deployment
├── Dockerfile             # Backend container definition
├── nginx.conf             # Nginx configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | sqlite:///./meeting_minutes.db |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 |
| `SECRET_KEY` | JWT signing key | - |
| `OPENAI_API_KEY` | OpenAI API key for GPT models | - |
| `PYANNOTE_ACCESS_TOKEN` | Pyannote.audio access token | - |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | 500000000 |

### Supported Audio Formats
- WAV, MP3, FLAC, M4A, OGG, WebM
- Maximum file size: 500MB
- Recommended: 16kHz sample rate

## 📊 Performance & Scalability

### Processing Times (approximate)
- **Audio Upload**: ~1-2 seconds
- **Transcription**: ~0.1x real-time (10min audio = 1min processing)
- **Summarization**: ~30-60 seconds
- **Export Generation**: ~5-10 seconds

### Resource Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ (for AI models)
- **Storage**: 10GB+ for application and models
- **GPU**: Optional, improves transcription speed by 3x

## 🔍 Advanced Features

### Search Capabilities
```python
# Search across all meetings
GET /api/v1/transcription/search?query=project&case_sensitive=false

# Search within specific meeting
GET /api/v1/transcription/{meeting_id}/search?query=deadline

# Get highlighted transcript
GET /api/v1/transcription/{meeting_id}/highlight?query=action
```

### Analytics Endpoints
```python
# Meeting overview
GET /api/v1/analytics/overview?days=30

# Duration analysis
GET /api/v1/analytics/duration-analysis?days=7

# Action items analysis
GET /api/v1/analytics/action-items-analysis?days=30
```

## 🚀 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Run backend tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend backend/tests/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.meetingminutes.ai](https://docs.meetingminutes.ai)
- **Issues**: [GitHub Issues](https://github.com/your-org/meeting-minutes-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/meeting-minutes-ai/discussions)
- **Email**: support@meetingminutes.ai

## 🙏 Acknowledgments

- OpenAI for Whisper speech recognition
- Hugging Face for transformer models
- Pyannote.audio for speaker diarization
- FastAPI and the Python community

---

<div align="center">

**⭐ If you find this project useful, please give it a star! ⭐**

Made with ❤️ by the Meeting Minutes AI Team

</div>
