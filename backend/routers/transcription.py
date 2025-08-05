from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import re

from ..database import get_db
from ..models.user import User
from ..models.meeting import Meeting, Transcript
from ..routers.auth import get_current_active_user

router = APIRouter()

@router.get("/search")
def search_transcripts(
    query: str = Query(..., min_length=2),
    meeting_id: Optional[int] = Query(None),
    case_sensitive: bool = Query(False),
    whole_words_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search transcripts across user's meetings."""
    
    # Base query - get user's meetings with transcripts
    base_query = db.query(Meeting, Transcript).join(
        Transcript, Meeting.id == Transcript.meeting_id
    ).filter(Meeting.user_id == current_user.id)
    
    # Filter by specific meeting if provided
    if meeting_id:
        base_query = base_query.filter(Meeting.id == meeting_id)
    
    meetings_with_transcripts = base_query.all()
    
    search_results = []
    
    for meeting, transcript in meetings_with_transcripts:
        # Perform text search
        matches = find_text_matches(
            text=transcript.full_text,
            query=query,
            case_sensitive=case_sensitive,
            whole_words_only=whole_words_only,
            include_context=True
        )
        
        # Also search in segments if available
        segment_matches = []
        if transcript.segments:
            for segment in transcript.segments:
                segment_text = segment.get("text", "") if isinstance(segment, dict) else ""
                segment_match_results = find_text_matches(
                    text=segment_text,
                    query=query,
                    case_sensitive=case_sensitive,
                    whole_words_only=whole_words_only,
                    include_context=False
                )
                
                if segment_match_results:
                    segment_matches.append({
                        "segment": segment,
                        "matches": segment_match_results
                    })
        
        if matches or segment_matches:
            search_results.append({
                "meeting": {
                    "id": meeting.id,
                    "title": meeting.title,
                    "created_at": meeting.created_at,
                    "duration": meeting.duration
                },
                "transcript_matches": matches,
                "segment_matches": segment_matches,
                "total_matches": len(matches) + sum(len(sm["matches"]) for sm in segment_matches)
            })
    
    # Sort by relevance (number of matches)
    search_results.sort(key=lambda x: x["total_matches"], reverse=True)
    
    # Apply pagination
    total_results = len(search_results)
    paginated_results = search_results[skip:skip + limit]
    
    return {
        "results": paginated_results,
        "total": total_results,
        "query": query,
        "page_info": {
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total_results
        }
    }

@router.get("/{meeting_id}/search")
def search_meeting_transcript(
    meeting_id: int,
    query: str = Query(..., min_length=2),
    case_sensitive: bool = Query(False),
    whole_words_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search within a specific meeting's transcript."""
    
    # Verify meeting ownership
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Search in full text
    full_text_matches = find_text_matches(
        text=transcript.full_text,
        query=query,
        case_sensitive=case_sensitive,
        whole_words_only=whole_words_only,
        include_context=True,
        context_length=100
    )
    
    # Search in segments with timestamps
    segment_matches = []
    if transcript.segments:
        for i, segment in enumerate(transcript.segments):
            segment_text = segment.get("text", "") if isinstance(segment, dict) else ""
            matches = find_text_matches(
                text=segment_text,
                query=query,
                case_sensitive=case_sensitive,
                whole_words_only=whole_words_only,
                include_context=False
            )
            
            if matches:
                segment_matches.append({
                    "segment_index": i,
                    "segment": segment,
                    "matches": matches
                })
    
    return {
        "meeting_id": meeting_id,
        "meeting_title": meeting.title,
        "query": query,
        "full_text_matches": full_text_matches,
        "segment_matches": segment_matches,
        "total_matches": len(full_text_matches) + len(segment_matches),
        "highlighted_text": highlight_text_matches(
            transcript.full_text, query, case_sensitive, whole_words_only
        )
    }

@router.get("/{meeting_id}/highlight")
def get_highlighted_transcript(
    meeting_id: int,
    query: str = Query(..., min_length=2),
    case_sensitive: bool = Query(False),
    whole_words_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transcript with highlighted search terms."""
    
    # Verify meeting ownership
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Highlight the full text
    highlighted_text = highlight_text_matches(
        transcript.full_text, query, case_sensitive, whole_words_only
    )
    
    # Highlight segments if available
    highlighted_segments = []
    if transcript.segments:
        for segment in transcript.segments:
            segment_copy = segment.copy() if isinstance(segment, dict) else {}
            if "text" in segment_copy:
                segment_copy["highlighted_text"] = highlight_text_matches(
                    segment_copy["text"], query, case_sensitive, whole_words_only
                )
            highlighted_segments.append(segment_copy)
    
    return {
        "meeting_id": meeting_id,
        "query": query,
        "highlighted_full_text": highlighted_text,
        "highlighted_segments": highlighted_segments,
        "original_transcript": {
            "id": transcript.id,
            "full_text": transcript.full_text,
            "word_count": transcript.word_count,
            "confidence_score": transcript.confidence_score
        }
    }

def find_text_matches(
    text: str, 
    query: str, 
    case_sensitive: bool = False,
    whole_words_only: bool = False,
    include_context: bool = True,
    context_length: int = 50
) -> List[dict]:
    """Find all matches of query in text with optional context."""
    
    # Prepare search pattern
    pattern_query = re.escape(query)
    
    if whole_words_only:
        pattern_query = r'\b' + pattern_query + r'\b'
    
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(pattern_query, flags)
    
    matches = []
    
    for match in pattern.finditer(text):
        match_info = {
            "start": match.start(),
            "end": match.end(),
            "matched_text": match.group(),
        }
        
        if include_context:
            # Get context around the match
            context_start = max(0, match.start() - context_length)
            context_end = min(len(text), match.end() + context_length)
            
            context = text[context_start:context_end]
            
            # Mark the relative position of the match within the context
            relative_start = match.start() - context_start
            relative_end = match.end() - context_start
            
            match_info.update({
                "context": context,
                "context_start": context_start,
                "context_end": context_end,
                "relative_match_start": relative_start,
                "relative_match_end": relative_end
            })
        
        matches.append(match_info)
    
    return matches

def highlight_text_matches(
    text: str,
    query: str,
    case_sensitive: bool = False,
    whole_words_only: bool = False,
    highlight_tag: str = "mark"
) -> str:
    """Highlight all occurrences of query in text with HTML tags."""
    
    if not query or not text:
        return text
    
    # Prepare search pattern
    pattern_query = re.escape(query)
    
    if whole_words_only:
        pattern_query = r'\b' + pattern_query + r'\b'
    
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(pattern_query, flags)
    
    # Replace matches with highlighted version
    def replace_match(match):
        return f'<{highlight_tag}>{match.group()}</{highlight_tag}>'
    
    highlighted_text = pattern.sub(replace_match, text)
    
    return highlighted_text

@router.get("/{meeting_id}/keywords")
def extract_keywords(
    meeting_id: int,
    max_keywords: int = Query(20, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extract keywords from meeting transcript."""
    
    # Verify meeting ownership
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Simple keyword extraction using word frequency
    keywords = extract_keywords_from_text(transcript.full_text, max_keywords)
    
    return {
        "meeting_id": meeting_id,
        "meeting_title": meeting.title,
        "keywords": keywords,
        "extraction_method": "frequency_based"
    }

def extract_keywords_from_text(text: str, max_keywords: int = 20) -> List[dict]:
    """Extract keywords using simple frequency analysis."""
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'within',
        'this', 'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'we',
        'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
        'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
        'themselves', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
        'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now',
        'would', 'could', 'should', 'might', 'must', 'shall', 'may', 'said',
        'say', 'says', 'go', 'goes', 'went', 'get', 'gets', 'got', 'come',
        'comes', 'came', 'like', 'likes', 'liked', 'well', 'also', 'back',
        'know', 'think', 'see', 'want', 'use', 'work', 'way', 'make', 'take',
        'time', 'people', 'year', 'day', 'good', 'new', 'first', 'last',
        'long', 'great', 'little', 'right', 'old', 'different', 'small',
        'large', 'next', 'early', 'young', 'important', 'few', 'public',
        'bad', 'same', 'able'
    }
    
    # Clean and tokenize text
    import re
    from collections import Counter
    
    # Remove punctuation and convert to lowercase
    cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = cleaned_text.split()
    
    # Filter out stop words and short words
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word not in stop_words
    ]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get top keywords
    top_words = word_counts.most_common(max_keywords)
    
    # Calculate total words for frequency percentage
    total_filtered_words = len(filtered_words)
    
    keywords = []
    for word, count in top_words:
        keywords.append({
            "word": word,
            "frequency": count,
            "percentage": round((count / total_filtered_words) * 100, 2) if total_filtered_words > 0 else 0
        })
    
    return keywords