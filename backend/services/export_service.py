from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

import io
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

class ExportService:
    """Service for exporting meeting data to various formats."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.darkgreen
        ))
    
    def export_meeting_report_pdf(
        self,
        meeting_data: Dict,
        transcript_data: Dict,
        summary_data: Dict,
        action_items: List[Dict],
        speakers: List[Dict]
    ) -> bytes:
        """Export comprehensive meeting report as PDF."""
        
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story (content)
            story = []
            
            # Title page
            self._add_pdf_title_page(story, meeting_data)
            
            # Executive summary
            self._add_pdf_executive_summary(story, summary_data)
            
            # Meeting details
            self._add_pdf_meeting_details(story, meeting_data, transcript_data, speakers)
            
            # Key points and decisions
            self._add_pdf_key_points(story, summary_data)
            
            # Action items
            self._add_pdf_action_items(story, action_items)
            
            # Full transcript
            self._add_pdf_transcript(story, transcript_data)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info("PDF report generated successfully")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise
    
    def export_meeting_report_docx(
        self,
        meeting_data: Dict,
        transcript_data: Dict,
        summary_data: Dict,
        action_items: List[Dict],
        speakers: List[Dict]
    ) -> bytes:
        """Export comprehensive meeting report as DOCX."""
        
        try:
            # Create document
            doc = Document()
            
            # Title page
            self._add_docx_title_page(doc, meeting_data)
            
            # Executive summary
            self._add_docx_executive_summary(doc, summary_data)
            
            # Meeting details
            self._add_docx_meeting_details(doc, meeting_data, transcript_data, speakers)
            
            # Key points and decisions
            self._add_docx_key_points(doc, summary_data)
            
            # Action items
            self._add_docx_action_items(doc, action_items)
            
            # Full transcript
            self._add_docx_transcript(doc, transcript_data)
            
            # Save to buffer
            buffer = io.BytesIO()
            doc.save(buffer)
            docx_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info("DOCX report generated successfully")
            return docx_bytes
            
        except Exception as e:
            logger.error(f"DOCX generation failed: {str(e)}")
            raise
    
    def export_transcript_only_pdf(self, meeting_data: Dict, transcript_data: Dict) -> bytes:
        """Export transcript-only PDF."""
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Title
            title = Paragraph(f"Meeting Transcript: {meeting_data['title']}", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Meeting info
            meeting_info = f"""
            <b>Date:</b> {meeting_data.get('created_at', 'N/A')}<br/>
            <b>Duration:</b> {self._format_duration(meeting_data.get('duration'))}<br/>
            <b>Word Count:</b> {transcript_data.get('word_count', 0):,} words<br/>
            <b>Language:</b> {transcript_data.get('language_detected', 'N/A')}
            """
            story.append(Paragraph(meeting_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Transcript
            story.append(Paragraph("Full Transcript", self.styles['CustomHeading']))
            
            # Split transcript into paragraphs for better formatting
            transcript_text = transcript_data.get('full_text', '')
            paragraphs = transcript_text.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['Normal']))
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Transcript PDF generation failed: {str(e)}")
            raise
    
    def _add_pdf_title_page(self, story: List, meeting_data: Dict):
        """Add title page to PDF."""
        title = Paragraph(f"Meeting Minutes", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 30))
        
        subtitle = Paragraph(meeting_data['title'], self.styles['Heading1'])
        story.append(subtitle)
        story.append(Spacer(1, 20))
        
        meeting_info = f"""
        <b>Meeting Date:</b> {self._format_datetime(meeting_data.get('meeting_date'))}<br/>
        <b>Created:</b> {self._format_datetime(meeting_data.get('created_at'))}<br/>
        <b>Duration:</b> {self._format_duration(meeting_data.get('duration'))}<br/>
        <b>Status:</b> {meeting_data.get('status', 'N/A')}<br/>
        <b>Language:</b> {meeting_data.get('language', 'en')}
        """
        
        if meeting_data.get('participants'):
            participants_str = ', '.join(meeting_data['participants'])
            meeting_info += f"<br/><b>Participants:</b> {participants_str}"
        
        story.append(Paragraph(meeting_info, self.styles['Normal']))
        story.append(PageBreak())
    
    def _add_pdf_executive_summary(self, story: List, summary_data: Dict):
        """Add executive summary to PDF."""
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        exec_summary = summary_data.get('executive_summary', 'No summary available.')
        story.append(Paragraph(exec_summary, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        if summary_data.get('brief_summary'):
            story.append(Paragraph("Brief Summary", self.styles['CustomSubheading']))
            story.append(Paragraph(summary_data['brief_summary'], self.styles['Normal']))
            story.append(Spacer(1, 20))
    
    def _add_pdf_meeting_details(self, story: List, meeting_data: Dict, transcript_data: Dict, speakers: List[Dict]):
        """Add meeting details section to PDF."""
        story.append(Paragraph("Meeting Details", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        # Statistics table
        stats_data = [
            ['Metric', 'Value'],
            ['Duration', self._format_duration(meeting_data.get('duration'))],
            ['Word Count', f"{transcript_data.get('word_count', 0):,}"],
            ['Speaker Count', str(len(speakers))],
            ['File Format', meeting_data.get('file_format', 'N/A')],
            ['File Size', self._format_file_size(meeting_data.get('file_size', 0))]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Speakers section
        if speakers:
            story.append(Paragraph("Speakers", self.styles['CustomSubheading']))
            speaker_data = [['Speaker', 'Speaking Time', 'Word Count']]
            
            for speaker in speakers:
                speaking_time = self._format_duration(speaker.get('total_speaking_time'))
                word_count = str(speaker.get('word_count', 0))
                speaker_name = speaker.get('identified_name', speaker.get('speaker_label', 'Unknown'))
                speaker_data.append([speaker_name, speaking_time, word_count])
            
            speaker_table = Table(speaker_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            speaker_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(speaker_table)
            story.append(Spacer(1, 20))
    
    def _add_pdf_key_points(self, story: List, summary_data: Dict):
        """Add key points and decisions to PDF."""
        # Key Points
        key_points = summary_data.get('key_points', [])
        if key_points:
            story.append(Paragraph("Key Discussion Points", self.styles['CustomHeading']))
            story.append(Spacer(1, 12))
            
            for i, point in enumerate(key_points, 1):
                story.append(Paragraph(f"{i}. {point}", self.styles['Normal']))
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 20))
        
        # Decisions
        decisions = summary_data.get('decisions_made', [])
        if decisions:
            story.append(Paragraph("Decisions Made", self.styles['CustomHeading']))
            story.append(Spacer(1, 12))
            
            for i, decision in enumerate(decisions, 1):
                story.append(Paragraph(f"{i}. {decision}", self.styles['Normal']))
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 20))
    
    def _add_pdf_action_items(self, story: List, action_items: List[Dict]):
        """Add action items to PDF."""
        if not action_items:
            return
        
        story.append(Paragraph("Action Items", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        # Action items table
        action_data = [['Description', 'Assignee', 'Priority', 'Status', 'Due Date']]
        
        for item in action_items:
            due_date = self._format_datetime(item.get('due_date')) if item.get('due_date') else 'Not set'
            action_data.append([
                item.get('description', '')[:100] + ('...' if len(item.get('description', '')) > 100 else ''),
                item.get('assignee', 'Unassigned'),
                item.get('priority', 'Medium'),
                item.get('status', 'Pending'),
                due_date
            ])
        
        action_table = Table(action_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(action_table)
        story.append(Spacer(1, 20))
    
    def _add_pdf_transcript(self, story: List, transcript_data: Dict):
        """Add full transcript to PDF."""
        story.append(PageBreak())
        story.append(Paragraph("Full Transcript", self.styles['CustomHeading']))
        story.append(Spacer(1, 12))
        
        transcript_text = transcript_data.get('full_text', 'No transcript available.')
        
        # Split into paragraphs for better formatting
        paragraphs = transcript_text.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), self.styles['Normal']))
                story.append(Spacer(1, 12))
    
    def _add_docx_title_page(self, doc: Document, meeting_data: Dict):
        """Add title page to DOCX."""
        title = doc.add_heading('Meeting Minutes', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(meeting_data['title'], level=1)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Spacer
        
        meeting_info = doc.add_paragraph()
        meeting_info.add_run(f"Meeting Date: ").bold = True
        meeting_info.add_run(self._format_datetime(meeting_data.get('meeting_date')))
        meeting_info.add_run('\n')
        
        meeting_info.add_run("Created: ").bold = True
        meeting_info.add_run(self._format_datetime(meeting_data.get('created_at')))
        meeting_info.add_run('\n')
        
        meeting_info.add_run("Duration: ").bold = True
        meeting_info.add_run(self._format_duration(meeting_data.get('duration')))
        meeting_info.add_run('\n')
        
        meeting_info.add_run("Status: ").bold = True
        meeting_info.add_run(meeting_data.get('status', 'N/A'))
        
        if meeting_data.get('participants'):
            meeting_info.add_run('\n')
            meeting_info.add_run("Participants: ").bold = True
            meeting_info.add_run(', '.join(meeting_data['participants']))
        
        doc.add_page_break()
    
    def _add_docx_executive_summary(self, doc: Document, summary_data: Dict):
        """Add executive summary to DOCX."""
        doc.add_heading('Executive Summary', level=1)
        
        exec_summary = summary_data.get('executive_summary', 'No summary available.')
        doc.add_paragraph(exec_summary)
        
        if summary_data.get('brief_summary'):
            doc.add_heading('Brief Summary', level=2)
            doc.add_paragraph(summary_data['brief_summary'])
    
    def _add_docx_meeting_details(self, doc: Document, meeting_data: Dict, transcript_data: Dict, speakers: List[Dict]):
        """Add meeting details to DOCX."""
        doc.add_heading('Meeting Details', level=1)
        
        # Add statistics table
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Metric'
        hdr_cells[1].text = 'Value'
        
        stats = [
            ('Duration', self._format_duration(meeting_data.get('duration'))),
            ('Word Count', f"{transcript_data.get('word_count', 0):,}"),
            ('Speaker Count', str(len(speakers))),
            ('File Format', meeting_data.get('file_format', 'N/A')),
            ('File Size', self._format_file_size(meeting_data.get('file_size', 0)))
        ]
        
        for metric, value in stats:
            row_cells = table.add_row().cells
            row_cells[0].text = metric
            row_cells[1].text = value
        
        # Speakers section
        if speakers:
            doc.add_paragraph()
            doc.add_heading('Speakers', level=2)
            
            speaker_table = doc.add_table(rows=1, cols=3)
            speaker_table.style = 'Table Grid'
            
            hdr_cells = speaker_table.rows[0].cells
            hdr_cells[0].text = 'Speaker'
            hdr_cells[1].text = 'Speaking Time'
            hdr_cells[2].text = 'Word Count'
            
            for speaker in speakers:
                row_cells = speaker_table.add_row().cells
                row_cells[0].text = speaker.get('identified_name', speaker.get('speaker_label', 'Unknown'))
                row_cells[1].text = self._format_duration(speaker.get('total_speaking_time'))
                row_cells[2].text = str(speaker.get('word_count', 0))
    
    def _add_docx_key_points(self, doc: Document, summary_data: Dict):
        """Add key points and decisions to DOCX."""
        # Key Points
        key_points = summary_data.get('key_points', [])
        if key_points:
            doc.add_heading('Key Discussion Points', level=1)
            
            for point in key_points:
                p = doc.add_paragraph(point, style='List Bullet')
        
        # Decisions
        decisions = summary_data.get('decisions_made', [])
        if decisions:
            doc.add_heading('Decisions Made', level=1)
            
            for decision in decisions:
                p = doc.add_paragraph(decision, style='List Bullet')
    
    def _add_docx_action_items(self, doc: Document, action_items: List[Dict]):
        """Add action items to DOCX."""
        if not action_items:
            return
        
        doc.add_heading('Action Items', level=1)
        
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Description'
        hdr_cells[1].text = 'Assignee'
        hdr_cells[2].text = 'Priority'
        hdr_cells[3].text = 'Status'
        hdr_cells[4].text = 'Due Date'
        
        for item in action_items:
            row_cells = table.add_row().cells
            row_cells[0].text = item.get('description', '')
            row_cells[1].text = item.get('assignee', 'Unassigned')
            row_cells[2].text = item.get('priority', 'Medium')
            row_cells[3].text = item.get('status', 'Pending')
            row_cells[4].text = self._format_datetime(item.get('due_date')) if item.get('due_date') else 'Not set'
    
    def _add_docx_transcript(self, doc: Document, transcript_data: Dict):
        """Add full transcript to DOCX."""
        doc.add_page_break()
        doc.add_heading('Full Transcript', level=1)
        
        transcript_text = transcript_data.get('full_text', 'No transcript available.')
        doc.add_paragraph(transcript_text)
    
    def _format_datetime(self, dt) -> str:
        """Format datetime for display."""
        if dt is None:
            return 'N/A'
        
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_duration(self, duration_seconds) -> str:
        """Format duration in seconds to human readable format."""
        if not duration_seconds:
            return 'N/A'
        
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _format_file_size(self, size_bytes) -> str:
        """Format file size in bytes to human readable format."""
        if not size_bytes:
            return 'N/A'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"