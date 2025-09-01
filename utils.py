import PyPDF2
from typing import List, Dict, Tuple
import re

def load_pdf(file_path: str, return_page_info: bool = False) -> str or Tuple[str, List[Dict]]:
    """Load PDF and optionally return page information for citations"""
    text = ""
    page_info = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                text += page_text
                
                if return_page_info:
                    page_info.append({
                        'page': page_num,
                        'content': page_text
                    })
                    
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return ("", []) if return_page_info else ""
    
    if return_page_info:
        return text, page_info
    return text

def load_txt(file_path: str) -> str:
    """Load text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading TXT: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence ending within the last 100 characters
            last_period = text.rfind('.', start, end)
            last_exclaim = text.rfind('!', start, end)
            last_question = text.rfind('?', start, end)
            
            sentence_end = max(last_period, last_exclaim, last_question)
            
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - chunk_overlap
        
        if start >= len(text):
            break
    
    return chunks

def highlight_text_in_pdf(text: str, highlight_phrase: str) -> str:
    """Highlight specific phrases in text (for display purposes)"""
    if not highlight_phrase:
        return text
    
    # Simple highlighting - wrap matched text in markdown
    pattern = re.compile(re.escape(highlight_phrase), re.IGNORECASE)
    return pattern.sub(f"**{highlight_phrase}**", text)

def create_citation(source_docs: List[Dict]) -> str:
    """Create citation string from source documents"""
    citations = []
    seen = set()
    
    for doc in source_docs:
        metadata = doc.metadata
        source = metadata.get('source', 'Unknown')
        page = metadata.get('page_number', 'Unknown')
        
        citation_key = f"{source}_{page}"
        if citation_key not in seen:
            citations.append(f"{source} (Page {page})")
            seen.add(citation_key)
    
    return "; ".join(citations)

def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extract key phrases from text for highlighting"""
    # Simple key phrase extraction
    sentences = text.split('.')
    phrases = []
    
    for sentence in sentences[:max_phrases]:
        sentence = sentence.strip()
        if len(sentence) > 20 and len(sentence) < 100:
            phrases.append(sentence)
    
    return phrases