from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from pathlib import Path
import aiofiles
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.meeting import Meeting, Transcript, Summary, ActionItem, Speaker
from ..schemas.meeting import (
    MeetingCreate, MeetingUpdate, Meeting as MeetingSchema, MeetingList,
    TranscriptResponse, SummaryResponse, ActionItemResponse, SpeakerResponse,
    ProcessingStatus
)
from ..routers.auth import get_current_active_user
from ..core.config import settings
from ..services import AudioProcessor, TranscriptionService, SummarizationService, SpeakerDiarization
from ..services.export_service import ExportService

router = APIRouter()

# Initialize services (singleton pattern could be used here)
audio_processor = AudioProcessor()
transcription_service = TranscriptionService()
summarization_service = SummarizationService()
speaker_diarization = SpeakerDiarization()
export_service = ExportService()

@router.post("/upload", response_model=MeetingSchema)
async def upload_meeting_file(
    background_tasks: BackgroundTasks,
    title: str,
    description: Optional[str] = None,
    language: str = "en",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process meeting audio/video file."""
    
    # Validate file format
    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    if file_extension not in settings.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(settings.SUPPORTED_FORMATS)}"
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_path = Path(settings.UPLOAD_DIR) / "audio" / f"{file_id}.{file_extension}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create meeting record
        meeting = Meeting(
            title=title,
            description=description,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file.size,
            file_format=file_extension,
            language=language,
            user_id=current_user.id,
            status="uploaded"
        )
        
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        
        # Start background processing
        background_tasks.add_task(process_meeting_audio, meeting.id, str(file_path), db)
        
        return meeting
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_meeting_audio(meeting_id: int, file_path: str, db: Session):
    """Background task to process uploaded audio file."""
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return
        
        # Update status to processing
        meeting.status = "processing"
        meeting.processing_progress = 10
        db.commit()
        
        # Step 1: Audio preprocessing
        processed_audio_path, audio_metadata = audio_processor.process_audio_file(file_path)
        meeting.duration = audio_metadata.get("processed_duration")
        meeting.processing_progress = 25
        db.commit()
        
        # Step 2: Speaker diarization
        diarization_result = speaker_diarization.diarize_speakers(processed_audio_path)
        
        # Save speaker information
        for speaker_label in diarization_result["speakers"]:
            speaker_stats = diarization_result["speaker_stats"].get(speaker_label, {})
            speaker = Speaker(
                meeting_id=meeting.id,
                speaker_label=speaker_label,
                total_speaking_time=speaker_stats.get("total_time"),
                word_count=0,  # Will be updated after transcription
            )
            db.add(speaker)
        
        meeting.speaker_count = diarization_result["num_speakers"]
        meeting.processing_progress = 50
        db.commit()
        
        # Step 3: Transcription with speaker information
        if diarization_result["segments"]:
            transcript_result = transcription_service.transcribe_with_speaker_timestamps(
                processed_audio_path, diarization_result["segments"]
            )
        else:
            transcript_result = transcription_service.transcribe_audio(
                processed_audio_path, language=meeting.language
            )
        
        # Save transcript
        transcript = Transcript(
            meeting_id=meeting.id,
            full_text=transcript_result["full_text"],
            segments=transcript_result.get("segments", []),
            confidence_score=transcript_result.get("confidence_score"),
            word_count=transcript_result["word_count"],
            language_detected=transcript_result.get("language_detected")
        )
        db.add(transcript)
        
        meeting.word_count = transcript_result["word_count"]
        meeting.processing_progress = 75
        db.commit()
        
        # Step 4: AI Summarization
        meeting_context = {
            "title": meeting.title,
            "date": meeting.created_at.isoformat(),
            "participants": meeting.participants or []
        }
        
        summary_result = summarization_service.generate_meeting_summary(
            transcript_result["full_text"], meeting_context
        )
        
        # Save summary
        summary = Summary(
            meeting_id=meeting.id,
            executive_summary=summary_result["executive_summary"],
            key_points=summary_result.get("key_points", []),
            decisions_made=summary_result.get("decisions_made", []),
            brief_summary=summary_result.get("brief_summary"),
            detailed_summary=summary_result.get("detailed_summary"),
            model_used=summary_result.get("model_used"),
            confidence_score=summary_result.get("confidence_score"),
            generation_time=summary_result.get("generation_time")
        )
        db.add(summary)
        db.commit()
        
        # Step 5: Extract action items
        action_items = summarization_service.extract_action_items(
            transcript_result["full_text"], summary_result
        )
        
        for item_data in action_items:
            action_item = ActionItem(
                meeting_id=meeting.id,
                description=item_data["description"],
                assignee=item_data.get("assignee"),
                due_date=item_data.get("due_date"),
                priority=item_data.get("priority", "medium"),
                context=item_data.get("context"),
                confidence_score=item_data.get("confidence_score"),
                extracted_by=item_data.get("extracted_by", "ai")
            )
            db.add(action_item)
        
        # Final update
        meeting.status = "completed"
        meeting.processing_progress = 100
        meeting.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Update meeting status to failed
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            db.commit()
        print(f"Processing failed for meeting {meeting_id}: {str(e)}")

@router.get("/", response_model=List[MeetingList])
def get_meetings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's meetings with pagination and filtering."""
    query = db.query(Meeting).filter(Meeting.user_id == current_user.id)
    
    if status:
        query = query.filter(Meeting.status == status)
    
    meetings = query.order_by(Meeting.created_at.desc()).offset(skip).limit(limit).all()
    return meetings

@router.get("/{meeting_id}", response_model=MeetingSchema)
def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific meeting details."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return meeting

@router.put("/{meeting_id}", response_model=MeetingSchema)
def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update meeting metadata."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Update fields
    for field, value in meeting_update.dict(exclude_unset=True).items():
        setattr(meeting, field, value)
    
    meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(meeting)
    
    return meeting

@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete meeting and associated files."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete associated file
    try:
        file_path = Path(meeting.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Delete from database (cascade will handle related records)
    db.delete(meeting)
    db.commit()
    
    return {"message": "Meeting deleted successfully"}

@router.get("/{meeting_id}/status", response_model=ProcessingStatus)
def get_processing_status(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting processing status."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Estimate completion time for processing meetings
    estimated_completion = None
    if meeting.status == "processing" and meeting.duration:
        # Rough estimate based on processing progress
        remaining_progress = 100 - meeting.processing_progress
        estimated_time = (meeting.duration * 0.1) * (remaining_progress / 100)
        estimated_completion = datetime.utcnow().timestamp() + estimated_time
    
    return ProcessingStatus(
        status=meeting.status,
        progress=meeting.processing_progress,
        message=f"Processing step {meeting.processing_progress}/100",
        estimated_completion=estimated_completion
    )

@router.get("/{meeting_id}/transcript", response_model=TranscriptResponse)
def get_meeting_transcript(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting transcript."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return transcript

@router.get("/{meeting_id}/summary", response_model=SummaryResponse)
def get_meeting_summary(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting summary."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return summary

@router.get("/{meeting_id}/action-items", response_model=List[ActionItemResponse])
def get_meeting_action_items(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting action items."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    return action_items

@router.get("/{meeting_id}/speakers", response_model=List[SpeakerResponse])
def get_meeting_speakers(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting speakers."""
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    speakers = db.query(Speaker).filter(Speaker.meeting_id == meeting_id).all()
    return speakers

@router.get("/{meeting_id}/export/pdf")
def export_meeting_pdf(
    meeting_id: int,
    include_transcript: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export meeting as PDF report."""
    # Get meeting data
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get related data
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    speakers = db.query(Speaker).filter(Speaker.meeting_id == meeting_id).all()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Convert to dictionaries
    meeting_data = {
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "created_at": meeting.created_at,
        "meeting_date": meeting.meeting_date,
        "duration": meeting.duration,
        "status": meeting.status,
        "language": meeting.language,
        "participants": meeting.participants,
        "file_format": meeting.file_format,
        "file_size": meeting.file_size
    }
    
    transcript_data = {
        "id": transcript.id,
        "full_text": transcript.full_text,
        "segments": transcript.segments,
        "word_count": transcript.word_count,
        "language_detected": transcript.language_detected,
        "confidence_score": transcript.confidence_score
    }
    
    summary_data = summary.__dict__ if summary else {}
    action_items_data = [item.__dict__ for item in action_items]
    speakers_data = [speaker.__dict__ for speaker in speakers]
    
    # Generate PDF
    if include_transcript:
        pdf_bytes = export_service.export_meeting_report_pdf(
            meeting_data, transcript_data, summary_data, action_items_data, speakers_data
        )
    else:
        pdf_bytes = export_service.export_transcript_only_pdf(meeting_data, transcript_data)
    
    # Return as file response
    filename = f"meeting_{meeting_id}_{meeting.title.replace(' ', '_')}.pdf"
    
    return FileResponse(
        path=None,
        media_type='application/pdf',
        filename=filename,
        content=pdf_bytes
    )

@router.get("/{meeting_id}/export/docx")
def export_meeting_docx(
    meeting_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export meeting as DOCX report."""
    # Get meeting data
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get related data
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    summary = db.query(Summary).filter(Summary.meeting_id == meeting_id).first()
    action_items = db.query(ActionItem).filter(ActionItem.meeting_id == meeting_id).all()
    speakers = db.query(Speaker).filter(Speaker.meeting_id == meeting_id).all()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Convert to dictionaries
    meeting_data = {
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "created_at": meeting.created_at,
        "meeting_date": meeting.meeting_date,
        "duration": meeting.duration,
        "status": meeting.status,
        "language": meeting.language,
        "participants": meeting.participants,
        "file_format": meeting.file_format,
        "file_size": meeting.file_size
    }
    
    transcript_data = {
        "id": transcript.id,
        "full_text": transcript.full_text,
        "segments": transcript.segments,
        "word_count": transcript.word_count,
        "language_detected": transcript.language_detected,
        "confidence_score": transcript.confidence_score
    }
    
    summary_data = summary.__dict__ if summary else {}
    action_items_data = [item.__dict__ for item in action_items]
    speakers_data = [speaker.__dict__ for speaker in speakers]
    
    # Generate DOCX
    docx_bytes = export_service.export_meeting_report_docx(
        meeting_data, transcript_data, summary_data, action_items_data, speakers_data
    )
    
    # Return as file response
    filename = f"meeting_{meeting_id}_{meeting.title.replace(' ', '_')}.docx"
    
    return FileResponse(
        path=None,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=filename,
        content=docx_bytes
    )