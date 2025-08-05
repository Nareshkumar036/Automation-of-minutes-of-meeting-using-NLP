from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import calendar

from ..database import get_db
from ..models.user import User
from ..models.meeting import Meeting, Transcript, Summary, ActionItem, Speaker
from ..schemas.meeting import MeetingStats
from ..routers.auth import get_current_active_user

router = APIRouter()

@router.get("/overview", response_model=MeetingStats)
def get_analytics_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics overview for the specified period."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get user's meetings in the period
    meetings_query = db.query(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    )
    
    # Basic statistics
    total_meetings = meetings_query.count()
    completed_meetings = meetings_query.filter(Meeting.status == "completed").all()
    
    # Duration statistics
    total_duration = sum(m.duration or 0 for m in completed_meetings)
    average_meeting_length = total_duration / len(completed_meetings) if completed_meetings else 0
    
    # Transcript statistics
    total_words_transcribed = sum(m.word_count or 0 for m in completed_meetings)
    
    # Action items statistics
    action_items_query = db.query(ActionItem).join(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    )
    
    total_action_items = action_items_query.count()
    completed_action_items = action_items_query.filter(
        ActionItem.status == "completed"
    ).count()
    
    # Speaker analytics
    speaker_analytics = get_speaker_analytics(current_user.id, start_date, end_date, db)
    
    # Monthly breakdown
    monthly_stats = get_monthly_statistics(current_user.id, start_date, end_date, db)
    
    return MeetingStats(
        total_meetings=total_meetings,
        total_duration=total_duration,
        average_meeting_length=average_meeting_length,
        total_words_transcribed=total_words_transcribed,
        total_action_items=total_action_items,
        completed_action_items=completed_action_items,
        speaker_analytics=speaker_analytics,
        monthly_stats=monthly_stats
    )

@router.get("/meetings-by-status")
def get_meetings_by_status(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting counts grouped by status."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    status_counts = db.query(
        Meeting.status,
        func.count(Meeting.id).label('count')
    ).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    ).group_by(Meeting.status).all()
    
    return {
        "period_days": days,
        "status_breakdown": [
            {"status": status, "count": count}
            for status, count in status_counts
        ]
    }

@router.get("/meeting-frequency")
def get_meeting_frequency(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get meeting frequency over time."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Group by date
    daily_counts = db.query(
        func.date(Meeting.created_at).label('date'),
        func.count(Meeting.id).label('count')
    ).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    ).group_by(func.date(Meeting.created_at)).all()
    
    return {
        "period_days": days,
        "daily_frequency": [
            {"date": date.isoformat(), "count": count}
            for date, count in daily_counts
        ]
    }

@router.get("/duration-analysis")
def get_duration_analysis(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze meeting duration patterns."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    meetings = db.query(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date,
        Meeting.status == "completed",
        Meeting.duration.isnot(None)
    ).all()
    
    if not meetings:
        return {"message": "No completed meetings with duration data found"}
    
    durations = [m.duration for m in meetings if m.duration]
    
    # Calculate statistics
    total_duration = sum(durations)
    average_duration = total_duration / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    # Duration buckets
    buckets = {
        "0-15min": 0,
        "15-30min": 0,
        "30-60min": 0,
        "60-90min": 0,
        "90min+": 0
    }
    
    for duration in durations:
        duration_minutes = duration / 60
        if duration_minutes <= 15:
            buckets["0-15min"] += 1
        elif duration_minutes <= 30:
            buckets["15-30min"] += 1
        elif duration_minutes <= 60:
            buckets["30-60min"] += 1
        elif duration_minutes <= 90:
            buckets["60-90min"] += 1
        else:
            buckets["90min+"] += 1
    
    return {
        "period_days": days,
        "total_meetings": len(meetings),
        "total_duration_hours": round(total_duration / 3600, 2),
        "average_duration_minutes": round(average_duration / 60, 1),
        "min_duration_minutes": round(min_duration / 60, 1),
        "max_duration_minutes": round(max_duration / 60, 1),
        "duration_distribution": buckets
    }

@router.get("/action-items-analysis")
def get_action_items_analysis(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze action items patterns."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    action_items = db.query(ActionItem).join(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    ).all()
    
    if not action_items:
        return {"message": "No action items found in the specified period"}
    
    # Status breakdown
    status_counts = {}
    for item in action_items:
        status = item.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Priority breakdown
    priority_counts = {}
    for item in action_items:
        priority = item.priority
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Assignee breakdown (top 10)
    assignee_counts = {}
    for item in action_items:
        if item.assignee:
            assignee_counts[item.assignee] = assignee_counts.get(item.assignee, 0) + 1
    
    top_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Completion rate
    completed_count = status_counts.get("completed", 0)
    completion_rate = (completed_count / len(action_items)) * 100 if action_items else 0
    
    return {
        "period_days": days,
        "total_action_items": len(action_items),
        "completion_rate": round(completion_rate, 1),
        "status_breakdown": status_counts,
        "priority_breakdown": priority_counts,
        "top_assignees": [
            {"assignee": assignee, "count": count}
            for assignee, count in top_assignees
        ]
    }

@router.get("/transcript-analytics")
def get_transcript_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze transcript patterns and statistics."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    transcripts = db.query(Transcript).join(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date,
        Meeting.status == "completed"
    ).all()
    
    if not transcripts:
        return {"message": "No transcripts found in the specified period"}
    
    # Word count statistics
    word_counts = [t.word_count for t in transcripts if t.word_count]
    total_words = sum(word_counts)
    average_words = total_words / len(word_counts) if word_counts else 0
    
    # Language breakdown
    language_counts = {}
    for transcript in transcripts:
        lang = transcript.language_detected or "unknown"
        language_counts[lang] = language_counts.get(lang, 0) + 1
    
    # Confidence scores
    confidence_scores = [t.confidence_score for t in transcripts if t.confidence_score]
    average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    return {
        "period_days": days,
        "total_transcripts": len(transcripts),
        "total_words_transcribed": total_words,
        "average_words_per_meeting": round(average_words, 0),
        "average_confidence_score": round(average_confidence, 3) if confidence_scores else None,
        "language_breakdown": language_counts,
        "words_per_minute_estimate": round(total_words / sum(
            m.duration / 60 for m in [t.meeting for t in transcripts] if m.duration
        ), 1) if any(t.meeting.duration for t in transcripts) else None
    }

def get_speaker_analytics(user_id: int, start_date: datetime, end_date: datetime, db: Session) -> Dict[str, Any]:
    """Get speaker analytics for the specified period."""
    
    speakers = db.query(Speaker).join(Meeting).filter(
        Meeting.user_id == user_id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date,
        Meeting.status == "completed"
    ).all()
    
    if not speakers:
        return {"total_speakers": 0, "average_speakers_per_meeting": 0}
    
    # Calculate statistics
    total_speakers = len(set(s.speaker_label for s in speakers))
    meetings_with_speakers = len(set(s.meeting_id for s in speakers))
    average_speakers_per_meeting = total_speakers / meetings_with_speakers if meetings_with_speakers else 0
    
    # Speaking time distribution
    speaker_times = {}
    for speaker in speakers:
        if speaker.total_speaking_time:
            label = speaker.identified_name or speaker.speaker_label
            speaker_times[label] = speaker_times.get(label, 0) + speaker.total_speaking_time
    
    return {
        "total_speakers": total_speakers,
        "average_speakers_per_meeting": round(average_speakers_per_meeting, 1),
        "speaking_time_distribution": speaker_times
    }

def get_monthly_statistics(user_id: int, start_date: datetime, end_date: datetime, db: Session) -> List[Dict[str, Any]]:
    """Get monthly statistics breakdown."""
    
    monthly_data = db.query(
        extract('year', Meeting.created_at).label('year'),
        extract('month', Meeting.created_at).label('month'),
        func.count(Meeting.id).label('meeting_count'),
        func.sum(Meeting.duration).label('total_duration'),
        func.sum(Meeting.word_count).label('total_words')
    ).filter(
        Meeting.user_id == user_id,
        Meeting.created_at >= start_date,
        Meeting.created_at <= end_date
    ).group_by(
        extract('year', Meeting.created_at),
        extract('month', Meeting.created_at)
    ).all()
    
    monthly_stats = []
    for year, month, meeting_count, total_duration, total_words in monthly_data:
        month_name = calendar.month_name[int(month)]
        monthly_stats.append({
            "year": int(year),
            "month": int(month),
            "month_name": month_name,
            "meeting_count": meeting_count,
            "total_duration_hours": round((total_duration or 0) / 3600, 2),
            "total_words": total_words or 0
        })
    
    return sorted(monthly_stats, key=lambda x: (x["year"], x["month"]))

@router.get("/export-data")
def export_analytics_data(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export analytics data in specified format."""
    
    # Get all analytics data
    overview = get_analytics_overview(days, current_user, db)
    meetings_by_status = get_meetings_by_status(days, current_user, db)
    duration_analysis = get_duration_analysis(days, current_user, db)
    action_items_analysis = get_action_items_analysis(days, current_user, db)
    transcript_analytics = get_transcript_analytics(days, current_user, db)
    
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "period_days": days,
        "user_id": current_user.id,
        "overview": overview.dict(),
        "meetings_by_status": meetings_by_status,
        "duration_analysis": duration_analysis,
        "action_items_analysis": action_items_analysis,
        "transcript_analytics": transcript_analytics
    }
    
    if format == "json":
        return export_data
    elif format == "csv":
        # Convert to CSV format (simplified)
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and basic statistics
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Meetings", overview.total_meetings])
        writer.writerow(["Total Duration (hours)", round(overview.total_duration / 3600, 2)])
        writer.writerow(["Average Meeting Length (minutes)", round(overview.average_meeting_length / 60, 1)])
        writer.writerow(["Total Words Transcribed", overview.total_words_transcribed])
        writer.writerow(["Total Action Items", overview.total_action_items])
        writer.writerow(["Completed Action Items", overview.completed_action_items])
        
        csv_content = output.getvalue()
        output.close()
        
        return {"csv_data": csv_content}
    
    return export_data