from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

from .database import engine, Base
from .routers import auth, meetings, transcription, analytics
from .core.config import settings

# Load environment variables
load_dotenv()

# Create upload directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(f"{settings.UPLOAD_DIR}/audio").mkdir(parents=True, exist_ok=True)
Path(f"{settings.UPLOAD_DIR}/exports").mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Meeting Minutes AI Application...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Initialize AI models (will be done lazily)
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Meeting Minutes AI Application...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Meeting Transcription and Summarization System",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(meetings.router, prefix=f"{settings.API_V1_STR}/meetings", tags=["meetings"])
app.include_router(transcription.router, prefix=f"{settings.API_V1_STR}/transcription", tags=["transcription"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])

# Serve static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {
        "message": "Meeting Minutes AI - Automated Transcription and Summarization System",
        "version": settings.VERSION,
        "docs": "/docs",
        "api": f"{settings.API_V1_STR}"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )