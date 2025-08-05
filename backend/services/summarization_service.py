import openai
from transformers import pipeline
import re
from typing import Dict, List, Optional, Tuple
import logging
import time
from datetime import datetime, timedelta

from ..core.config import settings

logger = logging.getLogger(__name__)

class SummarizationService:
    """AI-powered summarization and action item extraction service."""
    
    def __init__(self):
        """Initialize summarization service."""
        self.openai_client = None
        self.local_summarizer = None
        self._setup_services()
    
    def _setup_services(self):
        """Setup AI services for summarization."""
        # Setup OpenAI if API key is available
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        
        # Setup local transformer model as fallback
        try:
            self.local_summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if settings.DEBUG else -1  # Use GPU if available
            )
            logger.info("Local summarization model loaded")
        except Exception as e:
            logger.warning(f"Failed to load local summarization model: {str(e)}")
    
    def generate_meeting_summary(self, transcript: str, meeting_context: Dict = None) -> Dict:
        """
        Generate comprehensive meeting summary.
        
        Args:
            transcript: Full meeting transcript
            meeting_context: Additional context about the meeting
            
        Returns:
            Dictionary with different summary types and metadata
        """
        start_time = time.time()
        
        try:
            logger.info("Generating meeting summary")
            
            # Use OpenAI if available, otherwise fallback to local model
            if self.openai_client and settings.OPENAI_API_KEY:
                summary_data = self._generate_openai_summary(transcript, meeting_context)
            else:
                summary_data = self._generate_local_summary(transcript)
            
            # Add processing metadata
            summary_data.update({
                "generation_time": time.time() - start_time,
                "word_count_original": len(transcript.split()),
                "compression_ratio": len(summary_data["executive_summary"].split()) / len(transcript.split())
            })
            
            logger.info(f"Summary generated in {summary_data['generation_time']:.2f}s")
            return summary_data
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            raise
    
    def _generate_openai_summary(self, transcript: str, context: Dict = None) -> Dict:
        """Generate summary using OpenAI GPT models."""
        try:
            # Prepare context information
            context_str = ""
            if context:
                context_str = f"""
                Meeting Title: {context.get('title', 'N/A')}
                Date: {context.get('date', 'N/A')}
                Participants: {', '.join(context.get('participants', []))}
                """
            
            # Create prompt for comprehensive summary
            prompt = f"""
            Please analyze the following meeting transcript and provide a comprehensive summary:
            
            {context_str}
            
            TRANSCRIPT:
            {transcript}
            
            Please provide:
            1. Executive Summary (2-3 sentences)
            2. Key Discussion Points (bullet points)
            3. Decisions Made (bullet points)
            4. Action Items with assignees and deadlines if mentioned
            5. Brief Summary (1 sentence)
            6. Detailed Summary (1-2 paragraphs)
            
            Format your response as JSON with the following structure:
            {{
                "executive_summary": "...",
                "key_points": ["...", "..."],
                "decisions_made": ["...", "..."],
                "action_items_raw": ["...", "..."],
                "brief_summary": "...",
                "detailed_summary": "..."
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            import json
            summary_data = json.loads(response.choices[0].message.content)
            summary_data["model_used"] = "gpt-3.5-turbo"
            
            return summary_data
            
        except Exception as e:
            logger.error(f"OpenAI summary generation failed: {str(e)}")
            # Fallback to local model
            return self._generate_local_summary(transcript)
    
    def _generate_local_summary(self, transcript: str) -> Dict:
        """Generate summary using local transformer model."""
        try:
            # Split transcript into chunks if too long
            max_chunk_length = 1024
            chunks = self._split_text_into_chunks(transcript, max_chunk_length)
            
            # Summarize each chunk
            chunk_summaries = []
            for chunk in chunks:
                if len(chunk.strip()) > 50:  # Only summarize substantial chunks
                    result = self.local_summarizer(
                        chunk,
                        max_length=150,
                        min_length=30,
                        do_sample=False
                    )
                    chunk_summaries.append(result[0]['summary_text'])
            
            # Combine chunk summaries
            combined_summary = " ".join(chunk_summaries)
            
            # Generate final summary from combined chunks
            if len(combined_summary) > max_chunk_length:
                final_result = self.local_summarizer(
                    combined_summary,
                    max_length=200,
                    min_length=50,
                    do_sample=False
                )
                executive_summary = final_result[0]['summary_text']
            else:
                executive_summary = combined_summary
            
            # Extract key points using simple NLP
            key_points = self._extract_key_points(transcript)
            
            return {
                "executive_summary": executive_summary,
                "brief_summary": executive_summary.split('.')[0] + '.',
                "detailed_summary": combined_summary,
                "key_points": key_points,
                "decisions_made": self._extract_decisions(transcript),
                "action_items_raw": self._extract_action_items_basic(transcript),
                "model_used": "facebook/bart-large-cnn"
            }
            
        except Exception as e:
            logger.error(f"Local summary generation failed: {str(e)}")
            # Return basic summary as last resort
            return self._generate_basic_summary(transcript)
    
    def _split_text_into_chunks(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract key discussion points using simple keyword analysis."""
        # Common meeting keywords and phrases
        key_phrases = [
            r"we decided", r"decision", r"conclusion", r"agreed",
            r"important", r"critical", r"issue", r"problem",
            r"next steps", r"follow up", r"action", r"proposal"
        ]
        
        key_points = []
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                for phrase in key_phrases:
                    if re.search(phrase, sentence, re.IGNORECASE):
                        key_points.append(sentence)
                        break
        
        return key_points[:10]  # Return top 10
    
    def _extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions made during the meeting."""
        decision_patterns = [
            r"we decided.*?[.!?]",
            r"decision.*?[.!?]", 
            r"agreed.*?[.!?]",
            r"concluded.*?[.!?]"
        ]
        
        decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            decisions.extend(matches)
        
        return list(set(decisions))[:5]  # Remove duplicates, return top 5
    
    def _extract_action_items_basic(self, transcript: str) -> List[str]:
        """Extract basic action items using pattern matching."""
        action_patterns = [
            r"will.*?[.!?]",
            r"should.*?[.!?]",
            r"need to.*?[.!?]",
            r"action.*?[.!?]",
            r"follow up.*?[.!?]",
            r"next steps.*?[.!?]"
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            action_items.extend(matches)
        
        return list(set(action_items))[:8]  # Remove duplicates, return top 8
    
    def _generate_basic_summary(self, transcript: str) -> Dict:
        """Generate very basic summary as last resort."""
        # Extract first and last few sentences
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) >= 4:
            summary = ". ".join(sentences[:2] + sentences[-2:])
        else:
            summary = ". ".join(sentences)
        
        return {
            "executive_summary": summary,
            "brief_summary": sentences[0] if sentences else "Meeting transcript processed.",
            "detailed_summary": summary,
            "key_points": sentences[:5],
            "decisions_made": [],
            "action_items_raw": [],
            "model_used": "basic_extraction"
        }
    
    def extract_action_items(self, transcript: str, summary_data: Dict = None) -> List[Dict]:
        """
        Extract structured action items from transcript and summary.
        
        Returns:
            List of action item dictionaries with assignee, due_date, priority
        """
        try:
            logger.info("Extracting action items")
            
            action_items = []
            
            # Get raw action items from summary or extract directly
            if summary_data and "action_items_raw" in summary_data:
                raw_items = summary_data["action_items_raw"]
            else:
                raw_items = self._extract_action_items_basic(transcript)
            
            # Process each raw action item
            for item in raw_items:
                processed_item = self._process_action_item(item, transcript)
                if processed_item:
                    action_items.append(processed_item)
            
            logger.info(f"Extracted {len(action_items)} action items")
            return action_items
            
        except Exception as e:
            logger.error(f"Action item extraction failed: {str(e)}")
            return []
    
    def _process_action_item(self, raw_item: str, full_transcript: str) -> Optional[Dict]:
        """Process raw action item into structured format."""
        try:
            # Extract assignee
            assignee = self._extract_assignee(raw_item)
            
            # Extract due date
            due_date = self._extract_due_date(raw_item)
            
            # Determine priority
            priority = self._determine_priority(raw_item)
            
            # Find context in transcript
            context = self._find_context(raw_item, full_transcript)
            
            return {
                "description": raw_item.strip(),
                "assignee": assignee,
                "due_date": due_date,
                "priority": priority,
                "context": context,
                "confidence_score": 0.7,  # Basic confidence score
                "extracted_by": "ai"
            }
            
        except Exception as e:
            logger.warning(f"Failed to process action item: {str(e)}")
            return None
    
    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extract assignee from action item text."""
        # Look for common patterns
        patterns = [
            r"([A-Z][a-z]+)\s+will",
            r"([A-Z][a-z]+)\s+should",
            r"([A-Z][a-z]+)\s+needs?\s+to"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from action item text."""
        # Look for date patterns
        date_patterns = [
            r"by\s+(\w+\s+\d+)",
            r"before\s+(\w+\s+\d+)",
            r"next\s+week",
            r"tomorrow",
            r"end\s+of\s+week"
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # For now, return a generic future date
                # In production, you'd want more sophisticated date parsing
                return datetime.now() + timedelta(weeks=1)
        
        return None
    
    def _determine_priority(self, text: str) -> str:
        """Determine priority level from action item text."""
        urgent_words = ["urgent", "critical", "asap", "immediately", "priority"]
        high_words = ["important", "soon", "quickly"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in urgent_words):
            return "urgent"
        elif any(word in text_lower for word in high_words):
            return "high"
        else:
            return "medium"
    
    def _find_context(self, action_item: str, transcript: str, context_window: int = 200) -> str:
        """Find surrounding context for action item in transcript."""
        # Find approximate location of action item in transcript
        action_words = action_item.split()[:3]  # First few words
        
        for i, word in enumerate(action_words):
            pos = transcript.lower().find(word.lower())
            if pos != -1:
                start = max(0, pos - context_window)
                end = min(len(transcript), pos + len(action_item) + context_window)
                return transcript[start:end].strip()
        
        return ""