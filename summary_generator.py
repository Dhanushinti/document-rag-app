import streamlit as st
import io
from datetime import datetime
from typing import Dict, List, Any
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class SummaryGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkgreen
        ))
    
    def generate_downloadable_summary(self, qa_responses: List[Dict[str, Any]], 
                                    document_metadata: Dict[str, Any],
                                    executive_summary: str) -> io.BytesIO:
        """Generate a comprehensive PDF summary"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Document Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Generation info
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        story.append(Paragraph(executive_summary, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Document Overview
        story.append(Paragraph("Document Overview", self.styles['CustomHeading']))
        
        doc_data = []
        for file_id, metadata in document_metadata.items():
            doc_data.append([
                metadata.get('filename', 'Unknown'),
                metadata.get('file_type', 'Unknown'),
                str(metadata.get('total_chunks', 0)),
                metadata.get('upload_time', '')[:10] if metadata.get('upload_time') else 'Unknown'
            ])
        
        if doc_data:
            doc_table = Table([['Filename', 'Type', 'Chunks', 'Upload Date']] + doc_data)
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(doc_table)
            story.append(Spacer(1, 20))
        
        # Q&A Section
        if qa_responses:
            story.append(Paragraph("Questions and Answers", self.styles['CustomHeading']))
            
            for i, qa in enumerate(qa_responses, 1):
                story.append(Paragraph(f"Q{i}: {qa.get('question', '')}", 
                                     self.styles['Heading3']))
                story.append(Paragraph(f"Answer: {qa.get('answer', '')}", 
                                     self.styles['Normal']))
                
                if qa.get('citations'):
                    story.append(Paragraph(f"Sources: {qa.get('citations', '')}", 
                                         self.styles['Italic']))
                
                story.append(Spacer(1, 15))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def create_markdown_summary(self, qa_responses: List[Dict[str, Any]], 
                               document_metadata: Dict[str, Any],
                               executive_summary: str) -> str:
        """Generate markdown summary"""
        
        markdown = f"""# Document Analysis Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{executive_summary}

## Document Overview

"""
        
        for file_id, metadata in document_metadata.items():
            markdown += f"- **{metadata.get('filename', 'Unknown')}** ({metadata.get('file_type', 'Unknown')})\n"
            markdown += f"  - Chunks: {metadata.get('total_chunks', 0)}\n"
            markdown += f"  - Upload Date: {metadata.get('upload_time', '')[:10] if metadata.get('upload_time') else 'Unknown'}\n\n"
        
        if qa_responses:
            markdown += "## Questions and Answers\n\n"
            
            for i, qa in enumerate(qa_responses, 1):
                markdown += f"### Q{i}: {qa.get('question', '')}\n\n"
                markdown += f"**Answer:** {qa.get('answer', '')}\n\n"
                
                if qa.get('citations'):
                    markdown += f"**Sources:** {qa.get('citations', '')}\n\n"
                
                markdown += "---\n\n"
        
        return markdown
    
    def export_conversation_json(self, conversation_history: List[Dict[str, Any]], 
                                document_metadata: Dict[str, Any]) -> str:
        """Export conversation history as JSON"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'document_metadata': document_metadata,
            'conversation_history': conversation_history
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)

class StreamlitDownloader:
    @staticmethod
    def create_download_button(content: Any, filename: str, mime_type: str, 
                             button_text: str, key: str = None):
        """Create a streamlit download button"""
        return st.download_button(
            label=button_text,
            data=content,
            file_name=filename,
            mime=mime_type,
            key=key
        )
    
    @staticmethod
    def create_pdf_download(summary_generator: SummaryGenerator, 
                           qa_responses: List[Dict[str, Any]], 
                           document_metadata: Dict[str, Any],
                           executive_summary: str):
        """Create PDF download button"""
        
        try:
            pdf_buffer = summary_generator.generate_downloadable_summary(
                qa_responses, document_metadata, executive_summary
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_analysis_report_{timestamp}.pdf"
            
            return StreamlitDownloader.create_download_button(
                content=pdf_buffer.getvalue(),
                filename=filename,
                mime_type="application/pdf",
                button_text="📄 Download PDF Report",
                key="pdf_download"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            return False
    
    @staticmethod
    def create_markdown_download(summary_generator: SummaryGenerator, 
                                qa_responses: List[Dict[str, Any]], 
                                document_metadata: Dict[str, Any],
                                executive_summary: str):
        """Create Markdown download button"""
        
        try:
            markdown_content = summary_generator.create_markdown_summary(
                qa_responses, document_metadata, executive_summary
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_analysis_report_{timestamp}.md"
            
            return StreamlitDownloader.create_download_button(
                content=markdown_content,
                filename=filename,
                mime_type="text/markdown",
                button_text="📝 Download Markdown Report",
                key="md_download"
            )
        except Exception as e:
            st.error(f"Error generating Markdown: {str(e)}")
            return False