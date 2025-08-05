from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    meeting_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    language: str = "en"

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    meeting_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    language: Optional[str] = None

class MeetingList(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    duration: Optional[float] = None
    word_count: Optional[int] = None
    speaker_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class Meeting(MeetingBase):
    id: int
    status: str
    processing_progress: int
    original_filename: str
    file_size: int
    file_format: str
    duration: Optional[float] = None
    word_count: Optional[int] = None
    speaker_count: Optional[int] = None
    average_speaking_time: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: int
    
    class Config:
        from_attributes = True

class TranscriptSegment(BaseModel):
    text: str
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None

class TranscriptResponse(BaseModel):
    id: int
    full_text: str
    segments: Optional[List[TranscriptSegment]] = None
    confidence_score: Optional[float] = None
    word_count: Optional[int] = None
    language_detected: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    id: int
    executive_summary: str
    key_points: Optional[List[str]] = None
    decisions_made: Optional[List[str]] = None
    brief_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActionItemResponse(BaseModel):
    id: int
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str
    status: str
    mentioned_at_timestamp: Optional[float] = None
    context: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SpeakerResponse(BaseModel):
    id: int
    speaker_label: str
    identified_name: Optional[str] = None
    total_speaking_time: Optional[float] = None
    word_count: Optional[int] = None
    average_words_per_minute: Optional[float] = None
    
    class Config:
        from_attributes = True

class MeetingStats(BaseModel):
    total_meetings: int
    total_duration: float
    average_meeting_length: float
    total_words_transcribed: int
    total_action_items: int
    completed_action_items: int
    speaker_analytics: Dict[str, Any]
    monthly_stats: List[Dict[str, Any]]

class ProcessingStatus(BaseModel):
    status: str
    progress: int
    message: Optional[str] = None
    estimated_completion: Optional[datetime] = None