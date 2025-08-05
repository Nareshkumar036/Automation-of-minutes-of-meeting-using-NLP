# 🚀 Quick Start Guide - Meeting Minutes AI

## Prerequisites

- **Docker & Docker Compose** (required)
- **8GB+ RAM** for AI models
- **10GB+ storage** for application and models

## 🎯 1-Minute Setup

### 1. Clone and Configure
```bash
git clone https://github.com/your-org/meeting-minutes-ai.git
cd meeting-minutes-ai
cp .env.example .env
```

### 2. Add API Keys (Optional but Recommended)
Edit `.env` file and add:
```env
OPENAI_API_KEY=your-openai-api-key-here
PYANNOTE_ACCESS_TOKEN=your-pyannote-token-here
```

### 3. Start Application
```bash
./run.sh start
```

### 4. Access the Application
- **Web Interface**: http://localhost
- **API Docs**: http://localhost/docs
- **Health Check**: http://localhost/health

## 🎙️ First Meeting Upload

### Using the API

1. **Register a User**
```bash
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "email": "demo@example.com", 
    "password": "password123",
    "full_name": "Demo User"
  }'
```

2. **Login**
```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=password123"
```

Save the `access_token` from the response.

3. **Upload Audio File**
```bash
curl -X POST "http://localhost/api/v1/meetings/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@your_meeting.mp3" \
  -F "title=Team Meeting" \
  -F "description=Weekly team standup"
```

4. **Check Processing Status**
```bash
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

5. **Get Results**
```bash
# Get transcript
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/transcript" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get summary
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get action items
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/action-items" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

6. **Export Reports**
```bash
# Export as PDF
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/export/pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o meeting_report.pdf

# Export as DOCX
curl -X GET "http://localhost/api/v1/meetings/{meeting_id}/export/docx" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o meeting_report.docx
```

## 📊 Key Features to Try

### 🔍 Search Functionality
```bash
# Search across all meetings
curl -X GET "http://localhost/api/v1/transcription/search?query=project" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Search within specific meeting
curl -X GET "http://localhost/api/v1/transcription/{meeting_id}/search?query=deadline" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 📈 Analytics
```bash
# Get overview analytics
curl -X GET "http://localhost/api/v1/analytics/overview?days=30" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get meeting frequency
curl -X GET "http://localhost/api/v1/analytics/meeting-frequency?days=7" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎯 Supported Audio Formats

- **WAV** (recommended)
- **MP3** 
- **FLAC**
- **M4A**
- **OGG**
- **WebM**

**Maximum file size**: 500MB  
**Recommended**: 16kHz sample rate, mono

## 🛠️ Management Commands

```bash
# Check application status
./run.sh status

# View logs
./run.sh logs

# View specific service logs
./run.sh logs backend

# Restart application
./run.sh restart

# Stop application
./run.sh stop

# Create backup
./run.sh backup

# Update application
./run.sh update
```

## 📝 Sample Meeting Processing Flow

1. **Upload** → Audio file uploaded and saved
2. **Preprocessing** → Audio cleaned and optimized (25% progress)
3. **Speaker Diarization** → Speakers identified (50% progress)
4. **Transcription** → Speech converted to text (75% progress)
5. **AI Analysis** → Summary and action items generated (100% progress)

**Typical processing time**: ~0.1x real-time (10-minute audio = 1 minute processing)

## 🔧 Configuration Tips

### For Better Performance
- Add OpenAI API key for better summaries
- Use GPU-enabled Docker for faster processing
- Increase RAM allocation for Docker

### For Production Use
- Change default passwords in `.env`
- Set up SSL certificates
- Configure backup strategy
- Monitor disk usage

## 🆘 Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check Docker status
docker --version
docker-compose --version

# Check logs
./run.sh logs
```

**Processing stuck at 0%**
```bash
# Check background workers
docker-compose logs celery-worker

# Restart workers
docker-compose restart celery-worker
```

**Audio upload fails**
- Check file size (max 500MB)
- Verify format is supported
- Ensure sufficient disk space

**No audio detected**
- Verify audio file has speech content
- Check audio quality/volume
- Try different audio format

### Getting Help

- **Logs**: `./run.sh logs`
- **Status**: `./run.sh status`
- **Documentation**: http://localhost/docs
- **Health Check**: http://localhost/health

## 🎉 What's Next?

After your first successful meeting processing:

1. **Explore Analytics** - View meeting patterns and insights
2. **Try Search** - Find specific topics across meetings
3. **Export Reports** - Generate professional meeting minutes
4. **Customize** - Adjust settings and configurations
5. **Scale** - Add more workers for higher throughput

---

🎙️ **Happy transcribing!** Your meetings will never be the same.