from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_format = Column(String(10), nullable=False)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    processing_progress = Column(Integer, default=0)  # 0-100
    
    # Meeting metadata
    meeting_date = Column(DateTime(timezone=True), nullable=True)
    participants = Column(JSON, nullable=True)  # List of participant names
    language = Column(String(10), default="en")
    
    # Analytics
    word_count = Column(Integer, nullable=True)
    speaker_count = Column(Integer, nullable=True)
    average_speaking_time = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="meetings")
    transcript = relationship("Transcript", back_populates="meeting", uselist=False)
    summary = relationship("Summary", back_populates="meeting", uselist=False)
    action_items = relationship("ActionItem", back_populates="meeting")
    speakers = relationship("Speaker", back_populates="meeting")
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title={self.title}, status={self.status})>"

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    full_text = Column(Text, nullable=False)
    
    # Segmented transcript with timestamps
    segments = Column(JSON, nullable=True)  # List of {text, start_time, end_time, speaker_id}
    
    # Processing metadata
    confidence_score = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    language_detected = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    
    # Relationships
    meeting = relationship("Meeting", back_populates="transcript")
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, meeting_id={self.meeting_id}, word_count={self.word_count})>"

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    executive_summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)  # List of key discussion points
    decisions_made = Column(JSON, nullable=True)  # List of decisions
    
    # Different summary types
    brief_summary = Column(Text, nullable=True)  # Short version
    detailed_summary = Column(Text, nullable=True)  # Detailed version
    
    # AI metadata
    model_used = Column(String(100), nullable=True)
    generation_time = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    
    # Relationships
    meeting = relationship("Meeting", back_populates="summary")
    
    def __repr__(self):
        return f"<Summary(id={self.id}, meeting_id={self.meeting_id})>"

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    assignee = Column(String(255), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    
    # Context information
    mentioned_at_timestamp = Column(Float, nullable=True)  # When mentioned in meeting
    context = Column(Text, nullable=True)  # Surrounding context from transcript
    
    # Confidence and metadata
    confidence_score = Column(Float, nullable=True)
    extracted_by = Column(String(50), default="ai")  # ai, manual
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    
    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")
    
    def __repr__(self):
        return f"<ActionItem(id={self.id}, assignee={self.assignee}, status={self.status})>"

class Speaker(Base):
    __tablename__ = "speakers"
    
    id = Column(Integer, primary_key=True, index=True)
    speaker_label = Column(String(50), nullable=False)  # SPEAKER_00, SPEAKER_01, etc.
    identified_name = Column(String(255), nullable=True)  # Manually identified name
    
    # Voice characteristics (for future matching)
    voice_profile = Column(JSON, nullable=True)
    
    # Speaking statistics
    total_speaking_time = Column(Float, nullable=True)  # Total seconds spoken
    word_count = Column(Integer, nullable=True)
    average_words_per_minute = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    
    # Relationships
    meeting = relationship("Meeting", back_populates="speakers")
    
    def __repr__(self):
        return f"<Speaker(id={self.id}, label={self.speaker_label}, name={self.identified_name})>"