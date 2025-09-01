import os
import tempfile
from datetime import datetime
from typing import List, Dict, Tuple, Any
import streamlit as st
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from utils import load_pdf, load_txt, chunk_text
import uuid
import json

class DocumentProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        
    def process_document(self, uploaded_file, file_id: str = None) -> Tuple[bool, str, Dict]:
        """Process a single document and return success status, message, and metadata"""
        try:
            if file_id is None:
                file_id = str(uuid.uuid4())
                
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract text based on file type
            if uploaded_file.name.endswith('.pdf'):
                text, page_info = load_pdf(tmp_path, return_page_info=True)
            elif uploaded_file.name.endswith('.txt'):
                text = load_txt(tmp_path)
                page_info = [{"page": 1, "content": text}]
            else:
                os.unlink(tmp_path)
                return False, "Unsupported file type. Please upload PDF or TXT files.", {}
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            # Check if text was extracted
            if not text.strip():
                return False, "No text could be extracted from the file.", {}
            
            # Chunk the text with metadata
            chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
            
            # Create document metadata
            doc_metadata = {
                'file_id': file_id,
                'filename': uploaded_file.name,
                'file_type': uploaded_file.name.split('.')[-1],
                'upload_time': datetime.now().isoformat(),
                'total_chunks': len(chunks),
                'page_info': page_info,
                'summary': self._generate_summary(text[:3000])  # Generate summary from first 3000 chars
            }
            
            # Create documents with enhanced metadata
            documents = []
            for i, chunk in enumerate(chunks):
                # Find which page this chunk belongs to
                page_num = self._find_page_number(chunk, page_info)
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'source': uploaded_file.name,
                        'file_id': file_id,
                        'chunk_id': i,
                        'page_number': page_num,
                        'file_type': uploaded_file.name.split('.')[-1]
                    }
                )
                documents.append(doc)
            
            return True, f"Document processed! Created {len(chunks)} chunks.", {
                'documents': documents,
                'metadata': doc_metadata
            }
            
        except Exception as e:
            return False, f"Error processing document: {str(e)}", {}
    
    def _generate_summary(self, text_sample: str) -> str:
        """Generate a quick summary of the document"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.3
            )
            
            prompt = f"""Generate a concise executive summary (3-4 sentences) of the following document content:

{text_sample}

Summary:"""
            
            response = llm.invoke(prompt)
            return response.content
        except:
            return "Summary generation failed - document content available for querying."
    
    def _find_page_number(self, chunk: str, page_info: List[Dict]) -> int:
        """Find which page a chunk belongs to"""
        for page in page_info:
            if chunk[:100] in page['content']:
                return page['page']
        return 1
    
    def process_multiple_documents(self, uploaded_files) -> Tuple[bool, str, Dict]:
        """Process multiple documents at once"""
        all_documents = []
        all_metadata = {}
        success_count = 0
        
        for uploaded_file in uploaded_files:
            file_id = str(uuid.uuid4())
            success, message, result = self.process_document(uploaded_file, file_id)
            
            if success:
                all_documents.extend(result['documents'])
                all_metadata[file_id] = result['metadata']
                success_count += 1
        
        if success_count > 0:
            return True, f"Processed {success_count}/{len(uploaded_files)} documents successfully.", {
                'documents': all_documents,
                'metadata': all_metadata
            }
        else:
            return False, "Failed to process any documents.", {}